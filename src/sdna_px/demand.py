from __future__ import annotations

import re
from typing import Any

from .engine import SpatialDNAError


CATEGORY_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Operational & Shift Leadership", ("operations","operational","shift","floor","foh","boh","dining","labor","service standards")),
    ("Financial & P&L Discipline", ("p&l","prime cost","inventory","cost","margin","financial","sales","reconciliation")),
    ("Workforce Training & Team Development", ("recruit","onboard","train","develop","workforce","retention","team")),
    ("Compliance, Health & Safety Standards", ("compliance","health","safety","food safety","liquor","mlcc","audit","certification")),
    ("Cross-Functional Systems & Guest Retention", ("guest","escalation","service culture","systems","multi-outlet","banquet","retention")),
)


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def _category_for(text: str) -> str:
    t = text.lower()
    scored: list[tuple[int, int, str]] = []
    for idx, (category, terms) in enumerate(CATEGORY_RULES):
        score = sum(1 for term in terms if term in t)
        scored.append((score, -idx, category))
    score, _, category = max(scored)
    return category if score else "Role-Specific Requirement"


def _weight_for(section: str, text: str) -> int:
    s = section.lower()
    t = text.lower()
    if any(x in s for x in ("require", "responsib", "qualification", "must")):
        return 5
    if any(x in t for x in ("required", "must", "responsible for", "minimum")):
        return 5
    if any(x in s for x in ("preferred", "skill", "keyword")):
        return 3
    return 4


def decompose_observation(observation: dict[str, Any]) -> dict[str, Any]:
    """Convert a Scout observation into addressable demand receptors without touching candidate data."""
    if observation.get("contract_version") != "SCOUT_TARGET_OBSERVATION_v1":
        raise SpatialDNAError("DEMAND_DECOMPOSITION_ERROR: expected SCOUT_TARGET_OBSERVATION_v1")

    envelope = observation.get("demand_envelope") or {}
    existing = envelope.get("receptors")
    if existing:
        # Idempotent pass-through for already decomposed, certified packets.
        return observation

    clauses = envelope.get("verbatim_clauses") or []
    if not clauses:
        raise SpatialDNAError("DEMAND_DECOMPOSITION_ERROR: no verbatim_clauses supplied by Scout")

    receptors = []
    for idx, clause in enumerate(clauses, 1):
        text = _normalize_text(str(clause.get("text", "")))
        if not text:
            raise SpatialDNAError(f"DEMAND_DECOMPOSITION_ERROR: empty clause at index {idx}")
        receptors.append({
            "receptor_id": f"D_{idx:02d}",
            "source_clause_id": clause.get("clause_id") or f"REQ-{idx:02d}",
            "category": clause.get("category") or _category_for(text),
            "verbatim_text": text,
            "weight": int(clause.get("weight") or _weight_for(str(clause.get("section", "")), text)),
        })

    out = dict(observation)
    out["demand_envelope"] = dict(envelope)
    out["demand_envelope"]["receptors"] = receptors
    out["demand_envelope"]["decomposition_receipt"] = {
        "mode": "DETERMINISTIC_STRUCTURAL_TAGGING",
        "candidate_data_accessed": False,
        "receptor_count": len(receptors),
        "verbatim_preserved": True,
    }
    return out
