from fastapi import APIRouter, HTTPException
import time
from app.models import QueryRequest, QueryResponse, RetrievalResult, FileType
from app.core.retrieval import retrieval_system
from app.core.hybrid_search import hybrid_search
from app.core.reranking import reranker
from app.utils.guardrails import guardrails
from app.utils.logging_config import log
from app.tracing.tracer import tracer, trace_operation
from app.config import settings

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
@trace_operation("query_execution")
async def query_documents(request: QueryRequest):
    start_time = time.time()
    
    try:
        is_valid, error_msg = guardrails.validate_query(request.query)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        sanitized_query = guardrails.sanitize_query(request.query)
        
        tracer.log_step("query_validated", {"query": sanitized_query})
        
        file_type_filter = None
        if request.file_types:
            file_type_filter = [ft.value for ft in request.file_types]
        
        if settings.enable_hybrid_search:
            results = hybrid_search.hybrid_retrieve(
                query=sanitized_query,
                top_k=request.top_k,
                file_types=file_type_filter
            )
            retrieval_method = "hybrid"
        else:
            results = retrieval_system.retrieve(
                query=sanitized_query,
                top_k=request.top_k,
                file_types=file_type_filter,
                similarity_threshold=request.similarity_threshold
            )
            retrieval_method = "dense"
        
        tracer.log_step("retrieval_complete", {"num_results": len(results)})
        
        reranked = False
        if request.enable_reranking and settings.enable_reranking:
            results = reranker.rerank(sanitized_query, results)
            reranked = True
            tracer.log_step("reranking_complete", {"num_results": len(results)})
        
        file_type_map = {
            'text': FileType.TEXT,
            'image': FileType.IMAGE,
            'pdf': FileType.PDF,
            'docx': FileType.DOCX,
            'xlsx': FileType.XLSX
        }
        
        retrieval_results = []
        for result in results:
            retrieval_results.append(RetrievalResult(
                document_id=result.get('document_id', 'unknown'),
                chunk_id=result['chunk_id'],
                content=result['content'],
                score=result.get('rerank_score', result['score']),
                file_type=file_type_map.get(result.get('file_type'), FileType.TEXT),
                filename=result.get('filename', 'unknown'),
                metadata=result.get('metadata', {}),
                chunk_index=result.get('chunk_index', 0)
            ))
        
        processing_time = time.time() - start_time
        
        return QueryResponse(
            success=True,
            query=sanitized_query,
            results=retrieval_results,
            total_results=len(retrieval_results),
            processing_time=processing_time,
            retrieval_method=retrieval_method,
            reranked=reranked
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Query error: {e}")
        processing_time = time.time() - start_time
        return QueryResponse(
            success=False,
            query=request.query,
            results=[],
            total_results=0,
            processing_time=processing_time,
            retrieval_method="none",
            reranked=False
        )


@router.get("/search")
async def simple_search(q: str, top_k: int = 10):
    try:
        is_valid, error_msg = guardrails.validate_query(q)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        sanitized_query = guardrails.sanitize_query(q)
        
        results = retrieval_system.retrieve(
            query=sanitized_query,
            top_k=top_k
        )
        
        return {
            "query": sanitized_query,
            "results": results,
            "total": len(results)
        }
        
    except Exception as e:
        log.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rebuild-index")
async def rebuild_search_index():
    try:
        hybrid_search.build_bm25_index()
        return {"success": True, "message": "Search index rebuilt successfully"}
    except Exception as e:
        log.error(f"Index rebuild error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


__all__ = ["router"]