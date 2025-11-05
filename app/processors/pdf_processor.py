from pathlib import Path
from typing import Dict, Any, List, Tuple
import fitz
from PIL import Image
import io
import pytesseract
from app.config import settings
from app.utils.logging_config import log
from app.utils.chunking import chunk_text


class PDFProcessor:
    
    def __init__(self):
        self.supported_extensions = ['.pdf']
        pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd
    
    def can_process(self, file_path: str) -> bool:
        return Path(file_path).suffix.lower() in self.supported_extensions
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        try:
            doc = fitz.open(pdf_path)
            text = ""
            
            for page in doc:
                text += page.get_text()
            
            doc.close()
            return text.strip()
        except Exception as e:
            log.error(f"Error extracting text from PDF: {e}")
            return ""
    
    def extract_images_from_pdf(self, pdf_path: str) -> List[Image.Image]:
        images = []
        
        try:
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                image_list = page.get_images(full=True)
                
                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    
                    image = Image.open(io.BytesIO(image_bytes))
                    images.append(image)
            
            doc.close()
            return images
        except Exception as e:
            log.error(f"Error extracting images from PDF: {e}")
            return []
    
    def ocr_on_images(self, images: List[Image.Image]) -> str:
        ocr_text = ""
        
        for img in images:
            try:
                text = pytesseract.image_to_string(
                    img,
                    lang=settings.ocr_language,
                    config=f'--dpi {settings.ocr_dpi}'
                )
                ocr_text += text + "\n"
            except Exception as e:
                log.error(f"OCR error on PDF image: {e}")
        
        return ocr_text.strip()
    
    def process(self, file_path: str) -> Tuple[List[str], Dict[str, Any]]:
        try:
            pdf_text = self.extract_text_from_pdf(file_path)
            
            images = self.extract_images_from_pdf(file_path)
            
            ocr_text = ""
            if images:
                ocr_text = self.ocr_on_images(images)
            
            combined_text = pdf_text
            if ocr_text and len(pdf_text) < 100:
                combined_text = pdf_text + "\n" + ocr_text
            
            if combined_text:
                # CRITICAL FIX: Actually chunk the PDF text properly!
                chunks_with_indices = chunk_text(combined_text, method="smart")
                chunks = [chunk for chunk, _ in chunks_with_indices]
            else:
                chunks = [f"PDF file: {Path(file_path).name} (no text extracted)"]
            
            metadata = {
                'file_type': 'pdf',
                'file_path': str(file_path),
                'filename': Path(file_path).name,
                'has_text': bool(pdf_text),
                'has_images': bool(images),
                'num_images': len(images),
                'text_length': len(pdf_text),
                'ocr_text_length': len(ocr_text),
                'total_chunks': len(chunks),
                'extension': Path(file_path).suffix
            }
            
            log.info(f"Processed PDF: {file_path} -> {len(chunks)} chunks, {len(images)} images")
            return chunks, metadata
            
        except Exception as e:
            log.error(f"Error processing PDF {file_path}: {e}")
            raise


pdf_processor = PDFProcessor()

__all__ = ["PDFProcessor", "pdf_processor"]