"""Performance tests for MCP Brain Service."""

import asyncio
import json
import statistics
import time
import pytest
import pytest_asyncio
import websockets
from typing import List


class TestPerformance:
    """Performance tests for semantic search."""
    
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
    async def test_characters(self, websocket_client) -> List[str]:
        """Create test characters for performance testing."""
        project_id = "performance_test_project"
        characters = [
            {
                "name": "Aragorn",
                "personality_description": "Noble ranger and rightful king, skilled in combat and leadership. Brave, loyal, and determined to protect his people.",
                "appearance_description": "Tall man with dark hair and weathered features, wearing ranger's clothes and carrying a sword."
            },
            {
                "name": "Gandalf",
                "personality_description": "Ancient and wise wizard, master of magic and guide to others. Patient, powerful, and deeply caring.",
                "appearance_description": "Old man with grey robes, a pointed hat, long beard, and a magical staff."
            },
            {
                "name": "Legolas",
                "personality_description": "Elven prince and master archer, graceful and deadly in battle. Proud, loyal, and connected to nature.",
                "appearance_description": "Tall elf with long blonde hair, elegant features, and carries a bow and arrows."
            },
            {
                "name": "Gimli",
                "personality_description": "Dwarven warrior with fierce loyalty and brave heart. Gruff exterior but deep friendships.",
                "appearance_description": "Short, stocky dwarf with red beard, heavy armor, and carries an axe."
            },
            {
                "name": "Frodo",
                "personality_description": "Brave hobbit with pure heart and strong will. Innocent but determined to do what's right.",
                "appearance_description": "Small hobbit with curly hair and large feet, often looks worried but determined."
            },
            {
                "name": "Boromir",
                "personality_description": "Proud warrior of Gondor, brave but tempted by power. Ultimately redeems himself through sacrifice.",
                "appearance_description": "Tall man with noble bearing, armor, and carries a shield and sword."
            },
            {
                "name": "Saruman",
                "personality_description": "Corrupted wizard seeking power and control. Intelligent but arrogant and manipulative.",
                "appearance_description": "Tall wizard in white robes (later many colors), with long hair and piercing eyes."
            },
            {
                "name": "Sauron",
                "personality_description": "Dark lord obsessed with domination and control. Pure evil, seeking to rule all of Middle-earth.",
                "appearance_description": "Appears as a great eye of fire, or as a dark armored figure with immense presence."
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
            
            if response_data["status"] == "success":
                character_ids.append(response_data["character_id"])
        
        return character_ids
    
    @pytest.mark.asyncio
    async def test_semantic_search_response_time(self, websocket_client, test_characters):
        """Test that semantic search meets p95 response time requirement (<1 minute)."""
        project_id = "performance_test_project"
        
        # Test queries with different complexities
        test_queries = [
            "brave warrior with sword",
            "wise magical wizard with ancient knowledge",
            "small creature with courage", 
            "evil dark lord seeking power",
            "noble leader and protector",
            "archer with bow and arrows",
            "corrupted wizard seeking control",
            "dwarf with axe and armor"
        ]
        
        response_times = []
        
        for query in test_queries:
            message = {
                "tool": "find_similar_characters",
                "project_id": project_id,
                "query": query
            }
            
            start_time = time.time()
            
            await websocket_client.send(json.dumps(message))
            response = await websocket_client.recv()
            
            end_time = time.time()
            response_time = end_time - start_time
            response_times.append(response_time)
            
            # Verify response is valid
            response_data = json.loads(response)
            assert response_data["status"] == "success"
            assert isinstance(response_data["results"], list)
        
        # Calculate statistics
        mean_time = statistics.mean(response_times)
        median_time = statistics.median(response_times)
        p95_time = sorted(response_times)[int(0.95 * len(response_times))]
        max_time = max(response_times)
        
        print(f"\nPerformance Results:")
        print(f"Mean response time: {mean_time:.3f}s")
        print(f"Median response time: {median_time:.3f}s") 
        print(f"P95 response time: {p95_time:.3f}s")
        print(f"Max response time: {max_time:.3f}s")
        print(f"Total queries: {len(test_queries)}")
        
        # Performance requirement: p95 response time < 1 minute (60 seconds)
        assert p95_time < 60.0, f"P95 response time {p95_time:.3f}s exceeds 60s requirement"
        
        # Additional performance checks for development
        assert mean_time < 10.0, f"Mean response time {mean_time:.3f}s is too high for development"
        assert max_time < 30.0, f"Max response time {max_time:.3f}s is too high"
    
    @pytest.mark.asyncio
    async def test_concurrent_search_performance(self, websocket_client, test_characters):
        """Test performance under concurrent load."""
        project_id = "performance_test_project"
        
        async def search_task(query_id: int) -> float:
            """Single search task."""
            uri = "ws://localhost:8002"
            try:
                async with websockets.connect(uri) as ws:
                    message = {
                        "tool": "find_similar_characters", 
                        "project_id": project_id,
                        "query": f"brave warrior number {query_id}"
                    }
                    
                    start_time = time.time()
                    
                    await ws.send(json.dumps(message))
                    response = await ws.recv()
                    
                    end_time = time.time()
                    
                    # Verify response
                    response_data = json.loads(response)
                    assert response_data["status"] == "success"
                    
                    return end_time - start_time
                    
            except Exception as e:
                print(f"Search task {query_id} failed: {e}")
                return float('inf')
        
        # Run 5 concurrent searches
        concurrent_tasks = 5
        start_time = time.time()
        
        tasks = [search_task(i) for i in range(concurrent_tasks)]
        response_times = await asyncio.gather(*tasks)
        
        total_time = time.time() - start_time
        
        # Filter out failed requests
        valid_times = [t for t in response_times if t != float('inf')]
        
        print(f"\nConcurrent Performance Results:")
        print(f"Concurrent tasks: {concurrent_tasks}")
        print(f"Successful tasks: {len(valid_times)}")
        print(f"Total time: {total_time:.3f}s")
        print(f"Mean task time: {statistics.mean(valid_times):.3f}s")
        print(f"Max task time: {max(valid_times):.3f}s")
        
        # All tasks should complete successfully
        assert len(valid_times) == concurrent_tasks, "Some concurrent tasks failed"
        
        # All concurrent tasks should complete within reasonable time
        assert total_time < 30.0, f"Concurrent tasks took too long: {total_time:.3f}s"
        assert max(valid_times) < 15.0, f"Slowest task was too slow: {max(valid_times):.3f}s"
    
    @pytest.mark.asyncio
    async def test_character_creation_performance(self, websocket_client):
        """Test character creation performance."""
        project_id = "creation_performance_test"
        
        character_data = {
            "project_id": project_id,
            "name": "Performance Test Character",
            "personality_description": "A character created for performance testing purposes. Should be quick to create and process.",
            "appearance_description": "Standard appearance for testing embedding generation and database operations."
        }
        
        creation_times = []
        
        # Create multiple characters to test consistency
        for i in range(5):
            message = {
                "tool": "create_character",
                **character_data,
                "name": f"Performance Test Character {i}"
            }
            
            start_time = time.time()
            
            await websocket_client.send(json.dumps(message))
            response = await websocket_client.recv()
            
            end_time = time.time()
            creation_time = end_time - start_time
            creation_times.append(creation_time)
            
            # Verify creation succeeded
            response_data = json.loads(response)
            assert response_data["status"] == "success"
        
        mean_creation_time = statistics.mean(creation_times)
        max_creation_time = max(creation_times)
        
        print(f"\nCharacter Creation Performance:")
        print(f"Mean creation time: {mean_creation_time:.3f}s")
        print(f"Max creation time: {max_creation_time:.3f}s")
        
        # Character creation should be fast
        assert mean_creation_time < 5.0, f"Mean creation time too slow: {mean_creation_time:.3f}s"
        assert max_creation_time < 10.0, f"Max creation time too slow: {max_creation_time:.3f}s"