from typing import List, Union
import openai
from PIL import Image
import torch
from sentence_transformers import SentenceTransformer
import numpy as np
from app.config import settings
from app.utils.logging_config import log
from app.core.cache import cache_manager
from app.tracing.tracer import tracer


class TextEmbedder:
    
    def __init__(self):
        self.model_name = settings.text_embedding_model
        self.use_openai = settings.openai_api_key and settings.validate_api_key()
        
        if not self.use_openai:
            log.warning("OpenAI API key not found, using sentence-transformers")
            self.local_model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def embed_text(self, text: str) -> List[float]:
        cached = cache_manager.get_embedding(text)
        if cached is not None:
            return cached
        
        try:
            if self.use_openai:
                embedding = self._embed_with_openai(text)
            else:
                embedding = self._embed_with_local(text)
            
            cache_manager.set_embedding(text, embedding)
            return embedding
        except Exception as e:
            log.error(f"Embedding error: {e}")
            raise
    
    def _embed_with_openai(self, text: str) -> List[float]:
        tracer.log_step("openai_embedding", {"text_length": len(text)})
        
        client = openai.OpenAI(api_key=settings.openai_api_key)
        response = client.embeddings.create(
            model=self.model_name,
            input=text
        )
        
        embedding = response.data[0].embedding
        tracer.log_llm_call(
            model=self.model_name,
            prompt=text[:100],
            response="embedding_generated",
            tokens_used=response.usage.total_tokens
        )
        
        return embedding
    
    def _embed_with_local(self, text: str) -> List[float]:
        embedding = self.local_model.encode(text, convert_to_tensor=True)
        return embedding.cpu().numpy().tolist()
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        embeddings = []
        for text in texts:
            embeddings.append(self.embed_text(text))
        return embeddings


class ImageEmbedder:
    
    def __init__(self):
        self.model_name = settings.image_embedding_model
        try:
            from transformers import CLIPProcessor, CLIPModel
            self.model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
            self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
            log.info("CLIP model loaded successfully")
        except Exception as e:
            log.error(f"Failed to load CLIP model: {e}")
            self.model = None
            self.processor = None
    
    def embed_image(self, image: Union[Image.Image, str]) -> List[float]:
        if self.model is None:
            raise RuntimeError("CLIP model not available")
        
        try:
            if isinstance(image, str):
                image = Image.open(image).convert("RGB")
            
            inputs = self.processor(images=image, return_tensors="pt")
            
            with torch.no_grad():
                image_features = self.model.get_image_features(**inputs)
            
            embedding = image_features.squeeze().cpu().numpy().tolist()
            return embedding
        except Exception as e:
            log.error(f"Image embedding error: {e}")
            raise
    
    def embed_image_with_text(self, image: Union[Image.Image, str], text: str = None) -> List[float]:
        if text:
            img_emb = self.embed_image(image)
            text_embedder = TextEmbedder()
            text_emb = text_embedder.embed_text(text)
            
            combined = np.array(img_emb) + np.array(text_emb[:len(img_emb)])
            return combined.tolist()
        
        return self.embed_image(image)


text_embedder = TextEmbedder()
image_embedder = ImageEmbedder()

__all__ = ["TextEmbedder", "ImageEmbedder", "text_embedder", "image_embedder"]