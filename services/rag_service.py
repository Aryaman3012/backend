"""
Graph RAG Service for answering questions using the knowledge graph
"""
import logging
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI, AsyncAzureOpenAI


from config import get_settings
from services.graph_service import graph_service

logger = logging.getLogger(__name__)


class GraphRAGService:
    """
    Retrieval-Augmented Generation service using the knowledge graph
    """
    
    def __init__(self):
        self.settings = get_settings()
        self._client: Optional[AsyncOpenAI] = None
    
    @property
    def client(self):
        """Get OpenAI client for RAG (supports OpenAI and Azure OpenAI)"""
        if self._client is None:
            provider = self.settings.llm_provider.lower()

            if provider == "azure":
                # Azure OpenAI client
                self._client = AsyncAzureOpenAI(
                    api_version=self.settings.azure_openai_api_version,
                    azure_endpoint=self.settings.azure_openai_endpoint,
                    api_key=self.settings.azure_openai_api_key
                )
                logger.info(f"RAG using Azure OpenAI: {self.settings.azure_openai_deployment_name}")
            elif provider == "openai":
                # Regular OpenAI or custom base URL
                if self.settings.openai_base_url:
                    self._client = AsyncOpenAI(
                        api_key=self.settings.openai_api_key,
                        base_url=self.settings.openai_base_url
                    )
                    logger.info(f"RAG using custom OpenAI API: {self.settings.openai_base_url}")
                else:
                    self._client = AsyncOpenAI(api_key=self.settings.openai_api_key)
                    logger.info(f"RAG using OpenAI: {self.settings.openai_model}")
            else:
                raise ValueError(f"Unsupported LLM provider: {provider}. Supported: 'openai', 'azure'")
        return self._client
    
    async def answer_question(
        self,
        question: str,
        group_id: Optional[str] = None,
        top_k: int = 10
    ) -> Dict[str, Any]:
        """
        Answer a question using Graph RAG

        1. Search the knowledge graph for relevant facts
        2. Build context from retrieved information
        3. Generate answer using LLM
        """
        logger.info(f"[RAG] Answering question for group '{group_id or 'default'}'")

        # Search for relevant facts in the knowledge graph
        search_results = await graph_service.search(
            query=question,
            group_id=group_id,
            top_k=top_k
        )

        if not search_results:
            logger.warning(f"[RAG] No relevant information found")
            return {
                "question": question,
                "answer": "I couldn't find any relevant information in the knowledge graph to answer this question.",
                "sources": [],
                "entities_used": [],
                "confidence": 0.0
            }

        # Build context from search results
        context = self._build_context(search_results)

        # Extract all entities mentioned
        all_entities = []
        for result in search_results:
            all_entities.extend(result.get("entities", []))
        unique_entities = list(set(all_entities))

        # Generate answer using LLM
        logger.info(f"[RAG] Generating answer using {self.settings.llm_provider}")
        answer, confidence = await self._generate_answer(question, context)

        logger.info(f"[RAG] Answer ready - confidence: {confidence:.2f}")

        # Format sources
        sources = [
            {
                "fact": r.get("description") or r.get("fact"),
                "source": r.get("entity") or r.get("source"),
                "score": r.get("score", 0.0)
            }
            for r in search_results
        ]

        return {
            "question": question,
            "answer": answer,
            "sources": sources,
            "entities_used": unique_entities,
            "confidence": confidence
        }
    
    def _build_context(self, search_results: List[Dict[str, Any]]) -> str:
        """Build context string from search results"""
        context_parts = []

        for i, result in enumerate(search_results, 1):
            # Handle GraphRAG result format (description/entity) or legacy format (fact/source)
            fact = result.get("description") or result.get("fact", "")
            source = result.get("entity") or result.get("source", "Unknown source")
            entities = result.get("entities", [])

            context_entry = f"[{i}] {fact}"
            if entities:
                context_entry += f" (Entities: {', '.join(entities)})"
            context_parts.append(context_entry)

        return "\n".join(context_parts)
    
    async def _generate_answer(
        self, 
        question: str, 
        context: str
    ) -> tuple[str, float]:
        """Generate answer using OpenAI"""
        
        system_prompt = """You are a helpful assistant that answers questions based on a knowledge graph.
You will be given relevant facts extracted from the knowledge graph.
Use these facts to provide accurate, comprehensive answers.

Guidelines:
- Only use information from the provided context
- If the context doesn't contain enough information, say so
- Be concise but thorough
- Cite specific facts when relevant
- If you're uncertain, express that uncertainty"""

        user_prompt = f"""Context from Knowledge Graph:
{context}

Question: {question}

Please provide a comprehensive answer based on the above context."""

        try:
            # Determine which model to use based on provider
            provider = self.settings.llm_provider.lower()
            if provider == "azure":
                model = self.settings.azure_openai_deployment_name
            elif provider == "openai":
                model = self.settings.openai_model or "gpt-4o"
            else:
                raise ValueError(f"Unsupported LLM provider: {provider}")
            
            response = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            answer = response.choices[0].message.content
            
            # Calculate confidence based on context relevance
            confidence = self._calculate_confidence(context, len(context.split('\n')))
            
            return answer, confidence
            
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return f"Error generating answer: {str(e)}", 0.0
    
    def _calculate_confidence(self, context: str, num_sources: int) -> float:
        """
        Calculate confidence score based on:
        - Number of relevant sources
        - Context length/richness
        """
        # Base confidence from number of sources
        source_confidence = min(num_sources / 5.0, 1.0) * 0.6
        
        # Additional confidence from context richness
        context_length = len(context)
        context_confidence = min(context_length / 2000.0, 1.0) * 0.4
        
        return round(source_confidence + context_confidence, 2)
    


# Global instance
rag_service = GraphRAGService()

