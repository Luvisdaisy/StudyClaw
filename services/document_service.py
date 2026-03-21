import os
import uuid
import hashlib
import asyncio
from typing import Optional, BinaryIO
from pathlib import Path
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader, UnstructuredMarkdownLoader

from database.models import Document, DocumentStatus
from utils.config_handler import chroma_cfg
from model.factory import embedding_model


class DocumentService:
    # Supported file types and their loaders
    LOADERS = {
        "pdf": PyPDFLoader,
        "md": TextLoader,  # Use TextLoader for markdown (unstructured not installed)
        "txt": TextLoader,
    }

    def __init__(self, session: AsyncSession, project_id: uuid.UUID):
        self.session = session
        self.project_id = project_id
        self.data_dir = Path("data/projects") / str(project_id)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Initialize text splitter
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chroma_cfg.get("chunk_size", 200),
            chunk_overlap=chroma_cfg.get("chunk_overlap", 20),
            separators=chroma_cfg.get("separators", ["\n\n", "\n", ".", "!", "?", "。", "！", "？", " ", ""]),
        )

    def _compute_file_hash(self, file_content: bytes) -> str:
        """Compute MD5 hash of file content"""
        return hashlib.md5(file_content).hexdigest()

    def _get_file_type(self, filename: str) -> Optional[str]:
        """Get file type from filename extension"""
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        return ext if ext in self.LOADERS else None

    async def upload_document(self, file_content: bytes, filename: str) -> Optional[Document]:
        """Upload and process a document"""
        file_type = self._get_file_type(filename)
        if not file_type:
            raise ValueError(f"Unsupported file type: {filename}")

        # Compute hash for deduplication
        file_hash = self._compute_file_hash(file_content)

        # Check for duplicate
        existing = await self.session.execute(
            select(Document).where(
                Document.project_id == self.project_id,
                Document.file_hash == file_hash,
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"Document {filename} already exists in this project")

        # Save file to disk
        file_path = self.data_dir / f"{uuid.uuid4()}_{filename}"
        with open(file_path, "wb") as f:
            f.write(file_content)

        # Create document record
        doc = Document(
            id=uuid.uuid4(),
            project_id=self.project_id,
            filename=filename,
            file_path=str(file_path),
            file_type=file_type,
            file_hash=file_hash,
            status=DocumentStatus.PENDING,
        )
        self.session.add(doc)
        await self.session.commit()

        # Process document (this will update status and chunk_count)
        await self._process_document(doc, file_path, file_type)

        # Refresh to get updated values and expire on commit to avoid lazy loading issues
        await self.session.refresh(doc)

        return doc

    def _sync_process_document(self, file_path: str, file_type: str, doc_id: str, project_id: str):
        """Synchronous document processing for running in thread pool"""
        from rag.vector_store import VectorStoreService

        # Load document
        loader_class = self.LOADERS.get(file_type)
        if not loader_class:
            raise ValueError(f"No loader for file type: {file_type}")

        loader = loader_class(file_path)
        documents = loader.load()

        if not documents:
            raise ValueError(f"No content loaded")

        # Split into chunks
        split_docs = self.splitter.split_documents(documents)
        if not split_docs:
            raise ValueError(f"Document splitting resulted in no chunks")

        # Add metadata
        for i, d in enumerate(split_docs):
            d.metadata["document_id"] = doc_id
            d.metadata["project_id"] = project_id
            d.metadata["chunk_index"] = i

        # Add to vector store
        vector_store = VectorStoreService(project_id=uuid.UUID(project_id))
        vector_store.add_documents(split_docs)

        return len(split_docs)

    async def _process_document(self, doc: Document, file_path: Path, file_type: str):
        """Process document: load, split, and add to vector store"""
        try:
            # Update status to processing
            doc.status = DocumentStatus.PROCESSING
            await self.session.flush()
            await self.session.refresh(doc)

            # Run synchronous document processing (direct call, not thread)
            # This is safe because LangChain operations are synchronous
            chunk_count = self._sync_process_document(
                str(file_path),
                file_type,
                str(doc.id),
                str(self.project_id)
            )

            # Update document status
            doc.status = DocumentStatus.COMPLETED
            doc.chunk_count = chunk_count
            await self.session.flush()
            await self.session.commit()

        except Exception as e:
            # Rollback happens automatically when session is closed
            raise e

    async def list_documents(self) -> list[Document]:
        """List all documents in project"""
        result = await self.session.execute(
            select(Document)
            .where(Document.project_id == self.project_id)
            .order_by(Document.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_document(self, document_id: uuid.UUID) -> Optional[Document]:
        """Get document by ID"""
        result = await self.session.execute(
            select(Document).where(
                Document.id == document_id,
                Document.project_id == self.project_id,
            )
        )
        return result.scalar_one_or_none()

    async def delete_document(self, document_id: uuid.UUID) -> bool:
        """Delete document and its file"""
        doc = await self.get_document(document_id)
        if not doc:
            return False

        # Delete file
        file_path = Path(doc.file_path)
        if file_path.exists():
            file_path.unlink()

        # Delete from vector store
        try:
            from rag.vector_store import VectorStoreService

            vector_store = VectorStoreService(project_id=self.project_id)
            vector_store.delete_by_document_id(str(document_id))
        except Exception:
            pass  # Continue even if vector delete fails

        # Delete record
        await self.session.execute(
            delete(Document).where(Document.id == document_id)
        )
        await self.session.commit()
        return True
