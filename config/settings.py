from pydantic_settings import BaseSettings
from typing import Optional
import os
from pathlib import Path

_env_path = Path(__file__).resolve().parent.parent / ".env"

class Settings(BaseSettings):
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    model_name: str = "gpt-4-turbo-preview"
    embedding_model: str = "text-embedding-3-small"
    chroma_persist_dir: str = "./data/chroma_db"
    max_tokens: int = 2048
    temperature: float = 0.3
    chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k_results: int = 5
    
    class Config:
        env_file = str(_env_path)
        env_file_encoding = "utf-8"
        extra = "allow"

settings = Settings()

