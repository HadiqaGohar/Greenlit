"""
Parallel API Client - Handles real-time research and fact verification
Integrates with Parallel API for live research capabilities
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
import aiohttp

from ..config import settings

logger = logging.getLogger(__name__)


class ParallelClient:
    """
    Client for Parallel API integration
    Handles fact verification and real-time research
    """
    
    def __init__(self):
        self.api_key = settings.PARALLEL_API_KEY
        self.base_url = settings.PARALLEL_API_URL
        self.session = None
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            headers = {
                "Authorization": f"Bearer {self.api_key}" if self.api_key else "",
                "Content-Type": "application/json",
                "User-Agent": "Greenlit-AI/1.0"
            }
            self.session = aiohttp.ClientSession(headers=headers)
        return self.session
    
    async def research_query(
        self, 
        query: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Research a query using Parallel API
        
        Args:
            query: Research question to investigate
            context: Optional context for the research
        
        Returns:
            Research results with sources and summary
        """
        
        # For demo purposes, return mock data if no API key
        if not self.api_key or self.api_key == "your_parallel_api_key_here":
            return await self._mock_research_response(query, context)
        
        try:
            session = await self._get_session()
            
            # Parallel API request payload (adjust based on actual API spec)
            payload = {
                "query": query,
                "context": context or {},
                "max_results": 5,
                "include_sources": True
            }
            
            # Make API request
            async with session.post(
                f"{self.base_url}/research",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    return self._format_parallel_response(result)
                else:
                    logger.error(f"Parallel API error: {response.status}")
                    return await self._mock_research_response(query, context)
        
        except Exception as e:
            logger.error(f"Parallel API request failed: {str(e)}")
            return await self._mock_research_response(query, context)
    
    def _format_parallel_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Format Parallel API response to standard format"""
        
        return {
            "summary": response.get("summary", "Research completed"),
            "sources": [
                {
                    "title": source.get("title", "Unknown Source"),
                    "url": source.get("url", ""),
                    "credibility": source.get("credibility", 0.7)
                }
                for source in response.get("sources", [])
            ],
            "confidence": response.get("confidence", 0.75),
            "research_time": response.get("research_time", 1.2),
            "metadata": {
                "api_provider": "parallel",
                "query_processed": response.get("query_processed", True)
            }
        }
    
    async def _mock_research_response(
        self, 
        query: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Mock research response for development/demo purposes
        Provides realistic-looking data based on query content
        """
        
        # Add small delay to simulate API call
        await asyncio.sleep(0.5)
        
        query_lower = query.lower()
        
        # Mock responses based on query content
        if "titanic" in query_lower:
            return {
                "summary": "The RMS Titanic was a British passenger liner that sank in the North Atlantic Ocean on April 15, 1912, after striking an iceberg during her maiden voyage from Southampton to New York City.",
                "sources": [
                    {"title": "Titanic - Encyclopedia Britannica", "url": "https://www.britannica.com/topic/Titanic", "credibility": 0.95},
                    {"title": "Titanic Historical Society", "url": "https://www.titanic-titanic.com", "credibility": 0.85}
                ],
                "confidence": 0.95,
                "research_time": 1.1,
                "metadata": {"api_provider": "mock", "query_processed": True}
            }
        
        elif "1912" in query_lower:
            return {
                "summary": "1912 was a significant year marked by the sinking of the Titanic, the Republic of China establishment, and various other historical events.",
                "sources": [
                    {"title": "1912 - Historical Events", "url": "https://www.history.com/topics/1912", "credibility": 0.90},
                    {"title": "Timeline of 1912", "url": "https://en.wikipedia.org/wiki/1912", "credibility": 0.80}
                ],
                "confidence": 0.85,
                "research_time": 0.8,
                "metadata": {"api_provider": "mock", "query_processed": True}
            }
        
        elif "iphone" in query_lower:
            return {
                "summary": "The iPhone was first released by Apple in 2007, making any reference to iPhones in 1912 historically inaccurate.",
                "sources": [
                    {"title": "iPhone History - Apple", "url": "https://www.apple.com/iphone/", "credibility": 0.95},
                    {"title": "History of Mobile Phones", "url": "https://www.history.com/topics/mobile-phones", "credibility": 0.85}
                ],
                "confidence": 0.98,
                "research_time": 0.6,
                "metadata": {"api_provider": "mock", "query_processed": True}
            }
        
        elif any(location in query_lower for location in ["new york", "london", "paris", "tokyo"]):
            return {
                "summary": f"Geographic information about the location mentioned in: {query}",
                "sources": [
                    {"title": "Geographic Reference", "url": "https://www.nationalgeographic.com", "credibility": 0.90},
                    {"title": "Location Database", "url": "https://www.geonames.org", "credibility": 0.85}
                ],
                "confidence": 0.80,
                "research_time": 0.9,
                "metadata": {"api_provider": "mock", "query_processed": True}
            }
        
        else:
            # Generic response for unrecognized queries
            return {
                "summary": f"Research completed for query: {query}. This is a mock response for development purposes.",
                "sources": [
                    {"title": "General Reference", "url": "https://www.example.com/reference", "credibility": 0.70},
                    {"title": "Research Database", "url": "https://www.example.com/database", "credibility": 0.65}
                ],
                "confidence": 0.60,
                "research_time": 1.0,
                "metadata": {"api_provider": "mock", "query_processed": True}
            }
    
    async def batch_research(
        self, 
        queries: List[str], 
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Research multiple queries in parallel
        
        Args:
            queries: List of research questions
            context: Optional context for all queries
        
        Returns:
            List of research results
        """
        
        # Process queries concurrently with rate limiting
        semaphore = asyncio.Semaphore(5)  # Limit concurrent requests
        
        async def research_with_semaphore(query: str):
            async with semaphore:
                return await self.research_query(query, context)
        
        results = await asyncio.gather(*[
            research_with_semaphore(query) for query in queries
        ], return_exceptions=True)
        
        # Handle exceptions and return valid results
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
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    def __del__(self):
        """Cleanup on deletion"""
        if hasattr(self, 'session') and self.session and not self.session.closed:
            try:
                asyncio.create_task(self.session.close())
            except:
                pass


# Singleton instance for reuse
_parallel_client_instance = None

async def get_parallel_client() -> ParallelClient:
    """Get shared Parallel client instance"""
    global _parallel_client_instance
    
    if _parallel_client_instance is None:
        _parallel_client_instance = ParallelClient()
    
    return _parallel_client_instance