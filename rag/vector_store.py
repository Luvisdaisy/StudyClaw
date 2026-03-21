import uuid
from typing import Optional
from langchain_core.documents import Document as LCDocument
from langchain_chroma import Chroma
from utils.config_handler import chroma_cfg
from model.factory import embedding_model


class VectorStoreService:
    """
    Vector store service with project-level isolation.
    Each project has its own Chroma collection named `project_{project_id}`.
    """

    def __init__(self, project_id: Optional[uuid.UUID] = None):
        """
        Initialize VectorStoreService for a specific project.

        Args:
            project_id: UUID of the project. If None, uses default collection from config.
        """
        if project_id:
            collection_name = f"project_{str(project_id)}"
        else:
            collection_name = chroma_cfg.get("collection_name", "default")

        persist_dir = chroma_cfg.get("persist_directory", "chroma_db")
        self._project_id = project_id
        self._collection_name = collection_name

        self.vector_store = Chroma(
            collection_name=collection_name,
            embedding_function=embedding_model,
            persist_directory=persist_dir,
        )

    @property
    def project_id(self) -> Optional[uuid.UUID]:
        return self._project_id

    @property
    def collection_name(self) -> str:
        return self._collection_name

    def get_retriever(self, k: int = None):
        """Get retriever with configurable k value"""
        if k is None:
            k = chroma_cfg.get("k", 3)
        return self.vector_store.as_retriever(
            search_kwargs={"k": k}
        )

    def add_documents(self, documents: list[LCDocument]):
        """Add documents to the vector store"""
        if not documents:
            return
        self.vector_store.add_documents(documents)

    def delete_by_document_id(self, document_id: str):
        """Delete all chunks associated with a document ID"""
        try:
            # Get all IDs with matching document_id in metadata
            collection = self.vector_store._collection
            if collection is None:
                return

            # Get all metadatas and filter
            ids_to_delete = []
            for idx, metadata in enumerate(collection.get(include=["metadatas"])["metadatas"]):
                if metadata and metadata.get("document_id") == document_id:
                    ids_to_delete.append(collection.get(include=[])["ids"][idx])

            if ids_to_delete:
                self.vector_store.delete(ids_to_delete)
        except Exception as e:
            # Log error but don't raise - deletion failure shouldn't block document deletion
            print(f"Warning: Failed to delete vectors for document {document_id}: {e}")

    def delete_all(self):
        """Delete all documents from the collection"""
        self.vector_store.delete(where={})

    def get_collection_stats(self) -> dict:
        """Get statistics about the collection"""
        try:
            collection = self.vector_store._collection
            if collection:
                count = collection.count()
                return {
                    "collection_name": self._collection_name,
                    "document_count": count,
                    "project_id": str(self._project_id) if self._project_id else None,
                }
        except Exception:
            pass
        return {
            "collection_name": self._collection_name,
            "document_count": 0,
            "project_id": str(self._project_id) if self._project_id else None,
        }


# Backward compatibility - default collection service
_default_vector_store = None


def get_default_vector_store() -> VectorStoreService:
    """Get or create the default vector store (for backward compatibility)"""
    global _default_vector_store
    if _default_vector_store is None:
        _default_vector_store = VectorStoreService()
    return _default_vector_store
