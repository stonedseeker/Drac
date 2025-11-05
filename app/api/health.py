from fastapi import APIRouter
from datetime import datetime
from app.models import HealthResponse
from app.database.vector_store import vector_store
from app.database.metadata_store import metadata_store
from app.core.cache import cache_manager
from app.config import settings

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    try:
        doc_count = vector_store.count()
        database_status = "healthy"
    except Exception as e:
        doc_count = 0
        database_status = f"unhealthy: {str(e)}"
    
    try:
        cache_stats = cache_manager.stats()
        cache_status = "healthy"
    except Exception as e:
        cache_status = f"unhealthy: {str(e)}"
    
    metadata_count = metadata_store.count()
    
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        timestamp=datetime.now(),
        database_status=database_status,
        cache_status=cache_status,
        total_documents=metadata_count,
        total_chunks=doc_count
    )


@router.get("/stats")
async def get_stats():
    return {
        "total_documents": metadata_store.count(),
        "total_chunks": vector_store.count(),
        "cache_stats": cache_manager.stats(),
        "settings": {
            "chunk_size": settings.chunk_size,
            "top_k_results": settings.top_k_results,
            "enable_reranking": settings.enable_reranking,
            "enable_hybrid_search": settings.enable_hybrid_search
        }
    }


@router.get("/debug/chunks")
async def debug_chunks():
    try:
        results = vector_store.collection.get()
        return {
            "total_chunks": len(results['ids']) if results['ids'] else 0,
            "sample_chunks": [
                {
                    "id": results['ids'][i],
                    "content_preview": results['documents'][i][:200] if results['documents'] else "",
                    "metadata": results['metadatas'][i] if results['metadatas'] else {}
                }
                for i in range(min(5, len(results['ids']) if results['ids'] else 0))
            ]
        }
    except Exception as e:
        return {"error": str(e)}


__all__ = ["router"]