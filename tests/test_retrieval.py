import pytest
from app.core.retrieval import retrieval_system
from app.core.embeddings import text_embedder
from app.database.vector_store import vector_store


def test_text_embedder():
    text = "This is a test sentence for embedding."
    embedding = text_embedder.embed_text(text)
    
    assert embedding is not None
    assert isinstance(embedding, list)
    assert len(embedding) > 0


def test_retrieval_empty_query():
    from app.utils.guardrails import guardrails
    
    is_valid, error = guardrails.validate_query("")
    assert not is_valid
    assert error is not None


def test_retrieval_valid_query():
    from app.utils.guardrails import guardrails
    
    is_valid, error = guardrails.validate_query("valid query text")
    assert is_valid
    assert error is None


def test_sanitize_query():
    from app.utils.guardrails import guardrails
    
    dirty_query = "  test   query  <script>alert('xss')</script>  "
    clean_query = guardrails.sanitize_query(dirty_query)
    
    assert "<script>" not in clean_query
    assert clean_query.strip() == clean_query
    assert "  " not in clean_query


def test_cache_operations():
    from app.core.cache import cache_manager
    
    test_key = "test_key"
    test_value = {"data": "test"}
    
    cache_manager.set(test_key, test_value)
    
    retrieved = cache_manager.get(test_key)
    assert retrieved == test_value
    
    cache_manager.clear()