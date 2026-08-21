"""
Gemini Client - Updated to use Gemini 3.1 Flash Lite via OpenRouter
Handles AI interactions for all Gemini-powered agents
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
import os
import json

import aiohttp
from ..config import settings

logger = logging.getLogger(__name__)


class GeminiClient:
    """
    OpenRouter-based Gemini client for multi-agent system
    Uses Gemini 3.1 Flash Lite via OpenRouter API
    """
    
    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.base_url = settings.OPENROUTER_BASE_URL
        self.model_name = settings.GEMINI_MODEL
        self.session = None
        
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment variables")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://greenlit-ai.com",  # Required by OpenRouter
                "X-Title": "Greenlit AI - Production Research"  # Optional app name
            }
            self.session = aiohttp.ClientSession(headers=headers)
        return self.session
    
    async def generate_content(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2000
    ) -> str:
        """
        Generate content using Gemini 3.1 Flash Lite via OpenRouter
        
        Args:
            prompt: User prompt for the AI
            system_prompt: Optional system prompt to set behavior
            temperature: Creativity level (0.0-1.0)
            max_tokens: Maximum response length
        
        Returns:
            Generated text response
        """
        
        try:
            session = await self._get_session()
            
            # Format messages for OpenRouter API
            messages = []
            
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            
            messages.append({
                "role": "user", 
                "content": prompt
            })
            
            # OpenRouter API request payload
            payload = {
                "model": self.model_name,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "top_p": 0.9,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0
            }
            
            # Make API request
            async with session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"OpenRouter API error {response.status}: {error_text}")
                    raise Exception(f"OpenRouter API error: {response.status}")
                
                result = await response.json()
                
                # Extract content from OpenRouter response
                if "choices" in result and len(result["choices"]) > 0:
                    content = result["choices"][0]["message"]["content"]
                    
                    # Log usage statistics if available
                    if "usage" in result:
                        usage = result["usage"]
                        logger.info(
                            f"OpenRouter usage - Input: {usage.get('prompt_tokens', 0)} tokens, "
                            f"Output: {usage.get('completion_tokens', 0)} tokens"
                        )
                    
                    return content.strip()
                else:
                    logger.error(f"Unexpected OpenRouter response format: {result}")
                    raise Exception("Invalid response format from OpenRouter")
        
        except asyncio.TimeoutError:
            logger.error("OpenRouter API request timed out")
            raise Exception("Gemini API request timed out")
        
        except Exception as e:
            logger.error(f"Gemini content generation failed: {str(e)}")
            raise Exception(f"Gemini API error: {str(e)}")
    
    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()


# Singleton instance for reuse across agents
_gemini_client_instance = None

async def get_gemini_client() -> GeminiClient:
    """Get shared Gemini client instance"""
    global _gemini_client_instance
    
    if _gemini_client_instance is None:
        _gemini_client_instance = GeminiClient()
    
    return _gemini_client_instance