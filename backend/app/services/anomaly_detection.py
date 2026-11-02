from datetime import timedelta
from sqlalchemy.orm import Session
from app.models.entities import (
    Application, Interview, Feedback, Offer, JobRequisition, Issue, GroundTruthLabel
)

def detect_issues(db: Session) -> list[Issue]:
    """Detect recruitment exceptions and attach matching ground-truth labels."""
    found: dict[tuple[str, str, str], str] = {}

    # Interviews conflict only when their time intervals genuinely overlap.
    interviews = db.query(Interview).filter(Interview.status.in_(["scheduled", "completed"])).all()
    for interview in interviews:
        if not interview.interviewer_available:
            found[("unavailable_interviewer", "interview", interview.interview_id)] = (
                "Interview is assigned to an unavailable interviewer."
            )
    for index, first in enumerate(interviews):
        first_end = first.scheduled_at + timedelta(minutes=first.duration_minutes)
        for second in interviews[index + 1:]:
            if first.interviewer_id != second.interviewer_id:
                continue
            second_end = second.scheduled_at + timedelta(minutes=second.duration_minutes)
            if first.scheduled_at < second_end and second.scheduled_at < first_end:
                found[("interviewer_conflict", "interview", second.interview_id)] = (
                    f"Interviewer has overlapping interviews: {first.interview_id} and {second.interview_id}."
                )

    # An application cannot advance to offer/hired while any interview lacks feedback.
    advanced = db.query(Application).filter(Application.stage.in_(["offer", "hired"])).all()
    for application in advanced:
        interview_rows = db.query(Interview).filter_by(application_id=application.id).all()
        missing = [item for item in interview_rows if not db.query(Feedback.id).filter_by(interview_id=item.id).first()]
        if missing:
            found[("missing_feedback_stage_advanced", "application", application.application_id)] = (
                "Application advanced without feedback for at least one interview."
            )

    # Offers must remain within the associated requisition's approved salary band.
    offers = db.query(Offer).all()
    for offer in offers:
        application = db.get(Application, offer.application_id)
        if not application:
            continue
        requisition = db.get(JobRequisition, application.requisition_id)
        if requisition and not requisition.salary_min <= offer.salary <= requisition.salary_max:
            found[("salary_outside_band", "offer", offer.offer_id)] = (
                f"Offer salary {offer.salary} is outside approved band {requisition.salary_min}-{requisition.salary_max}."
            )

    # Report the closed requisition once, matching the ground-truth entity.
    closed_requisitions = db.query(JobRequisition).filter_by(status="closed").all()
    for requisition in closed_requisitions:
        active = db.query(Application.id).filter_by(requisition_id=requisition.id, status="active").first()
        if active:
            found[("closed_role_active_application", "requisition", requisition.requisition_id)] = (
                "Closed requisition still has active applications."
            )

    labels = {
        (label.issue_type, label.entity_type, label.entity_id): label.ground_truth
        for label in db.query(GroundTruthLabel).all()
    }
    existing = {
        (issue.issue_type, issue.entity_type, issue.entity_id)
        for issue in db.query(Issue).filter_by(resolved=False).all()
    }
    fresh = []
    for key, description in found.items():
        if key in existing:
            continue
        fresh.append(Issue(
            issue_type=key[0], entity_type=key[1], entity_id=key[2],
            description=description, ground_truth=labels.get(key, "unlabelled")
        ))
    db.add_all(fresh)
    db.commit()
    return fresh
