"""Integration tests for semantic search user story."""

import json
import pytest
import pytest_asyncio
import websockets
from websockets.exceptions import ConnectionClosed


class TestSemanticSearchIntegration:
    """Integration tests for the semantic search user story."""
    
    @pytest_asyncio.fixture
    async def websocket_client(self):
        """Create WebSocket client connection."""
        uri = "ws://localhost:8002"
        try:
            async with websockets.connect(uri) as websocket:
                yield websocket
        except ConnectionRefusedError:
            pytest.skip("WebSocket server not running")
    
    @pytest_asyncio.fixture
    async def populated_project(self, websocket_client):
        """Create a project with multiple characters for testing semantic search."""
        project_id = "semantic_search_test_project"
        characters = [
            {
                "name": "Merlin",
                "personality_description": "Ancient and wise wizard, master of magic and advisor to kings.",
                "appearance_description": "Elderly man with a long white beard, flowing robes, and piercing blue eyes."
            },
            {
                "name": "Gandalf",
                "personality_description": "Wise and powerful wizard, guide and protector of hobbits.",
                "appearance_description": "Old man with grey robes, a pointed hat, and a magical staff."
            },
            {
                "name": "Conan",
                "personality_description": "Fierce barbarian warrior with incredible strength and courage.",
                "appearance_description": "Muscular man with black hair, wielding a massive sword."
            },
            {
                "name": "Hermione",
                "personality_description": "Brilliant young witch, studious and logical problem-solver.",
                "appearance_description": "Young woman with bushy brown hair and bright eyes."
            },
            {
                "name": "Aragorn",
                "personality_description": "Noble ranger and rightful king, skilled in combat and leadership.",
                "appearance_description": "Tall man with dark hair, wearing ranger's clothes and carrying a sword."
            }
        ]
        
        character_ids = []
        for character in characters:
            message = {
                "tool": "create_character",
                "project_id": project_id,
                **character
            }
            await websocket_client.send(json.dumps(message))
            response = await websocket_client.recv()
            response_data = json.loads(response)
            assert response_data["status"] == "success"
            character_ids.append(response_data["character_id"])
        
        return {"project_id": project_id, "character_ids": character_ids}
    
    @pytest.mark.asyncio
    async def test_semantic_search_for_wizards(self, websocket_client, populated_project):
        """Test semantic search can find wizard-like characters."""
        # User Story: As a writer, I want to search for characters 
        # using natural language queries so that I can find 
        # similar characters based on their personality and appearance.
        
        search_message = {
            "tool": "find_similar_characters",
            "project_id": populated_project["project_id"],
            "query": "wise magical wizard with knowledge of ancient arts"
        }
        
        await websocket_client.send(json.dumps(search_message))
        response = await websocket_client.recv()
        response_data = json.loads(response)
        
        assert response_data["status"] == "success"
        assert isinstance(response_data["results"], list)
        assert len(response_data["results"]) > 0
        
        # Should find wizard-like characters (Merlin, Gandalf, possibly Hermione)
        found_names = [result["name"] for result in response_data["results"]]
        assert "Merlin" in found_names or "Gandalf" in found_names
        
        # Verify similarity scores are valid
        for result in response_data["results"]:
            assert 0 <= result["similarity_score"] <= 1
            assert isinstance(result["similarity_score"], (int, float))
    
    @pytest.mark.asyncio
    async def test_semantic_search_for_warriors(self, websocket_client, populated_project):
        """Test semantic search can find warrior-like characters."""
        search_message = {
            "tool": "find_similar_characters",
            "project_id": populated_project["project_id"],
            "query": "strong fighter with sword and combat skills"
        }
        
        await websocket_client.send(json.dumps(search_message))
        response = await websocket_client.recv()
        response_data = json.loads(response)
        
        assert response_data["status"] == "success"
        assert isinstance(response_data["results"], list)
        
        # Should find warrior-like characters (Conan, Aragorn)
        if response_data["results"]:
            found_names = [result["name"] for result in response_data["results"]]
            # At least one warrior should be found
            warrior_names = {"Conan", "Aragorn"}
            assert any(name in found_names for name in warrior_names)
    
    @pytest.mark.asyncio
    async def test_semantic_search_appearance_based(self, websocket_client, populated_project):
        """Test semantic search based on appearance descriptions."""
        search_message = {
            "tool": "find_similar_characters",
            "project_id": populated_project["project_id"],
            "query": "person with long white beard and robes"
        }
        
        await websocket_client.send(json.dumps(search_message))
        response = await websocket_client.recv()
        response_data = json.loads(response)
        
        assert response_data["status"] == "success"
        assert isinstance(response_data["results"], list)
        
        # Should find characters matching the appearance (Merlin should be top result)
        if response_data["results"]:
            found_names = [result["name"] for result in response_data["results"]]
            # Merlin has "long white beard" and "flowing robes"
            assert "Merlin" in found_names
    
    @pytest.mark.asyncio
    async def test_semantic_search_ranking_by_relevance(self, websocket_client, populated_project):
        """Test that search results are ranked by similarity score."""
        search_message = {
            "tool": "find_similar_characters",
            "project_id": populated_project["project_id"],
            "query": "ancient wise wizard with magical powers"
        }
        
        await websocket_client.send(json.dumps(search_message))
        response = await websocket_client.recv()
        response_data = json.loads(response)
        
        assert response_data["status"] == "success"
        assert isinstance(response_data["results"], list)
        
        if len(response_data["results"]) > 1:
            # Results should be sorted by similarity score (highest first)
            scores = [result["similarity_score"] for result in response_data["results"]]
            assert scores == sorted(scores, reverse=True), "Results should be sorted by similarity score"
    
    @pytest.mark.asyncio
    async def test_semantic_search_empty_query(self, websocket_client, populated_project):
        """Test semantic search with empty query."""
        search_message = {
            "tool": "find_similar_characters",
            "project_id": populated_project["project_id"],
            "query": ""
        }
        
        await websocket_client.send(json.dumps(search_message))
        response = await websocket_client.recv()
        response_data = json.loads(response)
        
        # Should handle empty query gracefully
        assert response_data["status"] in ["success", "error"]
        if response_data["status"] == "success":
            assert isinstance(response_data["results"], list)
    
    @pytest.mark.asyncio
    async def test_semantic_search_nonexistent_project(self, websocket_client):
        """Test semantic search in a project that doesn't exist."""
        search_message = {
            "tool": "find_similar_characters",
            "project_id": "nonexistent_project_id",
            "query": "any character"
        }
        
        await websocket_client.send(json.dumps(search_message))
        response = await websocket_client.recv()
        response_data = json.loads(response)
        
        # Should return success with empty results
        assert response_data["status"] == "success"
        assert isinstance(response_data["results"], list)
        assert len(response_data["results"]) == 0
    
    @pytest.mark.asyncio
    async def test_semantic_search_performance(self, websocket_client, populated_project):
        """Test that semantic search meets performance requirements (p95 < 1 minute)."""
        import time
        
        search_message = {
            "tool": "find_similar_characters",
            "project_id": populated_project["project_id"],
            "query": "character with magical abilities and wisdom"
        }
        
        start_time = time.time()
        await websocket_client.send(json.dumps(search_message))
        response = await websocket_client.recv()
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # Performance requirement: p95 response time < 1 minute (60 seconds)
        assert response_time < 60.0, f"Search took {response_time:.2f}s, should be < 60s"
        
        response_data = json.loads(response)
        assert response_data["status"] == "success"