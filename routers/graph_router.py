"""
API routes for Knowledge Graph operations
"""
import time
import logging
from datetime import datetime
from typing import Optional, Dict

from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Form
from pydantic import BaseModel, Field

from models.schemas import (
    UploadResponse,
    QuestionRequest,
    QuestionResponse,
    GraphStats,
    GraphVisualization,
    HealthResponse,
    DeleteGraphRequest,
    DeleteGraphResponse,
    EnvironmentUpdateRequest,
    EnvironmentUpdateResponse,
    FullConfigResponse
)
from services.graph_service import graph_service
from services.rag_service import rag_service
from config import get_settings, update_settings_from_dict, get_current_env_vars

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/graph", tags=["Knowledge Graph"])
settings = get_settings()


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(..., description="Document to process (PDF, DOCX, TXT, MD)"),
    group_id: Optional[str] = Form(default=None, description="Group ID for the knowledge graph")
):
    """
    Upload a document and create a knowledge graph from it.

    Supported formats: PDF, DOCX, TXT, MD
    """
    start_time = time.time()
    group_id = group_id or "default"

    # Validate file type
    allowed_extensions = {".pdf", ".docx", ".txt", ".md"}
    file_ext = "." + file.filename.split(".")[-1].lower() if "." in file.filename else ""

    if file_ext not in allowed_extensions:
        logger.warning(f"[UPLOAD] Rejected unsupported file type: {file_ext}")
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file_ext}. Allowed: {allowed_extensions}"
        )

    try:
        # Read file content
        content = await file.read()

        if len(content) == 0:
            logger.warning("[UPLOAD] Rejected empty file")
            raise HTTPException(status_code=400, detail="Empty file uploaded")

        # Process document and create knowledge graph
        logger.info(f"[UPLOAD] Processing {file.filename} ({len(content)} bytes) for group '{group_id}'")
        document_id, nodes_created, edges_created = await graph_service.process_document(
            file_content=content,
            filename=file.filename,
            group_id=group_id
        )

        processing_time = time.time() - start_time
        logger.info(f"[UPLOAD] Completed {file.filename} - {nodes_created} nodes, {edges_created} edges in {processing_time:.1f}s")

        return UploadResponse(
            success=True,
            message=f"Successfully processed {file.filename}",
            document_id=document_id,
            nodes_created=nodes_created,
            edges_created=edges_created,
            processing_time_seconds=round(processing_time, 2)
        )

    except ValueError as e:
        logger.warning(f"[UPLOAD] Validation error for {file.filename}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[UPLOAD] Error processing document {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")


@router.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """
    Ask a question and get an answer based on the knowledge graph using Graph RAG.
    """
    try:
        logger.info(f"[ASK] Answering question for group '{request.group_id or 'default'}'")
        result = await rag_service.answer_question(
            question=request.question,
            group_id=request.group_id,
            top_k=request.top_k
        )

        sources_count = len(result.get('sources', []))
        confidence = result.get('confidence', 0)
        logger.info(f"[ASK] Answer generated - {sources_count} sources, confidence: {confidence:.2f}")

        return QuestionResponse(**result)

    except Exception as e:
        logger.error(f"[ASK] Failed to answer question: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error answering question: {str(e)}")


@router.get("/stats", response_model=GraphStats)
async def get_graph_stats(
    group_id: Optional[str] = Query(default=None, description="Filter by group ID")
):
    """
    Get statistics about the knowledge graph.
    """
    try:
        stats = await graph_service.get_graph_stats(group_id)
        total_nodes = stats.get('total_nodes', 0)
        total_edges = stats.get('total_edges', 0)
        logger.info(f"[STATS] Graph stats - {total_nodes} nodes, {total_edges} edges")
        return GraphStats(**stats)
    except Exception as e:
        logger.error(f"[STATS] Failed to get graph stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")


@router.get("/visualize", response_model=GraphVisualization)
async def get_graph_visualization(
    group_id: Optional[str] = Query(default=None, description="Filter by group ID"),
    limit: int = Query(default=100, ge=1, le=500, description="Maximum nodes to return")
):
    """
    Get graph data for visualization (nodes and edges).
    """
    try:
        data = await graph_service.get_graph_visualization(group_id, limit)
        nodes_count = len(data['nodes'])
        edges_count = len(data['edges'])
        logger.info(f"[VISUALIZE] Retrieved graph data - {nodes_count} nodes, {edges_count} edges")
        return GraphVisualization(
            nodes=data["nodes"],
            edges=data["edges"]
        )
    except Exception as e:
        logger.error(f"[VISUALIZE] Failed to get visualization data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting visualization: {str(e)}")


@router.post("/search")
async def search_graph(
    query: str = Query(..., min_length=1, description="Search query"),
    group_id: Optional[str] = Query(default=None, description="Filter by group ID"),
    top_k: int = Query(default=10, ge=1, le=50, description="Number of results")
):
    """
    Search the knowledge graph for relevant facts.
    """
    try:
        results = await graph_service.search(
            query=query,
            group_id=group_id,
            top_k=top_k
        )
        results_count = len(results)
        logger.info(f"[SEARCH] Found {results_count} results for query")
        return {"results": results, "count": results_count}
    except Exception as e:
        logger.error(f"[SEARCH] Failed to search graph: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error searching: {str(e)}")


@router.delete("/delete", response_model=DeleteGraphResponse)
async def delete_graph(request: DeleteGraphRequest):
    """
    Delete a knowledge graph by group ID.
    """
    if not request.confirm:
        logger.warning(f"[DELETE] Attempted to delete graph '{request.group_id}' without confirmation")
        raise HTTPException(
            status_code=400,
            detail="Please set 'confirm' to true to delete the graph"
        )

    try:
        logger.info(f"[DELETE] Deleting graph '{request.group_id}'")
        nodes_deleted, edges_deleted = await graph_service.delete_graph(request.group_id)
        logger.info(f"[DELETE] Deleted graph '{request.group_id}' - {nodes_deleted} nodes, {edges_deleted} edges")

        return DeleteGraphResponse(
            success=True,
            message=f"Successfully deleted graph: {request.group_id}",
            nodes_deleted=nodes_deleted,
            edges_deleted=edges_deleted
        )
    except Exception as e:
        logger.error(f"[DELETE] Failed to delete graph '{request.group_id}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting graph: {str(e)}")


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Check the health of the service and Neo4j connection.
    """
    neo4j_connected = await graph_service.check_connection()

    status = "healthy" if neo4j_connected else "degraded"
    logger.info(f"[HEALTH] Status: {status}, Neo4j: {'connected' if neo4j_connected else 'disconnected'}")

    return HealthResponse(
        status=status,
        neo4j_connected=neo4j_connected,
        timestamp=datetime.now()
    )


@router.get("/groups")
async def list_groups():
    """
    List all knowledge graph groups.
    """
    try:
        stats = await graph_service.get_graph_stats()
        groups = stats.get("groups", [])
        logger.info(f"[GROUPS] Found {len(groups)} knowledge graph groups")
        return {"groups": groups}
    except Exception as e:
        logger.error(f"[GROUPS] Failed to list groups: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing groups: {str(e)}")


class FullConfigResponse(BaseModel):
    """Complete configuration response with all settings and env vars"""
    # Provider settings
    llm_provider: str
    embedding_provider: str

    # LLM Configuration
    llm_model: Optional[str] = None
    llm_deployment: Optional[str] = None
    llm_api_key_masked: bool = False

    # Embedding Configuration
    embedding_model: Optional[str] = None
    embedding_deployment: Optional[str] = None
    embedding_api_key_masked: bool = False

    # API endpoints
    azure_endpoint: Optional[str] = None
    azure_api_version: Optional[str] = None
    openai_base_url: Optional[str] = None

    # Neo4j Configuration
    neo4j_uri: Optional[str] = None
    neo4j_username: Optional[str] = None
    neo4j_database: Optional[str] = None
    neo4j_password_masked: bool = False

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True

    # Processing settings
    chunk_size: int = 1000
    chunk_overlap: int = 200

    # All environment variables (masked)
    environment_variables: Dict[str, str] = Field(default_factory=dict)


@router.api_route("/config", methods=["GET", "POST"])
async def handle_configuration(request: Optional[EnvironmentUpdateRequest] = None):
    """
    Unified configuration endpoint.
    GET: Retrieve complete configuration
    POST: Update configuration with environment variables
    """
    # Handle POST request (update configuration)
    if request and hasattr(request, 'env_vars') and request.env_vars:
        try:
            # Update settings with new environment variables
            updated_settings = update_settings_from_dict(request.env_vars)

            # Get list of updated variables
            updated_vars = list(request.env_vars.keys())

            # Check if restart is required (for major config changes)
            requires_restart = any(var in [
                'LLM_PROVIDER', 'EMBEDDING_PROVIDER', 'AZURE_OPENAI_ENDPOINT',
                'AZURE_OPENAI_API_KEY', 'OPENAI_API_KEY', 'NEO4J_URI'
            ] for var in updated_vars)

            logger.info(f"[CONFIG] Updated {len(updated_vars)} settings" + (" (restart required)" if requires_restart else ""))

            return EnvironmentUpdateResponse(
                success=True,
                message=f"Configuration updated successfully. {len(updated_vars)} variables changed.",
                updated_vars=updated_vars,
                requires_restart=requires_restart
            )

        except Exception as e:
            logger.error(f"[CONFIG] Error updating configuration: {e}")
            raise HTTPException(status_code=500, detail=f"Error updating configuration: {str(e)}")
    try:
        settings = get_settings()

        # Get current env vars with masking
        env_vars = get_current_env_vars()
        sensitive_keys = ['API_KEY', 'PASSWORD']
        for key in env_vars:
            if any(sensitive in key.upper() for sensitive in sensitive_keys):
                env_vars[key] = "***"

        # Build response using FullConfigResponse model
        return FullConfigResponse(
            llm_provider=settings.llm_provider,
            embedding_provider=settings.embedding_provider,

            # LLM Configuration - explicitly show the model used for GraphRAG creation
            llm_model=settings.openai_model if settings.llm_provider == "openai" else None,
            llm_deployment=settings.azure_openai_deployment_name if settings.llm_provider == "azure" else None,
            llm_api_key_masked=bool(settings.openai_api_key if settings.llm_provider == "openai" else settings.azure_openai_api_key),

            # Embedding Configuration
            embedding_model=settings.openai_embedding_model if settings.embedding_provider == "openai" else None,
            embedding_deployment=settings.azure_openai_embedding_deployment if settings.embedding_provider == "azure" else None,
            embedding_api_key_masked=bool(settings.openai_api_key if settings.embedding_provider == "openai" else settings.azure_openai_api_key),

            # API endpoints
            azure_endpoint=settings.azure_openai_endpoint,
            azure_api_version=settings.azure_openai_api_version,
            openai_base_url=settings.openai_base_url,

            # Neo4j Configuration
            neo4j_uri=settings.neo4j_uri,
            neo4j_username=settings.neo4j_username,
            neo4j_database=settings.neo4j_database,
            neo4j_password_masked=bool(settings.neo4j_password),

            # Server settings
            host=settings.host,
            port=settings.port,
            debug=settings.debug,

            # Processing settings
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,

            # All environment variables (masked)
            environment_variables=env_vars
        )

    except Exception as e:
        logger.error(f"Error getting full configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting configuration: {str(e)}")


@router.post("/config", response_model=EnvironmentUpdateResponse)
async def update_configuration(request: EnvironmentUpdateRequest):
    """
    Update configuration and environment variables.
    This single endpoint handles all configuration updates.
    """
    try:
        # Update settings with new environment variables
        updated_settings = update_settings_from_dict(request.env_vars)

        # Get list of updated variables
        updated_vars = list(request.env_vars.keys())

        # Check if restart is required (for major config changes)
        requires_restart = any(var in [
            'LLM_PROVIDER', 'EMBEDDING_PROVIDER', 'AZURE_OPENAI_ENDPOINT',
            'AZURE_OPENAI_API_KEY', 'OPENAI_API_KEY', 'NEO4J_URI'
        ] for var in updated_vars)

        return EnvironmentUpdateResponse(
            success=True,
            message=f"Configuration updated successfully. {len(updated_vars)} variables changed.",
            updated_vars=updated_vars,
            requires_restart=requires_restart
        )

    except Exception as e:
        logger.error(f"Error updating configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating configuration: {str(e)}")

