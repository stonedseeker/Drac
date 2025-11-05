from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class FileType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    PDF = "pdf"
    DOCX = "docx"
    XLSX = "xlsx"
    PPTX = "pptx"


class QueryType(str, Enum):
    FACTUAL = "factual"
    EXPLORATORY = "exploratory"
    CROSS_MODAL = "cross_modal"


class DocumentMetadata(BaseModel):
    document_id: str
    filename: str
    file_type: FileType
    file_size: int  # bytes
    upload_timestamp: datetime
    num_chunks: int
    source_path: str
    additional_metadata: Optional[Dict[str, Any]] = None


class UploadResponse(BaseModel):
    success: bool
    message: str
    document_id: Optional[str] = None
    metadata: Optional[DocumentMetadata] = None
    processing_time: float  # seconds
    chunks_created: Optional[int] = None


class BatchUploadResponse(BaseModel):
    success: bool
    total_files: int
    successful_uploads: int
    failed_uploads: int
    results: List[UploadResponse]
    total_processing_time: float


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=1000)
    query_type: Optional[QueryType] = QueryType.FACTUAL
    top_k: Optional[int] = Field(default=10, ge=1, le=50)
    similarity_threshold: Optional[float] = Field(default=0.7, ge=0.0, le=1.0)
    enable_reranking: Optional[bool] = True
    file_types: Optional[List[FileType]] = None
    
    @validator('query')
    def validate_query(cls, v):
        if not v.strip():
            raise ValueError("Query cannot be empty or whitespace only")
        return v.strip()


class RetrievalResult(BaseModel):
    document_id: str
    chunk_id: str
    content: str
    score: float
    file_type: FileType
    filename: str
    metadata: Dict[str, Any]
    chunk_index: int


class QueryResponse(BaseModel):
    success: bool
    query: str
    results: List[RetrievalResult]
    total_results: int
    processing_time: float
    retrieval_method: str  # "dense", "sparse", "hybrid"
    reranked: bool = False


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime
    database_status: str
    cache_status: str
    total_documents: int
    total_chunks: int


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class DocumentSummaryRequest(BaseModel):
    document_id: str
    max_length: Optional[int] = Field(default=150, ge=50, le=500)


class DocumentSummaryResponse(BaseModel):
    success: bool
    document_id: str
    summary: str
    processing_time: float


class ConversationMemory(BaseModel):
    conversation_id: str
    messages: List[Dict[str, str]]
    created_at: datetime
    last_updated: datetime


class QueryExpansionResponse(BaseModel):
    original_query: str
    expanded_queries: List[str]
    expansion_method: str


class CacheStats(BaseModel):
    total_entries: int
    hit_rate: float
    miss_rate: float
    size_mb: float


class SystemStats(BaseModel):
    total_documents: int
    total_chunks: int
    total_storage_mb: float
    cache_stats: CacheStats
    uptime_seconds: float


__all__ = [
    "FileType",
    "QueryType",
    "DocumentMetadata",
    "UploadResponse",
    "BatchUploadResponse",
    "QueryRequest",
    "RetrievalResult",
    "QueryResponse",
    "HealthResponse",
    "ErrorResponse",
    "DocumentSummaryRequest",
    "DocumentSummaryResponse",
    "ConversationMemory",
    "QueryExpansionResponse",
    "CacheStats",
    "SystemStats",
]