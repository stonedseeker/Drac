from typing import List, Dict, Any
import openai
from app.config import settings
from app.utils.logging_config import log
from app.tracing.tracer import tracer


class Reranker:
    
    def __init__(self):
        self.enabled = settings.enable_reranking
        self.top_k = settings.reranking_top_k
        self.use_openai = settings.openai_api_key and settings.validate_api_key()
    
    def rerank_with_openai(self, query: str, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not self.use_openai:
            return results
        
        try:
            client = openai.OpenAI(api_key=settings.openai_api_key)
            
            scored_results = []
            
            for result in results[:10]:
                prompt = f"""Rate the relevance of this content to the query on a scale of 0-10.
Query: {query}
Content: {result['content'][:500]}

Respond with only a number between 0 and 10."""
                
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=10,
                    temperature=0
                )
                
                score_text = response.choices[0].message.content.strip()
                
                try:
                    relevance_score = float(score_text)
                    result['rerank_score'] = relevance_score / 10.0
                except ValueError:
                    result['rerank_score'] = result['score']
                
                scored_results.append(result)
                
                tracer.log_llm_call(
                    model="gpt-3.5-turbo",
                    prompt=prompt[:100],
                    response=score_text,
                    tokens_used=response.usage.total_tokens
                )
            
            scored_results.sort(key=lambda x: x['rerank_score'], reverse=True)
            
            for result in results[10:]:
                result['rerank_score'] = result['score']
                scored_results.append(result)
            
            log.info("Reranked results using OpenAI")
            return scored_results
            
        except Exception as e:
            log.error(f"Reranking error: {e}")
            return results
    
    def simple_rerank(self, query: str, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        query_terms = set(query.lower().split())
        
        for result in results:
            content_terms = set(result['content'].lower().split())
            overlap = len(query_terms.intersection(content_terms))
            
            term_score = overlap / len(query_terms) if query_terms else 0
            result['rerank_score'] = (result['score'] * 0.7) + (term_score * 0.3)
        
        results.sort(key=lambda x: x['rerank_score'], reverse=True)
        
        log.info("Reranked results using simple term overlap")
        return results
    
    def rerank(self, query: str, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not self.enabled or not results:
            return results
        
        if self.use_openai and len(results) <= 10:
            return self.rerank_with_openai(query, results)
        else:
            return self.simple_rerank(query, results)


reranker = Reranker()

__all__ = ["Reranker", "reranker"]