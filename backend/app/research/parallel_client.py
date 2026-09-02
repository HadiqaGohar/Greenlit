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
            # Try with "core" processor for faster results
            task_run = await client.task_run.create(
                input=query,
                processor="core"
            )
            
            logger.info(f"Parallel API task created: {task_run.run_id} for query: {query[:60]}...")
            
            # Poll for results with shorter interval
            result = await client.task_run.result(run_id=task_run.run_id)
            
            logger.info(f"Parallel API task completed: {task_run.run_id}")
            
            # Format the response
            return self._format_response(result, query)
        
        except Exception as e:
            logger.error(f"Parallel API request failed: {str(e)}")
            return self._basic_fallback(query)
    
    def _format_response(self, result: Any, query: str) -> Dict[str, Any]:
        """Format Parallel SDK response to standard format with rich citation parsing"""
        from urllib.parse import urlparse
        
        # 1. Extract content / summary
        summary_text = ""
        content = getattr(result, 'content', None)
        if content:
            if isinstance(content, dict):
                summary_text = str(content.get('output', content.get('answer', content.get('summary', ''))))
            elif isinstance(content, str):
                summary_text = content
            else:
                summary_text = str(content)
        
        if not summary_text:
            output = getattr(result, 'output', None)
            if output:
                if isinstance(output, dict):
                    summary_text = str(output.get('output', output.get('answer', '')))
                else:
                    summary_text = str(output)
            else:
                summary_text = str(result)
        
        # 2. Extract citations / sources from basis, citations, or sources
        sources = []
        seen_urls = set()
        
        def add_citation(url: str, title: Optional[str] = None, excerpt: Optional[str] = None, cred: float = 0.85):
            if not url or url in seen_urls:
                return
            seen_urls.add(url)
            clean_title = title
            if not clean_title or clean_title == "None" or clean_title == "Unknown":
                try:
                    parsed = urlparse(url)
                    clean_title = parsed.netloc.replace("www.", "").capitalize()
                except Exception:
                    clean_title = "Web Source"
            sources.append({
                "title": clean_title,
                "url": url,
                "excerpt": excerpt or "",
                "credibility": cred
            })
        
        # Check basis (Parallel TaskRunJsonOutput FieldBasis structure)
        basis = getattr(result, 'basis', None)
        basis_confidence_val = None
        if basis and isinstance(basis, (list, tuple)):
            for b in basis:
                # Capture reasoning if summary was not detailed
                reasoning = getattr(b, 'reasoning', None)
                if reasoning and (not summary_text or len(summary_text) < 20):
                    summary_text = reasoning
                
                # Check confidence in basis
                b_conf = getattr(b, 'confidence', None)
                if b_conf:
                    if isinstance(b_conf, str):
                        conf_map = {"high": 0.9, "medium": 0.75, "low": 0.4}
                        basis_confidence_val = conf_map.get(b_conf.lower(), 0.75)
                    elif isinstance(b_conf, (int, float)):
                        basis_confidence_val = float(b_conf)
                
                # Check citations inside FieldBasis
                cits = getattr(b, 'citations', None) or []
                for c in cits:
                    c_url = getattr(c, 'url', None) or (c.get('url') if isinstance(c, dict) else '')
                    c_title = getattr(c, 'title', None) or (c.get('title') if isinstance(c, dict) else '')
                    c_excerpts = getattr(c, 'excerpts', None) or (c.get('excerpts') if isinstance(c, dict) else [])
                    excerpt_str = " | ".join(c_excerpts) if isinstance(c_excerpts, list) else str(c_excerpts or '')
                    add_citation(c_url, c_title, excerpt_str, 0.85)
        
        # Check direct citations attribute
        if hasattr(result, 'citations') and result.citations:
            for c in result.citations:
                c_url = getattr(c, 'url', '') if hasattr(c, 'url') else (c.get('url') if isinstance(c, dict) else '')
                c_title = getattr(c, 'title', '') if hasattr(c, 'title') else (c.get('title') if isinstance(c, dict) else '')
                add_citation(c_url, c_title)
                
        # Check direct sources attribute
        if hasattr(result, 'sources') and result.sources:
            for s in result.sources:
                s_url = getattr(s, 'url', '') if hasattr(s, 'url') else (s.get('url') if isinstance(s, dict) else '')
                s_title = getattr(s, 'title', '') if hasattr(s, 'title') else (s.get('title') if isinstance(s, dict) else '')
                s_cred = getattr(s, 'credibility', 0.8) if hasattr(s, 'credibility') else 0.8
                add_citation(s_url, s_title, cred=s_cred)
        
        # 3. Extract confidence
        raw_conf = getattr(result, 'confidence', None) or basis_confidence_val or 0.8
        if isinstance(raw_conf, str):
            conf_map = {"high": 0.9, "medium": 0.75, "low": 0.4}
            confidence = conf_map.get(raw_conf.lower(), 0.75)
        else:
            confidence = float(raw_conf) if raw_conf is not None else 0.75
            
        return {
            "summary": summary_text or f"Research completed for: {query}",
            "sources": sources,
            "confidence": confidence,
            "metadata": {
                "api_provider": "parallel",
                "query_processed": True,
                "sources_count": len(sources)
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
