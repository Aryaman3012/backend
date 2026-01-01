"""
Knowledge Graph RAG Backend
FastAPI application for generating knowledge graphs from documents
and answering questions using Graph RAG
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings, update_settings_from_dict
from routers.graph_router import router as graph_router
from services.graph_service import graph_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    logger.info("Starting Knowledge Graph RAG Backend")
    settings = get_settings()

    # Check graph service availability
    try:
        available = await graph_service.check_connection()
        if available:
            logger.info("GraphRAG service ready")
        else:
            logger.warning("GraphRAG service unavailable")
    except Exception as e:
        logger.error(f"Failed to check GraphRAG service: {e}")

    logger.info(f"API server started on port {settings.port}")

    yield

    # Shutdown
    logger.info("Shutting down server")


# Create FastAPI application
app = FastAPI(
    title="Knowledge Graph RAG API",
    description="""
    A powerful API for generating knowledge graphs from documents 
    and answering questions using Graph RAG (Retrieval-Augmented Generation).
    
    ## Features
    
    - **Document Upload**: Upload PDF, DOCX, TXT, or MD files to create knowledge graphs
    - **Graph RAG Q&A**: Ask questions and get answers based on the knowledge graph
    - **Graph Visualization**: Get graph data for visualization
    - **Multi-Graph Support**: Organize knowledge into separate groups
    
    ## How it works
    
    1. Upload a document via `/api/graph/upload`
    2. The system extracts text, identifies entities and relationships
    3. A knowledge graph is built in Neo4j using LLM-based entity extraction
    4. Ask questions via `/api/graph/ask` to get RAG-powered answers
    """,
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(graph_router)


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Knowledge Graph RAG API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/graph/health"
    }


@app.get("/ping")
async def ping():
    """Simple ping endpoint"""
    return {"status": "pong"}


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=False  # Temporarily disabled for direct log viewing
    )

