from typing import List, Dict, Any, Optional
from app.core.embeddings import text_embedder
from app.database.vector_store import vector_store
from app.database.metadata_store import metadata_store
from app.core.cache import cache_manager
from app.utils.logging_config import log
from app.config import settings


class RetrievalSystem:
    
    def __init__(self):
        self.top_k = settings.top_k_results
        self.similarity_threshold = settings.similarity_threshold
    
    def retrieve(
        self,
        query: str,
        top_k: int = None,
        file_types: List[str] = None,
        similarity_threshold: float = None
    ) -> List[Dict[str, Any]]:
        
        top_k = top_k or self.top_k
        similarity_threshold = similarity_threshold or 0.0  # DEBUG: Accept any result
        
        cached_result = cache_manager.get_query_result(query)
        if cached_result:
            log.info("Retrieved results from cache")
            return cached_result[:top_k]
        
        query_embedding = text_embedder.embed_text(query)
        
        where_filter = None
        if file_types:
            where_filter = {"file_type": {"$in": file_types}}
        
        results = vector_store.query(
            query_embedding=query_embedding,
            n_results=top_k * 2,
            where=where_filter
        )
        
        formatted_results = []
        
        if results['ids'] and len(results['ids'][0]) > 0:
            for i in range(len(results['ids'][0])):
                chunk_id = results['ids'][0][i]
                distance = results['distances'][0][i]
                score = 1 - distance
                
                if score < similarity_threshold:
                    continue
                
                metadata = results['metadatas'][0][i]
                
                result = {
                    'chunk_id': chunk_id,
                    'document_id': metadata.get('document_id', 'unknown'),
                    'content': results['documents'][0][i],
                    'score': float(score),
                    'metadata': metadata,
                    'file_type': metadata.get('file_type', 'text'),
                    'filename': metadata.get('filename', 'unknown'),
                    'chunk_index': metadata.get('chunk_index', 0)
                }
                
                formatted_results.append(result)
        
        formatted_results.sort(key=lambda x: x['score'], reverse=True)
        formatted_results = formatted_results[:top_k]
        
        cache_manager.set_query_result(query, formatted_results)
        
        log.info(f"Retrieved {len(formatted_results)} results for query")
        return formatted_results
    
    def retrieve_by_document_id(self, document_id: str) -> List[Dict[str, Any]]:
        results = vector_store.query(
            query_embedding=[0] * settings.embedding_dimension,
            n_results=1000,
            where={"document_id": document_id}
        )
        
        formatted_results = []
        
        if results['ids'] and len(results['ids'][0]) > 0:
            for i in range(len(results['ids'][0])):
                result = {
                    'chunk_id': results['ids'][0][i],
                    'document_id': document_id,
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'chunk_index': results['metadatas'][0][i].get('chunk_index', 0)
                }
                formatted_results.append(result)
        
        formatted_results.sort(key=lambda x: x['chunk_index'])
        return formatted_results


retrieval_system = RetrievalSystem()

__all__ = ["RetrievalSystem", "retrieval_system"]