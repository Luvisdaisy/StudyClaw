from abc import ABC, abstractmethod
from typing import Optional
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.chat_models.tongyi import ChatTongyi, BaseChatModel
from langchain_core.embeddings import Embeddings
from utils.config_handler import rag_cfg
import os
import dotenv

dotenv.load_dotenv()
API_KEY = os.getenv("DASHSCOPE_API_KEY")


class BaseModelFactory(ABC):
    @abstractmethod
    def generator(self) -> Optional[Embeddings | BaseChatModel]:
        pass


class ChatModelFactory(BaseModelFactory):
    def generator(self) -> Optional[Embeddings | BaseChatModel]:
        return ChatTongyi(model=rag_cfg["chat_model_name"], api_key=API_KEY)


class EmbeddingModelFactory(BaseModelFactory):
    def generator(self) -> Optional[Embeddings | BaseChatModel]:
        return DashScopeEmbeddings(
            model=rag_cfg["embedding_model_name"],
            dashscope_api_key=API_KEY,
        )


chat_model = ChatModelFactory().generator()
embedding_model = EmbeddingModelFactory().generator()
