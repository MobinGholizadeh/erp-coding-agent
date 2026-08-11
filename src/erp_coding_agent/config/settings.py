from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import BaseModel, Field

class AgentSettings(BaseModel):
    max_attempts: int = Field(default=5)
    max_files_changed: int = Field(default=30)
    timeout_seconds: int = Field(default=1800)

class LLMSettings(BaseModel):
    provider: str = Field(default="qwen")
    base_url: str = Field(default="http://localhost:8000/v1")
    model: str = Field(default="qwen-coder-32b")
    temperature: float = Field(default=0.1)
    api_key: str | None = Field(default=None)
    timeout_seconds: int = Field(default=60)
    max_retries: int = Field(default=3)
    max_tokens: int = Field(default=4096)

class KnowledgeSettings(BaseModel):
    base_url: str = Field(default="http://localhost:8001/api/v1")
    timeout_seconds: int = Field(default=30)

class RepositorySettings(BaseModel):
    root: str = Field(default="/workspace/ERP")

class BuildSettings(BaseModel):
    command: str = Field(default="dotnet build")

class TestSettings(BaseModel):
    command: str = Field(default="dotnet test")

class GitSettings(BaseModel):
    auto_branch: bool = Field(default=True)
    auto_checkpoint: bool = Field(default=True)

class Settings(BaseSettings):
    agent: AgentSettings = Field(default_factory=AgentSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    knowledge: KnowledgeSettings = Field(default_factory=KnowledgeSettings)
    repository: RepositorySettings = Field(default_factory=RepositorySettings)
    build: BuildSettings = Field(default_factory=BuildSettings)
    test: TestSettings = Field(default_factory=TestSettings)
    git: GitSettings = Field(default_factory=GitSettings)

    model_config = SettingsConfigDict(
        env_nested_delimiter="__", 
        env_file=".env",
        env_file_encoding="utf-8"
    )

def get_settings() -> Settings:
    return Settings()
