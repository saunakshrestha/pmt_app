
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from ninja import Schema
from datetime import datetime, date

# ---------------- Users -----------------
class UsersDetail(Schema):
    id: int
    name: str
    username: str
    email: str


# ---------------- Roles -----------------
class RoleCreateIn(Schema):
    name: str
    permission_codenames: List[str]

class RoleOut(Schema):
    id: int
    name: str
    permission_codenames: List[str]

class AssignProjectRoleIn(Schema):
    project_id: int
    user_id: int
    role_id: int

# ---------------- Project -----------------

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


# ---------------- Project Member -----------------
class ProjectMemberIn(Schema):
    project_id: int
    user_id: int
    role_id: int  # Refers to Role object

class ProjectMemberPatchIn(Schema):
    role_id: Optional[int]

class ProjectMemberOut(Schema):
    id: int
    project_id: int
    user_id: int
    role_id: int
    joined_at: datetime

# ---------------- Board -----------------
class BoardIn(Schema):
    name: str

class BoardPatchIn(Schema):
    name: Optional[str]

class BoardOut(Schema):
    id: int
    name: str
    project_id: int
    created_by: Optional[UsersDetail] = {}
    created_at: datetime

# -------------------- Sprint Schemas --------------------

class SprintIn(Schema):
    name: str
    goal: Optional[str] = ""
    start_date: date
    end_date: date
    status: str = Field(..., pattern="^(planned|active|closed)$")

class SprintPatchIn(Schema):
    name: Optional[str]
    goal: Optional[str]
    start_date: Optional[date]
    end_date: Optional[date]
    status: Optional[str] = Field(None, pattern="^(planned|active|closed)$")

class SprintOut(Schema):
    id: int
    name: str
    goal: Optional[str]
    start_date: date
    end_date: date
    status: str
    board_id: int
    created_at: datetime
    updated_at: datetime


# -------------------- Task Schemas --------------------

class TaskIn(Schema):
    title: str
    description: Optional[str] = ""
    task_type: str = Field("task", pattern="^(task|bug|story|epic|subtask)$")
    status: str = Field("todo", pattern="^(todo|in_progress|done|blocked)$")
    priority: str = Field("medium", pattern="^(low|medium|high|urgent)$")
    assignee_id: Optional[int] = None
    label_ids: Optional[List[int]] = None
    sprint_id: Optional[int] = None
    parent_id: Optional[int] = None
    story_points: Optional[int] = None
    due_date: Optional[date] = None
    start_date: Optional[date] = None
    completed_at: Optional[datetime] = None

    model_config = {
        "from_attributes": True
    }


class TaskPatchIn(Schema):
    title: Optional[str]
    description: Optional[str] = ""
    task_type: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    assignee_id: Optional[int] = None
    label_ids: Optional[List[int]] = None
    sprint_id: Optional[int] = None
    parent_id: Optional[int] = None
    story_points: Optional[int] = None
    due_date: Optional[date] = None
    start_date: Optional[date] = None
    completed_at: Optional[datetime] = None


class TaskOut(Schema):
    id: int
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = ""
    task_type: str = "task"
    status: str = "todo"
    priority: str = "medium"
    assignee_id: Optional[int]
    label_ids: Optional[List[int]] = []
    sprint_id: Optional[int] = None
    parent_id: Optional[int] = None
    story_points: Optional[int] = None
    due_date: Optional[date] = None
    start_date: Optional[date] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime  # Fixed missing type annotation


class LabelIn(Schema):
    name: str
    color: str  # e.g. "#RRGGBB"

class LabelPatchIn(Schema):
    name: Optional[str]
    color: Optional[str]  # e.g. "#RRGGBB"

class LabelOut(Schema):
    id: int
    name: str
    color: str

# -------------------- Comment Schemas --------------------
class CommentIn(Schema):
    content: str = ""
    parent_id: Optional[int] = None

class CommentPatchIn(Schema):
    content: Optional[str] = None
    parent_id: Optional[int] = None

class CommentOut(Schema):
    id: int
    content: str = ""
    user_id: int
    task_id: int
    parent_id: Optional[int] = None
    created_at: datetime
    edited_at: Optional[datetime] = None
    is_edited: bool