"""Database seeding script for MCP Brain Service with sample character data."""

import asyncio
import logging
import os
from typing import List

from src.lib.database import get_neo4j_connection, close_neo4j_connection
from src.lib.embeddings import get_embedding_service
from src.models.character import CharacterCreate
from src.services.character_service import CharacterService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sample character data for movie generation platform
SAMPLE_CHARACTERS = [
    {
        "project_id": "demo-project-001",
        "name": "Elena Rodriguez",
        "personality_description": "A determined and intelligent cybersecurity expert with a dry sense of humor. She's methodical in her approach to problems, often staying up late to crack complex codes. Despite her serious demeanor, she has a soft spot for rescue animals and volunteers at local shelters on weekends. She struggles with trusting others due to past betrayals but is fiercely loyal to those who earn her respect.",
        "appearance_description": "A 32-year-old Latina woman with shoulder-length curly black hair often pulled back in a messy bun. She has warm brown eyes behind black-rimmed glasses, olive skin, and stands about 5'6\". Usually dressed in comfortable hoodies and jeans with worn sneakers. Has a small scar above her left eyebrow from a childhood accident and tends to fidget with a silver bracelet when thinking."
    },
    {
        "project_id": "demo-project-001", 
        "name": "Marcus Chen",
        "personality_description": "An optimistic and charismatic street food vendor who dreams of opening his own restaurant. He's incredibly hardworking, getting up at 4 AM daily to prep ingredients. Marcus has an infectious laugh and treats every customer like family. He's secretly struggling financially to support his elderly parents but never lets it show. He believes that good food can bring people together and heal hearts.",
        "appearance_description": "A 28-year-old Asian-American man with short black hair and kind, expressive dark brown eyes. He's about 5'8\" with a lean but strong build from years of physical work. Often wears a colorful apron over simple t-shirts and jeans, with comfortable sneakers suitable for standing all day. Has flour-stained hands and a warm, genuine smile that lights up his whole face."
    },
    {
        "project_id": "demo-project-001",
        "name": "Dr. Amelia Hartwell",
        "personality_description": "A brilliant but eccentric marine biologist who is more comfortable with sea creatures than people. She speaks in rapid bursts when excited about her research and has little patience for bureaucracy or small talk. Amelia is passionate about ocean conservation and can be ruthlessly direct when advocating for environmental protection. She finds peace diving in coral reefs and has an encyclopedic knowledge of marine ecosystems.",
        "appearance_description": "A 45-year-old woman with wild, salt-and-pepper curly hair that seems to have a life of its own. She has bright green eyes that sparkle with curiosity, fair skin weathered by sun and salt water, and stands about 5'4\". Often dressed in practical field clothes - cargo pants, tank tops, and sturdy boots. Has multiple small scars on her hands from handling marine specimens and usually carries a waterproof notebook."
    },
    {
        "project_id": "demo-project-002",
        "name": "Captain Jake Morrison",
        "personality_description": "A former military pilot turned commercial airline captain who struggles with PTSD from his combat days. He's incredibly disciplined and safety-focused but battles anxiety attacks that he hides from his crew and passengers. Jake is mentoring young pilots and finds purpose in teaching the next generation. He's haunted by a mission that went wrong but channels his guilt into being the best pilot he can be.",
        "appearance_description": "A 38-year-old man with graying temples in his short brown hair and piercing blue eyes that seem to see everything. He's 6'1\" with a military bearing and broad shoulders. Always impeccably dressed in his pilot uniform or crisp civilian clothes. Has a small tattoo of wings on his wrist covered by his watch and a slight tremor in his hands that he tries to hide when stressed."
    },
    {
        "project_id": "demo-project-002",
        "name": "Luna Blackwood",
        "personality_description": "A mysterious antiquarian bookshop owner who seems to know more about ancient texts than anyone should. She's quietly observant, speaks in riddles sometimes, and has an uncanny ability to recommend exactly the right book to each customer. Luna is deeply knowledgeable about folklore and mythology, and some say she practices old traditions. She's kind but maintains an air of mystery that both attracts and intimidates people.",
        "appearance_description": "A woman of indeterminate age (could be 35 or 55) with long silver hair often braided with small trinkets and beads. She has unusual violet-gray eyes and pale skin with intricate henna-like tattoos on her hands and forearms. About 5'5\" with a willowy build, usually dressed in flowing skirts, vintage blouses, and many layered necklaces. Always smells faintly of old books and lavender."
    },
    {
        "project_id": "demo-project-002",
        "name": "Tommy Nguyen",
        "personality_description": "An 16-year-old tech prodigy who dropped out of high school to work on revolutionary AI algorithms. He's brilliant but socially awkward, more comfortable coding than talking to people his own age. Tommy is driven by a desire to create technology that helps people, particularly inspired by wanting to develop assistive tech for his deaf younger sister. He's naive about the business world but fiercely protective of his family.",
        "appearance_description": "A slight Asian-American teenager with messy black hair that falls over his eyes and thick-rimmed glasses held together with tape. About 5'7\" and thin from forgetting to eat when absorbed in coding. Usually wears oversized hoodies, worn jeans, and beat-up sneakers. Has nervous habits like bouncing his leg and adjusting his glasses when thinking. Often has energy drink stains on his clothes."
    }
]


async def seed_database():
    """Seed the database with sample character data."""
    try:
        logger.info("Starting database seeding...")
        
        # Initialize connections
        logger.info("Connecting to Neo4j database...")
        neo4j_connection = await get_neo4j_connection()
        
        logger.info("Initializing embedding service...")
        embedding_service = get_embedding_service()
        
        # Initialize character service
        character_service = CharacterService(
            neo4j_connection=neo4j_connection,
            embedding_service=embedding_service
        )
        
        # Clear existing data (optional - remove if you want to preserve existing data)
        logger.info("Clearing existing sample data...")
        await clear_sample_data(neo4j_connection)
        
        # Create sample characters
        logger.info(f"Creating {len(SAMPLE_CHARACTERS)} sample characters...")
        created_characters = []
        
        for i, char_data in enumerate(SAMPLE_CHARACTERS, 1):
            logger.info(f"Creating character {i}/{len(SAMPLE_CHARACTERS)}: {char_data['name']}")
            
            character_create = CharacterCreate(**char_data)
            character = await character_service.create_character(character_create)
            created_characters.append(character)
            
            logger.info(f"✅ Created character: {character.name} (ID: {character.id})")
        
        # Test similarity search
        logger.info("Testing similarity search...")
        await test_similarity_search(character_service)
        
        logger.info("✅ Database seeding completed successfully!")
        logger.info(f"Created {len(created_characters)} characters across {len(set(c['project_id'] for c in SAMPLE_CHARACTERS))} projects")
        
    except Exception as e:
        logger.error(f"❌ Database seeding failed: {e}")
        raise
    finally:
        # Clean up connections
        await close_neo4j_connection()


async def clear_sample_data(neo4j_connection):
    """Clear existing sample data from demo projects."""
    try:
        async with neo4j_connection.session() as session:
            # Delete characters from demo projects
            query = """
            MATCH (c:Character)
            WHERE c.project_id STARTS WITH 'demo-project'
            DELETE c
            RETURN count(c) as deleted_count
            """
            
            result = await session.run(query)
            record = await result.single()
            deleted_count = record["deleted_count"] if record else 0
            
            logger.info(f"Cleared {deleted_count} existing demo characters")
            
    except Exception as e:
        logger.warning(f"Failed to clear existing data: {e}")


async def test_similarity_search(character_service: CharacterService):
    """Test the similarity search functionality."""
    try:
        test_queries = [
            ("demo-project-001", "tech-savvy problem solver"),
            ("demo-project-002", "mysterious bookshop owner"),
            ("demo-project-001", "food enthusiast chef"),
        ]
        
        for project_id, query in test_queries:
            logger.info(f"Testing similarity search: '{query}' in {project_id}")
            results = await character_service.find_similar_characters(project_id, query, limit=3)
            
            for i, result in enumerate(results, 1):
                logger.info(f"  {i}. {result.name} (similarity: {result.similarity_score:.3f})")
                
    except Exception as e:
        logger.warning(f"Similarity search test failed: {e}")


def main():
    """Main entry point for seeding script."""
    # Ensure we have the required environment variables
    required_env_vars = ["NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD", "JINA_API_KEY"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please set these in your .env file or environment")
        return 1
    
    try:
        asyncio.run(seed_database())
        return 0
    except Exception as e:
        logger.error(f"Seeding script failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())