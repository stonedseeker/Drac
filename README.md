# DRAC: Dynamic Retrieval Across Content

A production-ready Retrieval-Augmented Generation system that processes and queries multiple data formats including images, text documents, and PDFs with mixed content.

### Core Capabilities
- Multi-format document processing (TXT, PDF, PNG, JPG, JPEG, DOCX, XLSX)
- Dense vector search using OpenAI embeddings
- Sparse retrieval using BM25
- Hybrid search combining dense and sparse methods
- Reranking for improved results
- OCR for image and PDF text extraction
- Intelligent text chunking
- Metadata management
- Caching for performance
- LLM traceability
- Input/output guardrails

### Features
- Batch document upload
- Async processing
- Query expansion
- Cross-modal retrieval
- RESTful API with FastAPI
- Interactive web interface
- Comprehensive logging
- Unit tests


## Prerequisites

- Python 3.11.9
- Tesseract OCR
- OpenAI API key
- Windows 11 / Linux / macOS

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/stonedseeker/Drac.git
cd Drac
```

### 2. Create Conda Environment

```bash
conda create -n Drac python=3.11.9 -y
conda activate Drac
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Tesseract OCR

**Windows:**
Download and install from: https://github.com/UB-Mannheim/tesseract/wiki
Default path: `C:\Program Files\Tesseract-OCR\tesseract.exe`

**Linux:**
```bash
sudo apt-get install tesseract-ocr
```

**macOS:**
```bash
brew install tesseract
```

### 5. Configure Environment

Edit `.env`:
```env
OPENAI_API_KEY=your_openai_api_key_here
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
```

## Usage

### Start the API Server

```bash
cd Drac
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Server will be available at: http://localhost:8000

### API Documentation

Interactive API docs: http://localhost:8000/docs

## API Endpoints

### Upload Document

```bash
curl -X POST "http://localhost:8000/api/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.pdf"
```

### Batch Upload

```bash
curl -X POST "http://localhost:8000/api/upload/batch" \
  -F "files=@doc1.pdf" \
  -F "files=@doc2.txt" \
  -F "files=@image.png"
```

### Query Documents

```bash
curl -X POST "http://localhost:8000/api/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is machine learning?",
    "top_k": 10,
    "enable_reranking": true
  }'
```

### Health Check

```bash
curl http://localhost:8000/health
```

## Sample Queries

```python
import requests

response = requests.post('http://localhost:8000/api/query', json={
    'query': 'Find documents about sales data',
    'top_k': 5,
    'enable_reranking': True,
    'file_types': ['pdf', 'xlsx']
})

results = response.json()
```

## Testing

Run all tests:

```bash
pytest tests/ -v
```

Run specific test file:

```bash
pytest tests/test_ingestion.py -v
```

Run with coverage:

```bash
pytest tests/ --cov=app --cov-report=html
```

## Future Enhancements

- [ ] Support for audio/video files
- [ ] Multi-language support
- [ ] Document summarization
- [ ] Conversation memory
- [ ] Advanced analytics
- [ ] User authentication
- [ ] Cloud deployment
- [ ] GPU acceleration

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

