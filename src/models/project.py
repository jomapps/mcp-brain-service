"""Project data model."""

from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, Field


class Project(BaseModel):
    """Project data model."""
    
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique identifier for the project")
    name: str = Field(..., description="The name of the project")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of when the project was created")
    
    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ProjectCreate(BaseModel):
    """Project creation model."""
    
    name: str = Field(..., description="The name of the project")


class ProjectResponse(BaseModel):
    """Project response model for API."""
    
    id: str
    name: str
    created_at: datetime
    
    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }