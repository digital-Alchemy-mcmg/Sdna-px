from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from mara_b_workbench import (
    admit_boundary_b, build_b2_tree, prepare_b3_candidates, prepare_b4_requests,
    reconcile_b4, record_b3_selection, validate_b1_decomposition,
)


SOURCE = "Restaurant General Manager. Must lead daily operations. P&L experience preferred. Apply at careers@example.invalid."
OBSERVATION_UUID = "70fe2e30-fc27-51b5-b49d-81d186c7cc4f"


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def run_fixture(repo_root: Path) -> dict:
    sidecar = {"sidecar_id": "SID-B-FIXTURE", "records": [{"Observation_ID": "OBS-B-FIXTURE", "Source_URL": "https://example.invalid/job"}]}
    release = {
        "schema": "SCOUT_B1_RELEASE_v1", "status": "AUTHORIZED", "destination": "B1",
        "a4_submission_sha256": "a" * 64, "a5_decision_id": "A5-FIXTURE", "a5_disposition_sha256": "b" * 64,
        "authorized_observation_uuids": [OBSERVATION_UUID],
        "sidecar_lookup": [{"observation_uuid": OBSERVATION_UUID, "observation_id": "OBS-B-FIXTURE", "record_index": 0, "source_key": "https://example.invalid/job"}],
    }
    release["release_sha256"] = digest(release)
    source = {"observation_uuid": OBSERVATION_UUID, "source_text": SOURCE, "source_ref": "fixture://job", "source_sha256": digest(SOURCE)}
    admission = admit_boundary_b(release, sidecar, source)

    primitive_specs = [("P-1", "Must lead daily operations.", "hard", "duty"), ("P-2", "P&L experience preferred.", "soft", "qualification")]
    primitives = []
    for primitive_id, text, marker, kind in primitive_specs:
        start = SOURCE.index(text)
        primitives.append({"primitive_id": primitive_id, "text": text, "marker": marker, "kind": kind, "span_start": start, "span_end": start + len(text), "qualifiers": []})
    b1 = validate_b1_decomposition(admission, {
        "adapter_id": "SIMULATED-TARGET-DECOMPOSER", "instruction_version": "fixture-v1", "intent_version": "fixture-v1",
        "application_routing": {"origin": "fixture://job", "destination": "careers@example.invalid"}, "primitives": primitives, "ambiguities": [],
    })
    b2 = build_b2_tree(b1, {
        "adapter_id": "SIMULATED-TARGET-CLASSIFIER", "instruction_version": "fixture-v1", "intent_version": "fixture-v1",
        "domains": {"P-1": "Operations Leadership", "P-2": "Financial Discipline"},
    })
    candidates = prepare_b3_candidates(str(repo_root), b2, {
        "adapter_id": "SIMULATED-PLANE-ROUTER", "instruction_version": "fixture-v1", "intent_version": "fixture-v1",
        "planes_by_node": {node["node_id"]: ["plane_02"] for node in b2["nodes"]},
    })
    selections = {}
    for node in b2["nodes"]:
        eligible = candidates["candidates_by_node"][node["node_id"]]
        selected = eligible[0]
        selections[node["node_id"]] = {
            "considered_atom_ids": [atom["atom_id"] for atom in eligible[:2]], "selected_atom_ids": [selected["atom_id"]],
            "proposition": selected["proposition"], "rationale": "Simulated selection for interface verification",
        }
    b3 = record_b3_selection(candidates, {"adapter_id": "SIMULATED-EVIDENCE-SELECTOR", "instruction_version": "fixture-v1", "intent_version": "fixture-v1", "selections": selections})
    requests = prepare_b4_requests(str(repo_root), b2, b3, intent_version="fixture-v1", criteria_version="fixture-v1")
    responses = []
    for request in requests:
        atom = request["selected_evidence"][0]
        responses.append({
            "node_id": request["node_id"], "auditor_id": "SIMULATED-TRUTH-AUDITOR", "auditor_version": "fixture-only",
            "criteria_version": "fixture-v1", "intent_version": "fixture-v1", "disposition": "PASS",
            "reason": "Synthetic response used only to verify the interface", "source_refs": [atom["evidence_provenance"]],
            "evidence_atom_refs": [atom["atom_id"]], "evidence_ceiling": atom["semantic_ceiling"],
            "verified_proposition": atom["proposition"], "unsupported_scope": [], "hard_gate_satisfied": True,
            "decision_trace": {"material_evidence": [atom["atom_id"]], "selected_conclusion": "PASS"},
        })
    b4 = reconcile_b4(b2, b3, requests, responses)
    return {"boundary_b": admission, "b1": b1, "b2": b2, "b3": b3, "b4_requests": requests, "b4": b4, "simulation": True}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    outputs = run_fixture(args.repo_root)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, value in outputs.items():
        if isinstance(value, (dict, list)):
            (args.output_dir / f"{name}.json").write_text(json.dumps(value, indent=2) + "\n")
    print(json.dumps({"status": outputs["b4"]["handoff"]["status"], "simulation": True, "b5_executed": False, "node_count": len(outputs["b4"]["nodes"])}, indent=2))


if __name__ == "__main__":
    main()
