from pydantic import BaseModel, ConfigDict, Field

class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

class StageUpdate(BaseModel):
    stage: str = Field(pattern="^(applied|screening|interview|offer|hired|rejected|withdrawn)$")
    actor: str = "recruiter"
    reason: str = ""

class OfferCreate(BaseModel):
    application_id: int
    salary: float = Field(gt=0)
    approved_by: str | None = None

class IssueOut(ORMModel):
    id: int
    issue_type: str
    entity_type: str
    entity_id: str
    severity: str
    description: str
    resolved: bool

from datetime import datetime
from pydantic import Field

class RequisitionCreate(BaseModel):
    title: str = Field(min_length=2, max_length=120)
    department_id: int
    salary_min: float = Field(gt=0)
    salary_max: float = Field(gt=0)
    required_skill_ids: list[int] = []

class InterviewCreate(BaseModel):
    application_id: int
    interviewer_id: int
    round_name: str = Field(min_length=2, max_length=40)
    scheduled_at: datetime
    duration_minutes: int = Field(default=60, ge=15, le=240)

class FeedbackCreate(BaseModel):
    interview_id: int
    interviewer_id: int
    technical_score: float = Field(ge=1, le=5)
    communication_score: float = Field(ge=1, le=5)
    recommendation: str = Field(pattern="^(strong_yes|yes|no|strong_no)$")
    comments: str = ""

class OfferDecision(BaseModel):
    status: str = Field(pattern="^(accepted|rejected|withdrawn)$")
    actor: str
    reason: str = ""

class ApplicationCreate(BaseModel):
    requisition_id: int
    candidate_id: int


class IssueResolve(BaseModel):
    actor: str
    resolution_note: str = Field(min_length=3, max_length=1000)
