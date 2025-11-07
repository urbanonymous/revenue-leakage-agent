"""FastAPI server for Revenue Leakage Agent"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import get_settings
from src.routes import investigation, proposals, chat, audit

# Get settings
settings = get_settings()

# Create FastAPI app with configured settings
app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version
)

# Configure CORS with settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Include routers
app.include_router(investigation.router)
app.include_router(proposals.router)
app.include_router(chat.router)
app.include_router(audit.router)


# Health check endpoints
@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Revenue Leakage Detection Agent",
        "version": "1.0.0"
    }


@app.get("/api/health")
async def health():
    """Detailed health check"""
    from src.services import get_sandbox_manager
    sandbox = get_sandbox_manager()
    
    return {
        "status": "healthy",
        "openai_configured": bool(settings.openai_api_key),
        "openai_model": settings.openai_model,
        "api_version": settings.api_version,
        "sandbox_stats": sandbox.get_stats()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        reload=settings.reload
    )

