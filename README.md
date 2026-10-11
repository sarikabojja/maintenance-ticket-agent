# AI Agent for Maintenance Ticket Prioritization

A small, self-contained demonstration for classifying, prioritizing, and routing renewable-energy maintenance tickets. The application uses a six-row dummy dataset, transparent domain rules, and TF-IDF cosine similarity retrieval as a fallback for ticket descriptions that do not match a known rule.

**Live application:** https://maintenance-ticket-agent.onrender.com

**GitHub repository:** https://github.com/sarikabojja/maintenance-ticket-agent

## Features

- FastAPI backend with a ticket-analysis endpoint (`POST /api/run`)
- Bundled maintenance ticket examples (`GET /api/tickets`)
- Health/demo endpoint (`GET /api/demo`)
- Evaluation endpoint (`GET /api/evaluate`)
- Single-page frontend served by FastAPI at `/`
- Ticket category classification and severity scoring
- Probable root cause, recommended next action, and assigned team
- TF-IDF similarity retrieval for unmatched descriptions
- Human-review indicators for uncertain cases
- No external LLM API keys or embedding API keys required

## Project structure

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
├── .gitignore
├── .python-version
├── Procfile
├── requirements.txt
└── README.md
```

## Requirements

- Python 3.10
- pip
- Git (optional for local execution, useful for cloning the repository)

## Run locally on Windows

1. Clone the repository or download the project ZIP.
2. Open PowerShell in the project root directory.
3. Create and activate a virtual environment:

   ```powershell
   py -3.10 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

4. Install the dependencies:

   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

5. Start the application:

   ```powershell
   uvicorn backend.app:app --reload
   ```

6. Open the following URLs in your browser:

   - Frontend: http://127.0.0.1:8000
   - API documentation: http://127.0.0.1:8000/docs
   - Demo endpoint: http://127.0.0.1:8000/api/demo
   - Ticket examples: http://127.0.0.1:8000/api/tickets
   - Evaluation endpoint: http://127.0.0.1:8000/api/evaluate

## Run the tests

With the virtual environment activated, run:

```powershell
python -m unittest discover -s tests -v
```

The two included unit tests cover the bundled known tickets and the human-review behavior for an unknown ticket description.

## Try the API

Example PowerShell request:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/run" -Method Post -ContentType "application/json" -Body '{"text":"Gearbox vibration has increased for turbine WTG-12 with abnormal noise","asset_type":"wind"}'
```

You can also select a bundled example directly from the web interface.

## API response fields

The ticket-analysis response includes:

- `category`
- `severity`
- `severity_score`
- `probable_root_cause`
- `recommended_next_action`
- `assigned_team`
- `method`
- `evidence`
- `severity_rule`
- `requires_human_review`
- `limitations`

## Method and assumptions

1. **Rule-based classification:** Phrase-based domain rules identify the six known fault categories.
2. **Severity scoring:** Severity is assigned using urgency phrases and category-specific defaults. The score is a heuristic demonstration score, not a calibrated probability.
3. **Root-cause suggestions:** Probable root causes are hypotheses associated with ticket categories. They are not confirmed diagnoses.
4. **TF-IDF retrieval:** For descriptions that do not match a known rule, TF-IDF cosine similarity retrieves a related bundled example when similarity meets the configured threshold of 0.12. Otherwise, the ticket can be assigned `needs_review`.
5. **Asset type:** The user can provide an asset type or allow the application to infer it from the description.
6. **Human oversight:** Recommendations must be checked by qualified maintenance personnel, especially for critical or uncertain tickets.

## Evaluation

The `/api/evaluate` endpoint compares predictions with the expected labels in the six bundled records.

Observed evaluation results:

| Metric | Result |
|---|---:|
| Dataset size | 6 tickets |
| Category matches | 6/6 |
| Category match rate | 100% |
| Severity matches | 6/6 |
| Severity match rate | 100% |

**Important:** This is an in-sample smoke test, not a held-out accuracy estimate. The rules were designed around the small supplied dataset, which contains only one example per category. These results do not establish reliable performance on new, real-world maintenance tickets.

For meaningful future evaluation, collect a larger set of expert-reviewed historical tickets. Where the sample size permits, use separate training, validation, and test sets, and report per-class precision, recall, F1-score, and a confusion matrix. Keep near-duplicate tickets in the same split to reduce data leakage.

## Deployment

### Current deployment: Render

The application is deployed on Render.

**Live URL:** https://maintenance-ticket-agent.onrender.com

The service uses the following start command:

```bash
uvicorn backend.app:app --host 0.0.0.0 --port $PORT
```

To verify the deployment, check the homepage, `/api/demo`, `/docs`, and `/api/evaluate`.

The free Render service may spin down after inactivity, so the first request can take longer to respond.

### Railway deployment

The repository includes a `Procfile` with the Railway-compatible start command:

```text
web: uvicorn backend.app:app --host 0.0.0.0 --port $PORT
```

To deploy on Railway, connect the GitHub repository, configure the service to use the repository root, and verify the build and deployment logs. Open the generated public domain and test the application endpoints.

**Note:** The current public deployment is on Render; the Railway deployment has not been verified.

## Limitations and production-readiness gaps

- Only six synthetic/demo tickets are included.
- Rules may miss synonyms, misspellings, multi-fault reports, and unseen asset types.
- TF-IDF retrieval is lexical rather than semantic, so similar words do not necessarily imply similar faults.
- Severity scores are heuristic and are not calibrated against operational risk.
- Root causes and recommended actions require domain-expert review.
- The demonstration does not connect to SCADA, CMMS, work orders, or live asset telemetry.
- Production deployment would require authentication, authorization, audit logs, monitoring, rate limiting, security review, versioned rules, and human approval for safety-critical actions.

## Security

The application does not require external LLM APIs, embedding APIs, API keys, or other secrets in its current implementation. Do not commit credentials or sensitive operational data to the repository.