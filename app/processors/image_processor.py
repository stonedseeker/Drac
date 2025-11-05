from pathlib import Path
from typing import Dict, Any, List, Tuple
from PIL import Image
import pytesseract
from app.config import settings
from app.utils.logging_config import log
from app.utils.chunking import chunk_text


class ImageProcessor:
    
    def __init__(self):
        self.supported_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']
        pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd
    
    def can_process(self, file_path: str) -> bool:
        return Path(file_path).suffix.lower() in self.supported_extensions
    
    def extract_text_from_image(self, image_path: str) -> str:
        try:
            image = Image.open(image_path)
            
            text = pytesseract.image_to_string(
                image,
                lang=settings.ocr_language,
                config=f'--dpi {settings.ocr_dpi}'
            )
            
            return text.strip()
        except Exception as e:
            log.error(f"OCR error for {image_path}: {e}")
            return ""
    
    def process(self, file_path: str) -> Tuple[List[str], Dict[str, Any]]:
        try:
            image = Image.open(file_path)
            
            ocr_text = self.extract_text_from_image(file_path)
            
            if ocr_text:
                chunks_with_indices = chunk_text(ocr_text, method="smart")
                chunks = [chunk for chunk, _ in chunks_with_indices]
            else:
                chunks = [f"Image file: {Path(file_path).name} (no text detected)"]
            
            metadata = {
                'file_type': 'image',
                'file_path': str(file_path),
                'filename': Path(file_path).name,
                'image_size': image.size,
                'image_mode': image.mode,
                'has_text': bool(ocr_text),
                'ocr_text_length': len(ocr_text),
                'total_chunks': len(chunks),
                'extension': Path(file_path).suffix
            }
            
            log.info(f"Processed image: {file_path} -> {len(chunks)} chunks")
            return chunks, metadata
            
        except Exception as e:
            log.error(f"Error processing image {file_path}: {e}")
            raise


image_processor = ImageProcessor()

__all__ = ["ImageProcessor", "image_processor"]