import yaml
from pathlib import Path
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from src.utils.path_tool import get_abs_path, get_project_root  # 假设你的路径工具在这里


# 1. 定义嵌套的子模型 (对应 YAML 的层级)
class AgentConfig(BaseModel):
    external_data_path: Path
    temperature: float
    message_save_num: int

    @field_validator("external_data_path", mode="after")
    @classmethod
    def make_absolute(cls, v: Path) -> Path:
        if not v.is_absolute():
            return get_project_root() / v
        return v


class RagConfig(BaseModel):
    chat_model_name: str
    embedding_model_name: str


class PromptConfig(BaseModel):
    # 使用 Path 类型，Pydantic 会自动验证路径字符串
    main_prompt_path: Path
    rag_summarize_prompt_path: Path
    report_prompt_path: Path
    law_prompt_path: Path

    @field_validator("*", mode="after")
    @classmethod
    def make_absolute(cls, v: Path) -> Path:
        if not v.is_absolute():
            # 自动拼接：项目根目录 / YAML里的相对路径
            return get_project_root() / v
        return v


class ChromaConfig(BaseModel):
    persist_directory: Path
    collection_name: str
    k: int
    data_path: Path
    md5_hex_store: Path
    allow_knowledge_file_type: list[str]
    separatoes: list[str]
    chunk_size: int
    chunk_overlap: int

    @field_validator("persist_directory", "data_path", "md5_hex_store", mode="after")
    @classmethod
    def make_absolute(cls, v: Path) -> Path:
        if not v.is_absolute():
            return get_project_root() / v
        return v


# 2. 定义全局配置类 (继承自 BaseSettings)
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",  # 必须加上这一行
        extra="ignore",
    )
    # 变量名必须与 YAML 的一级 Key 一致
    agent: AgentConfig
    rag: RagConfig
    prompts: PromptConfig
    chroma: ChromaConfig

    # 配置读取优先级 (环境变量 > .env)
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @classmethod
    def load_from_yaml(cls):
        """核心方法：从 YAML 加载并实例化"""
        yaml_path = get_abs_path("config/settings.yml")

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
