from __future__ import annotations

from typing import Iterable

SOFT_SUPPORT_WEIGHTS = {1: 0.25, 2: 0.40}
SOFT_SUPPORT_CEILING = 0.50

def soft_interpretive_support(independent_sources: int) -> float:
    if independent_sources <= 0:
        return 0.0
    return SOFT_SUPPORT_WEIGHTS.get(independent_sources, SOFT_SUPPORT_CEILING)

def objective_authority(*, authoritative_source: bool, contradicted: bool = False) -> float:
    if contradicted:
        return 0.0
    return 1.0 if authoritative_source else 0.0

def contextual_ratio(candidate_value: float, baseline: float, target_anchor: float | None = None) -> float:
    """Semantic magnitude, not evidence confidence."""
    if baseline <= 0:
        raise ValueError("baseline must be > 0")
    if candidate_value < baseline:
        return 0.0
    comparison = target_anchor if target_anchor is not None and target_anchor > 0 else baseline
    return candidate_value / comparison

def hard_gate(candidate_value: float, required_value: float) -> bool:
    return candidate_value >= required_value

def defensible_without_retreat(*, supported: bool, materially_misleading: bool = False) -> bool:
    return bool(supported and not materially_misleading)

def independent_cluster_support(source_ids: Iterable[str]) -> float:
    """Caller supplies sources already determined independent and semantically convergent."""
    return soft_interpretive_support(len(set(source_ids)))
