from typing import Tuple, Optional
import re
from app.config import settings


class QueryGuardrails:
    
    def __init__(self):
        self.min_length = settings.min_query_length
        self.max_length = settings.max_query_length
        self.blocked_patterns = [
            r'<script.*?>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
        ]
    
    def validate_query(self, query: str) -> Tuple[bool, Optional[str]]:
        if not query or not query.strip():
            return False, "Query cannot be empty"
        
        query = query.strip()
        
        if len(query) < self.min_length:
            return False, f"Query too short (minimum {self.min_length} characters)"
        
        if len(query) > self.max_length:
            return False, f"Query too long (maximum {self.max_length} characters)"
        
        for pattern in self.blocked_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return False, "Query contains potentially malicious content"
        
        return True, None
    
    def sanitize_query(self, query: str) -> str:
        query = query.strip()
        query = re.sub(r'\s+', ' ', query)
        query = re.sub(r'[<>]', '', query)
        return query


class FileGuardrails:
    
    def __init__(self):
        self.max_file_size = settings.max_file_size * 1024 * 1024
        self.allowed_extensions = settings.get_allowed_extensions()
    
    def validate_file(self, filename: str, file_size: int) -> Tuple[bool, Optional[str]]:
        if file_size > self.max_file_size:
            return False, f"File too large (maximum {settings.max_file_size}MB)"
        
        if file_size == 0:
            return False, "File is empty"
        
        ext = self.get_extension(filename)
        if ext not in self.allowed_extensions:
            return False, f"File type not allowed. Allowed: {', '.join(self.allowed_extensions)}"
        
        return True, None
    
    def get_extension(self, filename: str) -> str:
        return '.' + filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''


guardrails = QueryGuardrails()
file_guardrails = FileGuardrails()

__all__ = ["QueryGuardrails", "FileGuardrails", "guardrails", "file_guardrails"]