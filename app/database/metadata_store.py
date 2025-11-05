import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.config import settings
from app.utils.logging_config import log


class MetadataStore:
    
    def __init__(self):
        self.metadata_dir = Path(settings.chroma_dir) / "metadata"
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.metadata_dir / "index.json"
        self._load_index()
    
    def _load_index(self):
        if self.index_file.exists():
            with open(self.index_file, 'r') as f:
                self.index = json.load(f)
        else:
            self.index = {}
            self._save_index()
    
    def _save_index(self):
        with open(self.index_file, 'w') as f:
            json.dump(self.index, f, indent=2)
    
    def add_document(self, document_id: str, metadata: Dict[str, Any]):
        metadata['document_id'] = document_id
        metadata['created_at'] = metadata.get('created_at', datetime.now().isoformat())
        
        doc_file = self.metadata_dir / f"{document_id}.json"
        with open(doc_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        self.index[document_id] = {
            'filename': metadata.get('filename', 'unknown'),
            'file_type': metadata.get('file_type', 'unknown'),
            'created_at': metadata['created_at']
        }
        self._save_index()
        
        log.info(f"Metadata saved for document: {document_id}")
    
    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        doc_file = self.metadata_dir / f"{document_id}.json"
        
        if doc_file.exists():
            with open(doc_file, 'r') as f:
                return json.load(f)
        
        return None
    
    def delete_document(self, document_id: str):
        doc_file = self.metadata_dir / f"{document_id}.json"
        
        if doc_file.exists():
            doc_file.unlink()
        
        if document_id in self.index:
            del self.index[document_id]
            self._save_index()
        
        log.info(f"Metadata deleted for document: {document_id}")
    
    def list_documents(self, file_type: str = None) -> List[Dict[str, Any]]:
        documents = []
        
        for doc_id, info in self.index.items():
            if file_type is None or info.get('file_type') == file_type:
                full_metadata = self.get_document(doc_id)
                if full_metadata:
                    documents.append(full_metadata)
        
        return documents
    
    def count(self) -> int:
        return len(self.index)
    
    def search_by_filename(self, filename: str) -> List[Dict[str, Any]]:
        results = []
        
        for doc_id, info in self.index.items():
            if filename.lower() in info.get('filename', '').lower():
                full_metadata = self.get_document(doc_id)
                if full_metadata:
                    results.append(full_metadata)
        
        return results


metadata_store = MetadataStore()

__all__ = ["MetadataStore", "metadata_store"]