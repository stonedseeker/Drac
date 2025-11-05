from typing import List, Dict, Any
from rank_bm25 import BM25Okapi
from app.core.retrieval import retrieval_system
from app.database.vector_store import vector_store
from app.utils.logging_config import log
from app.config import settings


class HybridSearch:
    
    def __init__(self):
        self.dense_weight = settings.dense_weight
        self.sparse_weight = settings.sparse_weight
        self.bm25_index = None
        self.documents = []
        self.doc_ids = []
    
    def build_bm25_index(self):
        try:
            count = vector_store.count()
            
            if count == 0:
                log.warning("No documents in vector store for BM25 indexing")
                return
            
            results = vector_store.collection.get()
            
            if not results['documents']:
                log.warning("No documents retrieved for BM25 indexing")
                return
            
            self.documents = results['documents']
            self.doc_ids = results['ids']
            
            tokenized_docs = [doc.lower().split() for doc in self.documents]
            self.bm25_index = BM25Okapi(tokenized_docs)
            
            log.info(f"BM25 index built with {len(self.documents)} documents")
        except Exception as e:
            log.error(f"Error building BM25 index: {e}")
            self.bm25_index = None
    
    def sparse_retrieval(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        if self.bm25_index is None:
            self.build_bm25_index()
        
        if self.bm25_index is None:
            return []
        
        tokenized_query = query.lower().split()
        scores = self.bm25_index.get_scores(tokenized_query)
        
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        
        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                results.append({
                    'chunk_id': self.doc_ids[idx],
                    'content': self.documents[idx],
                    'score': float(scores[idx]),
                    'method': 'sparse'
                })
        
        return results
    
    def hybrid_retrieve(
        self,
        query: str,
        top_k: int = 10,
        file_types: List[str] = None
    ) -> List[Dict[str, Any]]:
        
        dense_results = retrieval_system.retrieve(
            query=query,
            top_k=top_k * 2,
            file_types=file_types
        )
        
        sparse_results = self.sparse_retrieval(query, top_k=top_k * 2)
        
        combined_scores = {}
        
        for result in dense_results:
            chunk_id = result['chunk_id']
            combined_scores[chunk_id] = {
                'dense_score': result['score'] * self.dense_weight,
                'sparse_score': 0,
                'result': result
            }
        
        for result in sparse_results:
            chunk_id = result['chunk_id']
            if chunk_id in combined_scores:
                combined_scores[chunk_id]['sparse_score'] = result['score'] * self.sparse_weight
            else:
                dense_info = vector_store.get_document(chunk_id)
                if dense_info:
                    combined_scores[chunk_id] = {
                        'dense_score': 0,
                        'sparse_score': result['score'] * self.sparse_weight,
                        'result': {
                            'chunk_id': chunk_id,
                            'content': dense_info['document'],
                            'metadata': dense_info['metadata'],
                            'score': 0
                        }
                    }
        
        final_results = []
        for chunk_id, scores in combined_scores.items():
            final_score = scores['dense_score'] + scores['sparse_score']
            result = scores['result']
            result['score'] = final_score
            result['dense_score'] = scores['dense_score']
            result['sparse_score'] = scores['sparse_score']
            result['retrieval_method'] = 'hybrid'
            final_results.append(result)
        
        final_results.sort(key=lambda x: x['score'], reverse=True)
        
        log.info(f"Hybrid search returned {len(final_results[:top_k])} results")
        return final_results[:top_k]


hybrid_search = HybridSearch()

__all__ = ["HybridSearch", "hybrid_search"]