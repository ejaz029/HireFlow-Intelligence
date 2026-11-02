# HireFlow Intelligence

**End-to-end recruitment operations and decision intelligence platform.** Built for the YottaFlex Associate AI Forward Deployed Engineer code challenge.

HireFlow models requisitions, candidates, applications, skills, resumes, screening rules, interviews, interviewers, feedback, offers, workflow events and data-quality issues. It uses synthetic candidate data only. Screening uses job-related skills and experience; it does not use demographic attributes.

## Quick start

### 1. Start MySQL and the API

Configure `.env` using `.env.example`:

```env
DATABASE_URL=mysql+pymysql://hireflow:your_password@localhost:3306/hireflow
CORS_ORIGINS=http://localhost:5173
```

Start the MySQL database using Docker Compose:

```bash
docker compose up --build -d
```

From the repository root, install backend dependencies and start the API:

```bash
cd backend
python -m venv .venv
```

Activate the environment:

```powershell
# Windows
.venv\Scripts\activate
```

```bash
# macOS/Linux
source .venv/bin/activate
```

Install dependencies and run:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API: http://localhost:8000  
Swagger: http://localhost:8000/docs  
Health: http://localhost:8000/api/health

### 2. Generate deterministic datasets

From the backend directory:

```bash
python -m generator.generate --scale starter --seed 20261022 --output ../data/generated
python -m validation.validate ../data/generated
python -m generator.seed_from_csv --folder ../data/generated --reset
```

Use `--scale full` for the challenge target volumes. The starter and full modes use the same generation logic and fixed seed.

### 3. Start the frontend

Open another terminal from the repository root:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173.

## Current API surface

- `GET /api/dashboard` — counts, stage distribution, offer acceptance, screening pass, feedback completeness and availability metrics
- `GET /api/requisitions` — requisition register
- `POST /api/requisitions` and `POST /api/requisitions/{id}/approve` — requisition request and approval
- `GET /api/applications` and `POST /api/applications` — application register and duplicate-safe submission
- `GET /api/interviews`, `GET /api/interviewers`, `GET /api/interviewer-availability`, `POST /api/interviews` — interview schedule and availability validation
- `GET /api/feedback` and `POST /api/feedback` — structured interviewer feedback
- `GET /api/offers` and `POST /api/offers/{id}/decision` — offer register and candidate decision
- `POST /api/applications/{id}/screen` — explainable screening score
- `POST /api/applications/{id}/transition` — validated lifecycle transition with event record
- `POST /api/offers` — creates an offer only after interview feedback and explicit approval, within salary band
- `POST /api/issues/scan` — runs exception detection
- `GET /api/issues` and `POST /api/issues/{id}/resolve` — exception register and audited resolution
- `GET /api/events` — append-only workflow event history

## Data volumes

Full mode targets 100 requisitions, 2,000 candidates, 3,000 unique applications, 600 interviews and 150 offers. The generator also creates departments, skills, candidate skill bridge rows, requisition skill bridge rows (separate bridge-table CSV), resume metadata, interviewers, interviewer availability windows, structured feedback and workflow event history.

## Important design decisions

1. Deterministic identifiers and fixed seed make the synthetic dataset reproducible.
2. Parent data is generated before dependent records.
3. `ground_truth.csv` is stored separately from input tables; do not join it into model features.
4. Duplicate applications are represented as a labelled rejected duplicate attempt rather than corrupting the valid baseline's uniqueness constraint.
5. Workflow changes are stored as events. The current application stage is a projection, not a replacement for history.
6. Offer creation requires the application to be at interview stage, feedback for every interview, an approver, and a salary within the requisition band.
7. Exceptions are stored in a separate issue register and do not silently mutate source records.

## Validation and reproducibility

The validation script checks key uniqueness, foreign-key joins, bridge-table integrity, enum values, salary bands, feedback score ranges and required volume counts, then writes `validation_summary.json`. Run `python scripts/check_reproducibility.py` from the repository root to regenerate the full dataset twice and compare SHA-256 checksums. See `docs/business_rules.md` and `docs/data_dictionary.md`.

## Limitations to close before final submission

- Add authenticated role-based access and formal approval permissions if required by the evaluator.
- Expand arithmetic reconciliation and role-permission tests.
- Add interactive create/edit forms to the frontend for requisitions, interviews, feedback and offers; the API workflows are already available.

These are explicit follow-up tasks; do not represent them as already implemented.

### Ground-truth evaluation

The deterministic generator writes six labelled edge cases to `data/ground_truth/ground_truth.csv`. The database seeder stores these separately in `ground_truth_labels`; the duplicate-application case is recorded as a prevented attempt and is not counted as a detector anomaly. After seeding, run `POST /api/issues/scan` and inspect `GET /api/issues/evaluation` to compare detected issues with the five labelled anomalies. The evaluation reports precision, recall, missed anomalies, and unexpected detections.

### Database Configuration

The project uses MySQL with SQLAlchemy and PyMySQL. Configure the `DATABASE_URL` environment variable in `.env` with your MySQL connection details. Keep database credentials out of version control.
