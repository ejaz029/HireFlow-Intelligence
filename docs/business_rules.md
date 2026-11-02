# Business rules and decision policy

## Screening

Score only job-related criteria:

`total = skill_match_percentage * skills_weight + experience_score * experience_weight`

The default weights are 0.80 and 0.20. Skill match is the percentage of required skills for which the candidate meets the minimum proficiency. Experience score is capped at 100 (10 points per year). The synthetic generator uses deterministic policy bands: below 40 is rejected, 40–59.99 remains in screening/review, and 60 or above is eligible for interview scheduling. A 5% seeded exogenous withdrawal event models candidate withdrawal; this is not a screening feature. The configurable minimum score determines pass vs review/reject. No name, location, age, gender, religion, caste, disability or other protected/demographic proxy is used in scoring.

## Lifecycle

- applied -> screening, withdrawn, rejected
- screening -> interview, rejected, withdrawn
- interview -> offer, rejected, withdrawn
- offer -> hired, rejected, withdrawn
- hired, rejected and withdrawn are terminal

Every transition writes a WorkflowEvent with prior state, next state, actor, reason and timestamp. Invalid transitions return HTTP 409.

## Interview and feedback

An interviewer cannot be double-booked for overlapping intervals. Scheduling requires an available InterviewerAvailability window that fully contains the requested interval, then checks for overlaps. The issue scanner flags unavailable interviewers and overlapping interview windows. Feedback is structured with technical score, communication score, recommendation and comments. Advancing to offer requires feedback for every scheduled interview associated with the application.

## Offers

An offer requires an application at interview stage, all interview feedback, a named approver and salary within the requisition's approved range. Rejected or accepted outcomes are recorded as offer statuses, not generated as independent ground-truth facts.

## Exceptions

The baseline generator creates valid records first. Deliberate negative scenarios are labelled separately in `data/ground_truth/ground_truth.csv`. They must not be used as input features. Anomaly records describe expected detection/action and do not silently alter unrelated source records.
