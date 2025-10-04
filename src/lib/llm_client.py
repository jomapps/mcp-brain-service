"""
OpenRouter LLM Client for Brain Service
Provides LLM operations for theme extraction, summaries, and analysis
"""

import os
import logging
from typing import List, Dict, Any, Optional
import aiohttp
import json

logger = logging.getLogger(__name__)


class OpenRouterClient:
    """Client for OpenRouter API"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        self.default_model = os.getenv("OPENROUTER_DEFAULT_MODEL", "anthropic/claude-sonnet-4.5")
        self.backup_model = os.getenv("OPENROUTER_BACKUP_MODEL", "qwen/qwen3-vl-235b-a22b-thinking")
        
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable is required")
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        use_backup: bool = False
    ) -> Dict[str, Any]:
        """
        Send a chat completion request to OpenRouter
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use (defaults to OPENROUTER_DEFAULT_MODEL)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            use_backup: Use backup model if True
            
        Returns:
            Response dict with 'content' and 'usage' keys
        """
        if model is None:
            model = self.backup_model if use_backup else self.default_model
        
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://brain.ft.tc",
            "X-Title": "MCP Brain Service"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"OpenRouter API error: {response.status} - {error_text}")
                        raise Exception(f"OpenRouter API error: {response.status}")
                    
                    result = await response.json()
                    
                    return {
                        "content": result["choices"][0]["message"]["content"],
                        "usage": result.get("usage", {}),
                        "model": model
                    }
        except Exception as e:
            logger.error(f"Failed to call OpenRouter API: {e}")
            raise
    
    async def extract_themes(
        self,
        contents: List[str],
        department: str,
        max_themes: int = 5
    ) -> List[str]:
        """
        Extract key themes from a list of content items
        
        Args:
            contents: List of text content to analyze
            department: Department context (e.g., 'story', 'character')
            max_themes: Maximum number of themes to extract
            
        Returns:
            List of theme strings
        """
        combined_content = "\n\n---\n\n".join(contents[:10])  # Limit to first 10 items
        
        messages = [
            {
                "role": "system",
                "content": f"You are an expert at analyzing {department} content and extracting key themes. Be concise and specific."
            },
            {
                "role": "user",
                "content": f"""Analyze the following {department} content and extract the {max_themes} most important themes or topics.

Content:
{combined_content}

Return ONLY a JSON array of theme strings, like: ["theme1", "theme2", "theme3"]
Do not include any other text or explanation."""
            }
        ]
        
        try:
            response = await self.chat_completion(messages, temperature=0.3, max_tokens=500)
            content = response["content"].strip()
            
            # Try to parse JSON from response
            # Handle cases where LLM might wrap in markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            themes = json.loads(content)
            
            if isinstance(themes, list):
                return themes[:max_themes]
            else:
                logger.warning(f"Unexpected theme format: {themes}")
                return []
                
        except Exception as e:
            logger.error(f"Failed to extract themes: {e}")
            return []
    
    async def generate_summary(
        self,
        contents: List[str],
        context: str = "",
        max_length: int = 200
    ) -> str:
        """
        Generate an aggregated summary from multiple content items
        
        Args:
            contents: List of text content to summarize
            context: Additional context for the summary
            max_length: Maximum length of summary in words
            
        Returns:
            Summary string
        """
        combined_content = "\n\n---\n\n".join(contents[:15])  # Limit to first 15 items
        
        messages = [
            {
                "role": "system",
                "content": "You are an expert at synthesizing information and creating concise summaries."
            },
            {
                "role": "user",
                "content": f"""Create a concise summary (max {max_length} words) that captures the key points from the following content.

{f'Context: {context}' if context else ''}

Content:
{combined_content}

Provide ONLY the summary text, no preamble or explanation."""
            }
        ]
        
        try:
            response = await self.chat_completion(messages, temperature=0.5, max_tokens=500)
            return response["content"].strip()
        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            return ""
    
    async def analyze_coverage(
        self,
        gather_items: List[Dict[str, str]],
        department: str,
        department_description: str
    ) -> Dict[str, Any]:
        """
        Analyze content coverage and identify gaps
        
        Args:
            gather_items: List of dicts with 'content' and 'summary' keys
            department: Department slug
            department_description: Description of department scope
            
        Returns:
            Dict with coverage analysis including gaps and recommendations
        """
        # Prepare content for analysis
        items_text = "\n\n".join([
            f"Item {i+1}:\nSummary: {item.get('summary', 'N/A')}\nContent: {item.get('content', '')[:500]}..."
            for i, item in enumerate(gather_items[:20])  # Limit to 20 items
        ])
        
        messages = [
            {
                "role": "system",
                "content": f"You are an expert at analyzing {department} content coverage and identifying gaps."
            },
            {
                "role": "user",
                "content": f"""Analyze the coverage of the following {department} gather items against the department scope.

Department: {department}
Scope: {department_description}

Gather Items ({len(gather_items)} total):
{items_text}

Provide a JSON response with this EXACT structure (all fields are required):
{{
  "coveredAspects": [
    {{
      "aspect": "Aspect name",
      "coverage": 85,
      "itemCount": 5,
      "quality": "excellent"
    }}
  ],
  "gaps": [
    {{
      "aspect": "Missing aspect",
      "coverage": 20,
      "itemCount": 0,
      "severity": "high",
      "suggestion": "Specific actionable suggestion"
    }}
  ],
  "recommendations": ["Recommendation 1", "Recommendation 2"]
}}

IMPORTANT:
- coverage must be a number 0-100
- itemCount must be a number (0 for gaps)
- quality must be one of: excellent, good, fair, poor
- severity must be one of: high, medium, low
- All fields are REQUIRED

Return ONLY valid JSON, no other text."""
            }
        ]
        
        try:
            response = await self.chat_completion(
                messages,
                temperature=0.3,
                max_tokens=2000
            )
            content = response["content"].strip()
            
            # Parse JSON from response
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            analysis = json.loads(content)
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze coverage: {e}")
            # Return minimal structure on error
            return {
                "coveredAspects": [],
                "gaps": [],
                "recommendations": ["Unable to analyze coverage due to an error"]
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if OpenRouter API is accessible"""
        try:
            messages = [{"role": "user", "content": "Hello"}]
            await self.chat_completion(messages, max_tokens=10)
            return {"status": "healthy", "service": "OpenRouter"}
        except Exception as e:
            return {"status": "unhealthy", "service": "OpenRouter", "error": str(e)}


# Singleton instance
_llm_client: Optional[OpenRouterClient] = None


def get_llm_client() -> OpenRouterClient:
    """Get or create LLM client singleton"""
    global _llm_client
    if _llm_client is None:
        _llm_client = OpenRouterClient()
    return _llm_client

