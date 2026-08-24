"""
Gemini Client - Uses official Google Gen AI SDK
Handles AI interactions for all Gemini-powered agents
"""

import asyncio
import logging
from typing import Optional

from google import genai
from google.genai import types

from ..config import settings

logger = logging.getLogger(__name__)


class GeminiClient:
    """
    Google Gen AI SDK-based client for multi-agent system
    Uses Gemini models via the official google-genai package
    """
    
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL
        self._client = None
        self._async_client = None
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
    
    def _get_client(self) -> genai.Client:
        """Get or create sync client"""
        if self._client is None:
            self._client = genai.Client(api_key=self.api_key)
        return self._client
    
    def _get_async_client(self) -> genai.Client:
        """Get or create async client"""
        if self._async_client is None:
            self._async_client = genai.Client(api_key=self.api_key)
        return self._async_client
    
    async def generate_content(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2000
    ) -> str:
        """
        Generate content using Gemini model
        
        Args:
            prompt: User prompt for the AI
            system_prompt: Optional system prompt to set behavior
            temperature: Creativity level (0.0-1.0)
            max_tokens: Maximum response length
        
        Returns:
            Generated text response
        """
        
        try:
            client = self._get_async_client()
            
            config = types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                top_p=0.9,
            )
            
            if system_prompt:
                config.system_instruction = system_prompt
            
            response = await client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config
            )
            
            if response.text:
                logger.info(f"Gemini response generated ({len(response.text)} chars)")
                return response.text.strip()
            else:
                logger.error("Gemini returned empty response")
                raise Exception("Empty response from Gemini")
        
        except Exception as e:
            logger.error(f"Gemini content generation failed: {str(e)}")
            raise Exception(f"Gemini API error: {str(e)}")
    
    async def close(self):
        """Clean up client resources"""
        # google-genai clients don't require explicit cleanup
        self._client = None
        self._async_client = None


# Singleton instance for reuse across agents
_gemini_client_instance = None

async def get_gemini_client() -> GeminiClient:
    """Get shared Gemini client instance"""
    global _gemini_client_instance
    
    if _gemini_client_instance is None:
        _gemini_client_instance = GeminiClient()
    
    return _gemini_client_instance


async def close_gemini_client():
    """Close the shared Gemini client"""
    global _gemini_client_instance
    if _gemini_client_instance:
        await _gemini_client_instance.close()
        _gemini_client_instance = None
