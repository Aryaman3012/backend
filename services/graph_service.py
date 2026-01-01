"""
Knowledge Graph Service using Microsoft GraphRAG
"""
import asyncio
import json
import logging
import os
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from uuid import uuid4

from config import get_settings
from services.document_processor import DocumentProcessor

# Lazy import GraphRAG to avoid startup issues
try:
    from graphrag.api import build_index, global_search  # type: ignore
    import pandas as pd
    GRAPHRAG_AVAILABLE = True
except ImportError:
    GRAPHRAG_AVAILABLE = False
    build_index = None
    global_search = None
    pd = None

logger = logging.getLogger(__name__)


class GraphService:
    """Service for managing knowledge graphs using Microsoft GraphRAG"""

    def __init__(self):
        self.settings = get_settings()
        self.document_processor = DocumentProcessor()
        self._workspaces = {}  # group_id -> workspace path

    def _get_workspace_path(self, group_id: str) -> str:
        """Get workspace path for a group"""
        if group_id not in self._workspaces:
            # Create a temporary directory for each group
            temp_dir = tempfile.gettempdir()
            workspace_path = os.path.join(temp_dir, f"graphrag_{group_id}")
            self._workspaces[group_id] = workspace_path
        return self._workspaces[group_id]


    def _create_graphrag_config_v2(self, group_id: str):
        """Create GraphRAG 2.x configuration"""
        from graphrag.config.load_config import create_graphrag_config
        import os

        workspace_path = self._get_workspace_path(group_id)

        # Ensure directories exist
        for subdir in ['input', 'output', 'cache', 'reports']:
            os.makedirs(os.path.join(workspace_path, subdir), exist_ok=True)

        # Create the new GraphRAG 2.x config with dynamic provider support
        config_dict = {
            'models': {
                'default_chat_model': {
                    'type': 'azure_openai_chat' if self.settings.llm_provider == 'azure' else 'openai_chat',
                    'model': self._get_llm_model_config(),
                    'api_key': self._get_llm_api_key(),
                    'api_base': self._get_llm_api_base(),
                    'api_version': self.settings.azure_openai_api_version if self.settings.llm_provider == "azure" else None,
                    'deployment_name': self.settings.azure_openai_deployment_name if self.settings.llm_provider == "azure" else None,
                    'max_tokens': 2000
                },
                'default_embedding_model': {
                    'type': 'azure_openai_embedding' if self.settings.embedding_provider == 'azure' else 'openai_embedding',
                    'model': self._get_embedding_model_config(),  # Use the configured model from env
                    'api_key': self._get_embedding_api_key(),
                    'api_base': self._get_embedding_api_base(),
                    'api_version': self.settings.azure_openai_api_version if self.settings.embedding_provider == "azure" else None,
                    'deployment_name': self.settings.azure_openai_embedding_deployment if self.settings.embedding_provider == "azure" else None
                }
            },
            'input': {
                'type': 'file',
                'file_type': 'text',
                'base_dir': os.path.join(workspace_path, "input"),
                'file_pattern': '.*\\.txt$',
                'source_column': 'text',
                'text_column': 'text',
                'title_column': 'title'
            },
            'chunks': {
                'size': self.settings.chunk_size,
                'overlap': self.settings.chunk_overlap
            },
            'output': {
                'type': 'file',
                'base_dir': os.path.join(workspace_path, "output")
            },
            'cache': {
                'type': 'file',
                'base_dir': os.path.join(workspace_path, "cache")
            },
            'reporting': {
                'type': 'file',
                'base_dir': os.path.join(workspace_path, "reports")
            }
        }

        return create_graphrag_config(config_dict, root_dir=workspace_path)

    def _get_llm_model_config(self) -> str:
        """Get LLM model configuration"""
        if self.settings.llm_provider == "azure":
            return self.settings.azure_openai_deployment_name
        elif self.settings.llm_provider == "groq":
            return self.settings.groq_model
        else:
            return self.settings.openai_model

    def _get_llm_api_key(self) -> str:
        """Get LLM API key"""
        if self.settings.llm_provider == "azure":
            return self.settings.azure_openai_api_key
        elif self.settings.llm_provider == "groq":
            return self.settings.groq_api_key
        else:
            return self.settings.openai_api_key

    def _get_llm_api_base(self) -> Optional[str]:
        """Get LLM API base URL"""
        if self.settings.llm_provider == "azure":
            return self.settings.azure_openai_endpoint
        elif self.settings.llm_provider == "groq":
            return "https://api.groq.com/openai/v1"
        else:
            return None

    def _get_embedding_model_config(self) -> str:
        """Get embedding model configuration"""
        if self.settings.embedding_provider == "azure":
            return self.settings.azure_openai_embedding_deployment
        elif self.settings.embedding_provider == "groq":
            return self.settings.groq_embedding_model
        else:
            return self.settings.openai_embedding_model

    def _get_embedding_api_key(self) -> str:
        """Get embedding API key"""
        if self.settings.embedding_provider == "azure":
            return self.settings.azure_openai_api_key
        elif self.settings.embedding_provider == "groq":
            return self.settings.groq_api_key
        else:
            return self.settings.openai_api_key

    def _get_embedding_api_base(self) -> Optional[str]:
        """Get embedding API base URL"""
        if self.settings.embedding_provider == "azure":
            return self.settings.azure_openai_endpoint
        elif self.settings.embedding_provider == "groq":
            return "https://api.groq.com/openai/v1"
        else:
            return None

    async def _get_graphrag_stats(self, group_id: str) -> Dict[str, Any]:
        """Get statistics from GraphRAG output"""
        workspace_path = self._get_workspace_path(group_id)
        output_dir = Path(workspace_path) / "output"

        try:
            # Read entities parquet file (GraphRAG 2.x naming)
            entities_file = output_dir / "entities.parquet"
            if entities_file.exists():
                import pandas as pd
                entities_df = pd.read_parquet(entities_file)
                total_entities = len(entities_df)
            else:
                total_entities = 0

            # Read relationships parquet file (GraphRAG 2.x naming)
            relationships_file = output_dir / "relationships.parquet"
            if relationships_file.exists():
                relationships_df = pd.read_parquet(relationships_file)
                total_relationships = len(relationships_df)
            else:
                total_relationships = 0

            return {
                "total_entities": total_entities,
                "total_relationships": total_relationships
            }

        except Exception as e:
            logger.error(f"Failed to read GraphRAG stats: {e}")
            return {"total_entities": 0, "total_relationships": 0}

    async def process_document(
        self,
        file_content: bytes,
        filename: str,
        group_id: Optional[str] = None
    ) -> Tuple[str, int, int]:
        """
        Process a document using Microsoft GraphRAG

        Returns:
            Tuple of (document_id, nodes_created, edges_created)
        """
        if not GRAPHRAG_AVAILABLE:
            raise RuntimeError("Microsoft GraphRAG is not installed or not available")

        document_id = f"doc_{uuid4().hex[:12]}"
        group_id = group_id or self.settings.default_group_id

        logger.info(f"[GRAPHRAG] Processing {filename} for group '{group_id}'")

        # Extract text from document
        text = await self.document_processor.extract_text(file_content, filename)

        if not text.strip():
            logger.warning(f"[GRAPHRAG] No text content extracted from {filename}")
            raise ValueError("No text content could be extracted from the document")

        logger.info(f"[GRAPHRAG] Extracted text from {filename} ({len(text)} chars)")

        # Create workspace for this group if it doesn't exist
        workspace_path = self._get_workspace_path(group_id)
        os.makedirs(workspace_path, exist_ok=True)

        # Create input documents DataFrame for GraphRAG 2.x
        import pandas as pd
        from datetime import datetime
        documents_df = pd.DataFrame([{
            'id': document_id,
            'text': text,
            'title': filename,
            'source': filename,
            'creation_date': datetime.now().isoformat()
        }])

        try:
            # Create GraphRAG config
            config = self._create_graphrag_config_v2(group_id)

            # Run GraphRAG indexing pipeline using new 2.x API
            logger.info(f"[GRAPHRAG] Starting entity extraction and indexing...")
            results = await build_index(
                config=config,
                input_documents=documents_df,
                verbose=False  # Disable verbose GraphRAG output
            )
            logger.info(f"[GRAPHRAG] Indexing completed successfully")

            # Get stats from the output
            stats = await self._get_graphrag_stats(group_id)
            nodes_created = stats.get('total_entities', 0)
            edges_created = stats.get('total_relationships', 0)

            # Store the group for later use
            self._workspaces[group_id] = workspace_path

            logger.info(f"[GRAPHRAG] Created knowledge graph - {nodes_created} nodes, {edges_created} edges")
            return document_id, nodes_created, edges_created

        except Exception as e:
            logger.error(f"[GRAPHRAG] Failed to process {filename}: {str(e)}")
            raise

    async def search(
        self,
        query: str,
        group_id: Optional[str] = None,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search the knowledge graph using GraphRAG global search
        """
        if not GRAPHRAG_AVAILABLE:
            return []

        group_id = group_id or self.settings.default_group_id

        if group_id not in self._workspaces:
            return []

        workspace_path = self._workspaces[group_id]
        output_dir = Path(workspace_path) / "output"

        # Load the required DataFrames for GraphRAG 2.x
        try:
            entities_df = pd.read_parquet(output_dir / "entities.parquet")
            communities_df = pd.read_parquet(output_dir / "communities.parquet")
            community_reports_df = pd.read_parquet(output_dir / "community_reports.parquet")
        except FileNotFoundError:
            logger.warning(f"GraphRAG output files not found for group {group_id}")
            return []

        # Create config for GraphRAG 2.x
        config = self._create_graphrag_config_v2(group_id)

        try:
            # Use GraphRAG 2.x global search API
            response, context = await global_search(
                config=config,
                entities=entities_df,
                communities=communities_df,
                community_reports=community_reports_df,
                community_level=1,
                dynamic_community_selection=True,
                response_type="Multiple Paragraphs",
                query=query,
                verbose=False
            )

            # Parse results
            results = []
            if response:
                results.append({
                    "entity": "Query Result",
                    "type": "RESPONSE",
                    "description": str(response)[:1000],  # Limit response length
                    "relationships": [],
                    "score": 1.0
                })

            return results[:top_k]

        except Exception as e:
            logger.error(f"GraphRAG global search failed: {e}")
            return []

    async def get_graph_stats(self, group_id: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics about the knowledge graph"""
        if not GRAPHRAG_AVAILABLE:
            return {
                "total_nodes": 0,
                "total_edges": 0,
                "node_types": {},
                "edge_types": {},
                "groups": list(self._workspaces.keys())
            }

        group_id = group_id or self.settings.default_group_id

        if group_id not in self._workspaces:
            return {
                "total_nodes": 0,
                "total_edges": 0,
                "node_types": {},
                "edge_types": {},
                "groups": list(self._workspaces.keys())
            }

        # Get real stats from GraphRAG output
        stats = await self._get_graphrag_stats(group_id)

        return {
            "total_nodes": stats.get("total_entities", 0),
            "total_edges": stats.get("total_relationships", 0),
            "node_types": {"Entity": stats.get("total_entities", 0)},
            "edge_types": {"RELATIONSHIP": stats.get("total_relationships", 0)},
            "groups": list(self._workspaces.keys())
        }

    async def get_graph_visualization(
        self,
        group_id: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get nodes and edges for visualization from GraphRAG output"""
        if not GRAPHRAG_AVAILABLE:
            return {"nodes": [], "edges": []}

        group_id = group_id or self.settings.default_group_id

        if group_id not in self._workspaces:
            return {"nodes": [], "edges": []}

        workspace_path = self._workspaces[group_id]
        output_dir = Path(workspace_path) / "output"

        nodes = []
        edges = []

        try:
            # Read entities (GraphRAG 2.x naming)
            entities_file = output_dir / "entities.parquet"
            if entities_file.exists():
                entities_df = pd.read_parquet(entities_file)
                for _, row in entities_df.head(limit).iterrows():
                    nodes.append({
                        "id": str(row.get("id", "")),
                        "name": row.get("title", "Unknown"),
                        "type": row.get("type", "Entity"),
                        "properties": {"description": row.get("description", "")}
                    })

            # Read relationships (GraphRAG 2.x naming)
            relationships_file = output_dir / "relationships.parquet"
            if relationships_file.exists():
                relationships_df = pd.read_parquet(relationships_file)
                for _, row in relationships_df.head(limit).iterrows():
                    edges.append({
                        "id": str(row.get("id", "")),
                        "source": str(row.get("source", "")),
                        "target": str(row.get("target", "")),
                        "relationship": row.get("description", "RELATED"),
                        "properties": {"description": row.get("description", "")}
                    })

        except Exception as e:
            logger.error(f"Failed to read GraphRAG visualization data: {e}")

        return {"nodes": nodes, "edges": edges}

    async def delete_graph(self, group_id: str) -> Dict[str, int]:
        """Delete all data for a specific group"""
        if group_id in self._workspaces:
            workspace_path = self._workspaces[group_id]
            import shutil
            try:
                shutil.rmtree(workspace_path)
                del self._workspaces[group_id]
                return {"nodes_deleted": 0, "edges_deleted": 0}  # We don't track exact counts
            except Exception as e:
                logger.error(f"Failed to delete GraphRAG workspace: {e}")

        return {"nodes_deleted": 0, "edges_deleted": 0}

    async def check_connection(self) -> bool:
        """Check if GraphRAG can be initialized"""
        return GRAPHRAG_AVAILABLE

    async def get_groups(self) -> List[str]:
        """Get all group IDs"""
        return list(self._workspaces.keys())


# Global instance
graph_service = GraphService()