from sqlalchemy.orm import Session
from app.models.entities import Application, CandidateSkill, RequisitionSkill, ScreeningRule

def calculate_screening_score(required: list[tuple[int, int]], candidate_levels: dict[int, int], years_experience: float, skills_weight: float = 0.8, experience_weight: float = 0.2, threshold: float = 60) -> dict:
    """Pure, explainable scoring function using only job-related criteria."""
    if not required:
        skill_score = 100.0
    else:
        skill_score = 100 * sum(1 for skill_id, level in required if candidate_levels.get(skill_id, 0) >= level) / len(required)
    experience_score = min(100.0, max(0.0, years_experience) * 10)
    total = round(skill_score * skills_weight + experience_score * experience_weight, 2)
    return {"score": total, "skill_match": round(skill_score, 2), "experience_score": round(experience_score, 2), "threshold": threshold, "decision": "pass" if total >= threshold else "review_or_reject", "matched_skills": sum(1 for skill_id, level in required if candidate_levels.get(skill_id, 0) >= level), "required_skills": len(required)}

def score_application(db: Session, application: Application) -> dict:
    required_rows = db.query(RequisitionSkill).filter_by(requisition_id=application.requisition_id).all()
    candidate = db.query(CandidateSkill).filter_by(candidate_id=application.candidate_id).all()
    required = [(row.skill_id, row.required_level) for row in required_rows]
    candidate_levels = {row.skill_id: row.proficiency for row in candidate}
    rule = db.query(ScreeningRule).filter_by(requisition_id=application.requisition_id).first()
    sw = rule.skills_weight if rule else 0.8
    ew = rule.experience_weight if rule else 0.2
    threshold = rule.minimum_score if rule else 60
    result = calculate_screening_score(required, candidate_levels, application.candidate.years_experience, sw, ew, threshold)
    application.screening_score = result["score"]
    return result
