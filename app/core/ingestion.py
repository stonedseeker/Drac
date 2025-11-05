from pathlib import Path
from typing import Dict, Any, List, Tuple
import uuid
from datetime import datetime
import shutil
from app.processors.text_processor import text_processor
from app.processors.image_processor import image_processor
from app.processors.pdf_processor import pdf_processor
from app.processors.docx_processor import docx_processor
from app.processors.xlsx_processor import xlsx_processor
from app.core.embeddings import text_embedder, image_embedder
from app.database.vector_store import vector_store
from app.database.metadata_store import metadata_store
from app.utils.logging_config import log
from app.config import settings


class DocumentIngestion:
    
    def __init__(self):
        self.processors = {
            'text': text_processor,
            'image': image_processor,
            'pdf': pdf_processor,
            'docx': docx_processor,
            'xlsx': xlsx_processor
        }
    
    def get_processor(self, file_path: str):
        for processor_type, processor in self.processors.items():
            if processor.can_process(file_path):
                return processor, processor_type
        return None, None
    
    def ingest_document(self, file_path: str, document_id: str = None) -> Tuple[str, Dict[str, Any]]:
        if document_id is None:
            document_id = str(uuid.uuid4())
        
        processor, processor_type = self.get_processor(file_path)
        
        if processor is None:
            raise ValueError(f"No processor available for file: {file_path}")
        
        log.info(f"Processing {file_path} with {processor_type} processor")
        
        chunks, file_metadata = processor.process(file_path)
        
        chunk_ids = []
        chunk_embeddings = []
        chunk_metadatas = []
        chunk_texts = []
        
        for idx, chunk in enumerate(chunks):
            chunk_id = f"{document_id}_chunk_{idx}"
            
            # Always use text embeddings for consistency (1536 dimensions)
            embedding = text_embedder.embed_text(chunk)
            
            chunk_metadata = {
                'document_id': document_id,
                'chunk_index': idx,
                'chunk_id': chunk_id,
                'file_type': processor_type,
                'filename': file_metadata['filename'],
                'source_path': file_metadata['file_path']
            }
            
            chunk_ids.append(chunk_id)
            chunk_embeddings.append(embedding)
            chunk_metadatas.append(chunk_metadata)
            chunk_texts.append(chunk)
        
        vector_store.add_documents(
            texts=chunk_texts,
            embeddings=chunk_embeddings,
            metadatas=chunk_metadatas,
            ids=chunk_ids
        )
        
        doc_metadata = {
            'document_id': document_id,
            'filename': file_metadata['filename'],
            'file_type': processor_type,
            'file_path': file_metadata['file_path'],
            'file_size': Path(file_path).stat().st_size,
            'upload_timestamp': datetime.now().isoformat(),
            'num_chunks': len(chunks),
            'processor_metadata': file_metadata
        }
        
        metadata_store.add_document(document_id, doc_metadata)
        
        log.info(f"Ingested document {document_id}: {len(chunks)} chunks")
        return document_id, doc_metadata
    
    async def ingest_batch(self, file_paths: List[str]) -> List[Tuple[str, Dict[str, Any]]]:
        results = []
        
        for file_path in file_paths:
            try:
                doc_id, metadata = self.ingest_document(file_path)
                results.append((doc_id, metadata))
            except Exception as e:
                log.error(f"Failed to ingest {file_path}: {e}")
                results.append((None, {'error': str(e), 'file_path': file_path}))
        
        return results
    
    def save_uploaded_file(self, file_content: bytes, filename: str) -> str:
        upload_path = Path(settings.upload_dir)
        upload_path.mkdir(exist_ok=True)
        
        file_id = str(uuid.uuid4())
        extension = Path(filename).suffix
        saved_filename = f"{file_id}{extension}"
        file_path = upload_path / saved_filename
        
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        return str(file_path)


document_ingestion = DocumentIngestion()

__all__ = ["DocumentIngestion", "document_ingestion"]