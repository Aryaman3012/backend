"""
Configuration settings for the Knowledge Graph RAG Backend
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # LLM Provider: "openai" or "azure"
    llm_provider: str = "azure"

    # Embedding Provider: "openai" or "azure"
    embedding_provider: str = "azure"
    
    # OpenAI / OpenRouter settings
    openai_api_key: str = ""
    openai_base_url: str = ""  # Leave empty for default OpenAI
    openai_model: str = "gpt-4o"
    openai_embedding_model: str = "text-embedding-3-small"
    
    
    # Groq settings
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"  # For LLM
    groq_embedding_model: str = "nomic-embed-text-v1.5"  # Groq embedding model

    # Azure OpenAI specific settings
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_api_version: str = "2024-02-01"
    azure_openai_deployment_name: str = "gpt-4o"
    azure_openai_embedding_deployment: str = ""

    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_username: str = "neo4j"
    neo4j_password: str = ""
    neo4j_database: str = "neo4j"

    # Neo4j Aura (optional)
    aura_instanceid: str = ""
    aura_instancename: str = ""


    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True

    # Graph settings
    default_group_id: str = "default_knowledge_graph"

    # Chunking settings
    chunk_size: int = 1000
    chunk_overlap: int = 200

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra env vars not defined in Settings


def get_settings() -> Settings:
    """Get settings instance (not cached for dynamic updates)"""
    return Settings()


def update_settings_from_dict(settings_dict: dict) -> Settings:
    """Update settings from a dictionary and return new Settings instance"""
    # Update environment variables
    for key, value in settings_dict.items():
        if value is not None:
            os.environ[key.upper()] = str(value)

    # Create new settings instance with updated env vars
    return Settings()


def get_current_env_vars() -> dict:
    """Get current environment variables as a dictionary"""
    settings = get_settings()
    env_vars = {}

    # LLM Provider settings
    env_vars['LLM_PROVIDER'] = settings.llm_provider
    env_vars['EMBEDDING_PROVIDER'] = settings.embedding_provider

    # OpenAI settings
    if settings.openai_api_key:
        env_vars['OPENAI_API_KEY'] = settings.openai_api_key
    if settings.openai_base_url:
        env_vars['OPENAI_BASE_URL'] = settings.openai_base_url
    if settings.openai_model:
        env_vars['OPENAI_MODEL'] = settings.openai_model
    if settings.openai_embedding_model:
        env_vars['OPENAI_EMBEDDING_MODEL'] = settings.openai_embedding_model

    # Azure OpenAI settings
    if settings.azure_openai_endpoint:
        env_vars['AZURE_OPENAI_ENDPOINT'] = settings.azure_openai_endpoint
    if settings.azure_openai_api_key:
        env_vars['AZURE_OPENAI_API_KEY'] = settings.azure_openai_api_key
    if settings.azure_openai_api_version:
        env_vars['AZURE_OPENAI_API_VERSION'] = settings.azure_openai_api_version
    if settings.azure_openai_deployment_name:
        env_vars['AZURE_OPENAI_DEPLOYMENT_NAME'] = settings.azure_openai_deployment_name
    if settings.azure_openai_embedding_deployment:
        env_vars['AZURE_OPENAI_EMBEDDING_DEPLOYMENT'] = settings.azure_openai_embedding_deployment

    # Neo4j settings
    if settings.neo4j_uri:
        env_vars['NEO4J_URI'] = settings.neo4j_uri
    if settings.neo4j_username:
        env_vars['NEO4J_USERNAME'] = settings.neo4j_username
    if settings.neo4j_password:
        env_vars['NEO4J_PASSWORD'] = settings.neo4j_password
    if settings.neo4j_database:
        env_vars['NEO4J_DATABASE'] = settings.neo4j_database

    return env_vars

