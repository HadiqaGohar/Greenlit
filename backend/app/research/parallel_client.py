"""
Parallel API Client - Uses official parallel-web SDK
Handles real-time research and fact verification
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional

from parallel import AsyncParallel

from ..config import settings

logger = logging.getLogger(__name__)


class ParallelClient:
    """
    Official Parallel SDK client for fact verification and research
    Uses parallel-web package (async)
    """
    
    def __init__(self):
        self.api_key = settings.PARALLEL_API_KEY
        self._client = None
        
    def _get_client(self) -> AsyncParallel:
        """Get or create the Parallel SDK client"""
        if self._client is None:
            self._client = AsyncParallel(api_key=self.api_key)
        return self._client
    
    async def research_query(
        self, 
        query: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Research a query using Parallel Search API
        
        Args:
            query: Research question to investigate
            context: Optional context for the research
        
        Returns:
            Research results with sources and summary
        """
        
        if not self.api_key:
            logger.warning("No PARALLEL_API_KEY configured - falling back to basic response")
            return self._basic_fallback(query)
        
        try:
            client = self._get_client()
            
            # Use Parallel's task_run API for deep research
            task_run = await client.task_run.create(
                input=query,
                processor="core"
            )
            
            # Poll for results
            result = await client.task_run.result(run_id=task_run.run_id)
            
            # Format the response
            return self._format_response(result, query)
        
        except Exception as e:
            logger.error(f"Parallel API request failed: {str(e)}")
            return self._basic_fallback(query)
    
    def _format_response(self, result: Any, query: str) -> Dict[str, Any]:
        """Format Parallel SDK response to standard format"""
        
        # Extract output from the result
        output = getattr(result, 'output', None) or str(result)
        
        # Extract sources if available
        sources = []
        if hasattr(result, 'sources') and result.sources:
            for source in result.sources:
                sources.append({
                    "title": getattr(source, 'title', 'Unknown'),
                    "url": getattr(source, 'url', ''),
                    "credibility": getattr(source, 'credibility', 0.7)
                })
        
        # Extract confidence if available
        confidence = getattr(result, 'confidence', 0.75)
        
        return {
            "summary": str(output) if output else f"Research completed for: {query}",
            "sources": sources,
            "confidence": float(confidence) if confidence else 0.75,
            "metadata": {
                "api_provider": "parallel",
                "query_processed": True
            }
        }
    
    def _basic_fallback(self, query: str) -> Dict[str, Any]:
        """Basic fallback when API is not available"""
        return {
            "summary": f"Research query: {query}. Configure PARALLEL_API_KEY for live research.",
            "sources": [],
            "confidence": 0.5,
            "metadata": {
                "api_provider": "fallback",
                "query_processed": False
            }
        }
    
    async def batch_research(
        self, 
        queries: List[str], 
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Research multiple queries concurrently"""
        
        semaphore = asyncio.Semaphore(5)
        
        async def research_with_semaphore(query: str):
            async with semaphore:
                return await self.research_query(query, context)
        
        results = await asyncio.gather(*[
            research_with_semaphore(query) for query in queries
        ], return_exceptions=True)
        
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Batch research failed for query {i}: {result}")
                valid_results.append({
                    "summary": f"Research failed for query: {queries[i]}",
                    "sources": [],
                    "confidence": 0.0,
                    "error": str(result)
                })
            else:
                valid_results.append(result)
        
        return valid_results
    
    async def close(self):
        """Clean up client resources"""
        if self._client:
            await self._client.close()
            self._client = None


# Singleton instance for reuse
_parallel_client_instance = None

async def get_parallel_client() -> ParallelClient:
    """Get shared Parallel client instance"""
    global _parallel_client_instance
    
    if _parallel_client_instance is None:
        _parallel_client_instance = ParallelClient()
    
    return _parallel_client_instance


async def close_parallel_client():
    """Close the shared Parallel client"""
    global _parallel_client_instance
    if _parallel_client_instance:
        await _parallel_client_instance.close()
        _parallel_client_instance = None
