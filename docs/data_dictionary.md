# HireFlow Intelligence — Data Dictionary

## 1. Overview

This document describes the database schema used by HireFlow Intelligence.

It covers all 17 SQLAlchemy entities, including the 12 core entities and 5 supporting entities. For each entity, it documents fields, data types, defaults, constraints, relationships, and relevant lifecycle information.

**Database conventions**
- Primary keys are integer IDs unless otherwise specified.
- Foreign keys reference the integer primary key of the related entity.
- Business identifiers are separate from internal database IDs.
- Timestamps use SQLAlchemy `DateTime`.
- Salary values represent monetary amounts in INR.
- Synthetic candidate and recruitment data is used in the generated dataset.

**Important:** Application-level validation is distinguished from database constraints. A field stored as `String` does not automatically enforce an enum or a permitted set of values.

---

## 2. Core Entities

### 2.1 Department

**Table:** `departments`

| Field | Type | Constraints / Default |
|---|---|---|
| id | Integer | Primary key |
| code | String(20) | Unique, indexed |
| name | String(100) | Unique |

**Relationships**
- One department can have multiple job requisitions.
- One department can have multiple interviewers.

**Lifecycle:** No explicit lifecycle states are defined.

### 2.2 JobRequisition

**Table:** `job_requisitions`

| Field | Type | Constraints / Default |
|---|---|---|
| id | Integer | Primary key |
| requisition_id | String(32) | Unique, indexed |
| department_id | Integer | Foreign key → departments.id |
| title | String(120) | Required |
| status | String(20) | Default: `approved` |
| salary_min | Float | Required |
| salary_max | Float | Required |
| created_at | DateTime | Default: UTC creation time |

**Relationships**
- Many requisitions belong to one department.
- One requisition can have multiple applications.
- One requisition can have multiple required skills through RequisitionSkill.
- A requisition can have screening rules.

**Lifecycle:** The model defines a default status of `approved`. Other permitted status values are not enforced by the database model.

### 2.3 Candidate

**Table:** `candidates`

| Field | Type | Constraints / Default |
|---|---|---|
| id | Integer | Primary key |
| candidate_id | String(24) | Unique, indexed |
| full_name | String(120) | Required |
| email | String(160) | Unique |
| location | String(80) | Required |
| years_experience | Float | Default: 0 |

**Relationships**
- One candidate can submit multiple applications.
- One candidate can have multiple skills through CandidateSkill.
- One candidate can have one resume artifact.

**Lifecycle:** No explicit candidate lifecycle states are defined.

### 2.4 Application

**Table:** `applications`

| Field | Type | Constraints / Default |
|---|---|---|
| id | Integer | Primary key |
| application_id | String(100) | Unique, indexed |
| requisition_id | Integer | Foreign key → job_requisitions.id |
| candidate_id | Integer | Foreign key → candidates.id |
| stage | String(30) | Default: `applied` |
| status | String(20) | Default: `active` |
| screening_score | Float | Nullable |
| applied_at | DateTime | Default: UTC creation time |

**Constraints**
- Unique combination of `requisition_id` and `candidate_id`.
- Prevents the same candidate from having multiple applications for the same requisition.

**Relationships**
- Many applications belong to one candidate.
- Many applications belong to one requisition.
- One application can have multiple interviews.
- An application can have at most one offer, enforced through the unique constraint on offers.application_id.

**Lifecycle:** The model defines default stage `applied` and status `active`. Valid transitions are handled by application workflow logic, not database enum constraints.

### 2.5 ResumeArtifact

**Table:** `resume_artifacts`

| Field | Type | Constraints / Default |
|---|---|---|
| id | Integer | Primary key |
| candidate_id | Integer | Foreign key → candidates.id, unique |
| file_name | String(160) | Required |
| file_type | String(20) | Default: `pdf` |
| content_hash | String(64) | Required |
| uploaded_at | DateTime | Default: UTC creation time |

**Constraints**
- Unique candidate_id ensures at most one resume artifact per candidate.

**Relationships**
- Each resume artifact belongs to one candidate.
- Each candidate can have at most one resume artifact.

### 2.6 Skill

**Table:** `skills`

| Field | Type | Constraints / Default |
|---|---|---|
| id | Integer | Primary key |
| name | String(60) | Unique |

**Relationships**
- Skills can be associated with multiple candidates through CandidateSkill.
- Skills can be associated with multiple requisitions through RequisitionSkill.

### 2.7 CandidateSkill

**Table:** `candidate_skills`

| Field | Type | Constraints / Default |
|---|---|---|
| id | Integer | Primary key |
| candidate_id | Integer | Foreign key → candidates.id |
| skill_id | Integer | Foreign key → skills.id |
| proficiency | Integer | Default: 1 |

**Constraints**
- Unique combination of `candidate_id` and `skill_id`.

**Relationships**
- Many-to-one with Candidate.
- Many-to-one with Skill.
- Implements the many-to-many relationship between candidates and skills.

### 2.8 ScreeningRule

**Table:** `screening_rules`

| Field | Type | Constraints / Default |
|---|---|---|
| id | Integer | Primary key |
| requisition_id | Integer | Foreign key → job_requisitions.id |
| minimum_score | Float | Default: 60 |
| skills_weight | Float | Default: 0.8 |
| experience_weight | Float | Default: 0.2 |

**Relationships**
- Each screening rule belongs to one requisition.
- A requisition can have multiple screening rule records at the database level.

**Validation considerations**
- The scoring logic uses skill and experience weights.
- Weight ranges and a total weight of 1 should be validated by application logic if required.

### 2.9 Interview

**Table:** `interviews`

| Field | Type | Constraints / Default |
|---|---|---|
| id | Integer | Primary key |
| interview_id | String(32) | Unique, indexed |
| application_id | Integer | Foreign key → applications.id |
| interviewer_id | Integer | Foreign key → interviewers.id |
| round_name | String(40) | Required |
| scheduled_at | DateTime | Required |
| duration_minutes | Integer | Default: 60 |
| status | String(20) | Default: `scheduled` |
| interviewer_available | Boolean | Default: true |

**Relationships**
- Each interview belongs to one application.
- Each interview is assigned to one interviewer.
- An application can have multiple interviews.
- An interviewer can conduct multiple interviews.
- Feedback records reference interviews.

**Lifecycle:** The default status is `scheduled`. Interview status changes are handled by workflow logic.

### 2.10 Interviewer

**Table:** `interviewers`

| Field | Type | Constraints / Default |
|---|---|---|
| id | Integer | Primary key |
| interviewer_id | String(24) | Unique |
| full_name | String(120) | Required |
| department_id | Integer | Foreign key → departments.id |

**Relationships**
- Each interviewer belongs to one department.
- An interviewer can conduct multiple interviews.
- An interviewer can have multiple availability records.
- An interviewer can submit multiple feedback records.

### 2.11 Feedback

**Table:** `feedback`

| Field | Type | Constraints / Default |
|---|---|---|
| id | Integer | Primary key |
| feedback_id | String(80) | Unique |
| interview_id | Integer | Foreign key → interviews.id |
| interviewer_id | Integer | Foreign key → interviewers.id |
| technical_score | Float | Required |
| communication_score | Float | Required |
| recommendation | String(20) | Required |
| comments | Text | Default: empty string |

**Relationships**
- Each feedback record belongs to one interview.
- Each feedback record belongs to one interviewer.
- An interview can have multiple feedback records at the database level.
- An interviewer can submit multiple feedback records.

**Validation considerations**
- Score ranges and permitted recommendation values are validated by application logic where implemented.

### 2.12 Offer

**Table:** `offers`

| Field | Type | Constraints / Default |
|---|---|---|
| id | Integer | Primary key |
| offer_id | String(32) | Unique, indexed |
| application_id | Integer | Foreign key → applications.id, unique |
| salary | Float | Required |
| status | String(20) | Default: `pending` |
| approved_by | String(120) | Nullable |
| created_at | DateTime | Default: UTC creation time |

**Constraints**
- Unique application_id allows at most one offer per application.

**Relationships**
- Each offer belongs to one application.
- Each application can have at most one offer.

**Lifecycle:** Default status is `pending`. Other offer statuses and approval transitions are governed by application workflow logic.

---

## 3. Supporting Entities

### 3.1 RequisitionSkill

**Table:** `requisition_skills`

| Field | Type | Constraints / Default |
|---|---|---|
| id | Integer | Primary key |
| requisition_id | Integer | Foreign key → job_requisitions.id |
| skill_id | Integer | Foreign key → skills.id |
| required_level | Integer | Default: 1 |

**Constraints**
- Unique combination of `requisition_id` and `skill_id`.

**Purpose:** Maps required skills to job requisitions and implements their many-to-many relationship.

### 3.2 InterviewerAvailability

**Table:** `interviewer_availability`

| Field | Type | Constraints / Default |
|---|---|---|
| id | Integer | Primary key |
| interviewer_id | Integer | Foreign key → interviewers.id |
| starts_at | DateTime | Required |
| ends_at | DateTime | Required |
| is_available | Boolean | Default: true |

**Constraints**
- Unique combination of `interviewer_id` and `starts_at`.

**Purpose:** Stores interviewer availability windows used during interview scheduling.

**Validation considerations:** Start and end timestamps should be checked to ensure that the end is later than the start. Availability overlap and scheduling conflict checks are handled by application logic.

### 3.3 WorkflowEvent

**Table:** `workflow_events`

| Field | Type | Constraints / Default |
|---|---|---|
| id | Integer | Primary key |
| entity_type | String(40) | Indexed |
| entity_id | String(100) | Indexed |
| from_state | String(40) | Nullable |
| to_state | String(40) | Required |
| actor | String(120) | Default: `system` |
| reason | Text | Default: empty string |
| created_at | DateTime | Default: UTC creation time |

**Purpose:** Records state transitions for tracked entities.

**Relationships:** Uses `entity_type` and `entity_id` as a polymorphic reference. These are not declared as conventional foreign keys in the SQLAlchemy model.

**Lifecycle:** Each event records the previous state, new state, actor, reason, and timestamp.

### 3.4 Issue

**Table:** `issues`

| Field | Type | Constraints / Default |
|---|---|---|
| id | Integer | Primary key |
| issue_type | String(60) | Indexed |
| entity_type | String(40) | Required |
| entity_id | String(100) | Required |
| severity | String(20) | Default: `high` |
| description | Text | Required |
| ground_truth | String(40) | Default: `anomaly` |
| resolved | Boolean | Default: false |
| resolved_by | String(120) | Nullable |
| resolution_note | Text | Nullable |
| resolved_at | DateTime | Nullable |
| detected_at | DateTime | Default: UTC creation time |

**Purpose:** Stores detected recruitment workflow exceptions and their resolution information.

**Relationships:** Uses `entity_type` and `entity_id` to identify the affected entity. These fields are not declared as foreign keys.

**Lifecycle**
- Unresolved: `resolved = false`
- Resolved: `resolved = true`

Resolution metadata includes the resolver, note, and resolution timestamp.

### 3.5 GroundTruthLabel

**Table:** `ground_truth_labels`

| Field | Type | Constraints / Default |
|---|---|---|
| id | Integer | Primary key |
| issue_type | String(60) | Indexed |
| entity_type | String(40) | Required |
| entity_id | String(100) | Indexed |
| ground_truth | String(60) | Required |
| expected_action | String(120) | Required |

**Constraints**
- Unique combination of `issue_type`, `entity_type`, and `entity_id`.

**Purpose:** Stores expected labels and actions for evaluating anomaly detection results.

**Important distinction:** GroundTruthLabel is a separate evaluation dataset. It is not a foreign-key child of Issue. The Issue table also has its own `ground_truth` field for issue records.

---

## 4. Entity Relationship Summary

| Parent Entity | Child / Mapping Entity | Relationship |
|---|---|---|
| Department | JobRequisition | One-to-many |
| Department | Interviewer | One-to-many |
| JobRequisition | Application | One-to-many |
| JobRequisition | RequisitionSkill | One-to-many |
| Skill | RequisitionSkill | One-to-many |
| Candidate | Application | One-to-many |
| Candidate | CandidateSkill | One-to-many |
| Skill | CandidateSkill | One-to-many |
| Candidate | ResumeArtifact | One-to-zero-or-one |
| JobRequisition | ScreeningRule | One-to-many at database level |
| Application | Interview | One-to-many |
| Interviewer | Interview | One-to-many |
| Interviewer | InterviewerAvailability | One-to-many |
| Interview | Feedback | One-to-many at database level |
| Interviewer | Feedback | One-to-many |
| Application | Offer | One-to-zero-or-one |
| WorkflowEvent | Tracked entity | Polymorphic reference |
| Issue | Affected entity | Polymorphic reference |
| GroundTruthLabel | Evaluation target | Logical reference, not a foreign key |

---

## 5. Identifier Conventions

The generated dataset uses business identifiers separate from internal integer primary keys.

| Entity | Example Identifier |
|---|---|
| Job requisition | `REQ-2026-000001` |
| Candidate | `CAND-000001` |
| Application | `APP-REQ-2026-000001-CAND-000001` |
| Interview | `INT-2026-000001` |
| Feedback | `FB-INT-2026-000001-INTV-0001` |
| Offer | `OFF-2026-000001` |

These are dataset naming conventions, not database-generated ID formats enforced by the column definitions.

---

## 6. Lifecycle and Validation Notes

The following values describe workflow behavior and defaults. The SQLAlchemy model stores these fields as strings and does not itself enforce the full set of permitted values.

| Entity | Field | Defined Default |
|---|---|---|
| JobRequisition | status | `approved` |
| Application | stage | `applied` |
| Application | status | `active` |
| Interview | status | `scheduled` |
| Offer | status | `pending` |
| Issue | resolved | `false` |
| Issue | severity | `high` |

Additional validation should be performed by application logic where applicable:

- Salary minimum should not exceed salary maximum.
- Screening scores should respect their configured score range.
- Screening weights should follow the configured scoring rules.
- Skill proficiency and required skill levels should follow their permitted ranges.
- Interview duration should be positive.
- Interview availability windows should have valid start and end timestamps.
- Interviewer scheduling should prevent conflicting bookings.
- Feedback scores and recommendations should follow the API validation rules.
- Application and offer state transitions should follow workflow rules.

---

## 7. Database Integrity

The schema uses:
- Primary keys for row identity.
- Foreign keys for relationships between core entities.
- Unique constraints to prevent duplicate business identifiers and mapping records.
- Nullable columns for optional workflow and resolution information.
- Defaults for initial workflow states and timestamps.
- Indexes on selected business identifiers and searchable fields.

Application-level validation and workflow services provide additional integrity checks beyond the constraints declared in the SQLAlchemy models.

---

## 8. Scope

This dictionary describes the SQLAlchemy models in `backend/app/models/entities.py`.

It documents the implemented schema, not an idealized future schema. Any additional API validation, workflow transitions, or business rules should be documented alongside their implementation and tests.