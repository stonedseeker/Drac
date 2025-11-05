from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.utils.logging_config import log
from app.api import health, upload, query

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Multimodal RAG System supporting text, images, PDFs, DOCX, and XLSX files"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["health"])
app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(query.router, prefix="/api", tags=["query"])


@app.on_event("startup")
async def startup_event():
    log.info(f"Starting {settings.app_name} v{settings.app_version}")
    settings.ensure_directories()
    log.info("Application startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    log.info("Shutting down application")


@app.get("/")
async def root():
    return {
        "message": "Multimodal RAG System API",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    log.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )


__all__ = ["app"]