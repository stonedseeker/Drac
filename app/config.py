from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path
from typing import List
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings(BaseSettings):    
    # OpenAI Configuration
    openai_api_key: str = Field(default="", env="OPENAI_API_KEY")
    
    # Tesseract Configuration
    tesseract_cmd: str = Field(
        default=r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        env="TESSERACT_CMD"
    )
    
    # Application Settings
    app_name: str = Field(default="Multimodal RAG System", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=True, env="DEBUG")
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    
    # File Upload Settings
    upload_dir: str = Field(default="./uploads", env="UPLOAD_DIR")
    max_file_size: int = Field(default=50, env="MAX_FILE_SIZE")  # MB
    allowed_extensions: str = Field(
        default=".txt,.pdf,.png,.jpg,.jpeg,.docx,.xlsx,.pptx",
        env="ALLOWED_EXTENSIONS"
    )
    
    # Vector Database Settings
    chroma_dir: str = Field(default="./chroma_db", env="CHROMA_DIR")
    collection_name: str = Field(default="multimodal_documents", env="COLLECTION_NAME")
    
    # Embedding Settings
    text_embedding_model: str = Field(
        default="text-embedding-3-small",
        env="TEXT_EMBEDDING_MODEL"
    )
    image_embedding_model: str = Field(
        default="clip-ViT-B-32",
        env="IMAGE_EMBEDDING_MODEL"
    )
    embedding_dimension: int = Field(default=1536, env="EMBEDDING_DIMENSION")
    
    # Chunking Settings
    chunk_size: int = Field(default=512, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=50, env="CHUNK_OVERLAP")
    max_chunks_per_doc: int = Field(default=100, env="MAX_CHUNKS_PER_DOC")
    
    # Retrieval Settings
    top_k_results: int = Field(default=10, env="TOP_K_RESULTS")
    similarity_threshold: float = Field(default=0.7, env="SIMILARITY_THRESHOLD")
    enable_reranking: bool = Field(default=True, env="ENABLE_RERANKING")
    reranking_top_k: int = Field(default=5, env="RERANKING_TOP_K")
    
    # Hybrid Search Settings
    enable_hybrid_search: bool = Field(default=True, env="ENABLE_HYBRID_SEARCH")
    dense_weight: float = Field(default=0.7, env="DENSE_WEIGHT")
    sparse_weight: float = Field(default=0.3, env="SPARSE_WEIGHT")
    
    # Cache Settings
    cache_dir: str = Field(default="./cache", env="CACHE_DIR")
    cache_enabled: bool = Field(default=True, env="CACHE_ENABLED")
    cache_ttl: int = Field(default=3600, env="CACHE_TTL")  # seconds
    
    # Logging Settings
    log_dir: str = Field(default="./logs", env="LOG_DIR")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="app.log", env="LOG_FILE")
    
    # Phoenix Tracing Settings
    enable_tracing: bool = Field(default=True, env="ENABLE_TRACING")
    phoenix_port: int = Field(default=6006, env="PHOENIX_PORT")
    
    # Processing Settings
    batch_size: int = Field(default=10, env="BATCH_SIZE")
    async_workers: int = Field(default=4, env="ASYNC_WORKERS")
    
    # OCR Settings
    ocr_language: str = Field(default="eng", env="OCR_LANGUAGE")
    ocr_dpi: int = Field(default=300, env="OCR_DPI")
    
    # Guardrails Settings
    enable_guardrails: bool = Field(default=True, env="ENABLE_GUARDRAILS")
    max_query_length: int = Field(default=1000, env="MAX_QUERY_LENGTH")
    min_query_length: int = Field(default=3, env="MIN_QUERY_LENGTH")
    
    # Performance Settings
    request_timeout: int = Field(default=300, env="REQUEST_TIMEOUT")  # seconds
    max_concurrent_requests: int = Field(default=10, env="MAX_CONCURRENT_REQUESTS")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def get_allowed_extensions(self) -> List[str]:
        return [ext.strip() for ext in self.allowed_extensions.split(",")]
    
    def ensure_directories(self):
        directories = [
            self.upload_dir,
            self.chroma_dir,
            self.cache_dir,
            self.log_dir,
        ]
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    def validate_api_key(self) -> bool:
        return bool(self.openai_api_key and self.openai_api_key != "your_openai_api_key_here")


# Global settings instance
settings = Settings()

# Ensure all directories exist
settings.ensure_directories()

# Export settings
__all__ = ["settings"]