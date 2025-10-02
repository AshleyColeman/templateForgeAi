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
        from .utils.logger import get_logger
        logger = get_logger(0)  # Use default logger
        
        prompt = self._build_prompt(url, html_snippet)
        
        try:
            import httpx
            import time
            
            logger.info("Sending request to Ollama at {}", self.config.ollama_host)
            logger.info("Using model: {}", self.config.ollama_model)
            logger.debug("Prompt length: {} chars", len(prompt))
            
            start_time = time.time()
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.config.ollama_host}/api/chat",
                    json={
                        "model": self.config.ollama_model,
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "stream": False,
                        "options": {
                            "temperature": self.config.model_temperature,
                            "num_predict": self.config.max_tokens
                        }
                    },
                    timeout=120.0  # Increased timeout for complex analysis
                )
                
                elapsed = time.time() - start_time
                logger.info("Ollama response received in {:.2f}s", elapsed)
                
                response.raise_for_status()
                
                result = response.json()
                # Ollama /api/chat returns message in result["message"]["content"]
                content = result.get("message", {}).get("content", "")
                logger.debug("Response length: {} chars", len(content))
                
                return self._parse_response(content, url)
                
        except httpx.ReadTimeout as e:
            logger.error("Ollama request timed out after 120s")
            logger.error("Model {} may be too slow or not loaded", self.config.ollama_model)
            raise AnalysisError(
                f"Ollama timeout: Model '{self.config.ollama_model}' took too long to respond. "
                f"Consider using a faster model or switching to OpenAI/Anthropic."
            )
        except httpx.HTTPStatusError as e:
            logger.error("Ollama HTTP error: {} {}", e.response.status_code, e.response.text)
            raise AnalysisError(f"Ollama HTTP error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            logger.error("Ollama API error: {}", str(e))
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
        """
        Build a robust analysis prompt for extracting category navigation from an e-commerce page.
        - Forces REAL selectors (no hallucinations).
        - Encourages multiple candidate patterns (top-nav, sidebar, dropdown, etc.).
        - Asks for small innerText evidence to verify selectors.
        - Captures interactions suitable for Playwright (click/hover/wait).
        - Adds include/exclude href rules to filter noise links.
        - Output is STRICT JSON (no comments, no trailing commas).
        """
        head = html_snippet[:4000]
        truncated_flag = len(html_snippet) > 4000

        return (
            "You are an expert DOM analyst helping a Python scraping agent detect PRODUCT CATEGORIES on a web page.\n"
            "Return ONLY valid JSON (UTF-8, no comments, no trailing commas). Do NOT include any explanation outside JSON.\n\n"
            "## GOAL\n"
            "Identify how categories (or similar: departments, collections, shop by, ranges, menus, taxonomy) are implemented.\n"
            "Produce REAL CSS selectors present in the HTML below, plus minimal interaction steps if disclosure menus are hidden.\n\n"
            "## HARD REQUIREMENTS\n"
            "1) Use ONLY classes/ids/structures that appear in the provided HTML. Do NOT invent selectors.\n"
            "2) Prefer stable anchors: landmark tags (nav, header, aside), ARIA roles (role='navigation'|'menu'|'tree'), data-* attributes.\n"
            "3) Provide 1–3 candidate 'nav models' (different plausible patterns). Rank by confidence.\n"
            "4) Include tiny evidence samples (innerText of 1–5 matched links) so a human can verify quickly.\n"
            "5) If categories are absent/hidden in this snippet, return empty selectors and a fallback plan.\n\n"
            "## WHAT TO LOOK FOR\n"
            "- Top navigation: <nav>, <header>, mega menus, hover menus, <ul>/<li> lists, role='menubar'.\n"
            "- Sidebars: <aside>, .sidebar, .filters, .categories, facets trees, accordion sections.\n"
            "- Dropdown/accordion/flyout panels: elements toggled by buttons with aria-expanded, aria-controls, data-toggle, etc.\n"
            "- Breadcrumb/JSON-LD hints: breadcrumb lists or ItemList that reveal taxonomy terms.\n"
            "- Synonyms: 'Departments', 'Collections', 'Ranges', 'Shop', 'Shop by', 'Brands' (brands may be categories on some sites).\n\n"
            "## NOISE TO AVOID (exclude via link filters)\n"
            "- Account, Login, Register, Cart, Basket, Wishlist, Help/FAQ, Contact, Blog, Checkout, Search, Language, Currency.\n"
            "- Very generic footers that are not category trees.\n\n"
            "## OUTPUT (STRICT JSON)\n"
            "{\n"
            '  "url": "<echo URL>",\n'
            '  "html_truncated": true|false,\n'
            '  "nav_models": [\n'
            "    {\n"
            '      "navigation_type": "top_nav|sidebar|dropdown|accordion|hover_menu|filter_sidebar|breadcrumbs|unknown",\n'
            '      "selectors": {\n'
            '        "nav_container": "REAL CSS selector for container",\n'
            '        "category_links": "REAL CSS selector for category anchors",\n'
            '        "top_level_items": "selector for top-level li/div nodes or anchors",\n'
            '        "flyout_panel": "selector for flyout/dropdown panels or null",\n'
            '        "subcategory_list": "selector for subcategory lists or null"\n'
            "      },\n"
            '      "interactions": [\n'
            '        {"type": "hover|click", "target": "selector", "wait_for": "selector to appear or null"}\n'
            "      ],\n"
            '      "link_filters": {\n'
            '        "include_href_patterns": ["regex or substring patterns like \\"/category\\", \\"/c/\\""],\n'
            '        "exclude_href_patterns": ["account|login|register|cart|wishlist|help|faq|contact|checkout|search|language|currency"]\n'
            "      },\n"
            '      "evidence": {\n'
            '        "sample_text": ["up to 5 innerText samples e.g. \\"Women\\", \\"Men\\", \\"Kids\\", \\"Sale\\""],\n'
            '        "counts": {"category_links": 0, "top_level_items": 0}\n'
            "      },\n"
            '      "confidence": 0.0\n'
            "    }\n"
            "  ],\n"
            '  "best_index": 0,\n'
            '  "fallback_plan": [\n'
            '    "If no categories found: try sitemap.xml for /category/ or /collections/, check JSON-LD ItemList, or scan <footer> with stricter include filters."\n'
            "  ],\n"
            '  "notes": ["brief reasoning on why the best model was chosen"]\n'
            "}\n\n"
            "## VALIDATION RULES\n"
            "- Every selector MUST match something that exists in the provided HTML.\n"
            "- Arrays may be empty if unknown; use empty arrays [] rather than null.\n"
            "- confidence in [0.0, 1.0]. best_index is the index of the strongest candidate in nav_models.\n\n"
            f"URL: {url}\n"
            f"HTML_SNIPPET_FIRST_4000_CHARS (truncated={str(truncated_flag).lower()}):\n"
            f"{head}\n"
            "END_OF_HTML_SNIPPET\n"
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
            
            # Handle new format with nav_models array
            if "nav_models" in structured and structured["nav_models"]:
                best_index = structured.get("best_index", 0)
                best_model = structured["nav_models"][best_index] if best_index < len(structured["nav_models"]) else structured["nav_models"][0]
                
                return {
                    "navigation_type": best_model.get("navigation_type", "unknown"),
                    "selectors": best_model.get("selectors", {}),
                    "interactions": best_model.get("interactions", []),
                    "confidence": float(best_model.get("confidence", 0.5)),
                    "notes": structured.get("notes", []),
                    "link_filters": best_model.get("link_filters", {}),
                    "evidence": best_model.get("evidence", {}),
                    "analyzed_at": self._get_timestamp()
                }
            
            # Fallback to old format
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
