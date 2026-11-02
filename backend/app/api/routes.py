from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.models.entities import Application, Candidate, JobRequisition, Interview, Offer, Issue, GroundTruthLabel, WorkflowEvent, Department, RequisitionSkill, Skill, Interviewer, InterviewerAvailability, Feedback
from app.schemas.common import StageUpdate, OfferCreate, IssueOut, RequisitionCreate, InterviewCreate, FeedbackCreate, OfferDecision, ApplicationCreate, IssueResolve
from app.services.screening import score_application
from app.services.workflow import transition_application
from app.services.anomaly_detection import detect_issues

router = APIRouter(prefix="/api")

@router.get("/health")
def health(): return {"status": "ok", "service": "hireflow-intelligence"}

@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    stages = dict(db.query(Application.stage, func.count(Application.id)).group_by(Application.stage).all())
    total_interviews = db.query(Interview).count()
    interviews_with_feedback = db.query(Feedback.interview_id).distinct().count()
    scored = db.query(Application).filter(Application.screening_score.is_not(None)).all()
    pass_rate = round(sum(1 for item in scored if item.screening_score >= 60) / len(scored) * 100, 2) if scored else 0
    return {"requisitions": db.query(JobRequisition).filter(JobRequisition.status.in_(["approved", "open"])).count(), "total_requisitions": db.query(JobRequisition).count(), "candidates": db.query(Candidate).count(), "applications": db.query(Application).count(), "interviews": total_interviews, "offers": db.query(Offer).count(), "open_issues": db.query(Issue).filter_by(resolved=False).count(), "stage_distribution": stages, "offer_acceptance_rate": _offer_rate(db), "screening_pass_rate": pass_rate, "feedback_completeness_rate": round(interviews_with_feedback / total_interviews * 100, 2) if total_interviews else 0, "interviewer_availability_rate": round(db.query(Interview).filter_by(interviewer_available=True).count() / total_interviews * 100, 2) if total_interviews else 0}

def _offer_rate(db):
    total = db.query(Offer).count()
    accepted = db.query(Offer).filter_by(status="accepted").count()
    return round(accepted/total*100, 2) if total else 0


@router.get("/departments")
def departments(db: Session = Depends(get_db)):
    return [{"id": x.id, "code": x.code, "name": x.name} for x in db.query(Department).all()]

@router.get("/skills")
def skills(db: Session = Depends(get_db)):
    return [{"id": x.id, "name": x.name} for x in db.query(Skill).all()]

@router.get("/candidates")
def candidates(db: Session = Depends(get_db)):
    return [{"id": x.id, "candidate_id": x.candidate_id, "full_name": x.full_name, "years_experience": x.years_experience} for x in db.query(Candidate).limit(1000).all()]

@router.get("/requisitions")
def requisitions(db: Session = Depends(get_db)):
    return [{"id": r.id, "requisition_id": r.requisition_id, "title": r.title, "status": r.status, "salary_min": r.salary_min, "salary_max": r.salary_max, "department": r.department.name} for r in db.query(JobRequisition).all()]


@router.post("/requisitions")
def create_requisition(payload: RequisitionCreate, db: Session = Depends(get_db)):
    if payload.salary_max < payload.salary_min: raise HTTPException(422, "salary_max must be greater than or equal to salary_min")
    department = db.get(Department, payload.department_id)
    if not department: raise HTTPException(404, "Department not found")
    req = JobRequisition(requisition_id=f"REQ-2026-{db.query(JobRequisition).count()+1:06d}", department_id=department.id, title=payload.title, status="pending_approval", salary_min=payload.salary_min, salary_max=payload.salary_max)
    db.add(req); db.flush()
    for skill_id in payload.required_skill_ids:
        if not db.get(Skill, skill_id): raise HTTPException(404, f"Skill {skill_id} not found")
        db.add(RequisitionSkill(requisition_id=req.id, skill_id=skill_id, required_level=2))
    db.add(WorkflowEvent(entity_type="requisition", entity_id=req.requisition_id, from_state=None, to_state="pending_approval", actor="requester", reason="New requisition submitted"))
    db.commit(); db.refresh(req)
    return {"requisition_id": req.requisition_id, "status": req.status}

@router.post("/requisitions/{requisition_pk}/approve")
def approve_requisition(requisition_pk: int, actor: str = "approver", db: Session = Depends(get_db)):
    req = db.get(JobRequisition, requisition_pk)
    if not req: raise HTTPException(404, "Requisition not found")
    if req.status != "pending_approval": raise HTTPException(409, "Only pending requisitions can be approved")
    req.status = "approved"
    db.add(WorkflowEvent(entity_type="requisition", entity_id=req.requisition_id, from_state="pending_approval", to_state="approved", actor=actor, reason="Requisition approved"))
    db.commit()
    return {"requisition_id": req.requisition_id, "status": req.status}

@router.get("/interviewers")
def interviewers(db: Session = Depends(get_db)):
    return [{"id": x.id, "interviewer_id": x.interviewer_id, "full_name": x.full_name} for x in db.query(Interviewer).all()]

@router.get("/interviews")
def interviews(db: Session = Depends(get_db)):
    return [{"id": x.id, "interview_id": x.interview_id, "application_id": x.application_id, "interviewer_id": x.interviewer_id, "round_name": x.round_name, "scheduled_at": x.scheduled_at, "status": x.status, "interviewer_available": x.interviewer_available} for x in db.query(Interview).order_by(Interview.scheduled_at.desc()).limit(1000).all()]

@router.post("/interviews")
def schedule_interview(payload: InterviewCreate, db: Session = Depends(get_db)):
    app = db.get(Application, payload.application_id)
    interviewer = db.get(Interviewer, payload.interviewer_id)
    if not app or not interviewer: raise HTTPException(404, "Application or interviewer not found")
    if app.stage not in ["screening", "interview"]: raise HTTPException(409, "Application is not eligible for interview scheduling")
    from datetime import timedelta
    start, end = payload.scheduled_at, payload.scheduled_at + timedelta(minutes=payload.duration_minutes)
    slots = db.query(InterviewerAvailability).filter(InterviewerAvailability.interviewer_id == interviewer.id, InterviewerAvailability.starts_at <= start, InterviewerAvailability.ends_at >= end, InterviewerAvailability.is_available.is_(True)).all()
    if not slots: raise HTTPException(409, "Interviewer has no available slot for the requested time")
    existing = db.query(Interview).filter(Interview.interviewer_id == interviewer.id, Interview.status == "scheduled").all()
    for item in existing:
        other_end = item.scheduled_at + timedelta(minutes=item.duration_minutes)
        if start < other_end and item.scheduled_at < end:
            raise HTTPException(409, f"Interviewer conflict with {item.interview_id}")
    iid = f"INT-2026-{db.query(Interview).count()+1:06d}"
    interview = Interview(interview_id=iid, application_id=app.id, interviewer_id=interviewer.id, round_name=payload.round_name, scheduled_at=start, duration_minutes=payload.duration_minutes, status="scheduled", interviewer_available=True)
    db.add(interview)
    db.add(WorkflowEvent(entity_type="interview", entity_id=iid, from_state=None, to_state="scheduled", actor="recruiter", reason="Interview scheduled after conflict check"))
    if app.stage == "screening":
        app.stage = "interview"
        db.add(WorkflowEvent(entity_type="application", entity_id=app.application_id, from_state="screening", to_state="interview", actor="recruiter", reason="Advanced after interview scheduling"))
    db.commit(); db.refresh(interview)
    return {"interview_id": iid, "status": interview.status}


@router.get("/feedback")
def feedback_records(db: Session = Depends(get_db)):
    return [{"id": x.id, "feedback_id": x.feedback_id, "interview_id": x.interview_id, "interviewer_id": x.interviewer_id, "technical_score": x.technical_score, "communication_score": x.communication_score, "recommendation": x.recommendation, "comments": x.comments} for x in db.query(Feedback).all()]

@router.post("/feedback")
def submit_feedback(payload: FeedbackCreate, db: Session = Depends(get_db)):
    interview = db.get(Interview, payload.interview_id)
    interviewer = db.get(Interviewer, payload.interviewer_id)
    if not interview or not interviewer: raise HTTPException(404, "Interview or interviewer not found")
    if interview.interviewer_id != interviewer.id: raise HTTPException(422, "Feedback interviewer must be assigned to this interview")
    if db.query(Feedback).filter_by(interview_id=interview.id, interviewer_id=interviewer.id).first(): raise HTTPException(409, "Feedback already exists for this interviewer and interview")
    feedback_id = f"FB-{interview.interview_id}-{interviewer.interviewer_id}"
    item = Feedback(feedback_id=feedback_id, interview_id=interview.id, interviewer_id=interviewer.id, technical_score=payload.technical_score, communication_score=payload.communication_score, recommendation=payload.recommendation, comments=payload.comments)
    db.add(item)
    db.add(WorkflowEvent(entity_type="feedback", entity_id=feedback_id, from_state=None, to_state="submitted", actor=interviewer.full_name, reason="Structured interview feedback submitted"))
    db.commit(); db.refresh(item)
    return {"feedback_id": feedback_id, "recommendation": item.recommendation}

@router.get("/offers")
def offers(db: Session = Depends(get_db)):
    return [{"id": x.id, "offer_id": x.offer_id, "application_id": x.application_id, "salary": x.salary, "status": x.status, "approved_by": x.approved_by} for x in db.query(Offer).all()]

@router.post("/offers/{offer_pk}/decision")
def decide_offer(offer_pk: int, payload: OfferDecision, db: Session = Depends(get_db)):
    offer = db.get(Offer, offer_pk)
    if not offer: raise HTTPException(404, "Offer not found")
    if offer.status != "pending": raise HTTPException(409, "Only pending offers can receive a decision")
    previous = offer.status; offer.status = payload.status
    db.add(WorkflowEvent(entity_type="offer", entity_id=offer.offer_id, from_state=previous, to_state=payload.status, actor=payload.actor, reason=payload.reason))
    application = db.get(Application, offer.application_id)
    next_stage = {"accepted": "hired", "rejected": "rejected", "withdrawn": "withdrawn"}[payload.status]
    previous_stage = application.stage
    if next_stage not in {"hired", "rejected", "withdrawn"}: raise HTTPException(409, "Invalid application outcome")
    application.stage = next_stage
    db.add(WorkflowEvent(entity_type="application", entity_id=application.application_id, from_state=previous_stage, to_state=next_stage, actor=payload.actor, reason=f"Offer decision: {payload.status}. {payload.reason}"))
    db.commit()
    return {"offer_id": offer.offer_id, "status": offer.status}


@router.post("/applications")
def create_application(payload: ApplicationCreate, db: Session = Depends(get_db)):
    req = db.get(JobRequisition, payload.requisition_id)
    candidate = db.get(Candidate, payload.candidate_id)
    if not req or not candidate: raise HTTPException(404, "Requisition or candidate not found")
    if req.status not in ["approved", "open"]: raise HTTPException(409, "Applications are not accepted for this requisition")
    existing = db.query(Application).filter_by(requisition_id=req.id, candidate_id=candidate.id).first()
    if existing: raise HTTPException(409, "Candidate has already applied to this requisition")
    application_id = f"APP-{req.requisition_id}-{candidate.candidate_id}"
    app = Application(application_id=application_id, requisition_id=req.id, candidate_id=candidate.id, stage="applied", status="active")
    db.add(app)
    db.add(WorkflowEvent(entity_type="application", entity_id=application_id, from_state=None, to_state="applied", actor="candidate", reason="Application submitted"))
    db.commit(); db.refresh(app)
    return {"application_id": app.application_id, "stage": app.stage}

@router.get("/interviewer-availability")
def interviewer_availability(db: Session = Depends(get_db)):
    return [{"id": x.id, "interviewer_id": x.interviewer_id, "starts_at": x.starts_at, "ends_at": x.ends_at, "is_available": x.is_available} for x in db.query(InterviewerAvailability).join(Interviewer, Interviewer.id == InterviewerAvailability.interviewer_id).all()]

@router.get("/applications")
def applications(stage: str | None = None, db: Session = Depends(get_db)):
    q = db.query(Application)
    if stage: q = q.filter_by(stage=stage)
    return [{"id": a.id, "application_id": a.application_id, "candidate": a.candidate.full_name, "candidate_id": a.candidate.candidate_id, "requisition": a.requisition.title, "stage": a.stage, "status": a.status, "screening_score": a.screening_score} for a in q.limit(500).all()]

@router.post("/applications/{application_pk}/screen")
def screen(application_pk: int, db: Session = Depends(get_db)):
    app = db.get(Application, application_pk)
    if not app: raise HTTPException(404, "Application not found")
    result = score_application(db, app)
    db.commit()
    return result

@router.post("/applications/{application_pk}/transition")
def transition(application_pk: int, payload: StageUpdate, db: Session = Depends(get_db)):
    app = db.get(Application, application_pk)
    if not app: raise HTTPException(404, "Application not found")
    if payload.stage == "offer":
        raise HTTPException(409, "Create an approved offer through POST /api/offers; offer creation advances the application")
    if payload.stage == "interview" and not db.query(Interview).filter_by(application_id=app.id).first():
        raise HTTPException(409, "Interview stage requires a scheduled interview")
    if payload.stage == "hired":
        accepted = db.query(Offer).filter_by(application_id=app.id, status="accepted").first()
        if not accepted: raise HTTPException(409, "Hiring requires an accepted offer")
    return {"application_id": transition_application(db, app, payload.stage, payload.actor, payload.reason).application_id, "stage": payload.stage}

@router.post("/offers")
def create_offer(payload: OfferCreate, db: Session = Depends(get_db)):
    from app.models.entities import Offer, Feedback
    app = db.get(Application, payload.application_id)
    if not app: raise HTTPException(404, "Application not found")
    if app.stage != "interview": raise HTTPException(409, "Offer can only be created after interview stage")
    interviews = db.query(Interview).filter_by(application_id=app.id).all()
    if not interviews or any(i.status != "completed" or not db.query(Feedback).filter_by(interview_id=i.id).first() for i in interviews): raise HTTPException(409, "All interview rounds must be completed and have feedback")
    if not payload.approved_by: raise HTTPException(409, "Offer approval is required")
    req = app.requisition
    if not req.salary_min <= payload.salary <= req.salary_max: raise HTTPException(422, "Salary outside approved requisition band")
    offer = Offer(offer_id=f"OFF-2026-{db.query(Offer).count()+1:06d}", application_id=app.id, salary=payload.salary, approved_by=payload.approved_by, status="pending")
    previous_stage = app.stage
    app.stage = "offer"
    db.add(offer)
    db.add(WorkflowEvent(entity_type="application", entity_id=app.application_id, from_state=previous_stage, to_state="offer", actor=payload.approved_by, reason="Advanced after approved offer creation"))
    db.add(WorkflowEvent(entity_type="offer", entity_id=offer.offer_id, from_state=None, to_state="pending", actor=payload.approved_by, reason="Offer created after approval"))
    db.commit(); db.refresh(offer)
    return {"offer_id": offer.offer_id, "status": offer.status}

@router.post("/issues/scan")
def scan_issues(db: Session = Depends(get_db)):
    fresh = detect_issues(db)
    return {"new_issues_detected": len(fresh)}


@router.post("/issues/{issue_pk}/resolve")
def resolve_issue(issue_pk: int, payload: IssueResolve, db: Session = Depends(get_db)):
    issue = db.get(Issue, issue_pk)
    if not issue: raise HTTPException(404, "Issue not found")
    if issue.resolved: raise HTTPException(409, "Issue is already resolved")
    from datetime import datetime
    issue.resolved = True
    issue.resolved_by = payload.actor
    issue.resolution_note = payload.resolution_note
    issue.resolved_at = datetime.utcnow()
    db.add(WorkflowEvent(entity_type="issue", entity_id=str(issue.id), from_state="open", to_state="resolved", actor=payload.actor, reason=payload.resolution_note))
    db.commit()
    return {"issue_id": issue.id, "resolved": issue.resolved, "resolved_by": issue.resolved_by}

@router.get("/issues/evaluation")
def issue_evaluation(db: Session = Depends(get_db)):
    """Compare detected issues with labelled anomalies; prevented duplicates are excluded."""
    expected = db.query(GroundTruthLabel).filter_by(ground_truth="anomaly").all()
    detected = db.query(Issue).all()
    expected_keys = {(x.issue_type, x.entity_type, x.entity_id) for x in expected}
    detected_keys = {(x.issue_type, x.entity_type, x.entity_id) for x in detected}
    true_positive = expected_keys & detected_keys
    missed = expected_keys - detected_keys
    unexpected = detected_keys - expected_keys
    precision = len(true_positive) / len(detected_keys) if detected_keys else 0.0
    recall = len(true_positive) / len(expected_keys) if expected_keys else 0.0
    return {
        "labelled_anomalies": len(expected_keys),
        "detected_issues": len(detected_keys),
        "true_positives": len(true_positive),
        "missed_anomalies": sorted([{"issue_type": x[0], "entity_type": x[1], "entity_id": x[2]} for x in missed], key=lambda x: x["issue_type"]),
        "unexpected_detections": sorted([{"issue_type": x[0], "entity_type": x[1], "entity_id": x[2]} for x in unexpected], key=lambda x: x["issue_type"]),
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "excluded_prevented_attempts": db.query(GroundTruthLabel).filter(GroundTruthLabel.ground_truth != "anomaly").count()
    }

@router.get("/issues", response_model=list[IssueOut])
def issues(db: Session = Depends(get_db)):
    return db.query(Issue).order_by(Issue.detected_at.desc()).limit(500).all()

@router.get("/events")
def events(db: Session = Depends(get_db)):
    return [{"entity_type": e.entity_type, "entity_id": e.entity_id, "from_state": e.from_state, "to_state": e.to_state, "actor": e.actor, "reason": e.reason, "created_at": e.created_at} for e in db.query(WorkflowEvent).order_by(WorkflowEvent.created_at.desc()).limit(200).all()]
