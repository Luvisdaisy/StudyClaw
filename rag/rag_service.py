import uuid
from typing import Optional
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

from model.factory import chat_model
from rag.vector_store import VectorStoreService
from utils.prompt_loader import load_rag_prompts


class RagService:
    """
    RAG service with project-level support.
    Each project uses its own vector store collection.
    """

    def __init__(self, project_id: Optional[uuid.UUID] = None):
        """
        Initialize RAG service for a specific project.

        Args:
            project_id: UUID of the project. If None, uses default collection.
        """
        self.project_id = project_id
        self.vector_store = VectorStoreService(project_id=project_id)
        self.retriever = self.vector_store.get_retriever()
        self.prompt_text = load_rag_prompts()
        self.prompt_template = PromptTemplate.from_template(self.prompt_text)
        self.model = chat_model
        self.chain = self._init_chain()

    def _init_chain(self):
        """Initialize the RAG chain"""
        chain = self.prompt_template | self.model | StrOutputParser()
        return chain

    def retrieve_docs(self, query: str) -> list[Document]:
        """Retrieve relevant documents"""
        return self.retriever.invoke(query)

    def rag_summarize(self, query: str) -> str:
        """Synchronous RAG summarize"""
        context_docs = self.retrieve_docs(query)
        context = self._format_context(context_docs)

        return self.chain.invoke({
            "input": query,
            "context": context,
        })

    async def arag_summarize(self, query: str) -> str:
        """Async RAG summarize"""
        context_docs = self.retrieve_docs(query)
        context = self._format_context(context_docs)

        return await self.chain.ainvoke({
            "input": query,
            "context": context,
        })

    def _format_context(self, docs: list[Document]) -> str:
        """Format documents as context string"""
        context = ""
        for i, doc in enumerate(docs, 1):
            context += f"【参考资料{i}】: 参考资料：{doc.page_content} | 参考元数据：{doc.metadata}\n"
        return context

    def get_stats(self) -> dict:
        """Get vector store statistics"""
        return self.vector_store.get_collection_stats()


# Factory function for project-specific RAG
def get_rag_service(project_id: Optional[uuid.UUID] = None) -> RagService:
    """Get RAG service for a specific project"""
    return RagService(project_id=project_id)
