"""
Pydantic schemas for API requests and responses
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class FileType(str, Enum):
    """Supported file types"""
    PDF = "pdf"
    TXT = "txt"
    DOCX = "docx"
    MD = "md"


class UploadResponse(BaseModel):
    """Response after file upload and graph creation"""
    success: bool
    message: str
    document_id: str
    nodes_created: int = 0
    edges_created: int = 0
    processing_time_seconds: float = 0.0


class QuestionRequest(BaseModel):
    """Request to ask a question against the knowledge graph"""
    question: str = Field(..., min_length=1, max_length=2000)
    group_id: Optional[str] = Field(default=None, description="Knowledge graph group to query")
    top_k: int = Field(default=10, ge=1, le=50, description="Number of relevant facts to retrieve")


class QuestionResponse(BaseModel):
    """Response to a question"""
    question: str
    answer: str
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    entities_used: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class GraphNode(BaseModel):
    """Representation of a node in the knowledge graph"""
    id: str
    name: str
    type: str
    properties: Dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    """Representation of an edge in the knowledge graph"""
    id: str
    source: str
    target: str
    relationship: str
    properties: Dict[str, Any] = Field(default_factory=dict)


class GraphStats(BaseModel):
    """Statistics about the knowledge graph"""
    total_nodes: int
    total_edges: int
    node_types: Dict[str, int]
    edge_types: Dict[str, int]
    groups: List[str]


class GraphVisualization(BaseModel):
    """Data for graph visualization"""
    nodes: List[GraphNode]
    edges: List[GraphEdge]


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    neo4j_connected: bool
    timestamp: datetime


class DeleteGraphRequest(BaseModel):
    """Request to delete a knowledge graph"""
    group_id: str
    confirm: bool = False


class DeleteGraphResponse(BaseModel):
    """Response after graph deletion"""
    success: bool
    message: str
    nodes_deleted: int = 0
    edges_deleted: int = 0


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


class ProviderConfig(BaseModel):
    """Configuration for LLM/Embedding providers"""
    provider: str  # "openai" or "azure"
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    api_version: Optional[str] = None
    model: Optional[str] = None  # LLM model (for chat/completion)
    deployment_name: Optional[str] = None  # Azure deployment for LLM
    embedding_model: Optional[str] = None  # Embedding model name
    embedding_deployment: Optional[str] = None  # Azure deployment for embeddings


class EnvironmentConfig(BaseModel):
    """Complete environment configuration"""
    llm_provider: str = "azure"
    embedding_provider: str = "azure"
    llm_config: ProviderConfig
    embedding_config: ProviderConfig
    neo4j_uri: Optional[str] = None
    neo4j_username: Optional[str] = None
    neo4j_password: Optional[str] = None
    neo4j_database: Optional[str] = None


class EnvironmentUpdateRequest(BaseModel):
    """Request to update environment variables"""
    env_vars: Dict[str, str] = Field(..., description="Environment variables to update")


class EnvironmentUpdateResponse(BaseModel):
    """Response after environment update"""
    success: bool
    message: str
    updated_vars: List[str] = Field(default_factory=list)
    requires_restart: bool = False


