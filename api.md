# Knowledge Graph RAG API Documentation

## Overview

The Knowledge Graph RAG API provides a comprehensive set of endpoints for managing knowledge graphs, processing documents with Microsoft GraphRAG 2.x, and performing Graph RAG (Retrieval-Augmented Generation) queries. Supports dynamic configuration of OpenAI and Azure OpenAI providers through a unified configuration endpoint.

## Base URL
```
http://localhost:8000/api/graph
```

## Authentication
Currently, no authentication is required. Configure API keys through environment variables or the unified configuration endpoint.

## Key Features

- **GraphRAG 2.x Integration**: Advanced knowledge graph construction with entity extraction and relationship mapping
- **Multi-Provider Support**: OpenAI and Azure OpenAI with dynamic switching
- **Unified Configuration**: Single endpoint for all environment variable management
- **Real-time Updates**: Change providers and settings without server restart
- **Secure Credential Handling**: Automatic masking of sensitive API keys

---

## Configuration Management

### Unified Configuration Endpoint
Single endpoint for all configuration operations - retrieve current settings and update them dynamically.

**Endpoint:** `GET|POST /config`

#### GET: Retrieve Complete Configuration
Get current provider settings, API configurations, and all environment variables.

**Request:**
```http
GET /api/graph/config
```

**Response:**
```json
{
  "llm_provider": "azure",
  "embedding_provider": "azure",

  "llm_model": null,
  "llm_deployment": "gpt-4o",
  "llm_api_key_masked": true,

  "embedding_model": null,
  "embedding_deployment": "text-embedding-3-small",
  "embedding_api_key_masked": true,

  "azure_endpoint": "https://your-resource.openai.azure.com/",
  "azure_api_version": "2024-12-01-preview",
  "openai_base_url": null,

  "neo4j_uri": "neo4j+s://your-instance.databases.neo4j.io",
  "neo4j_username": "neo4j",
  "neo4j_database": "neo4j",
  "neo4j_password_masked": true,

  "host": "0.0.0.0",
  "port": 8000,
  "debug": true,
  "chunk_size": 1000,
  "chunk_overlap": 200,

  "environment_variables": {
    "LLM_PROVIDER": "azure",
    "EMBEDDING_PROVIDER": "azure",
    "AZURE_OPENAI_ENDPOINT": "https://your-resource.openai.azure.com/",
    "AZURE_OPENAI_API_KEY": "***",
    "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-4o",
    "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": "text-embedding-3-small",
    "NEO4J_URI": "neo4j+s://your-instance.databases.neo4j.io",
    "NEO4J_USERNAME": "neo4j",
    "NEO4J_PASSWORD": "***",
    "HOST": "0.0.0.0",
    "PORT": "8000"
  }
}
```

**Key Fields:**
- `llm_deployment`: The Azure/OpenAI model used for **GraphRAG creation** (knowledge graph building)
- `embedding_deployment`: The model used for text embeddings
- `environment_variables`: All current environment variables (sensitive data masked with `***`)

#### POST: Update Configuration
Dynamically update environment variables and provider configurations.

**Request:**
```http
POST /api/graph/config
Content-Type: application/json

{
  "env_vars": {
    "LLM_PROVIDER": "openai",
    "EMBEDDING_PROVIDER": "azure",
    "OPENAI_API_KEY": "your-openai-key",
    "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": "text-embedding-3-small",
    "NEO4J_URI": "neo4j+s://new-instance.databases.neo4j.io"
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Configuration updated successfully. 5 variables changed.",
  "updated_vars": [
    "LLM_PROVIDER",
    "EMBEDDING_PROVIDER",
    "OPENAI_API_KEY",
    "AZURE_OPENAI_EMBEDDING_DEPLOYMENT",
    "NEO4J_URI"
  ],
  "requires_restart": true
}
```

**Notes:**
- `requires_restart`: Indicates if server restart is needed for changes to take full effect
- Changes are applied immediately where possible
- Sensitive data in updates is masked in responses
- Supports switching between OpenAI and Azure providers dynamically

**Response:**
```json
{
  "env_vars": {
    "LLM_PROVIDER": "azure",
    "AZURE_OPENAI_API_KEY": "***",
    "NEO4J_PASSWORD": "***",
    "HOST": "0.0.0.0"
  }
}
```

---

## Document Processing

### Upload Document
Process a document and create/update a knowledge graph using Microsoft GraphRAG 2.x.

**Endpoint:** `POST /upload`

**Content-Type:** `multipart/form-data`

**Parameters:**
- `file` (required): Document file (PDF, DOCX, TXT, MD)
- `group_id` (optional): Knowledge graph group identifier

**Processing Details:**
- Uses the currently configured LLM model (see `llm_deployment` in config)
- Performs entity extraction and relationship mapping
- Creates knowledge graph in Neo4j database
- Supports incremental updates to existing graphs

**Response:**
```json
{
  "success": true,
  "message": "Successfully processed document.pdf",
  "document_id": "doc_a1b2c3d4",
  "nodes_created": 5,
  "edges_created": 8,
  "processing_time_seconds": 12.34
}
```

**Supported Formats:**
- PDF (.pdf)
- Microsoft Word (.docx)
- Plain Text (.txt)
- Markdown (.md)

**Error Responses:**
- `400`: Unsupported file type or empty file
- `500`: Processing error (check provider configuration)

---

## Question Answering (Graph RAG)

### Ask Question
Perform a Graph RAG query to answer questions using the knowledge graph.

**Endpoint:** `POST /ask`

**Request Body:**
```json
{
  "question": "What are the key concepts discussed in the document?",
  "group_id": "optional_group_name",
  "top_k": 10
}
```

**Parameters:**
- `question` (required): Question to answer
- `group_id` (optional): Specific knowledge graph group
- `top_k` (optional): Number of relevant facts to retrieve (1-50, default: 10)

**Processing Details:**
- Searches the knowledge graph for relevant facts
- Uses the configured LLM model for answer generation
- Provides source attribution and confidence scores

**Response:**
```json
{
  "question": "What are the key concepts discussed in the document?",
  "answer": "The document discusses several key concepts including...",
  "sources": [
    {
      "fact": "Graph RAG is a technique for...",
      "source": "document.pdf",
      "score": 0.87
    }
  ],
  "entities_used": ["Graph RAG", "Knowledge Graph"],
  "confidence": 0.92
}
```

---

## Graph Data Access

### Get Graph Statistics
Retrieve statistics about knowledge graphs.

**Endpoint:** `GET /stats`

**Query Parameters:**
- `group_id` (optional): Filter by specific group

**Response:**
```json
{
  "total_nodes": 15,
  "total_edges": 23,
  "node_types": {
    "Person": 3,
    "Organization": 5,
    "Concept": 7
  },
  "edge_types": {
    "WORKS_AT": 3,
    "RELATED_TO": 20
  },
  "groups": ["default", "project_docs"]
}
```

### Get Graph Visualization Data
Get nodes and edges for graph visualization.

**Endpoint:** `GET /visualize`

**Query Parameters:**
- `group_id` (optional): Filter by specific group
- `limit` (optional): Maximum nodes to return (1-500, default: 100)

**Response:**
```json
{
  "nodes": [
    {
      "id": "entity_123",
      "name": "John Smith",
      "type": "Person",
      "properties": {
        "description": "Software engineer at Microsoft"
      }
    }
  ],
  "edges": [
    {
      "id": "rel_456",
      "source": "entity_123",
      "target": "entity_789",
      "relationship": "WORKS_AT",
      "properties": {
        "description": "Employment relationship"
      }
    }
  ]
}
```

### Search Graph
Perform semantic search across the knowledge graph.

**Endpoint:** `POST /search`

**Query Parameters:**
- `query` (required): Search query
- `group_id` (optional): Filter by specific group
- `top_k` (optional): Number of results (1-50, default: 10)

**Response:**
```json
{
  "results": [
    {
      "fact": "Graph RAG combines graph databases with LLM retrieval",
      "source": "introduction.pdf",
      "score": 0.94,
      "entities": ["Graph RAG", "LLM"]
    }
  ],
  "count": 1
}
```

### List Groups
Get all available knowledge graph groups.

**Endpoint:** `GET /groups`

**Response:**
```json
{
  "groups": ["default", "project_docs", "research_papers"]
}
```

---

## Graph Management

### Delete Graph
Remove a knowledge graph group and all its data.

**Endpoint:** `DELETE /delete`

**Request Body:**
```json
{
  "group_id": "group_to_delete",
  "confirm": true
}
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully deleted graph: group_to_delete",
  "nodes_deleted": 15,
  "edges_deleted": 23
}
```

**Notes:**
- Requires `confirm: true` to prevent accidental deletion
- Permanently removes all nodes and edges in the specified group

---

## Health Monitoring

### Health Check
Check service and database connectivity.

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "neo4j_connected": true,
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

**Status Values:**
- `healthy`: All services operational
- `degraded`: Neo4j connection issues
- `unhealthy`: Critical service failures

---

## Error Handling

All endpoints follow consistent error response format:

```json
{
  "detail": "Error description message"
}
```

**Common HTTP Status Codes:**
- `200`: Success
- `400`: Bad Request (invalid input)
- `404`: Not Found (invalid group_id)
- `500`: Internal Server Error (processing failures)

---

## Rate Limiting

Currently no rate limiting is implemented. Consider implementing based on your usage patterns.

---

## Versioning

Current API version: `1.0.0`

**Recent Updates (v1.0.0):**
- ✅ Unified configuration endpoint (`/config`)
- ✅ Multi-provider support (OpenAI + Azure OpenAI)
- ✅ GraphRAG 2.x integration
- ✅ Dynamic provider switching
- ✅ Complete environment variable exposure

Breaking changes will increment the major version number.

---

## Configuration Examples

### Switch to OpenAI
```bash
POST /api/graph/config
{
  "env_vars": {
    "LLM_PROVIDER": "openai",
    "EMBEDDING_PROVIDER": "openai",
    "OPENAI_API_KEY": "sk-your-key",
    "OPENAI_MODEL": "gpt-4o"
  }
}
```

### Switch to Azure OpenAI
```bash
POST /api/graph/config
{
  "env_vars": {
    "LLM_PROVIDER": "azure",
    "EMBEDDING_PROVIDER": "azure",
    "AZURE_OPENAI_API_KEY": "your-azure-key",
    "AZURE_OPENAI_ENDPOINT": "https://your-resource.openai.azure.com/"
  }
}
```

### Mixed Configuration
```bash
POST /api/graph/config
{
  "env_vars": {
    "LLM_PROVIDER": "azure",
    "EMBEDDING_PROVIDER": "openai",
    "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-4o",
    "OPENAI_API_KEY": "sk-your-key"
  }
}
```

---

## Support

For issues and questions:
1. **Configuration**: Check `/config` endpoint for current settings
2. **Provider Setup**: Verify API keys and endpoints in configuration
3. **Neo4j**: Ensure database connectivity and credentials
4. **GraphRAG**: Confirm LLM model configuration for graph creation
5. **Logs**: Review server logs for detailed error messages
6. **File Formats**: Ensure documents are in supported formats (PDF, DOCX, TXT, MD)
