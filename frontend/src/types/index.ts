export type Dashboard = { requisitions:number; total_requisitions:number; candidates:number; applications:number; interviews:number; offers:number; open_issues:number; offer_acceptance_rate:number; screening_pass_rate:number; feedback_completeness_rate:number; interviewer_availability_rate:number; stage_distribution:Record<string,number> };
export type Application = { id:number; application_id:string; candidate:string; candidate_id:string; requisition:string; stage:string; status:string; screening_score:number|null };
export type Issue = { id:number; issue_type:string; entity_type:string; entity_id:string; severity:string; description:string; resolved:boolean };
export type Requisition = { id:number; requisition_id:string; title:string; status:string; salary_min:number; salary_max:number; department:string };
export type Interview = { id:number; interview_id:string; application_id:number; interviewer_id:number; round_name:string; scheduled_at:string; status:string; interviewer_available:boolean };
export type Offer = { id:number; offer_id:string; application_id:number; salary:number; status:string; approved_by:string|null };
