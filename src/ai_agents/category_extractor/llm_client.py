"""LLM client supporting multiple providers (OpenAI, Anthropic, Ollama, OpenRouter)."""
from __future__ import annotations

import base64
import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from .config import get_config
from .errors import AnalysisError


class LLMClient(ABC):
    """Abstract base class for LLM clients."""
    
    @abstractmethod
    async def analyze_page(
        self, 
        url: str, 
        screenshot_b64: str, 
        html_snippet: str
    ) -> Dict[str, Any]:
        """Analyze a webpage with vision and text capabilities."""
        pass


class OpenAILLMClient(LLMClient):
    """OpenAI client for text and vision analysis."""
    
    def __init__(self, config=None):
        self.config = config or get_config()
        self._client = None
    
    @property
    def client(self):
        if self._client is None:
            try:
                import openai
                self._client = openai.AsyncOpenAI(
                    api_key=self.config.openai_api_key,
                    base_url=self.config.openai_base_url
                )
            except ImportError:
                raise ImportError("OpenAI library not installed. Run: pip install openai")
        return self._client
    
    async def analyze_page(
        self, 
        url: str, 
        screenshot_b64: str, 
        html_snippet: str
    ) -> Dict[str, Any]:
        """Analyze webpage using OpenAI GPT-4 Vision."""
        prompt = self._build_prompt(url, html_snippet)
        
        try:
            response = await self.client.chat.completions.create(
                model=self.config.openai_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{screenshot_b64}"
                                }
                            }
                        ]
                    }
                ],
                temperature=self.config.model_temperature,
                max_tokens=self.config.max_tokens
            )
            
            content = response.choices[0].message.content
            return self._parse_response(content, url)
            
        except Exception as e:
            raise AnalysisError(f"OpenAI API error: {e}")


class AnthropicLLMClient(LLMClient):
    """Anthropic client for text and vision analysis."""
    
    def __init__(self, config=None):
        self.config = config or get_config()
        self._client = None
    
    @property
    def client(self):
        if self._client is None:
            try:
                import anthropic
                self._client = anthropic.AsyncAnthropic(
                    api_key=self.config.anthropic_api_key
                )
            except ImportError:
                raise ImportError("Anthropic library not installed. Run: pip install anthropic")
        return self._client
    
    async def analyze_page(
        self, 
        url: str, 
        screenshot_b64: str, 
        html_snippet: str
    ) -> Dict[str, Any]:
        """Analyze webpage using Anthropic Claude Vision."""
        prompt = self._build_prompt(url, html_snippet)
        
        try:
            response = await self.client.messages.create(
                model=self.config.anthropic_model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.model_temperature,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": screenshot_b64
                            }
                        }
                    ]
                }]
            )
            
            content = response.content[0].text
            return self._parse_response(content, url)
            
        except Exception as e:
            raise AnalysisError(f"Anthropic API error: {e}")


class OllamaLLMClient(LLMClient):
    """Ollama client for local LLM inference."""
    
    def __init__(self, config=None):
        self.config = config or get_config()
    
    async def analyze_page(
        self, 
        url: str, 
        screenshot_b64: str, 
        html_snippet: str
    ) -> Dict[str, Any]:
        """Analyze webpage using local Ollama model."""
        prompt = self._build_prompt(url, html_snippet)
        
        try:
            import httpx
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.config.ollama_host}/api/generate",
                    json={
                        "model": self.config.ollama_model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": self.config.model_temperature,
                            "num_predict": self.config.max_tokens
                        }
                    },
                    timeout=60.0
                )
                response.raise_for_status()
                
                result = response.json()
                content = result.get("response", "")
                return self._parse_response(content, url)
                
        except Exception as e:
            raise AnalysisError(f"Ollama API error: {e}")


class OpenRouterLLMClient(LLMClient):
    """OpenRouter client for accessing various models."""
    
    def __init__(self, config=None):
        self.config = config or get_config()
        self._client = None
    
    @property
    def client(self):
        if self._client is None:
            try:
                import openai
                self._client = openai.AsyncOpenAI(
                    api_key=self.config.openrouter_api_key,
                    base_url="https://openrouter.ai/api/v1"
                )
            except ImportError:
                raise ImportError("OpenAI library not installed. Run: pip install openai")
        return self._client
    
    async def analyze_page(
        self, 
        url: str, 
        screenshot_b64: str, 
        html_snippet: str
    ) -> Dict[str, Any]:
        """Analyze webpage using OpenRouter model."""
        prompt = self._build_prompt(url, html_snippet)
        
        try:
            response = await self.client.chat.completions.create(
                model=self.config.openrouter_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{screenshot_b64}"
                                }
                            }
                        ]
                    }
                ],
                temperature=self.config.model_temperature,
                max_tokens=self.config.max_tokens
            )
            
            content = response.choices[0].message.content
            return self._parse_response(content, url)
            
        except Exception as e:
            raise AnalysisError(f"OpenRouter API error: {e}")


def create_llm_client(config=None) -> LLMClient:
    """Factory function to create the appropriate LLM client."""
    config = config or get_config()
    
    provider = config.llm_provider.lower()
    
    if provider == "openai":
        return OpenAILLMClient(config)
    elif provider == "anthropic":
        return AnthropicLLMClient(config)
    elif provider == "ollama":
        return OllamaLLMClient(config)
    elif provider == "openrouter":
        return OpenRouterLLMClient(config)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


# Mixin for common functionality
class LLMMixin:
    """Mixin providing common LLM functionality."""
    
    def _build_prompt(self, url: str, html_snippet: str) -> str:
        """Build the analysis prompt."""
        return (
            "Analyze this e-commerce webpage to identify product category navigation patterns. "
            "Look for navigation menus, category links, and hierarchical structures. "
            "Return a JSON response with the following structure:\n\n"
            "{\n"
            '  "navigation_type": "sidebar|hover_menu|dropdown|accordion|other",\n'
            '  "selectors": {\n'
            '    "nav_container": "CSS selector for main navigation",\n'
            '    "category_links": "CSS selector for category links",\n'
            '    "top_level_items": "CSS selector for top-level menu items",\n'
            '    "flyout_panel": "CSS selector for flyout/dropdown panels (if any)",\n'
            '    "subcategory_list": "CSS selector for subcategory lists (if any)"\n'
            "  },\n"
            '  "interactions": [\n'
            '    {"type": "hover|click|scroll", "target": "selector", "wait_for": "selector"}\n'
            "  ],\n"
            '  "confidence": 0.0-1.0,\n'
            '  "notes": ["observation1", "observation2"]\n'
            "}\n\n"
            f"URL: {url}\n"
            f"HTML snippet (first 4000 chars):\n{html_snippet[:4000]}"
        )
    
    def _parse_response(self, content: str, base_url: str) -> Dict[str, Any]:
        """Parse LLM response and extract structured data."""
        try:
            # Try to find JSON in the response
            import re
            
            # Look for JSON code block
            json_match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Look for JSON object
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    raise ValueError("No JSON found in response")
            
            structured = json.loads(json_str)
            
            # Validate and clean the response
            return {
                "navigation_type": structured.get("navigation_type", "unknown"),
                "selectors": structured.get("selectors", {}),
                "interactions": structured.get("interactions", []),
                "confidence": float(structured.get("confidence", 0.5)),
                "notes": structured.get("notes", []),
                "analyzed_at": self._get_timestamp()
            }
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            raise AnalysisError(f"Failed to parse LLM response: {e}\nResponse: {content}")
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.utcnow().isoformat()


# Apply mixin to all client classes
for client_class in [OpenAILLMClient, AnthropicLLMClient, OllamaLLMClient, OpenRouterLLMClient]:
    for method_name in ['_build_prompt', '_parse_response', '_get_timestamp']:
        setattr(client_class, method_name, getattr(LLMMixin, method_name))


__all__ = [
    "LLMClient", 
    "OpenAILLMClient", 
    "AnthropicLLMClient", 
    "OllamaLLMClient", 
    "OpenRouterLLMClient",
    "create_llm_client"
]
