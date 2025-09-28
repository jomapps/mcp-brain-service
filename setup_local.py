#!/usr/bin/env python3
"""
Local development setup script for MCP Brain Service
"""
import os
import sys
import subprocess
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a command and return success status"""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, check=True, 
                              capture_output=True, text=True)
        print(f"✅ {cmd}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {cmd}")
        print(f"Error: {e.stderr}")
        return False

def main():
    print("🚀 Setting up MCP Brain Service locally...")
    
    # Change to service directory
    service_dir = Path(__file__).parent
    os.chdir(service_dir)
    
    # Install dependencies
    print("\n📦 Installing dependencies...")
    if not run_command("pip install -r requirements.txt"):
        print("Failed to install requirements")
        return False
    
    # Install dev dependencies if available
    if Path("requirements-dev.txt").exists():
        run_command("pip install -r requirements-dev.txt")
    
    # Create .env file if it doesn't exist
    if not Path(".env").exists():
        print("\n📝 Creating .env file...")
        env_content = """# MCP Brain Service Local Development
PORT=8002
ENVIRONMENT=development
LOG_LEVEL=DEBUG

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,http://localhost:3010,ws://localhost:8002

# Neo4j Database (optional for local dev)
# NEO4J_URI=neo4j://localhost:7687
# NEO4J_USER=neo4j
# NEO4J_PASSWORD=password

# Jina AI Configuration (optional - will use mock embeddings if not set)
# JINA_API_KEY=your_jina_api_key_here
# JINA_MODEL_NAME=jina-embeddings-v3
"""
        with open(".env", "w") as f:
            f.write(env_content)
        print("✅ Created .env file")
    
    # Test imports
    print("\n🔍 Testing imports...")
    test_imports = [
        "import src.main",
        "from src.lib.embeddings import JinaEmbeddingService",
        "from src.services.character_service import CharacterService",
    ]
    
    for import_test in test_imports:
        try:
            exec(import_test)
            print(f"✅ {import_test}")
        except Exception as e:
            print(f"❌ {import_test} - {e}")
            return False
    
    print("\n🎉 Setup complete! Run the service with:")
    print("python src/main.py")
    print("\nOr with auto-reload:")
    print("uvicorn src.main:app --host 0.0.0.0 --port 8002 --reload")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)