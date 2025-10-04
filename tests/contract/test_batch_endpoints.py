"""
Contract tests for batch API endpoints
Tests request/response format compliance and validation
"""

import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Test API key
TEST_API_KEY = os.getenv("BRAIN_SERVICE_API_KEY", "ae6e18cb408bc7128f23585casdlaelwlekoqdsldsa")


# Helper to create test client
def get_test_client():
    """Create test client with proper transport"""
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
class TestBatchNodeCreation:
    """Test POST /api/v1/nodes/batch endpoint"""
    
    async def test_batch_create_success(self):
        """Test successful batch node creation"""
        async with get_test_client() as client:
            response = await client.post(
                "/api/v1/nodes/batch",
                headers={"Authorization": f"Bearer {TEST_API_KEY}"},
                json={
                    "nodes": [
                        {
                            "type": "GatherItem",
                            "content": "Test gather item content for story department",
                            "projectId": "507f1f77bcf86cd799439011",
                            "properties": {
                                "department": "story",
                                "isAutomated": True,
                                "iteration": 1
                            }
                        },
                        {
                            "type": "GatherItem",
                            "content": "Another test gather item for character development",
                            "projectId": "507f1f77bcf86cd799439011",
                            "properties": {
                                "department": "character",
                                "isAutomated": True
                            }
                        }
                    ]
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify response structure
            assert data["success"] is True
            assert data["created"] == 2
            assert len(data["nodeIds"]) == 2
            assert len(data["nodes"]) == 2
            
            # Verify timing info
            assert "timing" in data
            assert "embedding_time_ms" in data["timing"]
            assert "neo4j_write_time_ms" in data["timing"]
            assert "total_time_ms" in data["timing"]
            
            # Verify node structure
            node = data["nodes"][0]
            assert "id" in node
            assert node["type"] == "GatherItem"
            assert "properties" in node
            assert "embedding" in node
            assert node["embedding"]["dimensions"] > 0
    
    async def test_batch_create_missing_required_field(self):
        """Test batch creation with missing required field"""
        async with get_test_client() as client:
            response = await client.post(
                "/api/v1/nodes/batch",
                headers={"Authorization": f"Bearer {TEST_API_KEY}"},
                json={
                    "nodes": [
                        {
                            "type": "GatherItem",
                            # Missing content field
                            "projectId": "507f1f77bcf86cd799439011"
                        }
                    ]
                }
            )
            
            assert response.status_code == 422  # Validation error
    
    async def test_batch_create_invalid_project_id(self):
        """Test batch creation with invalid projectId format"""
        async with get_test_client() as client:
            response = await client.post(
                "/api/v1/nodes/batch",
                headers={"Authorization": f"Bearer {TEST_API_KEY}"},
                json={
                    "nodes": [
                        {
                            "type": "GatherItem",
                            "content": "Test content",
                            "projectId": "invalid-id"  # Not 24 hex chars
                        }
                    ]
                }
            )
            
            assert response.status_code == 422
    
    async def test_batch_create_exceeds_max_size(self):
        """Test batch creation exceeding max size of 50"""
        async with get_test_client() as client:
            # Create 51 nodes
            nodes = [
                {
                    "type": "GatherItem",
                    "content": f"Test content {i}",
                    "projectId": "507f1f77bcf86cd799439011"
                }
                for i in range(51)
            ]
            
            response = await client.post(
                "/api/v1/nodes/batch",
                headers={"Authorization": f"Bearer {TEST_API_KEY}"},
                json={"nodes": nodes}
            )
            
            assert response.status_code == 422  # Validation error
    
    async def test_batch_create_empty_batch(self):
        """Test batch creation with empty nodes array"""
        async with get_test_client() as client:
            response = await client.post(
                "/api/v1/nodes/batch",
                headers={"Authorization": f"Bearer {TEST_API_KEY}"},
                json={"nodes": []}
            )
            
            assert response.status_code == 422
    
    async def test_batch_create_unauthorized(self):
        """Test batch creation with invalid API key"""
        async with get_test_client() as client:
            response = await client.post(
                "/api/v1/nodes/batch",
                headers={"Authorization": "Bearer invalid-key"},
                json={
                    "nodes": [
                        {
                            "type": "GatherItem",
                            "content": "Test content",
                            "projectId": "507f1f77bcf86cd799439011"
                        }
                    ]
                }
            )

            assert response.status_code == 401


@pytest.mark.asyncio
class TestDuplicateSearch:
    """Test POST /api/v1/search/duplicates endpoint"""
    
    async def test_duplicate_search_success(self):
        """Test successful duplicate search"""
        async with get_test_client() as client:
            response = await client.post(
                "/api/v1/search/duplicates",
                headers={"Authorization": f"Bearer {TEST_API_KEY}"},
                json={
                    "content": "Test content to search for duplicates",
                    "projectId": "507f1f77bcf86cd799439011",
                    "threshold": 0.90,
                    "limit": 10
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify response structure
            assert "duplicates" in data
            assert isinstance(data["duplicates"], list)
            assert "query_embedding_time_ms" in data
            assert "search_time_ms" in data
            assert "total_time_ms" in data
    
    async def test_duplicate_search_with_filters(self):
        """Test duplicate search with type and department filters"""
        async with get_test_client() as client:
            response = await client.post(
                "/api/v1/search/duplicates",
                headers={"Authorization": f"Bearer {TEST_API_KEY}"},
                json={
                    "content": "Test content",
                    "projectId": "507f1f77bcf86cd799439011",
                    "threshold": 0.85,
                    "limit": 5,
                    "type": "GatherItem",
                    "department": "story",
                    "excludeNodeIds": ["some-node-id"]
                }
            )
            
            assert response.status_code == 200
    
    async def test_duplicate_search_invalid_threshold(self):
        """Test duplicate search with invalid threshold"""
        async with get_test_client() as client:
            response = await client.post(
                "/api/v1/search/duplicates",
                headers={"Authorization": f"Bearer {TEST_API_KEY}"},
                json={
                    "content": "Test content",
                    "projectId": "507f1f77bcf86cd799439011",
                    "threshold": 1.5  # Invalid: > 1.0
                }
            )
            
            assert response.status_code == 422


@pytest.mark.asyncio
class TestDepartmentContext:
    """Test GET /api/v1/context/department endpoint"""
    
    async def test_department_context_success(self):
        """Test successful department context retrieval"""
        async with get_test_client() as client:
            response = await client.get(
                "/api/v1/context/department",
                headers={"Authorization": f"Bearer {TEST_API_KEY}"},
                params={
                    "projectId": "507f1f77bcf86cd799439011",
                    "department": "character",
                    "previousDepartments": ["story", "visual"],
                    "limit": 20
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify response structure
            assert data["projectId"] == "507f1f77bcf86cd799439011"
            assert data["targetDepartment"] == "character"
            assert "context" in data
            assert "aggregatedSummary" in data
            assert "relevantNodes" in data
            assert "totalNodesAggregated" in data
            assert "timing" in data
    
    async def test_department_context_invalid_project_id(self):
        """Test department context with invalid projectId"""
        async with get_test_client() as client:
            response = await client.get(
                "/api/v1/context/department",
                headers={"Authorization": f"Bearer {TEST_API_KEY}"},
                params={
                    "projectId": "invalid",
                    "department": "character"
                }
            )
            
            assert response.status_code == 400


@pytest.mark.asyncio
class TestCoverageAnalysis:
    """Test POST /api/v1/analyze/coverage endpoint"""
    
    async def test_coverage_analysis_success(self):
        """Test successful coverage analysis"""
        async with get_test_client() as client:
            response = await client.post(
                "/api/v1/analyze/coverage",
                headers={"Authorization": f"Bearer {TEST_API_KEY}"},
                json={
                    "projectId": "507f1f77bcf86cd799439011",
                    "department": "story",
                    "gatherItems": [
                        {
                            "content": "Plot overview: The story follows a hero's journey",
                            "summary": "Main plot structure"
                        },
                        {
                            "content": "Character development: Protagonist grows through challenges",
                            "summary": "Character arc"
                        }
                    ],
                    "departmentDescription": "Story department handles narrative and plot"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify response structure
            assert data["department"] == "story"
            assert "coverageScore" in data
            assert 0 <= data["coverageScore"] <= 100
            assert "analysis" in data
            assert "coveredAspects" in data["analysis"]
            assert "gaps" in data["analysis"]
            assert "recommendations" in data["analysis"]
            assert "itemDistribution" in data
            assert "qualityMetrics" in data
            assert "timing" in data
    
    async def test_coverage_analysis_too_many_items(self):
        """Test coverage analysis with too many items"""
        async with get_test_client() as client:
            # Create 101 items
            items = [
                {"content": f"Content {i}", "summary": f"Summary {i}"}
                for i in range(101)
            ]
            
            response = await client.post(
                "/api/v1/analyze/coverage",
                headers={"Authorization": f"Bearer {TEST_API_KEY}"},
                json={
                    "projectId": "507f1f77bcf86cd799439011",
                    "department": "story",
                    "gatherItems": items
                }
            )
            
            assert response.status_code == 400

