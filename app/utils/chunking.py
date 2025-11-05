from typing import List, Tuple
import re
from app.config import settings


class TextChunker:
    
    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap
    
    def chunk_by_tokens(self, text: str) -> List[str]:
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), self.chunk_size - self.chunk_overlap):
            chunk = ' '.join(words[i:i + self.chunk_size])
            if chunk.strip():
                chunks.append(chunk)
        
        return chunks
    
    def chunk_by_sentences(self, text: str) -> List[str]:
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence.split())
            
            if current_length + sentence_length > self.chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                overlap_sentences = current_chunk[-2:] if len(current_chunk) > 2 else current_chunk
                current_chunk = overlap_sentences
                current_length = sum(len(s.split()) for s in current_chunk)
            
            current_chunk.append(sentence)
            current_length += sentence_length
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def chunk_by_paragraphs(self, text: str) -> List[str]:
        paragraphs = text.split('\n\n')
        chunks = []
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            words = para.split()
            if len(words) <= self.chunk_size:
                chunks.append(para)
            else:
                sub_chunks = self.chunk_by_tokens(para)
                chunks.extend(sub_chunks)
        
        return chunks
    
    def smart_chunk(self, text: str) -> List[Tuple[str, int]]:
        if '\n\n' in text and len(text.split('\n\n')) > 1:
            chunks = self.chunk_by_paragraphs(text)
        elif '.' in text or '!' in text or '?' in text:
            chunks = self.chunk_by_sentences(text)
        else:
            chunks = self.chunk_by_tokens(text)
        
        return [(chunk, i) for i, chunk in enumerate(chunks)]


def chunk_text(text: str, method: str = "smart") -> List[Tuple[str, int]]:
    chunker = TextChunker()
    
    if method == "smart":
        return chunker.smart_chunk(text)
    elif method == "sentences":
        chunks = chunker.chunk_by_sentences(text)
    elif method == "paragraphs":
        chunks = chunker.chunk_by_paragraphs(text)
    else:
        chunks = chunker.chunk_by_tokens(text)
    
    return [(chunk, i) for i, chunk in enumerate(chunks)]


__all__ = ["TextChunker", "chunk_text"]