from abc import ABC, abstractmethod
from langchain_core.embeddings import Embeddings
from langchain_community.chat_models.tongyi import BaseChatModel
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.chat_models.tongyi import ChatTongyi
from app.core.config import settings

class BaseModelFactory(ABC):
    @abstractmethod
    def generator(self) -> BaseChatModel |BaseChatModel|None:
        pass