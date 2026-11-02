"""Load generated CSV tables into the configured database. Run after generation."""
import argparse
from pathlib import Path
import pandas as pd
from sqlalchemy.orm import Session
from app.core.database import Base, engine, SessionLocal
from app.models.entities import (Department, JobRequisition, Candidate, Skill, RequisitionSkill, CandidateSkill, ResumeArtifact, ScreeningRule, Application, Interviewer, InterviewerAvailability, Interview, Feedback, Offer, WorkflowEvent, GroundTruthLabel)

def rows_from_ground_truth(root):
    path = root.parent / "ground_truth" / "ground_truth.csv"
    return pd.read_csv(path).to_dict("records") if path.exists() else []

def load(folder: str, reset: bool = False):
    root=Path(folder).resolve()
    Base.metadata.create_all(bind=engine)
    db: Session=SessionLocal()
    try:
        if reset:
            Base.metadata.drop_all(bind=engine); Base.metadata.create_all(bind=engine)
        def rows(name):
            path=root/f"{name}.csv"
            if not path.exists(): return []
            frame=pd.read_csv(path).astype(object)
            return frame.where(pd.notna(frame), None).to_dict("records")
        # Parent/master tables first.
        departments={r["department_id"]:Department(code=r["department_id"],name=r["name"]) for r in rows("departments")}
        db.add_all(departments.values()); db.flush()
        skills={r["name"]:Skill(name=r["name"]) for r in rows("skills")}; db.add_all(skills.values()); db.flush()
        candidates={r["candidate_id"]:Candidate(candidate_id=r["candidate_id"],full_name=r["full_name"],email=r["email"],location=r["location"],years_experience=float(r["years_experience"])) for r in rows("candidates")}
        db.add_all(candidates.values()); db.flush()
        requisitions={}
        for r in rows("job_requisitions"):
            req=JobRequisition(requisition_id=r["requisition_id"],department_id=departments[r["department_id"]].id,title=r["title"],status=r["status"],salary_min=float(r["salary_min"]),salary_max=float(r["salary_max"]))
            db.add(req); requisitions[r["requisition_id"]]=req
        db.flush()
        # Bridge and metadata tables.
        for r in rows("requisition_skills"):
            db.add(RequisitionSkill(requisition_id=requisitions[r["requisition_id"]].id,skill_id=skills[r["skill"]].id,required_level=int(r["required_level"])))
        for r in rows("candidate_skills"):
            db.add(CandidateSkill(candidate_id=candidates[r["candidate_id"]].id,skill_id=skills[r["skill"]].id,proficiency=int(r["proficiency"])))
        for r in rows("resume_artifacts"):
            db.add(ResumeArtifact(candidate_id=candidates[r["candidate_id"]].id,file_name=r["file_name"],file_type=r["file_type"],content_hash=r["content_hash"]))
        for r in rows("screening_rules"):
            db.add(ScreeningRule(requisition_id=requisitions[r["requisition_id"]].id,minimum_score=float(r["minimum_score"]),skills_weight=float(r["skills_weight"]),experience_weight=float(r["experience_weight"])))
        interviewers={}
        for r in rows("interviewers"):
            person=Interviewer(interviewer_id=r["interviewer_id"],full_name=r["full_name"],department_id=departments[r["department_id"]].id)
            db.add(person); interviewers[r["interviewer_id"]]=person
        db.flush()
        for r in rows("interviewer_availability"):
            db.add(InterviewerAvailability(interviewer_id=interviewers[r["interviewer_id"]].id,starts_at=pd.to_datetime(r["starts_at"]).to_pydatetime(),ends_at=pd.to_datetime(r["ends_at"]).to_pydatetime(),is_available=bool(r["is_available"])))
        applications={}
        for r in rows("applications"):
            app=Application(application_id=r["application_id"],requisition_id=requisitions[r["requisition_id"]].id,candidate_id=candidates[r["candidate_id"]].id,stage=r["stage"],status=r["status"],screening_score=float(r["screening_score"]))
            db.add(app); applications[r["application_id"]]=app
        db.flush()
        interviews={}
        for r in rows("interviews"):
            interview=Interview(interview_id=r["interview_id"],application_id=applications[r["application_id"]].id,interviewer_id=interviewers[r["interviewer_id"]].id,round_name=r["round_name"],scheduled_at=pd.to_datetime(r["scheduled_at"]).to_pydatetime(),duration_minutes=int(r["duration_minutes"]),status=r["status"],interviewer_available=bool(r["interviewer_available"]))
            db.add(interview); interviews[r["interview_id"]]=interview
        db.flush()
        for r in rows("feedback"):
            db.add(Feedback(feedback_id=r["feedback_id"],interview_id=interviews[r["interview_id"]].id,interviewer_id=interviewers[r["interviewer_id"]].id,technical_score=float(r["technical_score"]),communication_score=float(r["communication_score"]),recommendation=r["recommendation"],comments=r["comments"]))
        for r in rows("offers"):
            db.add(Offer(offer_id=r["offer_id"],application_id=applications[r["application_id"]].id,salary=float(r["salary"]),status=r["status"],approved_by=r["approved_by"],created_at=pd.to_datetime(r["created_at"]).to_pydatetime()))
        for r in rows("workflow_events"):
            db.add(WorkflowEvent(entity_type=r["entity_type"],entity_id=r["entity_id"],from_state=r["from_state"],to_state=r["to_state"],actor=r["actor"],reason=r["reason"],created_at=pd.to_datetime(r["created_at"]).to_pydatetime()))
        # Keep expected labels separate from detected issues so evaluation is meaningful.
        truth_path = root.parent / "ground_truth" / "ground_truth.csv"
        if truth_path.exists():
            truth_frame = pd.read_csv(truth_path).astype(object)
            truth = truth_frame.where(pd.notna(truth_frame), None).to_dict("records")
            for label in truth:
                key = (label["issue_type"], label["entity_type"], label["entity_id"])
                exists = db.query(GroundTruthLabel).filter_by(issue_type=key[0], entity_type=key[1], entity_id=key[2]).first()
                if not exists:
                    db.add(GroundTruthLabel(issue_type=key[0], entity_type=key[1], entity_id=key[2], ground_truth=label["ground_truth"], expected_action=label["expected_action"]))
        db.commit()
        return {"departments":len(departments),"skills":len(skills),"requisitions":len(requisitions),"candidates":len(candidates),"applications":len(applications),"interviewers":len(interviewers),"interviewer_availability":len(rows("interviewer_availability")),"interviews":len(interviews),"offers":len(rows("offers")),"workflow_events":len(rows("workflow_events")),"ground_truth_labels":len(rows_from_ground_truth(root))}
    except Exception:
        db.rollback(); raise
    finally: db.close()

if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("--folder",default="../data/generated"); p.add_argument("--reset",action="store_true"); a=p.parse_args(); print(load(a.folder,a.reset))
