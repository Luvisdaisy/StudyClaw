"""Tests for VectorStoreService."""
import uuid
from unittest.mock import MagicMock, patch, AsyncMock
import pytest
from langchain_core.documents import Document as LCDocument

from rag.vector_store import VectorStoreService


class TestVectorStoreServiceInit:
    """Tests for VectorStoreService initialization."""

    def test_init_with_project_id(self):
        """Test initialization with project ID creates correct collection name."""
        project_id = uuid.uuid4()
        service = VectorStoreService(project_id=project_id)

        assert service.project_id == project_id
        assert service.collection_name == f"project_{str(project_id)}"

    def test_init_without_project_id(self):
        """Test initialization without project ID uses default collection."""
        service = VectorStoreService(project_id=None)

        assert service.project_id is None

    @patch("rag.vector_store.Chroma")
    @patch("rag.vector_store.embedding_model")
    def test_collection_name_format(self, mock_embedding, mock_chroma):
        """Test collection name follows expected format."""
        project_id = uuid.uuid4()
        service = VectorStoreService(project_id=project_id)

        mock_chroma.assert_called_once()
        call_kwargs = mock_chroma.call_args.kwargs
        assert call_kwargs["collection_name"] == f"project_{str(project_id)}"


class TestVectorStoreServiceRetriever:
    """Tests for retriever functionality."""

    @patch("rag.vector_store.Chroma")
    @patch("rag.vector_store.embedding_model")
    def test_get_retriever_default_k(self, mock_embedding, mock_chroma_class):
        """Test get_retriever uses default k value from config."""
        mock_vector_store = MagicMock()
        mock_chroma_class.return_value = mock_vector_store

        service = VectorStoreService(project_id=uuid.uuid4())
        retriever = service.get_retriever()

        mock_vector_store.as_retriever.assert_called_once()
        call_kwargs = mock_vector_store.as_retriever.call_args.kwargs
        assert "search_kwargs" in call_kwargs
        assert "k" in call_kwargs["search_kwargs"]

    @patch("rag.vector_store.Chroma")
    @patch("rag.vector_store.embedding_model")
    def test_get_retriever_custom_k(self, mock_embedding, mock_chroma_class):
        """Test get_retriever uses custom k value when provided."""
        mock_vector_store = MagicMock()
        mock_chroma_class.return_value = mock_vector_store

        service = VectorStoreService(project_id=uuid.uuid4())
        retriever = service.get_retriever(k=5)

        call_kwargs = mock_vector_store.as_retriever.call_args.kwargs
        assert call_kwargs["search_kwargs"]["k"] == 5


class TestVectorStoreServiceAddDocuments:
    """Tests for adding documents."""

    @patch("rag.vector_store.Chroma")
    @patch("rag.vector_store.embedding_model")
    def test_add_documents_calls_vector_store(self, mock_embedding, mock_chroma_class):
        """Test add_documents delegates to vector store."""
        mock_vector_store = MagicMock()
        mock_chroma_class.return_value = mock_vector_store

        service = VectorStoreService(project_id=uuid.uuid4())

        docs = [
            LCDocument(page_content="Test content", metadata={"source": "test"}),
        ]
        service.add_documents(docs)

        mock_vector_store.add_documents.assert_called_once_with(docs)

    @patch("rag.vector_store.Chroma")
    @patch("rag.vector_store.embedding_model")
    def test_add_documents_empty_list(self, mock_embedding, mock_chroma_class):
        """Test add_documents with empty list does nothing."""
        mock_vector_store = MagicMock()
        mock_chroma_class.return_value = mock_vector_store

        service = VectorStoreService(project_id=uuid.uuid4())
        service.add_documents([])

        mock_vector_store.add_documents.assert_not_called()


class TestVectorStoreServiceDelete:
    """Tests for deletion operations."""

    @patch("rag.vector_store.Chroma")
    @patch("rag.vector_store.embedding_model")
    def test_delete_by_document_id(self, mock_embedding, mock_chroma_class):
        """Test delete_by_document_id removes all chunks for that document."""
        mock_collection = MagicMock()
        mock_collection.get.return_value = {"ids": ["id1", "id2", "id3"]}
        mock_vector_store = MagicMock()
        mock_vector_store._collection = mock_collection
        mock_chroma_class.return_value = mock_vector_store

        service = VectorStoreService(project_id=uuid.uuid4())
        service.delete_by_document_id("test_doc_id")

        mock_collection.get.assert_called_once()
        call_kwargs = mock_collection.get.call_args.kwargs
        assert call_kwargs["where"] == {"document_id": "test_doc_id"}

        mock_vector_store.delete.assert_called_once_with(["id1", "id2", "id3"])

    @patch("rag.vector_store.Chroma")
    @patch("rag.vector_store.embedding_model")
    def test_delete_by_document_id_no_chunks(self, mock_embedding, mock_chroma_class):
        """Test delete_by_document_id when no chunks exist."""
        mock_collection = MagicMock()
        mock_collection.get.return_value = {"ids": []}
        mock_vector_store = MagicMock()
        mock_vector_store._collection = mock_collection
        mock_chroma_class.return_value = mock_vector_store

        service = VectorStoreService(project_id=uuid.uuid4())
        service.delete_by_document_id("nonexistent_doc_id")

        mock_vector_store.delete.assert_not_called()

    @patch("rag.vector_store.Chroma")
    @patch("rag.vector_store.embedding_model")
    def test_delete_all(self, mock_embedding, mock_chroma_class):
        """Test delete_all removes all documents from collection."""
        mock_vector_store = MagicMock()
        mock_chroma_class.return_value = mock_vector_store

        service = VectorStoreService(project_id=uuid.uuid4())
        service.delete_all()

        mock_vector_store.delete.assert_called_once_with(where={})


class TestVectorStoreServiceStats:
    """Tests for collection statistics."""

    @patch("rag.vector_store.Chroma")
    @patch("rag.vector_store.embedding_model")
    def test_get_collection_stats(self, mock_embedding, mock_chroma_class):
        """Test get_collection_stats returns correct statistics."""
        mock_collection = MagicMock()
        mock_collection.count.return_value = 42
        mock_vector_store = MagicMock()
        mock_vector_store._collection = mock_collection
        mock_chroma_class.return_value = mock_vector_store

        project_id = uuid.uuid4()
        service = VectorStoreService(project_id=project_id)
        stats = service.get_collection_stats()

        assert stats["collection_name"] == f"project_{str(project_id)}"
        assert stats["document_count"] == 42
        assert stats["project_id"] == str(project_id)

    @patch("rag.vector_store.Chroma")
    @patch("rag.vector_store.embedding_model")
    def test_get_collection_stats_no_collection(self, mock_embedding, mock_chroma_class):
        """Test get_collection_stats handles missing collection."""
        mock_vector_store = MagicMock()
        mock_vector_store._collection = None
        mock_chroma_class.return_value = mock_vector_store

        service = VectorStoreService(project_id=uuid.uuid4())
        stats = service.get_collection_stats()

        assert stats["document_count"] == 0
