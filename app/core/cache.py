import hashlib
from typing import Any, Optional
from diskcache import Cache
from app.config import settings
from app.utils.logging_config import log


class CacheManager:
    
    def __init__(self):
        self.enabled = settings.cache_enabled
        self.cache = Cache(settings.cache_dir)
        self.ttl = settings.cache_ttl
    
    def _generate_key(self, prefix: str, data: str) -> str:
        hash_obj = hashlib.md5(data.encode())
        return f"{prefix}:{hash_obj.hexdigest()}"
    
    def get(self, key: str) -> Optional[Any]:
        if not self.enabled:
            return None
        
        try:
            value = self.cache.get(key)
            if value is not None:
                log.debug(f"Cache hit: {key}")
            return value
        except Exception as e:
            log.error(f"Cache get error: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = None):
        if not self.enabled:
            return
        
        try:
            expire_time = ttl or self.ttl
            self.cache.set(key, value, expire=expire_time)
            log.debug(f"Cache set: {key}")
        except Exception as e:
            log.error(f"Cache set error: {e}")
    
    def get_embedding(self, text: str) -> Optional[list]:
        key = self._generate_key("embedding", text)
        return self.get(key)
    
    def set_embedding(self, text: str, embedding: list):
        key = self._generate_key("embedding", text)
        self.set(key, embedding)
    
    def get_query_result(self, query: str) -> Optional[Any]:
        key = self._generate_key("query", query)
        return self.get(key)
    
    def set_query_result(self, query: str, result: Any):
        key = self._generate_key("query", query)
        self.set(key, result, ttl=1800)
    
    def clear(self):
        try:
            self.cache.clear()
            log.info("Cache cleared")
        except Exception as e:
            log.error(f"Cache clear error: {e}")
    
    def stats(self) -> dict:
        try:
            return {
                "size": self.cache.volume(),
                "count": len(self.cache)
            }
        except Exception as e:
            log.error(f"Cache stats error: {e}")
            return {"size": 0, "count": 0}


cache_manager = CacheManager()

__all__ = ["CacheManager", "cache_manager"]