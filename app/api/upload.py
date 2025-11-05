from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import time
from datetime import datetime
from app.models import UploadResponse, BatchUploadResponse, DocumentMetadata, FileType
from app.core.ingestion import document_ingestion
from app.utils.guardrails import file_guardrails
from app.utils.logging_config import log
from app.tracing.tracer import tracer, trace_operation

router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
@trace_operation("document_upload")
async def upload_document(file: UploadFile = File(...)):
    start_time = time.time()
    
    try:
        file_content = await file.read()
        file_size = len(file_content)
        
        is_valid, error_msg = file_guardrails.validate_file(file.filename, file_size)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        tracer.log_step("file_validation", {"filename": file.filename, "size": file_size})
        
        saved_path = document_ingestion.save_uploaded_file(file_content, file.filename)
        
        tracer.log_step("file_saved", {"path": saved_path})
        
        document_id, metadata = document_ingestion.ingest_document(saved_path)
        
        tracer.log_step("document_ingested", {"document_id": document_id, "chunks": metadata['num_chunks']})
        
        processing_time = time.time() - start_time
        
        file_type_map = {
            'text': FileType.TEXT,
            'image': FileType.IMAGE,
            'pdf': FileType.PDF,
            'docx': FileType.DOCX,
            'xlsx': FileType.XLSX
        }
        
        doc_metadata = DocumentMetadata(
            document_id=document_id,
            filename=metadata['filename'],
            file_type=file_type_map.get(metadata['file_type'], FileType.TEXT),
            file_size=metadata['file_size'],
            upload_timestamp=datetime.fromisoformat(metadata['upload_timestamp']),
            num_chunks=metadata['num_chunks'],
            source_path=saved_path,
            additional_metadata=metadata.get('processor_metadata')
        )
        
        return UploadResponse(
            success=True,
            message="Document uploaded and processed successfully",
            document_id=document_id,
            metadata=doc_metadata,
            processing_time=processing_time,
            chunks_created=metadata['num_chunks']
        )
        
    except Exception as e:
        log.error(f"Upload error: {e}")
        processing_time = time.time() - start_time
        return UploadResponse(
            success=False,
            message=f"Error processing document: {str(e)}",
            processing_time=processing_time
        )


@router.post("/upload/batch", response_model=BatchUploadResponse)
@trace_operation("batch_upload")
async def upload_batch(files: List[UploadFile] = File(...)):
    start_time = time.time()
    
    results = []
    successful = 0
    failed = 0
    
    for file in files:
        try:
            file_content = await file.read()
            file_size = len(file_content)
            
            is_valid, error_msg = file_guardrails.validate_file(file.filename, file_size)
            if not is_valid:
                results.append(UploadResponse(
                    success=False,
                    message=error_msg,
                    processing_time=0
                ))
                failed += 1
                continue
            
            saved_path = document_ingestion.save_uploaded_file(file_content, file.filename)
            document_id, metadata = document_ingestion.ingest_document(saved_path)
            
            file_type_map = {
                'text': FileType.TEXT,
                'image': FileType.IMAGE,
                'pdf': FileType.PDF,
                'docx': FileType.DOCX,
                'xlsx': FileType.XLSX
            }
            
            doc_metadata = DocumentMetadata(
                document_id=document_id,
                filename=metadata['filename'],
                file_type=file_type_map.get(metadata['file_type'], FileType.TEXT),
                file_size=metadata['file_size'],
                upload_timestamp=datetime.fromisoformat(metadata['upload_timestamp']),
                num_chunks=metadata['num_chunks'],
                source_path=saved_path,
                additional_metadata=metadata.get('processor_metadata')
            )
            
            results.append(UploadResponse(
                success=True,
                message="Document uploaded successfully",
                document_id=document_id,
                metadata=doc_metadata,
                processing_time=0,
                chunks_created=metadata['num_chunks']
            ))
            successful += 1
            
        except Exception as e:
            log.error(f"Batch upload error for {file.filename}: {e}")
            results.append(UploadResponse(
                success=False,
                message=f"Error: {str(e)}",
                processing_time=0
            ))
            failed += 1
    
    total_time = time.time() - start_time
    
    return BatchUploadResponse(
        success=True,
        total_files=len(files),
        successful_uploads=successful,
        failed_uploads=failed,
        results=results,
        total_processing_time=total_time
    )


@router.get("/documents")
async def list_documents():
    from app.database.metadata_store import metadata_store
    documents = metadata_store.list_documents()
    return {"total": len(documents), "documents": documents}


@router.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    try:
        from app.database.metadata_store import metadata_store
        from app.database.vector_store import vector_store
        
        metadata = metadata_store.get_document(document_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="Document not found")
        
        metadata_store.delete_document(document_id)
        
        return {"success": True, "message": f"Document {document_id} deleted"}
        
    except Exception as e:
        log.error(f"Delete error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


__all__ = ["router"]