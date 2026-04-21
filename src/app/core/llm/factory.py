from langchain_core.embeddings import Embeddings
from langchain_community.chat_models.tongyi import BaseChatModel
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.chat_models.tongyi import ChatTongyi
from app.shared.model.factory import BaseModelFactory
from app.core.config import settings


class ChatModelFactory(BaseModelFactory):
    def generator(
        self,
        model_name: str | None = None,
        temperature: float = 0,
    ) -> Embeddings | BaseChatModel | None:
        # 如果未显式传入模型名称，则回退到配置中的默认模型
        model_name = model_name or settings.rag.chat_model_name
        return ChatTongyi(model=model_name, temperature=temperature,enable_thinking=False)


class EmbeddingModelFactory(BaseModelFactory):
    def generator(self) -> Embeddings | BaseChatModel | None:
        return DashScopeEmbeddings(model=settings.rag.embedding_model_name)


class LocalEmbeddingModelFactory(BaseModelFactory):
    def generator(self) -> Embeddings | BaseChatModel | None:
        # 延迟导入本地 Embeddings，避免在只使用对话模型时也提前加载大模型
        from .model.BAAI import embeddings

        return embeddings


def get_chat_model(model_name: str | None = None, temperature: float = 0):
    return ChatModelFactory().generator(model_name=model_name, temperature=temperature)

def get_embedding_model(model_name: str | None = None):
    """获取 Embeddings 实例（同步接口）。

    - "BAAI": 使用本地 BGE 模型
    - 其他 / None: 使用默认的 DashScopeEmbeddings（DashScopeEmbedding）
    """

    if model_name == "BAAI":
        return LocalEmbeddingModelFactory().generator()
    return EmbeddingModelFactory().generator()