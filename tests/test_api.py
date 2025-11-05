import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "version" in data
    assert "database_status" in data


def test_stats_endpoint():
    response = client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_documents" in data
    assert "total_chunks" in data


def test_query_endpoint_missing_query():
    response = client.post("/api/query", json={})
    assert response.status_code == 422


def test_query_endpoint_empty_query():
    response = client.post("/api/query", json={"query": ""})
    assert response.status_code == 422


def test_query_endpoint_valid():
    response = client.post("/api/query", json={
        "query": "test query",
        "top_k": 5
    })
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "processing_time" in data


def test_simple_search_endpoint():
    response = client.get("/api/search?q=test&top_k=5")
    assert response.status_code == 200
    data = response.json()
    assert "query" in data
    assert "results" in data


def test_list_documents_endpoint():
    response = client.get("/api/documents")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "documents" in data