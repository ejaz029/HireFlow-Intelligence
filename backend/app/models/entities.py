from datetime import datetime, date
from sqlalchemy import String, Integer, Float, Boolean, Date, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class Department(Base):
    __tablename__ = "departments"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)

class JobRequisition(Base):
    __tablename__ = "job_requisitions"
    id: Mapped[int] = mapped_column(primary_key=True)
    requisition_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"))
    title: Mapped[str] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(20), default="approved")
    salary_min: Mapped[float] = mapped_column(Float)
    salary_max: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    department = relationship("Department")
    required_skills = relationship("RequisitionSkill", cascade="all, delete-orphan")

class Candidate(Base):
    __tablename__ = "candidates"
    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[str] = mapped_column(String(24), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(160), unique=True)
    location: Mapped[str] = mapped_column(String(80))
    years_experience: Mapped[float] = mapped_column(Float, default=0)

class Skill(Base):
    __tablename__ = "skills"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(60), unique=True)

class RequisitionSkill(Base):
    __tablename__ = "requisition_skills"
    id: Mapped[int] = mapped_column(primary_key=True)
    requisition_id: Mapped[int] = mapped_column(ForeignKey("job_requisitions.id"))
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"))
    required_level: Mapped[int] = mapped_column(Integer, default=1)
    __table_args__ = (UniqueConstraint("requisition_id", "skill_id"),)

class CandidateSkill(Base):
    __tablename__ = "candidate_skills"
    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id"))
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"))
    proficiency: Mapped[int] = mapped_column(Integer, default=1)
    __table_args__ = (UniqueConstraint("candidate_id", "skill_id"),)

class ResumeArtifact(Base):
    __tablename__ = "resume_artifacts"
    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id"), unique=True)
    file_name: Mapped[str] = mapped_column(String(160))
    file_type: Mapped[str] = mapped_column(String(20), default="pdf")
    content_hash: Mapped[str] = mapped_column(String(64))
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class ScreeningRule(Base):
    __tablename__ = "screening_rules"
    id: Mapped[int] = mapped_column(primary_key=True)
    requisition_id: Mapped[int] = mapped_column(ForeignKey("job_requisitions.id"))
    minimum_score: Mapped[float] = mapped_column(Float, default=60)
    skills_weight: Mapped[float] = mapped_column(Float, default=0.8)
    experience_weight: Mapped[float] = mapped_column(Float, default=0.2)

class Application(Base):
    __tablename__ = "applications"
    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    requisition_id: Mapped[int] = mapped_column(ForeignKey("job_requisitions.id"))
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id"))
    stage: Mapped[str] = mapped_column(String(30), default="applied")
    status: Mapped[str] = mapped_column(String(20), default="active")
    screening_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    applied_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("requisition_id", "candidate_id", name="uq_application_candidate_role"),)
    candidate = relationship("Candidate")
    requisition = relationship("JobRequisition")

class Interviewer(Base):
    __tablename__ = "interviewers"
    id: Mapped[int] = mapped_column(primary_key=True)
    interviewer_id: Mapped[str] = mapped_column(String(24), unique=True)
    full_name: Mapped[str] = mapped_column(String(120))
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"))

class InterviewerAvailability(Base):
    __tablename__ = "interviewer_availability"
    id: Mapped[int] = mapped_column(primary_key=True)
    interviewer_id: Mapped[int] = mapped_column(ForeignKey("interviewers.id"))
    starts_at: Mapped[datetime] = mapped_column(DateTime)
    ends_at: Mapped[datetime] = mapped_column(DateTime)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    __table_args__ = (UniqueConstraint("interviewer_id", "starts_at"),)

class Interview(Base):
    __tablename__ = "interviews"
    id: Mapped[int] = mapped_column(primary_key=True)
    interview_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id"))
    interviewer_id: Mapped[int] = mapped_column(ForeignKey("interviewers.id"))
    round_name: Mapped[str] = mapped_column(String(40))
    scheduled_at: Mapped[datetime] = mapped_column(DateTime)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=60)
    status: Mapped[str] = mapped_column(String(20), default="scheduled")
    interviewer_available: Mapped[bool] = mapped_column(Boolean, default=True)

class Feedback(Base):
    __tablename__ = "feedback"
    id: Mapped[int] = mapped_column(primary_key=True)
    feedback_id: Mapped[str] = mapped_column(String(80), unique=True)
    interview_id: Mapped[int] = mapped_column(ForeignKey("interviews.id"))
    interviewer_id: Mapped[int] = mapped_column(ForeignKey("interviewers.id"))
    technical_score: Mapped[float] = mapped_column(Float)
    communication_score: Mapped[float] = mapped_column(Float)
    recommendation: Mapped[str] = mapped_column(String(20))
    comments: Mapped[str] = mapped_column(Text, default="")

class Offer(Base):
    __tablename__ = "offers"
    id: Mapped[int] = mapped_column(primary_key=True)
    offer_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id"), unique=True)
    salary: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    approved_by: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class WorkflowEvent(Base):
    __tablename__ = "workflow_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(40), index=True)
    entity_id: Mapped[str] = mapped_column(String(100), index=True)
    from_state: Mapped[str | None] = mapped_column(String(40), nullable=True)
    to_state: Mapped[str] = mapped_column(String(40))
    actor: Mapped[str] = mapped_column(String(120), default="system")
    reason: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Issue(Base):
    __tablename__ = "issues"
    id: Mapped[int] = mapped_column(primary_key=True)
    issue_type: Mapped[str] = mapped_column(String(60), index=True)
    entity_type: Mapped[str] = mapped_column(String(40))
    entity_id: Mapped[str] = mapped_column(String(100))
    severity: Mapped[str] = mapped_column(String(20), default="high")
    description: Mapped[str] = mapped_column(Text)
    ground_truth: Mapped[str] = mapped_column(String(40), default="anomaly")
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    resolved_by: Mapped[str | None] = mapped_column(String(120), nullable=True)
    resolution_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class GroundTruthLabel(Base):
    __tablename__ = "ground_truth_labels"
    id: Mapped[int] = mapped_column(primary_key=True)
    issue_type: Mapped[str] = mapped_column(String(60), index=True)
    entity_type: Mapped[str] = mapped_column(String(40))
    entity_id: Mapped[str] = mapped_column(String(100), index=True)
    ground_truth: Mapped[str] = mapped_column(String(60))
    expected_action: Mapped[str] = mapped_column(String(120))
    __table_args__ = (UniqueConstraint("issue_type", "entity_type", "entity_id", name="uq_ground_truth_label"),)
