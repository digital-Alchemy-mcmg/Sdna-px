"""Portable MARA Segment B mechanical boundaries."""

from .core import (
    MaraBContractError,
    append_b_receipt,
    admit_boundary_b,
    build_b2_tree,
    prepare_b3_candidates,
    record_b3_selection,
    prepare_b4_requests,
    reconcile_b4,
    validate_b1_decomposition,
)

__all__ = [
    "MaraBContractError", "admit_boundary_b", "validate_b1_decomposition",
    "append_b_receipt",
    "build_b2_tree", "prepare_b3_candidates", "record_b3_selection",
    "prepare_b4_requests", "reconcile_b4",
]
