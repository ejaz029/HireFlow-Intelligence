# HireFlow Intelligence — System Architecture

## 1. Overview

HireFlow Intelligence is a recruitment operations and intelligence platform designed to manage the recruitment lifecycle, enforce business rules, identify workflow inconsistencies and provide measurable operational insights.

The system uses a modular architecture with a React frontend, FastAPI backend, SQLAlchemy persistence layer and MySQL database.

The solution also includes a deterministic synthetic data generator, data integrity validation and a rule-based anomaly detection service.

## 2. Architecture Diagram

flowchart TD
    UI["React + TypeScript Dashboard"] --> API["FastAPI REST API"]

    API --> WF["Workflow and Business Rules"]
    API --> SC["Explainable Screening Service"]
    API --> AD["Data Quality and Anomaly Detection"]

    WF --> DB[("MySQL Database")]
    SC --> DB
    AD --> DB

    DB --> EV["Workflow Event Records"]
    DB --> IR["Issue Register"]

    GEN["Deterministic Synthetic Data Generator"] --> EXP["CSV / JSON Exports"]
    EXP --> VAL["Integrity and Reproducibility Validation"]

    GT["Separate Ground Truth Labels"] --> EVAL["Anomaly Evaluation"]
    AD --> EVAL
    EVAL --> MET["Precision, Recall and Detection Results"]
```

## 3. Component Responsibilities

| Component | Responsibility |
|---|---|
| Frontend | Operational views, recruitment funnel metrics, application register, requisitions, interviews, offers and exception register. |
| FastAPI | Validated REST API access to recruitment entities, workflow operations and business decisions. |
| Workflow services | Enforce permitted lifecycle transitions and record relevant state changes as workflow events. |
| Screening service | Calculate weighted job-related skill and experience scores and provide an explainable reason breakdown. |
| Anomaly detection | Identify unavailable interviewers, scheduling conflicts, missing feedback progression, salary-band violations and active applications associated with closed roles. |
| Database | Persist recruitment entities, relationships, workflow events and detected issues using MySQL and SQLAlchemy. |
| Data generator | Create deterministic synthetic recruitment records using a configurable scale and fixed random seed. |
| Validation | Check primary-key uniqueness, foreign-key integrity, row counts, lifecycle consistency and reproducibility. |
| Ground truth and evaluation | Maintain separate anomaly labels and compare detected issues against expected outcomes using measurable metrics. |

## 4. Data Flow

flowchart TD
    A["Generate Master Data"] --> B["Generate Dependent Records"]
    B --> C["Validate IDs and Relationships"]
    C --> D["Seed MySQL Database"]

    D --> E["Recruitment Workflow"]
    E --> F["Application Screening"]
    F --> G["Interview Scheduling"]
    G --> H["Feedback Collection"]
    H --> I["Offer Management"]

    D --> J["Anomaly Detection"]
    I --> J

    J --> K["Issue Register"]
    K --> L["Ground Truth Evaluation"]
    L --> M["Precision and Recall Metrics"]

    E --> N["Workflow Event History"]
```

The generator creates master records before dependent records to preserve valid references. Generated records are exported and validated before database seeding.

During application operation, business services process recruitment activities and persist relevant state changes. The anomaly detection service identifies violations and records them in the issue register.

## 5. Entity Relationships and Cardinality

The following relationships describe the implemented relational model.

| Relationship | Cardinality | Description |
|---|---|---|
| Department → JobRequisition | 1:N | A department can own multiple requisitions. |
| Department → Interviewer | 1:N | A department can have multiple interviewers. |
| JobRequisition → Application | 1:N | A requisition can receive multiple applications. |
| Candidate → Application | 1:N | A candidate can submit applications to multiple requisitions. |
| Candidate → ResumeArtifact | 1:0..1 | A candidate can have zero or one resume artifact. |
| Candidate ↔ Skill | N:M | Implemented through CandidateSkill. |
| JobRequisition ↔ Skill | N:M | Implemented through RequisitionSkill. |
| JobRequisition → ScreeningRule | 1:N | A requisition can have multiple screening rules at database level. |
| Application → Interview | 1:N | An application can have multiple interview rounds. |
| Interviewer → Interview | 1:N | An interviewer can participate in multiple interviews. |
| Interviewer → InterviewerAvailability | 1:N | An interviewer can have multiple availability windows. |
| Interview → Feedback | 1:N | An interview can receive feedback from multiple panel members. |
| Interviewer → Feedback | 1:N | An interviewer can submit multiple feedback records. |
| Application → Offer | 1:0..1 | An application can have zero or one offer. |

### Supporting Entities

- **WorkflowEvent:** Stores recruitment workflow activity and state-change history.
- **Issue:** Stores detected workflow inconsistencies, affected entities, severity and detection details.
- **GroundTruthLabel:** Stores expected anomaly classifications separately from ordinary operational input data.

The Issue and GroundTruthLabel entities support anomaly tracking and evaluation.

## 6. Primary Keys and Business Identifiers

Internal database primary keys are separated from externally readable business identifiers.

| Entity | Business Identifier Convention |
|---|---|
| JobRequisition | `REQ-2026-000001` |
| Candidate | `CAND-000001` |
| Application | `APP-<requisition-id>-<candidate-id>` |
| Interview | `INT-2026-000001` |
| Feedback | `FB-<interview-id>-<interviewer-id>` |
| Offer | `OFF-2026-000001` |

Business identifiers are generated deterministically, use zero-padded counters where applicable and remain immutable after creation.

Foreign-key references must resolve to the corresponding parent records.

## 7. Workflow and Business Rules

The system supports the following recruitment lifecycle:

1. Create and approve job requisitions.
2. Define required skills and screening rules.
3. Register candidates and resume metadata.
4. Create applications linked to valid candidates and requisitions.
5. Evaluate applications using job-related screening criteria.
6. Schedule interviews after checking interviewer availability and scheduling conflicts.
7. Capture structured interviewer feedback.
8. Progress applications according to permitted workflow transitions.
9. Create and manage offers subject to the required workflow and approval conditions.

Business rules are enforced through backend validation and database constraints where implemented.

## 8. Screening and Decision Explainability

The screening service evaluates candidates using job-related criteria, including:

- Required skill matches.
- Relevant experience.
- Configurable scoring weights.
- Minimum screening thresholds.

The screening result includes the overall score, component scores, matched skills, required skills and screening decision.

Demographic attributes and unrelated personal characteristics are excluded from screening criteria.

## 9. Workflow Event History

Relevant recruitment state changes are recorded as workflow events.

These records provide traceability into recruitment activities, including stage progression and related operations.

The application records event history rather than relying only on the latest entity status. Append-only behavior is an application-level design intention, not a claim of database-enforced immutability.

## 10. Anomaly Detection and Evaluation

The anomaly detection service identifies the following required exception scenarios:

1. Interview scheduled for an unavailable interviewer.
2. Conflicting interviewer schedules.
3. Application advanced without required feedback.
4. Offer salary outside the approved salary band.
5. Closed requisition with active applications.

Each detected issue records its issue type, affected entity, severity, description and detection timestamp.

Repeated scans are designed to avoid inserting duplicate unresolved issues.

### Ground Truth Evaluation

Known anomalies are maintained separately from normal generated input data.

The evaluation process compares detected issues with labelled ground truth and calculates:

- True positives.
- Missed anomalies.
- Unexpected detections.
- Precision.
- Recall.

Prevented duplicate application attempts are evaluated separately from actual detected anomalies.

Evaluation results represent performance on the generated synthetic dataset and are not production performance claims.

## 11. Synthetic Data Generation and Validation

The generator creates the baseline dataset using a fixed random seed.

| Entity | Target Volume |
|---|---:|
| Job requisitions | 100 |
| Candidates | 2,000 |
| Applications | 3,000 |
| Interviews | 600 |
| Offers | 150 |

The generator supports configurable scales while maintaining consistent generation logic.

Validation includes:

- Primary-key uniqueness.
- Foreign-key integrity.
- Consistent business identifiers.
- Allowed lifecycle values.
- Date ordering.
- Derived-value consistency.
- Duplicate checks.
- Reproducibility through repeated generation and checksum comparison.

## 12. Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React, TypeScript, Vite |
| Backend | Python, FastAPI |
| ORM | SQLAlchemy |
| Database | MySQL |
| API Documentation | OpenAPI / Swagger |
| Data Generation | Python, CSV and JSON |
| Testing | Pytest |
| Version Control | Git and GitHub |

## 13. Effective Dates and Lifecycle States

The implementation uses timestamp fields such as `created_at`, `applied_at`, `scheduled_at` and `detected_at` to record relevant entity activity.

Lifecycle states are represented using application-level validation and string-based database fields.

A future production extension could introduce explicit `effective_from` and `effective_to` fields for requisition requirements and screening rules to support historical versioning and time-based policy evaluation.

## 14. Future Improvements

Potential extensions include:

- Role-based authentication and authorization.
- Database-enforced append-only event history.
- More comprehensive approval workflows.
- Historical versioning of screening rules.
- Background processing for large-scale anomaly scans.
- Advanced recruitment analytics and operational reporting.
