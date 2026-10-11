# AI Agent for Maintenance Ticket Prioritization

A small, self-contained demonstration for classifying, prioritizing, and routing renewable-energy maintenance tickets. It uses the supplied six-row dummy dataset, transparent domain rules, and TF-IDF retrieval as a fallback for descriptions that do not match a rule. It does not call external APIs and works locally without internet after dependencies are installed.

## Features

- FastAPI backend (`POST /api/run`)
- Bundled ticket examples (`GET /api/tickets`)
- Health/demo endpoint (`GET /api/demo`)
- Evaluation smoke test (`GET /api/evaluate`)
- Single-page frontend served by FastAPI at `/`
- Category, severity score, probable root cause, next action, and team routing
- Unknown tickets can be flagged for human review
- Railway start command in `Procfile`

## Project layout

```text
maintenance-ticket-agent/
├── backend/
│   ├── __init__.py
│   ├── app.py
│   └── triage.py
├── data/
│   └── maintenance_tickets.csv
├── frontend/
│   └── index.html
├── tests/
│   └── test_triage.py
├── Procfile
├── requirements.txt
└── README.md
```

## Run locally (Windows PowerShell)

1. Install Python 3.11 or 3.12. The pinned NumPy/scikit-learn versions may not support every newest Python version.
2. Open PowerShell in the project folder.
3. Create and activate a virtual environment:

   ```powershell
   py -3.11 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

4. Install dependencies:

   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

5. Start the API and frontend together:

   ```powershell
   uvicorn backend.app:app --reload
   ```

6. Open `http://127.0.0.1:8000`. API docs are at `http://127.0.0.1:8000/docs`.

## Try the API

PowerShell:

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/run -Method Post -ContentType "application/json" -Body '{"text":"Gearbox vibration has increased for turbine WTG-12 with abnormal noise","asset_type":"wind"}'
```

Or use the web page's sample selector.

## API response fields

- `category`
- `severity` and `severity_score`
- `probable_root_cause`
- `recommended_next_action`
- `assigned_team`
- `method`, `evidence`, and `severity_rule`
- `requires_human_review`
- `limitations`

## Method and assumptions

1. Phrase-based domain rules identify the six known fault categories.
2. Severity is assigned from explicit urgency phrases and documented category defaults. The score is an ordinal demonstration score, not a calibrated probability.
3. Root causes are hypotheses associated with categories; they are not confirmed diagnoses.
4. For unmatched descriptions, TF-IDF cosine similarity retrieves the closest bundled example only if similarity is at least 0.12. Otherwise the category is `needs_review`.
5. The asset type can be supplied by the user or inferred from words in the description.
6. Human review is important, especially for critical or uncertain cases.

## Evaluation

`GET /api/evaluate` compares outputs against the six bundled target labels. This is an **in-sample smoke test** because the rules were designed around the tiny supplied examples. It is not a held-out evaluation and must not be presented as evidence of generalization. With one example per category, meaningful supervised model validation is not possible.

For a larger evaluation, collect expert-reviewed historical tickets, use a stratified train/validation/test split where sample sizes permit, and report per-class precision, recall, F1, and a confusion matrix. Avoid leakage by keeping near-duplicate tickets in the same split.

## Limitations and production-readiness gaps

- Only six synthetic/demo tickets are bundled.
- Rules may miss synonyms, misspellings, multi-fault reports, and unseen asset types.
- TF-IDF retrieval is lexical, not semantic; similarity can be misleading.
- Severity scores are heuristic and not calibrated against operational risk.
- Root causes and recommended actions need domain-expert approval.
- This demo does not connect to SCADA, CMMS, work orders, or live asset telemetry.
- Production deployment needs authentication, authorization, audit logs, monitoring, rate limits, security review, versioned rules, and human approval for safety-critical actions.
- No external LLM or secret is required.

## Deploy to Railway

1. Push the entire project folder to a GitHub repository.
2. In Railway, create a new project and deploy from that repository.
3. Railway should detect Python. The root `Procfile` specifies:

   ```text
   web: uvicorn backend.app:app --host 0.0.0.0 --port $PORT
   ```

4. Ensure the service root is the repository root and the start command uses the Procfile. If the platform does not read the Procfile, set the same command as the service start command.
5. Check build and deploy logs.
6. Open the generated public domain. Confirm `/`, `/api/demo`, `/docs`, and `/api/evaluate` work.

Do not commit credentials or API keys. The application currently requires no secrets.
