import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any, Optional
import uuid
from app.config import settings
from app.utils.logging_config import log


class VectorStore:
    
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=settings.chroma_dir,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        
        self.collection = self.client.get_or_create_collection(
            name=settings.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        
        log.info(f"Vector store initialized: {settings.collection_name}")
    
    def add_documents(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
        ids: List[str] = None
    ) -> List[str]:
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in range(len(texts))]
        
        try:
            self.collection.add(
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            log.info(f"Added {len(texts)} documents to vector store")
            return ids
        except Exception as e:
            log.error(f"Error adding documents: {e}")
            raise
    
    def query(
        self,
        query_embedding: List[float],
        n_results: int = 10,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where,
                where_document=where_document
            )
            return results
        except Exception as e:
            log.error(f"Error querying vector store: {e}")
            raise
    
    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        try:
            result = self.collection.get(ids=[doc_id])
            if result['ids']:
                return {
                    'id': result['ids'][0],
                    'document': result['documents'][0],
                    'metadata': result['metadatas'][0]
                }
            return None
        except Exception as e:
            log.error(f"Error getting document: {e}")
            return None
    
    def delete_document(self, doc_id: str):
        try:
            self.collection.delete(ids=[doc_id])
            log.info(f"Deleted document: {doc_id}")
        except Exception as e:
            log.error(f"Error deleting document: {e}")
            raise
    
    def count(self) -> int:
        try:
            return self.collection.count()
        except Exception as e:
            log.error(f"Error counting documents: {e}")
            return 0
    
    def reset(self):
        try:
            self.client.delete_collection(name=settings.collection_name)
            self.collection = self.client.create_collection(
                name=settings.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            log.warning("Vector store reset")
        except Exception as e:
            log.error(f"Error resetting vector store: {e}")


vector_store = VectorStore()

__all__ = ["VectorStore", "vector_store"]