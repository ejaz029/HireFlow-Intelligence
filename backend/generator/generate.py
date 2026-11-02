"""Deterministic synthetic recruitment data generator. Run: python -m generator.generate --scale full --seed 20261022"""
import argparse, hashlib, json, random
from pathlib import Path
import pandas as pd

SKILLS = ["Python", "SQL", "FastAPI", "React", "TypeScript", "AWS", "Docker", "Machine Learning", "Communication", "Testing", "PostgreSQL", "Data Analysis"]
DEPARTMENTS = ["Engineering", "Data", "Product", "Operations", "Security"]
TITLES = ["Backend Engineer", "AI Engineer", "Data Analyst", "Frontend Engineer", "Platform Engineer", "QA Engineer"]
LOCATIONS = ["Bengaluru", "Pune", "Hyderabad", "Chennai", "Remote"]

def make_data(seed=20261022, scale="starter", output=None):
    rng = random.Random(seed)
    sizes = {"starter": (8, 100, 150, 30, 8), "full": (100, 2000, 3000, 600, 150)}
    nr, nc, na, ni, no = sizes[scale]
    out = Path(output or "../../data/generated").resolve(); out.mkdir(parents=True, exist_ok=True)
    departments = [{"department_id": f"DEP-{i+1:03d}", "name": n} for i,n in enumerate(DEPARTMENTS)]
    skills = [{"skill_id": f"SKL-{i+1:03d}", "name": n} for i,n in enumerate(SKILLS)]
    reqs=[]; requisition_skills=[]
    for i in range(nr):
        reqs.append({"requisition_id": f"REQ-2026-{i+1:06d}", "department_id": departments[i%len(departments)]["department_id"], "title": rng.choice(TITLES), "status": "closed" if i == 0 else "approved", "salary_min": rng.randrange(5,15)*100000, "salary_max": rng.randrange(16,30)*100000, "required_skills": rng.sample(SKILLS, k=3)})
        if reqs[-1]["salary_max"] <= reqs[-1]["salary_min"]: reqs[-1]["salary_max"] = reqs[-1]["salary_min"] + 500000
        for skill_name in reqs[-1]["required_skills"]:
            requisition_skills.append({"requisition_id": reqs[-1]["requisition_id"], "skill": skill_name, "required_level": rng.randint(2,4)})
    screening_rules=[{"requisition_id":req["requisition_id"],"minimum_score":60.0,"skills_weight":0.8,"experience_weight":0.2} for req in reqs]
    candidates=[]; candidate_skills=[]; resumes=[]
    first=["Aarav","Ishaan","Riya","Ananya","Kabir","Meera","Dev","Sana","Arjun","Tara"]
    last=["Shah","Rao","Nair","Das","Kapoor","Iyer","Khan","Patel","Joshi","Reddy"]
    for i in range(nc):
        cid=f"CAND-{i+1:06d}"; name=f"{rng.choice(first)} {rng.choice(last)} {i+1}"
        candidates.append({"candidate_id":cid,"full_name":name,"email":f"candidate{i+1:06d}@example.test","location":rng.choice(LOCATIONS),"years_experience":round(rng.uniform(0,12),1)})
        selected_skills=set(rng.sample(SKILLS,k=rng.randint(2,7)))
        if i==0: selected_skills.update(reqs[0]["required_skills"])
        for sk in sorted(selected_skills): candidate_skills.append({"candidate_id":cid,"skill":sk,"proficiency":5 if i==0 and sk in reqs[0]["required_skills"] else rng.randint(1,5)})
        resumes.append({"resume_id":f"RES-{i+1:06d}","candidate_id":cid,"file_name":f"{cid.lower()}.pdf","file_type":"pdf","content_hash":hashlib.sha256(f"{seed}:{cid}".encode()).hexdigest()})
    apps=[]
    # Sample unique requisition/candidate pairs up front so the requested volume is exact.
    pairs=[(r["requisition_id"], c["candidate_id"]) for r in reqs if r["status"] == "approved" for c in candidates]
    first_pair=(reqs[0]["requisition_id"], candidates[0]["candidate_id"])
    remaining=[pair for pair in pairs if pair != first_pair]
    selected_pairs=[first_pair] + rng.sample(remaining, k=max(0,min(na, len(pairs))-1))
    for i, pair in enumerate(selected_pairs):
        req=next(r for r in reqs if r["requisition_id"]==pair[0])
        cand=next(c for c in candidates if c["candidate_id"]==pair[1])
        appid=f"APP-{pair[0]}-{pair[1]}"
        required_levels={x["skill"]:x["required_level"] for x in requisition_skills if x["requisition_id"]==pair[0]}
        candidate_levels={x["skill"]:x["proficiency"] for x in candidate_skills if x["candidate_id"]==cand["candidate_id"]}
        matched=sum(1 for skill_name,level in required_levels.items() if candidate_levels.get(skill_name,0)>=level)
        skill_score=100*matched/len(required_levels) if required_levels else 100
        experience_score=min(100,cand["years_experience"]*10)
        score=round(skill_score*0.8+experience_score*0.2,2)
        stage="rejected" if score<40 else "screening"
        if stage!="rejected" and rng.random()<0.05: stage="withdrawn"  # Exogenous synthetic candidate withdrawal.
        apps.append({"application_id":appid,"requisition_id":pair[0],"candidate_id":pair[1],"stage":stage,"status":"withdrawn" if stage=="withdrawn" else ("closed" if stage=="rejected" else "active"),"screening_score":score,"applied_at":f"2026-{rng.randint(1,3):02d}-{rng.randint(1,28):02d}"})
    interviewers=[{"interviewer_id":f"INTV-{i+1:04d}","full_name":f"Interviewer {i+1}","department_id":departments[i%len(departments)]["department_id"]} for i in range(40)]
    interviews=[]; feedback=[]
    eligible=[a for a in apps if a["stage"] in ["screening","interview"]]
    for i in range(ni):
        if not eligible: break
        app=rng.choice(eligible)
        if i == 0:
            app["stage"] = "offer"  # Deliberate missing-feedback progression anomaly.
        elif app["stage"] == "screening":
            app["stage"] = "interview"
        iid=f"INT-2026-{i+1:06d}"
        if i < 2:
            interviewer=interviewers[0]
            date="2026-06-15T10:00:00"
        else:
            # Generate ordinary interviews without accidental interviewer overlaps.
            for _ in range(1000):
                interviewer=rng.choice(interviewers)
                date=f"2026-{rng.randint(4,10):02d}-{rng.randint(1,28):02d}T{rng.randint(9,16):02d}:00:00"
                start=pd.Timestamp(date); end=start+pd.Timedelta(minutes=60)
                conflicts=False
                for previous in interviews:
                    if previous["interviewer_id"] != interviewer["interviewer_id"]:
                        continue
                    previous_start=pd.Timestamp(previous["scheduled_at"])
                    previous_end=previous_start+pd.Timedelta(minutes=previous["duration_minutes"])
                    if start < previous_end and previous_start < end:
                        conflicts=True; break
                if not conflicts:
                    break
            else:
                raise RuntimeError("Unable to generate a conflict-free interview slot")
        unavailable=(i==0)
        interviews.append({"interview_id":iid,"application_id":app["application_id"],"interviewer_id":interviewer["interviewer_id"],"round_name":rng.choice(["Technical","System Design","Hiring Manager"]),"scheduled_at":date,"duration_minutes":60,"status":"completed" if i%19!=0 else "scheduled","interviewer_available":not unavailable})
        if i%19!=0: feedback.append({"feedback_id":f"FB-{iid}-{interviewer['interviewer_id']}","interview_id":iid,"interviewer_id":interviewer["interviewer_id"],"technical_score":rng.randint(1,5),"communication_score":rng.randint(1,5),"recommendation":rng.choice(["strong_yes","yes","no"]),"comments":"Synthetic structured interview feedback"})
    availability_map={}
    for interview in interviews:
        key=(interview["interviewer_id"],interview["scheduled_at"][:10])
        availability_map[key]={"interviewer_id":interview["interviewer_id"],"starts_at":interview["scheduled_at"][:10]+"T09:00:00","ends_at":interview["scheduled_at"][:10]+"T17:00:00","is_available":not (key==(interviewers[0]["interviewer_id"],"2026-06-15"))}
    interviewer_availability=list(availability_map.values())
    interview_ids_by_app={}
    for interview in interviews: interview_ids_by_app.setdefault(interview["application_id"],[]).append(interview["interview_id"])
    feedback_interview_ids={item["interview_id"] for item in feedback}
    offer_apps=[a for a in apps if a["stage"]=="interview" and interview_ids_by_app.get(a["application_id"]) and all(iid in feedback_interview_ids for iid in interview_ids_by_app[a["application_id"]])]
    rng.shuffle(offer_apps)
    offers=[]
    for i, app in enumerate(offer_apps[:no]):
        app["stage"]="offer"
        req=next(x for x in reqs if x["requisition_id"]==app["requisition_id"])
        salary=rng.randint(int(req["salary_min"]),int(req["salary_max"]))
        if i==0: salary=req["salary_max"]+500000
        app_interview_dates=[x["scheduled_at"] for x in interviews if x["application_id"]==app["application_id"]]
        created_at=max(app_interview_dates)[:10]+"T19:00:00"
        offers.append({"offer_id":f"OFF-2026-{i+1:06d}","application_id":app["application_id"],"salary":salary,"status":rng.choice(["pending","accepted","rejected"]),"approved_by":f"Approver {i%5+1}","created_at":created_at})
    # Explicit event history derived from final lifecycle states, not independently random.
    workflow_events=[]
    interview_dates_by_app={}
    for interview in interviews: interview_dates_by_app.setdefault(interview["application_id"],[]).append(interview["scheduled_at"])
    for app in apps:
        appid=app["application_id"]; stage=app["stage"]
        applied_at=app["applied_at"]+"T09:00:00"
        workflow_events.append({"entity_type":"application","entity_id":appid,"from_state":None,"to_state":"applied","actor":"system","reason":"Application submitted","created_at":applied_at})
        path={"applied":[],"screening":["screening"],"interview":["screening","interview"],"offer":["screening","interview","offer"],"rejected":["rejected"],"withdrawn":["withdrawn"]}.get(stage,[])
        previous="applied"
        last_interview=max(interview_dates_by_app.get(appid,[applied_at]))
        for next_state in path:
            if next_state=="screening": event_time=app["applied_at"]+"T10:00:00"
            elif next_state=="interview": event_time=last_interview[:10]+"T18:00:00"
            elif next_state=="offer": event_time=last_interview[:10]+"T19:00:00"
            else: event_time=app["applied_at"]+"T11:00:00"
            workflow_events.append({"entity_type":"application","entity_id":appid,"from_state":previous,"to_state":next_state,"actor":"system","reason":"Generated lifecycle event","created_at":event_time})
            previous=next_state
    for offer in offers:
        app_row=next(a for a in apps if a["application_id"]==offer["application_id"])
        event_time=max(interview_dates_by_app.get(app_row["application_id"],["2026-10-01T09:00:00"]))[:10]+"T19:00:00"
        workflow_events.append({"entity_type":"offer","entity_id":offer["offer_id"],"from_state":None,"to_state":"pending","actor":offer["approved_by"],"reason":"Offer approved and created","created_at":event_time})
        if offer["status"]!="pending":
            workflow_events.append({"entity_type":"offer","entity_id":offer["offer_id"],"from_state":"pending","to_state":offer["status"],"actor":"candidate","reason":"Candidate offer decision","created_at":event_time[:10]+"T20:00:00"})
    # Explicit, labelled edge cases. They are intentionally isolated in ground truth.
    anomalies=[]
    if interviews: anomalies.append({"issue_type":"unavailable_interviewer","entity_type":"interview","entity_id":interviews[0]["interview_id"],"ground_truth":"anomaly","expected_action":"block_or_reschedule"})
    if len(interviews)>1 and interviews[0]["interviewer_id"]==interviews[1]["interviewer_id"] and interviews[0]["scheduled_at"]==interviews[1]["scheduled_at"]:
        anomalies.append({"issue_type":"interviewer_conflict","entity_type":"interview","entity_id":interviews[1]["interview_id"],"ground_truth":"anomaly","expected_action":"reject_or_reschedule_conflicting_interview"})
    duplicate_base=next((a for a in apps if next(r for r in reqs if r["requisition_id"]==a["requisition_id"])["status"]=="approved"), apps[0] if apps else None)
    if duplicate_base:
        anomalies.append({"issue_type":"candidate_duplicate_application_attempt","entity_type":"application","entity_id":duplicate_base["application_id"],"ground_truth":"duplicate_attempt_prevented_by_unique_constraint","expected_action":"reject_duplicate"})
    if apps and interviews: anomalies.append({"issue_type":"missing_feedback_stage_advanced","entity_type":"application","entity_id":interviews[0]["application_id"],"ground_truth":"anomaly","expected_action":"block_stage_progression"})
    if offers: anomalies.append({"issue_type":"salary_outside_band","entity_type":"offer","entity_id":next((x["offer_id"] for x in offers if x["salary"]>next(r for r in reqs if r["requisition_id"]==next(a for a in apps if a["application_id"]==x["application_id"])["requisition_id"])["salary_max"]),offers[0]["offer_id"]),"ground_truth":"anomaly","expected_action":"block_offer_approval"})
    if reqs and apps: anomalies.append({"issue_type":"closed_role_active_application","entity_type":"requisition","entity_id":next((r["requisition_id"] for r in reqs if r["status"]=="closed"),reqs[0]["requisition_id"]),"ground_truth":"anomaly","expected_action":"close_or_withdraw_active_applications"})
    tables={"departments":departments,"skills":skills,"job_requisitions":reqs,"requisition_skills":requisition_skills,"screening_rules":screening_rules,"candidates":candidates,"candidate_skills":candidate_skills,"resume_artifacts":resumes,"applications":apps,"interviewers":interviewers,"interviewer_availability":interviewer_availability,"interviews":interviews,"feedback":feedback,"offers":offers,"workflow_events":workflow_events}
    for name,rows in tables.items():
        frame=pd.DataFrame(rows)
        frame.to_csv(out/f"{name}.csv",index=False)
        (out/f"{name}.json").write_text(frame.to_json(orient="records",indent=2))
    gt_dir=out.parent/"ground_truth"; gt_dir.mkdir(parents=True,exist_ok=True)
    pd.DataFrame(anomalies).to_csv(gt_dir/"ground_truth.csv",index=False)
    (gt_dir/"ground_truth.json").write_text(json.dumps(anomalies,indent=2))
    duplicate_attempts=[]
    if duplicate_base:
        duplicate_attempts=[{"attempt_id":"DUP-ATTEMPT-000001","requisition_id":duplicate_base["requisition_id"],"candidate_id":duplicate_base["candidate_id"],"original_application_id":duplicate_base["application_id"],"issue_type":"duplicate_application_attempt","ground_truth":"reject_duplicate","included_in_valid_applications":False}]
    pd.DataFrame(duplicate_attempts).to_csv(gt_dir/"duplicate_application_attempts.csv",index=False)
    (gt_dir/"duplicate_application_attempts.json").write_text(json.dumps(duplicate_attempts,indent=2))
    # Portable staging SQL export: each generated table is loaded as text into a seed staging table.
    def sql_value(value):
        if value is None or (isinstance(value,float) and pd.isna(value)): return "NULL"
        if isinstance(value,(dict,list)): value=json.dumps(value,separators=(",",":"))
        return "'"+str(value).replace("'","''")+"'"
    sql=["-- Generated synthetic seed staging data. No production or personal data.","BEGIN;"]
    for name,records in tables.items():
        if not records: continue
        columns=list(records[0].keys()); table="seed_"+name
        sql.append(f"CREATE TEMP TABLE {table} ({', '.join(c+' TEXT' for c in columns)});")
        for record in records:
            sql.append(f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(sql_value(record.get(c)) for c in columns)});")
    sql.append("COMMIT;")
    (out/"seed_data.sql").write_text("\n".join(sql)+"\n")
    manifest={"seed":seed,"scale":scale,"counts":{k:len(v) for k,v in tables.items()},"generator":"hireflow deterministic synthetic generator","synthetic_only":True,"requested_counts":{"job_requisitions":nr,"candidates":nc,"applications":na,"interviews":ni,"offers":no}}
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2))
    print(json.dumps(manifest,indent=2)); return tables

if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("--seed",type=int,default=20261022); p.add_argument("--scale",choices=["starter","full"],default="starter"); p.add_argument("--output",default="../../data/generated"); a=p.parse_args(); make_data(a.seed,a.scale,a.output)
