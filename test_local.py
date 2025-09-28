#!/usr/bin/env python3
"""
Local testing script for MCP Brain Service
"""
import asyncio
import json
import websockets
import aiohttp
from typing import Dict, Any

async def test_health_endpoint():
    """Test the HTTP health endpoint"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('http://localhost:8002/health') as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Health check: {data}")
                    return True
                else:
                    print(f"❌ Health check failed: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

async def test_websocket_connection():
    """Test WebSocket MCP connection"""
    try:
        uri = "ws://localhost:8002/"
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected")
            
            # Test character creation
            create_message = {
                "tool": "create_character",
                "project_id": "test-project",
                "name": "Test Character",
                "personality_description": "A brave and curious explorer",
                "appearance_description": "Tall with brown hair and keen eyes"
            }
            
            await websocket.send(json.dumps(create_message))
            response = await websocket.recv()
            data = json.loads(response)
            
            if data.get("status") == "success":
                print(f"✅ Character creation: {data}")
                character_id = data.get("character_id")
                
                # Test similarity search
                search_message = {
                    "tool": "find_similar_characters",
                    "project_id": "test-project", 
                    "query": "adventurous person"
                }
                
                await websocket.send(json.dumps(search_message))
                search_response = await websocket.recv()
                search_data = json.loads(search_response)
                
                if search_data.get("status") == "success":
                    print(f"✅ Similarity search: Found {len(search_data.get('characters', []))} characters")
                    return True
                else:
                    print(f"❌ Similarity search failed: {search_data}")
                    return False
            else:
                print(f"❌ Character creation failed: {data}")
                return False
                
    except Exception as e:
        print(f"❌ WebSocket test error: {e}")
        return False

async def main():
    print("🧪 Testing MCP Brain Service locally...")
    
    # Test health endpoint
    print("\n1. Testing health endpoint...")
    health_ok = await test_health_endpoint()
    
    if not health_ok:
        print("❌ Service not running. Start with: python src/main.py")
        return False
    
    # Test WebSocket functionality
    print("\n2. Testing WebSocket MCP protocol...")
    ws_ok = await test_websocket_connection()
    
    if health_ok and ws_ok:
        print("\n🎉 All tests passed! Service is working correctly.")
        return True
    else:
        print("\n❌ Some tests failed. Check the service logs.")
        return False

if __name__ == "__main__":
    asyncio.run(main())