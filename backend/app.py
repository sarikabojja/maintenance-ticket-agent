from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.triage import analyze_ticket

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "maintenance_tickets.csv"
FRONTEND_PATH = ROOT / "frontend"

app = FastAPI(
    title="AI Agent for Maintenance Ticket Prioritization",
    description="Rule-based and retrieval-assisted maintenance ticket triage demo.",
    version="1.0.0",
)

class Query(BaseModel):
    text: str = Field(..., min_length=3, max_length=2000)
    asset_type: Optional[str] = Field(default=None, max_length=50)

@app.get("/", response_class=HTMLResponse)
def home():
    """Serve the frontend and backend together for simple deployment."""
    index_path = FRONTEND_PATH / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=500, detail="Frontend index.html is missing.")
    return index_path.read_text(encoding="utf-8")

@app.get("/api/demo")
def demo():
    return {
        "case_study": "AI Agent for Maintenance Ticket Prioritization",
        "status": "running",
        "dataset_rows": _load_data().shape[0],
        "features": [
            "ticket category",
            "severity",
            "probable root cause",
            "recommended next action",
            "maintenance team routing",
        ],
        "method": "transparent domain rules with TF-IDF retrieval fallback",
        "limitation": "The bundled dataset has only six examples; predictions need expert review.",
    }

@app.get("/api/tickets")
def tickets():
    """Return the bundled demo tickets for the frontend's example selector."""
    df = _load_data()
    return {"tickets": df.fillna("").to_dict(orient="records")}

@app.post("/api/run")
def run_case(query: Query):
    result = analyze_ticket(query.text, query.asset_type)
    return {
        "input": query.text,
        "asset_type": query.asset_type or result.get("asset_type"),
        **result,
        "evaluation_hint": (
            "Use the bundled labels only as a tiny demonstration benchmark. "
            "They are not evidence of real-world generalization."
        ),
    }

@app.get("/api/evaluate")
def evaluate():
    """Evaluate the deterministic triage pipeline on the six bundled examples.
    This is an in-sample smoke test, not a held-out generalization estimate.
    """
    df = _load_data()
    rows = []
    for record in df.to_dict(orient="records"):
        prediction = analyze_ticket(record["description"], record["asset_type"])
        rows.append({
            "ticket_id": record["ticket_id"],
            "target_category": record["target_category"],
            "predicted_category": prediction["category"],
            "category_match": record["target_category"] == prediction["category"],
            "target_severity": record["target_severity"],
            "predicted_severity": prediction["severity"],
            "severity_match": record["target_severity"] == prediction["severity"],
        })
    n = len(rows)
    return {
        "dataset_size": n,
        "category_matches": sum(r["category_match"] for r in rows),
        "category_match_rate": round(sum(r["category_match"] for r in rows) / n, 3) if n else 0,
        "severity_matches": sum(r["severity_match"] for r in rows),
        "severity_match_rate": round(sum(r["severity_match"] for r in rows) / n, 3) if n else 0,
        "evaluation_type": "in-sample smoke test only; not a held-out test",
        "results": rows,
        "warning": "Six records are too few to establish reliable real-world accuracy.",
    }

def _load_data() -> pd.DataFrame:
    if not DATA_PATH.exists():
        raise HTTPException(status_code=500, detail=f"Dataset not found: {DATA_PATH.name}")
    return pd.read_csv(DATA_PATH)
