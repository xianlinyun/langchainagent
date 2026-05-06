import yaml
from pathlib import Path
from typing import Annotated

from pydantic import AfterValidator, BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
from src.utils.path_tool import get_abs_path, get_project_root, make_absolute

RelativePath = Annotated[Path, AfterValidator(make_absolute)]

# 1. 定义嵌套的子模型 (对应 YAML 的层级)
class AgentConfig(BaseModel):
    external_data_path: RelativePath
    temperature: float
    message_save_num: int


class RagConfig(BaseModel):
    chat_model_name: str
    embedding_model_name: str


class PromptConfig(BaseModel):
    main_prompt_path: RelativePath
    rag_summarize_prompt_path: RelativePath
    report_prompt_path: RelativePath
    law_prompt_path: RelativePath


class ChromaConfig(BaseModel):
    persist_directory: RelativePath
    collection_name: str
    k: int
    data_path: RelativePath
    md5_hex_store: RelativePath
    allow_knowledge_file_type: list[str]
    separatoes: list[str]
    chunk_size: int
    chunk_overlap: int


# 2. 定义全局配置类 (继承自 BaseSettings)
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=get_project_root() / ".env",
        env_nested_delimiter="__",
        extra="ignore",
    )
    # 变量名必须与 YAML 的一级 Key 一致
    agent: AgentConfig
    rag: RagConfig
    prompts: PromptConfig
    chroma: ChromaConfig

    @classmethod
    def load_from_yaml(cls):
        """核心方法：从 YAML 加载并实例化"""
        yaml_path = get_abs_path("configs/settings.yml")

        if not yaml_path.is_file():
            raise FileNotFoundError(f"配置文件缺失: {yaml_path}")

        with yaml_path.open("r", encoding="utf-8") as f:
            conf_data = yaml.safe_load(f)

        # 将字典解包传给 Settings 构造函数
        return cls(**conf_data)


# 3. 创建单例，供全项目调用
settings = Settings.load_from_yaml()
if __name__ == "__main__":
    print(settings.agent.external_data_path)
    print(settings.chroma.data_path)
