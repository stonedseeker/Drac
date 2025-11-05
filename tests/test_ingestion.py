import pytest
import tempfile
import os
from pathlib import Path
from app.core.ingestion import document_ingestion
from app.processors.text_processor import text_processor
from app.processors.image_processor import image_processor


def test_text_processor():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("This is a test document. It has multiple sentences. This helps test chunking.")
        temp_path = f.name
    
    try:
        chunks, metadata = text_processor.process(temp_path)
        
        assert len(chunks) > 0
        assert metadata['file_type'] == 'text'
        assert metadata['filename'].endswith('.txt')
        assert metadata['total_chunks'] == len(chunks)
    finally:
        os.unlink(temp_path)


def test_document_ingestion():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("Test document for ingestion pipeline.")
        temp_path = f.name
    
    try:
        doc_id, metadata = document_ingestion.ingest_document(temp_path)
        
        assert doc_id is not None
        assert metadata['document_id'] == doc_id
        assert metadata['num_chunks'] > 0
        assert 'upload_timestamp' in metadata
    finally:
        os.unlink(temp_path)


def test_get_processor():
    processor, proc_type = document_ingestion.get_processor('test.txt')
    assert proc_type == 'text'
    
    processor, proc_type = document_ingestion.get_processor('test.pdf')
    assert proc_type == 'pdf'
    
    processor, proc_type = document_ingestion.get_processor('test.png')
    assert proc_type == 'image'
    
    processor, proc_type = document_ingestion.get_processor('test.docx')
    assert proc_type == 'docx'
    
    processor, proc_type = document_ingestion.get_processor('test.xlsx')
    assert proc_type == 'xlsx'
    
    processor, proc_type = document_ingestion.get_processor('test.unknown')
    assert processor is None
    assert proc_type is None


def test_chunking():
    from app.utils.chunking import chunk_text
    
    text = "This is sentence one. This is sentence two. This is sentence three."
    chunks = chunk_text(text, method="sentences")
    
    assert len(chunks) > 0
    assert all(isinstance(chunk, tuple) for chunk in chunks)