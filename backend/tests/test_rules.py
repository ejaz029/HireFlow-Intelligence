from app.services.workflow import ALLOWED
from app.services.screening import calculate_screening_score

def test_terminal_states_cannot_progress():
    assert ALLOWED["hired"] == set()
    assert ALLOWED["rejected"] == set()
    assert ALLOWED["withdrawn"] == set()

def test_offer_requires_interview_path():
    assert "offer" in ALLOWED["interview"]
    assert "offer" not in ALLOWED["applied"]

def test_screening_score_is_explainable_and_job_related():
    result = calculate_screening_score([(1, 3), (2, 2), (3, 4)], {1: 4, 2: 2}, 5)
    assert result["skill_match"] == 66.67
    assert result["experience_score"] == 50
    assert result["score"] == 63.33
    assert result["decision"] == "pass"
    assert result["matched_skills"] == 2

def test_screening_score_caps_experience_and_handles_no_required_skills():
    result = calculate_screening_score([], {}, 20)
    assert result["skill_match"] == 100
    assert result["experience_score"] == 100
    assert result["score"] == 100

def test_transition_records_history():
    from app.services.workflow import transition_application
    class FakeDB:
        def __init__(self): self.events=[]; self.committed=False
        def add(self, item): self.events.append(item)
        def commit(self): self.committed=True
        def refresh(self, item): pass
    class FakeApplication:
        application_id="APP-TEST"
        stage="screening"
    db=FakeDB(); app=FakeApplication()
    transition_application(db, app, "interview", "recruiter", "Interview scheduled")
    assert app.stage=="interview"
    assert db.committed and len(db.events)==1
    assert db.events[0].from_state=="screening" and db.events[0].to_state=="interview"

def test_invalid_transition_returns_conflict():
    import pytest
    from fastapi import HTTPException
    from app.services.workflow import transition_application
    class FakeDB:
        def add(self, item): pass
        def commit(self): pass
        def refresh(self, item): pass
    class FakeApplication:
        application_id="APP-TEST"
        stage="applied"
    with pytest.raises(HTTPException) as exc:
        transition_application(FakeDB(), FakeApplication(), "hired", "recruiter")
    assert exc.value.status_code==409
