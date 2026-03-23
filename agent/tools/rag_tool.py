import uuid
import logging
from langchain_core.documents import Document
from langchain_core.tools import tool
from rag.vector_store import VectorStoreService
from utils.prompt_loader import load_rag_prompts

logger = logging.getLogger(__name__)


class RetrievalError(Exception):
    """Raised when document retrieval fails."""
    pass


class ProjectRagService:
    """RAG service for a specific project"""

    def __init__(self, project_id: uuid.UUID):
        self.project_id = project_id
        self.vector_store = VectorStoreService(project_id=project_id)
        self.retriever = self.vector_store.get_retriever()
        self.prompt_text = load_rag_prompts()

    def retrieve_docs(self, query: str, k: int = 3) -> list[Document]:
        """Retrieve relevant documents for a query"""
        self.retriever.search_kwargs["k"] = k
        return self.retriever.invoke(query)

    def format_context(self, query: str) -> str:
        """Retrieve docs and format as context string"""
        docs = self.retrieve_docs(query)
        if not docs:
            return "No relevant documents found."

        context = ""
        for i, doc in enumerate(docs, 1):
            context += f"【参考资料{i}】: {doc.page_content} | 元数据: {doc.metadata}\n"
        return context


# Global registry for project RAG services
_rag_services: dict[str, ProjectRagService] = {}


def get_rag_service(project_id: uuid.UUID) -> ProjectRagService:
    """Get or create RAG service for a project"""
    key = str(project_id)
    if key not in _rag_services:
        _rag_services[key] = ProjectRagService(project_id)
    return _rag_services[key]


def clear_rag_service(project_id: uuid.UUID):
    """Clear RAG service cache when project is deleted"""
    key = str(project_id)
    if key in _rag_services:
        del _rag_services[key]


@tool
def rag_summarize(query: str, project_id: str) -> str:
    """
    Search project documents and provide a summary based on the retrieved context.

    Args:
        query: The user's question or search query
        project_id: The UUID of the project to search in

    Returns:
        A formatted string containing retrieved context and the query response
    """
    try:
        rag_service = get_rag_service(uuid.UUID(project_id))
        context = rag_service.format_context(query)
        return f"检索到的上下文:\n{context}"
    except Exception as e:
        logger.error(f"Document retrieval failed in rag_summarize: {e}", exc_info=True)
        raise RetrievalError(f"Failed to retrieve documents: {e}") from e


@tool
def rag_retrieve(query: str, project_id: str, k: int = 3) -> str:
    """
    Retrieve relevant document chunks for a query without generating a response.

    Args:
        query: The search query
        project_id: The UUID of the project to search in
        k: Number of documents to retrieve (default: 3)

    Returns:
        Formatted string of retrieved document chunks
    """
    try:
        rag_service = get_rag_service(uuid.UUID(project_id))
        docs = rag_service.retrieve_docs(query, k=k)

        if not docs:
            return "No relevant documents found."

        result = f"找到 {len(docs)} 个相关文档:\n\n"
        for i, doc in enumerate(docs, 1):
            result += f"【文档 {i}】\n{doc.page_content}\n"
            result += f"来源: {doc.metadata.get('source', 'unknown')}\n\n"
        return result
    except Exception as e:
        logger.error(f"Document retrieval failed in rag_retrieve: {e}", exc_info=True)
        raise RetrievalError(f"Failed to retrieve documents: {e}") from e
