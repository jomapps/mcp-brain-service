"""Character data model."""

from datetime import datetime
from typing import List
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Character(BaseModel):
    """Character data model."""
    
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique identifier for the character")
    project_id: str = Field(..., description="Identifier for the project this character belongs to")
    name: str = Field(..., description="The name of the character")
    personality_description: str = Field(..., description="A textual description of the character's personality")
    appearance_description: str = Field(..., description="A textual description of the character's appearance")
    embedding_personality: List[float] = Field(default_factory=list, description="Embedding vector for the personality description")
    embedding_appearance: List[float] = Field(default_factory=list, description="Embedding vector for the appearance description")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of when the character was created")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of when the character was last updated")
    
    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CharacterCreate(BaseModel):
    """Character creation model."""
    
    project_id: str = Field(..., description="Identifier for the project this character belongs to")
    name: str = Field(..., description="The name of the character")
    personality_description: str = Field(..., description="A textual description of the character's personality")
    appearance_description: str = Field(..., description="A textual description of the character's appearance")


class CharacterResponse(BaseModel):
    """Character response model for API."""
    
    id: str
    name: str
    project_id: str
    personality_description: str
    appearance_description: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CharacterSearchResult(BaseModel):
    """Character search result model."""
    
    id: str
    name: str
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Similarity score between 0 and 1")
    
    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }