import os
from typing import List, Set, Any
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Core App Config
    PROJECT_NAME: str = "Enterprise AI Knowledge Assistant"
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    CORS_ORIGINS: Any = [
        "http://localhost:4200",
        "http://127.0.0.1:4200",
        "http://localhost",
        "http://127.0.0.1"
    ]
    
    # Database Config
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/knowledge_assistant",
        env="DATABASE_URL"
    )
    
    # JWT Auth Config
    JWT_SECRET: str = Field(default="supersecretkeyreplaceinproduction", env="JWT_SECRET")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Qdrant Config
    QDRANT_URL: str = Field(default="http://localhost:6333", env="QDRANT_URL")
    QDRANT_API_KEY: str = Field(default="", env="QDRANT_API_KEY")
    QDRANT_COLLECTION_NAME: str = "knowledge_base"

    # LLM Provider Keys
    OPENAI_API_KEY: str = Field(default="", env="OPENAI_API_KEY")
    GEMINI_API_KEY: str = Field(default="", env="GEMINI_API_KEY")
    ANTHROPIC_API_KEY: str = Field(default="", env="ANTHROPIC_API_KEY")
    GROQ_API_KEY: str = Field(default="", env="GROQ_API_KEY")

    # Ingestion Config
    UPLOAD_DIR: str = Field(default="storage/documents", env="UPLOAD_DIR")
    MAX_UPLOAD_SIZE_BYTES: int = Field(default=15 * 1024 * 1024, env="MAX_UPLOAD_SIZE_BYTES")  # 15MB
    ALLOWED_MIME_TYPES: Set[str] = {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain"
    }
    
    # RRF (Reciprocal Rank Fusion) Config
    RRF_K: int = 60
    TOP_K: int = 5

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str) -> str:
        if v and v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v

# Create globally accessible settings instance
settings = Settings()

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
