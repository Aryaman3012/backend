# Knowledge Graph RAG Backend

A powerful Python backend for generating knowledge graphs from documents and answering questions using **Microsoft GraphRAG 2.x** with **Retrieval-Augmented Generation**.

Built with **FastAPI**, **Neo4j**, and **Microsoft GraphRAG**. Supports both **OpenAI** and **Azure OpenAI** providers with dynamic configuration.

## Features

- 📄 **Document Upload**: Upload PDF, DOCX, TXT, or Markdown files
- 🕸️ **Knowledge Graph Generation**: Automatically extract entities and relationships using GraphRAG 2.x
- 🤖 **Graph RAG Q&A**: Ask questions and get answers based on the knowledge graph
- 📊 **Graph Visualization**: Get graph data for frontend visualization
- 🗂️ **Multi-Graph Support**: Organize knowledge into separate groups
- 🔄 **Multi-Provider Support**: Choose between OpenAI and Azure OpenAI for LLM and embeddings
- ⚙️ **Dynamic Configuration**: Frontend-driven environment variable management
- 🔒 **Provider Selection**: Configure different providers for LLM vs embeddings

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Frontend      │────▶│   FastAPI       │────▶│   Neo4j         │
│   (Your App)    │     │   Backend       │     │   Database      │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                        ┌────────▼────────┐
                        │  Microsoft      │
                        │  GraphRAG 2.x   │
                        └────────┬────────┘
                                 │
                   ┌─────────────┴─────────────┐
                   │                           │
            ┌──────▼─────┐             ┌──────▼─────┐
            │   OpenAI   │             │ Azure      │
            │   API      │             │ OpenAI     │
            └────────────┘             └────────────┘
```

## Prerequisites

- Python 3.10+
- Neo4j Database (local or cloud)
- **Choose one or both:** OpenAI API key AND/OR Azure OpenAI access
- Microsoft GraphRAG (automatically installed via requirements.txt)

## Quick Start

### 1. Install Neo4j

**Option A: Docker (Recommended)**
```bash
docker run \
    --name neo4j \
    -p 7474:7474 -p 7687:7687 \
    -e NEO4J_AUTH=neo4j/your_password_here \
    -e NEO4J_PLUGINS='["apoc"]' \
    neo4j:latest
```

**Option B: Neo4j Desktop**
Download from [neo4j.com](https://neo4j.com/download/)

### 2. Clone and Setup

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment

**Option A: Static Configuration (Traditional)**
```bash
# Copy example env file
cp .env.example .env

# Edit .env with your credentials
```

**Option B: Dynamic Configuration (Recommended)**
Use the frontend API to configure providers dynamically - no server restart required!

#### Provider Selection

Choose your preferred providers for LLM and embeddings:

| Provider | LLM | Embeddings | Configuration |
|----------|-----|------------|---------------|
| **OpenAI** | ✅ | ✅ | `OPENAI_API_KEY` |
| **Azure OpenAI** | ✅ | ✅ | Endpoint + API Key + Deployment |

#### Required Environment Variables

**Neo4j Configuration (always required):**
```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_neo4j_password
```

**Provider Configuration (choose one or both):**

*OpenAI:*
```env
LLM_PROVIDER=openai
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-4o
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

*Azure OpenAI:*
```env
LLM_PROVIDER=azure
EMBEDDING_PROVIDER=azure
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
AZURE_OPENAI_API_KEY=your-azure-openai-api-key
AZURE_OPENAI_API_VERSION=2024-12-01-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-small
```

**Mixed Configuration (different providers):**
```env
LLM_PROVIDER=azure
EMBEDDING_PROVIDER=openai
# Configure both Azure and OpenAI settings above
```

### 4. Run the Server

```bash
python main.py
```

Or with uvicorn directly:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

📋 **[Complete API Documentation](api.md)** - Detailed endpoint specifications, request/response examples, and error handling.

### Configuration Management

### Configuration Management

#### Get Environment Configuration
```http
GET /api/graph/config
```
Returns current provider settings and configurations.

#### Update Environment Configuration
```http
POST /api/graph/config/update
Content-Type: application/json

{
  "env_vars": {
    "LLM_PROVIDER": "azure",
    "EMBEDDING_PROVIDER": "openai",
    "AZURE_OPENAI_API_KEY": "your-azure-key",
    "OPENAI_API_KEY": "your-openai-key"
  }
}
```
Dynamically update provider configurations.

#### Get Environment Variables
```http
GET /api/graph/config/env-vars
```
Returns all environment variables (sensitive data masked).

### Core Graph Operations

#### Health Check
```http
GET /api/graph/health
```

#### Upload Document
```http
POST /api/graph/upload
Content-Type: multipart/form-data

file: <your_document>
group_id: optional_group_name
```

#### Ask Question (Graph RAG)
```http
POST /api/graph/ask
Content-Type: application/json

{
  "question": "What is the main topic of the document?",
  "group_id": "optional_group_name",
  "top_k": 10
}
```

#### Get Graph Stats
```http
GET /api/graph/stats?group_id=optional_group_name
```

#### Get Visualization Data
```http
GET /api/graph/visualize?group_id=optional_group_name&limit=100
```

#### Search Graph
```http
POST /api/graph/search?query=your_search&top_k=10
```

#### Delete Graph
```http
DELETE /api/graph/delete
Content-Type: application/json

{
  "group_id": "group_to_delete",
  "confirm": true
}
```

#### List Groups
```http
GET /api/graph/groups
```

📖 **See [api.md](api.md) for complete endpoint documentation, detailed examples, and error handling.**

## Frontend Integration

### Configure Providers (New!)
```javascript
// Get current configuration
const configResponse = await fetch('http://localhost:8000/api/graph/config');
const currentConfig = await configResponse.json();
console.log('Current LLM Provider:', currentConfig.llm_provider);

// Update configuration dynamically
const updateResponse = await fetch('http://localhost:8000/api/graph/config/update', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    env_vars: {
      LLM_PROVIDER: 'azure',
      EMBEDDING_PROVIDER: 'openai',
      AZURE_OPENAI_API_KEY: 'user-azure-key',
      AZURE_OPENAI_ENDPOINT: 'https://your-resource.openai.azure.com/',
      AZURE_OPENAI_DEPLOYMENT_NAME: 'gpt-4o',
      OPENAI_API_KEY: 'user-openai-key'
    }
  })
});

const updateResult = await updateResponse.json();
console.log('Configuration updated:', updateResult.message);
if (updateResult.requires_restart) {
  console.log('Server restart recommended for optimal performance');
}
```

### Upload a Document
```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('group_id', 'my_knowledge_base');

const response = await fetch('http://localhost:8000/api/graph/upload', {
  method: 'POST',
  body: formData
});

const result = await response.json();
console.log(`Created ${result.nodes_created} nodes and ${result.edges_created} edges`);
```

### Ask a Question
```javascript
const response = await fetch('http://localhost:8000/api/graph/ask', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    question: 'What are the key concepts?',
    group_id: 'my_knowledge_base',
    top_k: 10
  })
});

const result = await response.json();
console.log(result.answer);
console.log('Sources:', result.sources);
```

### Get Graph for Visualization
```javascript
const response = await fetch('http://localhost:8000/api/graph/visualize?group_id=my_knowledge_base');
const graphData = await response.json();

// Use with D3.js, vis.js, or any graph visualization library
console.log('Nodes:', graphData.nodes);
console.log('Edges:', graphData.edges);
```

## Project Structure

```
backend/
├── main.py                    # FastAPI application & lifespan
├── config.py                  # Dynamic configuration management
├── requirements.txt          # Python dependencies
├── README.md                 # This documentation
├── .env.example             # Environment template
├── models/
│   ├── __init__.py
│   └── schemas.py           # Pydantic schemas & API models
├── routers/
│   ├── __init__.py
│   └── graph_router.py      # API routes & endpoints
└── services/
    ├── __init__.py
    ├── document_processor.py # Multi-format document parsing
    ├── graph_service.py      # GraphRAG 2.x + Neo4j integration
    └── rag_service.py        # Multi-provider RAG Q&A
```

## How Graph RAG Works

1. **Document Processing**: Documents are parsed and text extracted (PDF, DOCX, TXT, MD)
2. **Text Chunking**: Content is split into manageable segments with overlap
3. **Entity Extraction**: Microsoft GraphRAG 2.x uses LLMs to identify entities and relationships
4. **Embedding Generation**: Text chunks and entities are embedded using selected provider
5. **Graph Construction**: Entities become nodes, relationships become edges in Neo4j
6. **Community Detection**: GraphRAG identifies related entity clusters
7. **Question Processing**: User questions are embedded and matched against the graph
8. **Context Retrieval**: Relevant facts, relationships, and communities are retrieved
9. **Answer Generation**: Selected LLM provider generates answers using graph context

## Configuration Options

### Provider Selection
| Variable | Description | Options | Default |
|----------|-------------|---------|---------|
| `LLM_PROVIDER` | Primary LLM provider | `openai`, `azure` | `azure` |
| `EMBEDDING_PROVIDER` | Embedding provider | `openai`, `azure` | `azure` |

### OpenAI Configuration
| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `OPENAI_API_KEY` | OpenAI API key | If using OpenAI | - |
| `OPENAI_BASE_URL` | Custom OpenAI base URL | Optional | - |
| `OPENAI_MODEL` | OpenAI model | Optional | `gpt-4o` |
| `OPENAI_EMBEDDING_MODEL` | OpenAI embedding model | Optional | `text-embedding-3-small` |

### Azure OpenAI Configuration
| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint URL | If using Azure | - |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key | If using Azure | - |
| `AZURE_OPENAI_API_VERSION` | Azure API version | Optional | `2024-12-01-preview` |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | Azure LLM deployment | Optional | `gpt-4o` |
| `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` | Azure embedding deployment | Optional | - |

### Neo4j Configuration
| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `NEO4J_URI` | Neo4j connection URI | Always | `bolt://localhost:7687` |
| `NEO4J_USERNAME` | Neo4j username | Always | `neo4j` |
| `NEO4J_PASSWORD` | Neo4j password | Always | - |
| `NEO4J_DATABASE` | Neo4j database name | Optional | `neo4j` |

### Server Configuration
| Variable | Description | Default |
|----------|-------------|---------|
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8000` |
| `DEBUG` | Debug mode | `true` |
| `CHUNK_SIZE` | Text chunk size | `1000` |
| `CHUNK_OVERLAP` | Chunk overlap | `200` |

## Recent Updates

### v1.0.0 Features
- ✅ **Microsoft GraphRAG 2.x** integration
- ✅ **Multi-Provider Support** (OpenAI + Azure OpenAI)
- ✅ **Dynamic Configuration** via frontend API
- ✅ **Provider Flexibility** (different providers for LLM vs embeddings)
- ✅ **Clean Architecture** with streamlined codebase
- ✅ **Comprehensive API** with 10+ endpoints
- ✅ **Real-time Provider Switching** without server restart

### Key Improvements
- Removed legacy code and unused dependencies
- Enhanced error handling and logging
- Improved security with masked sensitive data
- Better documentation and examples
- Flexible provider configuration options

## License

MIT

