"""Contract tests for WebSocket endpoints."""

import json
import pytest
import pytest_asyncio
import websockets
from websockets.exceptions import ConnectionClosed


class TestWebSocketContracts:
    """Contract tests for WebSocket API endpoints."""
    
    @pytest_asyncio.fixture
    async def websocket_client(self):
        """Create WebSocket client connection."""
        uri = "ws://localhost:8002"
        try:
            async with websockets.connect(uri) as websocket:
                yield websocket
        except ConnectionRefusedError:
            pytest.skip("WebSocket server not running")
    
    @pytest.mark.asyncio
    async def test_create_character_contract(self, websocket_client):
        """Test create_character tool contract."""
        # Arrange
        message = {
            "tool": "create_character",
            "project_id": "test_project_123",
            "name": "Gandalf",
            "personality_description": "A wise and powerful wizard, mentor to Frodo Baggins.",
            "appearance_description": "An old man with a long white beard, a pointy hat, and a staff."
        }
        
        # Act
        await websocket_client.send(json.dumps(message))
        response = await websocket_client.recv()
        response_data = json.loads(response)
        
        # Assert
        assert "status" in response_data
        assert response_data["status"] == "success"
        assert "message" in response_data
        assert "character_id" in response_data
        assert isinstance(response_data["character_id"], str)
        assert len(response_data["character_id"]) > 0
    
    @pytest.mark.asyncio
    async def test_create_character_missing_fields(self, websocket_client):
        """Test create_character with missing required fields."""
        # Arrange
        message = {
            "tool": "create_character",
            "name": "Incomplete Character"
            # Missing: project_id, personality_description, appearance_description
        }
        
        # Act
        await websocket_client.send(json.dumps(message))
        response = await websocket_client.recv()
        response_data = json.loads(response)
        
        # Assert
        assert "status" in response_data
        assert response_data["status"] == "error"
        assert "message" in response_data
    
    @pytest.mark.asyncio
    async def test_find_similar_characters_contract(self, websocket_client):
        """Test find_similar_characters tool contract."""
        # Arrange
        message = {
            "tool": "find_similar_characters",
            "project_id": "test_project_123",
            "query": "A powerful magic user"
        }
        
        # Act
        await websocket_client.send(json.dumps(message))
        response = await websocket_client.recv()
        response_data = json.loads(response)
        
        # Assert
        assert "status" in response_data
        assert response_data["status"] == "success"
        assert "results" in response_data
        assert isinstance(response_data["results"], list)
        
        # If results exist, validate structure
        if response_data["results"]:
            result = response_data["results"][0]
            assert "id" in result
            assert "name" in result
            assert "similarity_score" in result
            assert isinstance(result["similarity_score"], (int, float))
            assert 0 <= result["similarity_score"] <= 1
    
    @pytest.mark.asyncio
    async def test_find_similar_characters_missing_fields(self, websocket_client):
        """Test find_similar_characters with missing required fields."""
        # Arrange
        message = {
            "tool": "find_similar_characters",
            "query": "A powerful magic user"
            # Missing: project_id
        }
        
        # Act
        await websocket_client.send(json.dumps(message))
        response = await websocket_client.recv()
        response_data = json.loads(response)
        
        # Assert
        assert "status" in response_data
        assert response_data["status"] == "error"
        assert "message" in response_data
    
    @pytest.mark.asyncio
    async def test_invalid_tool_name(self, websocket_client):
        """Test invalid tool name handling."""
        # Arrange
        message = {
            "tool": "invalid_tool",
            "some_field": "some_value"
        }
        
        # Act
        await websocket_client.send(json.dumps(message))
        response = await websocket_client.recv()
        response_data = json.loads(response)
        
        # Assert
        assert "status" in response_data
        assert response_data["status"] == "error"
        assert "message" in response_data
    
    @pytest.mark.asyncio
    async def test_malformed_json(self, websocket_client):
        """Test malformed JSON handling."""
        # Arrange
        malformed_message = '{"tool": "create_character", "invalid": json}'
        
        # Act & Assert
        await websocket_client.send(malformed_message)
        response = await websocket_client.recv()
        response_data = json.loads(response)
        
        assert "status" in response_data
        assert response_data["status"] == "error"
        assert "message" in response_data