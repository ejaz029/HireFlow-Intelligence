import argparse, json
from pathlib import Path
import pandas as pd

ENUMS = {
    "applications": {"stage": {"applied","screening","interview","offer","hired","rejected","withdrawn"}, "status": {"active","withdrawn","closed"}},
    "job_requisitions": {"status": {"approved","closed"}},
    "offers": {"status": {"pending","accepted","rejected","withdrawn"}},
    "feedback": {"recommendation": {"strong_yes","yes","no","strong_no"}},
}

def validate(folder="../data/generated"):
    root=Path(folder).resolve(); report={"checks":{},"errors":[],"intentional_exceptions":{}}
    tables={p.stem:pd.read_csv(p) for p in root.glob("*.csv")}
    unique_cols={"departments":"department_id","skills":"skill_id","job_requisitions":"requisition_id","candidates":"candidate_id","applications":"application_id","interviews":"interview_id","offers":"offer_id","workflow_events":None}
    for table,col in unique_cols.items():
        if table in tables and col:
            ok=not tables[table][col].duplicated().any(); report["checks"][f"{table}.{col}.unique"]=ok
            if not ok: report["errors"].append(f"Duplicate primary/natural key: {table}.{col}")
    fk=[("job_requisitions","department_id","departments","department_id"),("interviewers","department_id","departments","department_id"),("requisition_skills","requisition_id","job_requisitions","requisition_id"),("screening_rules","requisition_id","job_requisitions","requisition_id"),("requisition_skills","skill","skills","name"),("candidate_skills","candidate_id","candidates","candidate_id"),("candidate_skills","skill","skills","name"),("applications","requisition_id","job_requisitions","requisition_id"),("applications","candidate_id","candidates","candidate_id"),("resume_artifacts","candidate_id","candidates","candidate_id"),("interviewer_availability","interviewer_id","interviewers","interviewer_id"),("interviews","application_id","applications","application_id"),("interviews","interviewer_id","interviewers","interviewer_id"),("feedback","interview_id","interviews","interview_id"),("feedback","interviewer_id","interviewers","interviewer_id"),("offers","application_id","applications","application_id")]
    for child,field,parent,parent_field in fk:
        if child in tables and parent in tables:
            ok=set(tables[child][field].dropna()).issubset(set(tables[parent][parent_field].dropna())); report["checks"][f"fk.{child}.{field}"]=ok
            if not ok: report["errors"].append(f"Foreign key failure: {child}.{field} -> {parent}.{parent_field}")
    if "applications" in tables:
        duplicate_pairs=tables["applications"].duplicated(["requisition_id","candidate_id"]).any()
        report["checks"]["applications.requisition_candidate_pair_unique"]=not duplicate_pairs
        if duplicate_pairs: report["errors"].append("Duplicate candidate/requisition applications in valid baseline")
    if all(name in tables for name in ["applications", "candidate_skills", "requisition_skills", "candidates"]):
        candidate_exp=tables["candidates"].set_index("candidate_id").years_experience.to_dict()
        candidate_skill_map={}
        for row in tables["candidate_skills"].itertuples(): candidate_skill_map.setdefault(row.candidate_id,{})[row.skill]=row.proficiency
        required_skill_map={}
        for row in tables["requisition_skills"].itertuples(): required_skill_map.setdefault(row.requisition_id,{})[row.skill]=row.required_level
        mismatch=[]
        for row in tables["applications"].itertuples():
            required=required_skill_map.get(row.requisition_id,{})
            candidate_skills=candidate_skill_map.get(row.candidate_id,{})
            matched=sum(1 for skill,level in required.items() if candidate_skills.get(skill,0)>=level)
            skill_score=100*matched/len(required) if required else 100
            experience_score=min(100,candidate_exp[row.candidate_id]*10)
            expected=round(skill_score*0.8+experience_score*0.2,2)
            if abs(expected-float(row.screening_score))>0.01: mismatch.append(row.application_id)
        report["checks"]["screening_scores_reconcile_to_source"]=len(mismatch)==0
        if mismatch: report["errors"].append(f"Screening score mismatches: {mismatch[:5]}")
    if "job_requisitions" in tables:
        ok=(tables["job_requisitions"].salary_min<=tables["job_requisitions"].salary_max).all()
        report["checks"]["requisition.salary_band_order"]=bool(ok)
        if not ok: report["errors"].append("Invalid requisition salary band")
    for table,fields in ENUMS.items():
        if table not in tables: continue
        for field,allowed in fields.items():
            ok=set(tables[table][field].dropna()).issubset(allowed)
            report["checks"][f"enum.{table}.{field}"]=bool(ok)
            if not ok: report["errors"].append(f"Invalid enum values in {table}.{field}")
    if "screening_rules" in tables:
        weights=tables["screening_rules"].skills_weight+tables["screening_rules"].experience_weight
        ok=tables["screening_rules"].minimum_score.between(0,100).all() and ((weights-1).abs()<0.0001).all()
        report["checks"]["screening_rules.weights_and_threshold_valid"]=bool(ok)
        if not ok: report["errors"].append("Screening rule weights must sum to 1 and threshold must be 0..100")
    if "feedback" in tables:
        ok=tables["feedback"].technical_score.between(1,5).all() and tables["feedback"].communication_score.between(1,5).all()
        report["checks"]["feedback.scores_range_1_5"]=bool(ok)
        if not ok: report["errors"].append("Feedback score outside 1..5")
    if "interviews" in tables:
        ok=(tables["interviews"].duration_minutes>0).all()
        report["checks"]["interviews.positive_duration"]=bool(ok)
        if not ok: report["errors"].append("Interview duration must be positive")
    if "applications" in tables and "interviews" in tables:
        app_dates=tables["applications"].set_index("application_id").applied_at
        interview_dates=tables["interviews"].copy()
        interview_dates["applied_at"] = interview_dates.application_id.map(app_dates)
        ok=(pd.to_datetime(interview_dates.scheduled_at) >= pd.to_datetime(interview_dates.applied_at)).all()
        report["checks"]["interviews.after_application_date"]=bool(ok)
        if not ok: report["errors"].append("Interview scheduled before application date")
    if "offers" in tables and "applications" in tables and "interviews" in tables and "feedback" in tables:
        app_stage=tables["applications"].set_index("application_id").stage
        interview_map=tables["interviews"].groupby("application_id").interview_id.apply(list).to_dict()
        feedback_ids=set(tables["feedback"].interview_id)
        invalid=[]
        for offer in tables["offers"].itertuples():
            app_id=tables["applications"].loc[tables["applications"].application_id==offer.application_id,"application_id"].iloc[0]
            linked=interview_map.get(app_id,[])
            interview_statuses=tables["interviews"].set_index("interview_id").loc[linked].status.tolist() if linked else []
            if app_stage[app_id] != "offer" or not linked or not all(x in feedback_ids for x in linked) or not all(x=="completed" for x in interview_statuses): invalid.append(offer.offer_id)
        report["checks"]["offers.have_interview_feedback"]=len(invalid)==0
        if invalid: report["errors"].append(f"Offers without completed interview feedback: {invalid[:5]}")
    if "offers" in tables and "applications" in tables and "job_requisitions" in tables:
        req_band=tables["job_requisitions"].set_index("requisition_id")
        app_req=tables["applications"].set_index("application_id").requisition_id
        out_of_band=[]
        for offer in tables["offers"].itertuples():
            req_id=app_req[offer.application_id]; band=req_band.loc[req_id]
            if not band.salary_min <= offer.salary <= band.salary_max: out_of_band.append(offer.offer_id)
        report["intentional_exceptions"]["offers_outside_salary_band"] = out_of_band
    manifest_path=root/"manifest.json"
    if manifest_path.exists():
        manifest=json.loads(manifest_path.read_text())
        expected=manifest.get("requested_counts",{})
        actual={k:len(tables[k]) for k in tables}
        count_checks={k:actual.get(k)==v for k,v in expected.items()}
        report["checks"]["required_volume_counts"]=all(count_checks.values())
        report["required_volume_counts"]={"expected":expected,"actual":{k:actual.get(k) for k in expected},"checks":count_checks}
        if not all(count_checks.values()): report["errors"].append("Required full/starter dataset volumes do not match manifest")
    gt=root.parent/"ground_truth"/"ground_truth.csv"
    if gt.exists():
        truth=pd.read_csv(gt)
        report["intentional_exceptions"]={"ground_truth_labels":len(truth),"issue_types":truth.issue_type.tolist()}
    report["row_counts"]={k:len(v) for k,v in tables.items()}; report["passed"]=not report["errors"]
    (root/"validation_summary.json").write_text(json.dumps(report,indent=2)); return report

if __name__=="__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("folder",nargs="?",default="../data/generated"); args=parser.parse_args()
    print(json.dumps(validate(args.folder),indent=2))
