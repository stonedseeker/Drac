from pathlib import Path
from typing import Dict, Any, List, Tuple
from app.utils.logging_config import log
from app.utils.chunking import chunk_text


class TextProcessor:
    
    def __init__(self):
        self.supported_extensions = ['.txt', '.md', '.csv', '.json', '.log']
    
    def can_process(self, file_path: str) -> bool:
        return Path(file_path).suffix.lower() in self.supported_extensions
    
    def process(self, file_path: str) -> Tuple[List[str], Dict[str, Any]]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not content.strip():
                raise ValueError("File is empty")
            
            chunks_with_indices = chunk_text(content, method="smart")
            chunks = [chunk for chunk, _ in chunks_with_indices]
            
            metadata = {
                'file_type': 'text',
                'file_path': str(file_path),
                'filename': Path(file_path).name,
                'total_characters': len(content),
                'total_chunks': len(chunks),
                'extension': Path(file_path).suffix
            }
            
            log.info(f"Processed text file: {file_path} -> {len(chunks)} chunks")
            return chunks, metadata
            
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
            
            chunks_with_indices = chunk_text(content, method="smart")
            chunks = [chunk for chunk, _ in chunks_with_indices]
            
            metadata = {
                'file_type': 'text',
                'file_path': str(file_path),
                'filename': Path(file_path).name,
                'total_characters': len(content),
                'total_chunks': len(chunks),
                'extension': Path(file_path).suffix,
                'encoding': 'latin-1'
            }
            
            return chunks, metadata
            
        except Exception as e:
            log.error(f"Error processing text file {file_path}: {e}")
            raise


text_processor = TextProcessor()

__all__ = ["TextProcessor", "text_processor"]