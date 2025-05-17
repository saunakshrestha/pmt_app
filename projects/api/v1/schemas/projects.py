
from pydantic import BaseModel, Field, field_validator
from typing import Optional

class ProjectIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None

class ProjectPatchIn(BaseModel):
    name: Optional[str] = Field(None, description="Project name")
    description: Optional[str] = Field(None, description="Project description")

class ProjectOut(ProjectIn):
    id: int
    class Config:
        from_attributes = True

class ResourceIn(BaseModel):
    code: str
    name: str
    description: Optional[str] = None

class ResourceOut(ResourceIn):
    id: int
    class Config:
        from_attributes = True

class RoleIn(BaseModel):
    tenant_id: Optional[int] = None
    name: str
    description: Optional[str] = None

class RoleOut(RoleIn):
    id: int
    class Config:
        from_attributes = True

# Continue defining RolePermissionIn/Out, ProjectIn/Out, etc., for other models
