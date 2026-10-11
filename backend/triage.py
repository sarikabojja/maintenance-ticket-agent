"""Transparent domain-rule triage with a small TF-IDF retrieval fallback.

The six bundled examples are a demonstration dataset, not a production training set.
Rules should be reviewed by renewable-energy maintenance subject-matter experts.
"""
from pathlib import Path
import re
from typing import Optional

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "maintenance_tickets.csv"

CATEGORY_RULES = [
    (("gearbox", "vibration", "abnormal noise"), "gearbox_vibration"),
    (("inverter", "temperature", "high temperature", "overheat", "overheating"), "inverter_thermal"),
    (("spillway", "inspection checklist", "checklist pending"), "inspection_compliance"),
    (("scada", "data missing", "missing data", "telemetry gap"), "data_gap"),
    (("blade pitch", "pitch error", "pitch system"), "pitch_system"),
    (("curtailment", "generation dashboard"), "grid_curtailment"),
]

CATEGORY_DETAILS = {
    "inverter_thermal": {
        "root_cause": "Possible inverter overheating, cooling issue, or thermal protection trip.",
        "next_action": "Review inverter alarms and cooling status; arrange an inspection following site safety procedures.",
        "team": "Solar electrical maintenance",
        "severity": "high",
        "severity_score": 75,
    },
    "gearbox_vibration": {
        "root_cause": "Possible gearbox wear, lubrication issue, or developing mechanical fault.",
        "next_action": "Escalate for urgent turbine inspection; follow site isolation and safety procedures before physical checks.",
        "team": "Wind turbine mechanical maintenance",
        "severity": "critical",
        "severity_score": 95,
    },
    "inspection_compliance": {
        "root_cause": "Scheduled inspection or maintenance checklist has not been completed or recorded.",
        "next_action": "Assign the pending checklist to the responsible maintenance owner and confirm completion against site procedure.",
        "team": "Hydro operations and compliance",
        "severity": "medium",
        "severity_score": 45,
    },
    "data_gap": {
        "root_cause": "Possible SCADA communication, telemetry, historian, or data-ingestion interruption.",
        "next_action": "Check SCADA connectivity, data acquisition and timestamps; notify operations if the gap persists.",
        "team": "SCADA and instrumentation support",
        "severity": "medium",
        "severity_score": 45,
    },
    "pitch_system": {
        "root_cause": "Possible blade pitch actuator, sensor, control, or pitch-system fault after a wind event.",
        "next_action": "Review turbine alarms and event logs; arrange a qualified wind-turbine inspection before returning equipment to service.",
        "team": "Wind turbine controls and mechanical maintenance",
        "severity": "high",
        "severity_score": 75,
    },
    "grid_curtailment": {
        "root_cause": "Possible mismatch between grid curtailment instructions and dashboard data integration or update logic.",
        "next_action": "Verify the curtailment instruction and source data, then reconcile the generation dashboard with grid/operations records.",
        "team": "Grid operations and SCADA support",
        "severity": "medium",
        "severity_score": 45,
    },
}

SEVERITY_RULES = [
    (("gearbox", "abnormal noise", "severe vibration", "fire", "smoke", "injury", "safety incident"), "critical", 95),
    (("tripping repeatedly", "high temperature", "pitch error", "power loss", "stopped generating", "shutdown"), "high", 75),
    (("inspection checklist pending", "checklist pending", "data missing", "scada data missing", "curtailment instruction"), "medium", 45),
]
SEVERITY_ORDER = {"low": 20, "medium": 45, "high": 75, "critical": 95}

def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()

def _load_examples():
    if not DATA_PATH.exists():
        return []
    try:
        return pd.read_csv(DATA_PATH).fillna("").to_dict(orient="records")
    except Exception:
        return []

def _rule_category(text: str) -> Optional[str]:
    for phrases, category in CATEGORY_RULES:
        if any(phrase in text for phrase in phrases):
            return category
    return None

def _retrieve_category(text: str):
    """Find the closest bundled description using TF-IDF cosine similarity."""
    examples = _load_examples()
    if not examples:
        return None, 0.0, None
    descriptions = [str(row.get("description", "")) for row in examples]
    corpus = descriptions + [text]
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
    matrix = vectorizer.fit_transform(corpus)
    scores = cosine_similarity(matrix[-1], matrix[:-1]).flatten()
    best_idx = int(scores.argmax())
    return examples[best_idx].get("target_category"), float(scores[best_idx]), examples[best_idx]

def _infer_asset(text: str, provided_asset: Optional[str]) -> str:
    if provided_asset and provided_asset.strip():
        return provided_asset.strip().lower()
    if any(w in text for w in ("inverter", "solar panel", "solar block")):
        return "solar"
    if any(w in text for w in ("turbine", "gearbox", "blade pitch", "wind gust")):
        return "wind"
    if any(w in text for w in ("spillway", "hydro", "gate maintenance")):
        return "hydro"
    if any(w in text for w in ("grid", "curtailment", "generation dashboard")):
        return "grid"
    return "unknown"

def _infer_severity(text: str, category: str) -> tuple[str, int, str]:
    # Safety-oriented conservative rule: an explicit severe signal should be escalated.
    for phrases, severity, score in SEVERITY_RULES:
        if any(phrase in text for phrase in phrases):
            return severity, score, "Matched a documented severity keyword rule."
    details = CATEGORY_DETAILS.get(category)
    if details:
        return details["severity"], details["severity_score"], "Used the category's documented default severity."
    return "medium", SEVERITY_ORDER["medium"], "Insufficient evidence; defaulted to medium for triage and requires human review."

def analyze_ticket(description: str, asset_type: Optional[str] = None) -> dict:
    clean = _normalise(description or "")
    if len(clean) < 3:
        raise ValueError("Please provide a maintenance description with at least 3 characters.")

    asset = _infer_asset(clean, asset_type)
    category = _rule_category(clean)
    method = "domain_rule"
    evidence = []

    if category:
        matching = [phrase for phrases, cat in CATEGORY_RULES if cat == category for phrase in phrases if phrase in clean]
        evidence.extend(matching[:4])
        similarity = None
    else:
        retrieved_category, similarity, example = _retrieve_category(clean)
        # Only reuse a retrieved category when the similarity is meaningful.
        if retrieved_category and similarity >= 0.12:
            category = retrieved_category
            method = "tfidf_retrieval_fallback"
            evidence = ["Closest bundled ticket description"]
        else:
            category = "needs_review"
            method = "fallback_needs_review"
            evidence = ["No strong domain-rule or retrieval match"]

    severity, severity_score, severity_reason = _infer_severity(clean, category)
    details = CATEGORY_DETAILS.get(category, {
        "root_cause": "Insufficient evidence to identify a likely root cause confidently.",
        "next_action": "Request additional asset details and have the maintenance team review the ticket.",
        "team": "Maintenance triage queue",
    })

    return {
        "asset_type": asset,
        "category": category,
        "severity": severity,
        "severity_score": severity_score,
        "probable_root_cause": details["root_cause"],
        "recommended_next_action": details["next_action"],
        "assigned_team": details["team"],
        "method": method,
        "evidence": evidence,
        "severity_rule": severity_reason,
        "requires_human_review": category == "needs_review" or severity == "critical",
        "limitations": [
            "The bundled dataset contains only six tickets and one example per category.",
            "Rules and retrieved examples are demonstrations, not validated production guidance.",
            "Root causes are hypotheses; a qualified maintenance professional must confirm them.",
        ],
    }
