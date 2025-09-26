"""Integration tests for character creation user story."""

import json
import pytest
import pytest_asyncio
import websockets
from websockets.exceptions import ConnectionClosed


class TestCharacterCreationIntegration:
    """Integration tests for the character creation user story."""
    
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
    async def test_complete_character_creation_flow(self, websocket_client):
        """Test complete character creation user story."""
        # User Story: As a writer, I want to create a character 
        # with personality and appearance descriptions so that 
        # the system can generate embeddings for semantic search.
        
        # Step 1: Create a character
        create_message = {
            "tool": "create_character",
            "project_id": "integration_test_project",
            "name": "Hermione Granger",
            "personality_description": "Brilliant, logical, and extremely studious witch. Known for her intelligence, quick thinking, and dedication to her friends.",
            "appearance_description": "Young woman with bushy brown hair, brown eyes, and a confident demeanor. Often carries books and has ink-stained fingers."
        }
        
        # Send character creation request
        await websocket_client.send(json.dumps(create_message))
        response = await websocket_client.recv()
        response_data = json.loads(response)
        
        # Verify character was created successfully
        assert response_data["status"] == "success"
        assert "character_id" in response_data
        character_id = response_data["character_id"]
        
        # Step 2: Verify character is searchable immediately after creation
        search_message = {
            "tool": "find_similar_characters",
            "project_id": "integration_test_project",
            "query": "intelligent young witch who loves books"
        }
        
        await websocket_client.send(json.dumps(search_message))
        search_response = await websocket_client.recv()
        search_data = json.loads(search_response)
        
        # Verify the created character can be found
        assert search_data["status"] == "success"
        assert isinstance(search_data["results"], list)
        
        # The character should be findable
        found_character = None
        for result in search_data["results"]:
            if result["id"] == character_id:
                found_character = result
                break
        
        assert found_character is not None, "Created character should be findable in search"
        assert found_character["name"] == "Hermione Granger"
        assert isinstance(found_character["similarity_score"], (int, float))
        assert 0 <= found_character["similarity_score"] <= 1
    
    @pytest.mark.asyncio
    async def test_character_creation_with_duplicate_names(self, websocket_client):
        """Test that characters with duplicate names can be created in the same project."""
        project_id = "duplicate_names_test_project"
        
        # Create first character
        first_character = {
            "tool": "create_character",
            "project_id": project_id,
            "name": "John Smith",
            "personality_description": "A brave knight with a noble heart.",
            "appearance_description": "Tall man with blonde hair and blue eyes, wearing armor."
        }
        
        await websocket_client.send(json.dumps(first_character))
        first_response = await websocket_client.recv()
        first_data = json.loads(first_response)
        
        assert first_data["status"] == "success"
        first_id = first_data["character_id"]
        
        # Create second character with same name but different descriptions
        second_character = {
            "tool": "create_character",
            "project_id": project_id,
            "name": "John Smith",
            "personality_description": "A cunning thief with a mysterious past.",
            "appearance_description": "Short man with dark hair and green eyes, wearing a hood."
        }
        
        await websocket_client.send(json.dumps(second_character))
        second_response = await websocket_client.recv()
        second_data = json.loads(second_response)
        
        assert second_data["status"] == "success"
        second_id = second_data["character_id"]
        
        # Verify they have different IDs
        assert first_id != second_id
    
    @pytest.mark.asyncio
    async def test_character_creation_cross_project_isolation(self, websocket_client):
        """Test that characters are isolated between projects."""
        # Create character in project A
        project_a_character = {
            "tool": "create_character",
            "project_id": "project_a",
            "name": "Isolated Character A",
            "personality_description": "Character that should only exist in project A.",
            "appearance_description": "Distinctive appearance A."
        }
        
        await websocket_client.send(json.dumps(project_a_character))
        response_a = await websocket_client.recv()
        data_a = json.loads(response_a)
        
        assert data_a["status"] == "success"
        character_a_id = data_a["character_id"]
        
        # Search in project B (should not find the character)
        search_in_b = {
            "tool": "find_similar_characters",
            "project_id": "project_b",
            "query": "Isolated Character A"
        }
        
        await websocket_client.send(json.dumps(search_in_b))
        search_response = await websocket_client.recv()
        search_data = json.loads(search_response)
        
        assert search_data["status"] == "success"
        
        # Verify character A is not found in project B
        found_ids = [result["id"] for result in search_data["results"]]
        assert character_a_id not in found_ids, "Character should not be found across projects"