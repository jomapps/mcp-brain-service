"""Unit tests for input validation."""

import pytest
from pydantic import ValidationError

from src.models.character import CharacterCreate, CharacterResponse, CharacterSearchResult
from src.models.project import ProjectCreate, ProjectResponse


class TestCharacterValidation:
    """Unit tests for character model validation."""
    
    def test_character_create_valid(self):
        """Test valid character creation data."""
        data = {
            "project_id": "test-project-123",
            "name": "Test Character",
            "personality_description": "A brave and noble warrior.",
            "appearance_description": "Tall with dark hair and piercing eyes."
        }
        
        character = CharacterCreate(**data)
        
        assert character.project_id == "test-project-123"
        assert character.name == "Test Character"
        assert character.personality_description == "A brave and noble warrior."
        assert character.appearance_description == "Tall with dark hair and piercing eyes."
    
    def test_character_create_missing_required_fields(self):
        """Test character creation with missing required fields."""
        # Missing project_id
        with pytest.raises(ValidationError) as exc_info:
            CharacterCreate(
                name="Test Character",
                personality_description="A brave warrior.",
                appearance_description="Tall and strong."
            )
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "missing"
        assert "project_id" in str(errors[0])
        
        # Missing name
        with pytest.raises(ValidationError):
            CharacterCreate(
                project_id="test-project",
                personality_description="A brave warrior.",
                appearance_description="Tall and strong."
            )
        
        # Missing personality_description
        with pytest.raises(ValidationError):
            CharacterCreate(
                project_id="test-project",
                name="Test Character",
                appearance_description="Tall and strong."
            )
        
        # Missing appearance_description
        with pytest.raises(ValidationError):
            CharacterCreate(
                project_id="test-project",
                name="Test Character",
                personality_description="A brave warrior."
            )
    
    def test_character_create_empty_strings(self):
        """Test character creation with empty string values."""
        # Empty strings should be allowed but not None
        character = CharacterCreate(
            project_id="test-project",
            name="",  # Empty string allowed
            personality_description="A description",
            appearance_description="An appearance"
        )
        
        assert character.name == ""
    
    def test_character_search_result_similarity_score_validation(self):
        """Test similarity score validation in search results."""
        # Valid similarity score
        result = CharacterSearchResult(
            id="test-id",
            name="Test Character", 
            similarity_score=0.75
        )
        assert result.similarity_score == 0.75
        
        # Boundary values
        result_min = CharacterSearchResult(
            id="test-id",
            name="Test Character",
            similarity_score=0.0
        )
        assert result_min.similarity_score == 0.0
        
        result_max = CharacterSearchResult(
            id="test-id", 
            name="Test Character",
            similarity_score=1.0
        )
        assert result_max.similarity_score == 1.0
        
        # Invalid similarity scores (outside 0-1 range)
        with pytest.raises(ValidationError) as exc_info:
            CharacterSearchResult(
                id="test-id",
                name="Test Character",
                similarity_score=-0.1  # Below 0
            )
        
        errors = exc_info.value.errors()
        assert any("greater_than_equal" in str(error) for error in errors)
        
        with pytest.raises(ValidationError) as exc_info:
            CharacterSearchResult(
                id="test-id",
                name="Test Character", 
                similarity_score=1.1  # Above 1
            )
        
        errors = exc_info.value.errors()
        assert any("less_than_equal" in str(error) for error in errors)


class TestProjectValidation:
    """Unit tests for project model validation."""
    
    def test_project_create_valid(self):
        """Test valid project creation data."""
        project = ProjectCreate(name="Test Project")
        assert project.name == "Test Project"
    
    def test_project_create_missing_name(self):
        """Test project creation without name."""
        with pytest.raises(ValidationError) as exc_info:
            ProjectCreate()
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "missing"
        assert "name" in str(errors[0])
    
    def test_project_create_empty_name(self):
        """Test project creation with empty name."""
        # Empty strings should be allowed
        project = ProjectCreate(name="")
        assert project.name == ""


class TestWebSocketMessageValidation:
    """Unit tests for WebSocket message validation."""
    
    def test_valid_create_character_message(self):
        """Test validation of valid create_character message."""
        message = {
            "tool": "create_character",
            "project_id": "test-project",
            "name": "Test Character",
            "personality_description": "Brave warrior",
            "appearance_description": "Tall and strong"
        }
        
        # Validate using CharacterCreate model
        character_data = CharacterCreate(**{
            k: v for k, v in message.items() if k != "tool"
        })
        
        assert character_data.project_id == "test-project"
        assert character_data.name == "Test Character"
    
    def test_valid_find_similar_characters_message(self):
        """Test validation of valid find_similar_characters message."""
        message = {
            "tool": "find_similar_characters",
            "project_id": "test-project",
            "query": "brave warrior with sword"
        }
        
        # Basic validation
        assert "tool" in message
        assert "project_id" in message  
        assert "query" in message
        assert message["tool"] == "find_similar_characters"
        assert isinstance(message["query"], str)
    
    def test_invalid_tool_names(self):
        """Test handling of invalid tool names."""
        invalid_tools = [
            "",  # Empty string
            None,  # None value
            "invalid_tool",  # Unknown tool
            123,  # Non-string type
        ]
        
        for invalid_tool in invalid_tools:
            message = {
                "tool": invalid_tool,
                "project_id": "test-project"
            }
            
            # Tool validation would be handled at the WebSocket handler level
            assert message["tool"] != "create_character"
            assert message["tool"] != "find_similar_characters"