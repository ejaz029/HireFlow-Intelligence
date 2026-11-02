from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.entities import Application, WorkflowEvent

ALLOWED = {"applied": {"screening", "withdrawn", "rejected"}, "screening": {"interview", "rejected", "withdrawn"}, "interview": {"offer", "rejected", "withdrawn"}, "offer": {"hired", "rejected", "withdrawn"}, "hired": set(), "rejected": set(), "withdrawn": set()}

def transition_application(db: Session, app: Application, new_stage: str, actor: str, reason: str = ""):
    if new_stage not in ALLOWED.get(app.stage, set()):
        raise HTTPException(409, f"Invalid lifecycle transition: {app.stage} -> {new_stage}")
    old = app.stage
    app.stage = new_stage
    db.add(WorkflowEvent(entity_type="application", entity_id=app.application_id, from_state=old, to_state=new_stage, actor=actor, reason=reason))
    db.commit()
    db.refresh(app)
    return app
