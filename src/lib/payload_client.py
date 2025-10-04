"""
PayloadCMS Client for Brain Service
Fetches department configurations from the main application
"""

import os
import logging
from typing import List, Dict, Any, Optional
import aiohttp

logger = logging.getLogger(__name__)


class PayloadCMSClient:
    """Client for PayloadCMS API"""
    
    def __init__(self):
        self.api_url = os.getenv("MAIN_APP_PAYLOAD_API_URL")
        self.api_key = os.getenv("MAIN_APP_PAYLOAD_API_KEY")
        
        if not self.api_url:
            raise ValueError("MAIN_APP_PAYLOAD_API_URL environment variable is required")
        if not self.api_key:
            raise ValueError("MAIN_APP_PAYLOAD_API_KEY environment variable is required")
        
        # Remove trailing slash if present
        self.api_url = self.api_url.rstrip('/')
    
    async def get_departments(self) -> List[Dict[str, Any]]:
        """
        Fetch all departments from PayloadCMS
        
        Returns:
            List of department dicts with 'slug', 'name', 'description' keys
        """
        url = f"{self.api_url}/departments"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"PayloadCMS API error: {response.status} - {error_text}")
                        # Return empty list on error instead of raising
                        return []
                    
                    result = await response.json()
                    
                    # PayloadCMS typically returns {docs: [...], ...}
                    departments = result.get("docs", [])
                    
                    return [
                        {
                            "slug": dept.get("slug", ""),
                            "name": dept.get("name", ""),
                            "description": dept.get("description", "")
                        }
                        for dept in departments
                    ]
        except Exception as e:
            logger.error(f"Failed to fetch departments from PayloadCMS: {e}")
            return []
    
    async def get_department_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a specific department by slug
        
        Args:
            slug: Department slug (e.g., 'story', 'character')
            
        Returns:
            Department dict or None if not found
        """
        departments = await self.get_departments()
        
        for dept in departments:
            if dept.get("slug") == slug:
                return dept
        
        return None
    
    async def validate_department(self, slug: str) -> bool:
        """
        Check if a department slug is valid
        
        Args:
            slug: Department slug to validate
            
        Returns:
            True if valid, False otherwise
        """
        dept = await self.get_department_by_slug(slug)
        return dept is not None
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if PayloadCMS API is accessible"""
        try:
            url = f"{self.api_url}/departments"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        return {"status": "healthy", "service": "PayloadCMS"}
                    else:
                        return {
                            "status": "unhealthy",
                            "service": "PayloadCMS",
                            "error": f"HTTP {response.status}"
                        }
        except Exception as e:
            return {"status": "unhealthy", "service": "PayloadCMS", "error": str(e)}


# Singleton instance
_payload_client: Optional[PayloadCMSClient] = None


def get_payload_client() -> PayloadCMSClient:
    """Get or create PayloadCMS client singleton"""
    global _payload_client
    if _payload_client is None:
        _payload_client = PayloadCMSClient()
    return _payload_client

