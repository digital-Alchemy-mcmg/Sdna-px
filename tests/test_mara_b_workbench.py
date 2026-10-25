from __future__ import annotations

import copy
import hashlib
import json
import re
import unittest
from pathlib import Path

from mara_b_workbench import (
    MaraBContractError,
    append_b_receipt,
    admit_boundary_b,
    build_b2_tree,
    prepare_b3_candidates,
    prepare_b4_requests,
    reconcile_b4,
    record_b3_selection,
    validate_b1_decomposition,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE = "Restaurant General Manager. Must lead daily operations. P&L experience preferred. Apply at careers@example.invalid."
OBS_UUID = "70fe2e30-fc27-51b5-b49d-81d186c7cc4f"


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def boundary_inputs():
    sidecar = {"sidecar_id": "SID-TEST", "records": [{"Observation_ID": "OBS-TEST", "Source_URL": "https://example.invalid/job"}]}
    release = {
        "schema": "SCOUT_B1_RELEASE_v1", "status": "AUTHORIZED", "destination": "B1",
        "a4_submission_sha256": "a" * 64, "a5_decision_id": "A5-TEST", "a5_disposition_sha256": "b" * 64,
        "authorized_observation_uuids": [OBS_UUID],
        "sidecar_lookup": [{"observation_uuid": OBS_UUID, "observation_id": "OBS-TEST", "record_index": 0, "source_key": "https://example.invalid/job"}],
    }
    release["release_sha256"] = digest(release)
    source = {"observation_uuid": OBS_UUID, "source_text": SOURCE, "source_ref": "fixture://job", "source_sha256": digest(SOURCE)}
    return release, sidecar, source


def b1_response(destination="careers@example.invalid"):
    parts = [
        ("P-1", "Must lead daily operations.", "hard", "duty"),
        ("P-2", "P&L experience preferred.", "soft", "qualification"),
    ]
    primitives = []
    for pid, text, marker, kind in parts:
        start = SOURCE.index(text)
        primitives.append({"primitive_id": pid, "text": text, "marker": marker, "kind": kind, "span_start": start, "span_end": start + len(text), "qualifiers": []})
    return {
        "adapter_id": "FIXTURE-TARGET-DECOMPOSER", "instruction_version": "test-v1", "intent_version": "test-v1",
        "application_routing": {"origin": "fixture://job", "destination": destination}, "primitives": primitives, "ambiguities": [],
    }


def stages_through_b3():
    release, sidecar, source = boundary_inputs()
    admission = admit_boundary_b(release, sidecar, source)
    b1 = validate_b1_decomposition(admission, b1_response())
    classifications = {
        "adapter_id": "FIXTURE-CLASSIFIER", "instruction_version": "test-v1", "intent_version": "test-v1",
        "domains": {"P-1": "Operations Leadership", "P-2": "Financial Discipline"},
    }
    tree = build_b2_tree(b1, classifications)
    routes = {
        "adapter_id": "FIXTURE-PLANE-ROUTER", "instruction_version": "test-v1", "intent_version": "test-v1",
        "planes_by_node": {node["node_id"]: ["plane_02"] for node in tree["nodes"]},
    }
    candidates = prepare_b3_candidates(str(ROOT), tree, routes)
    selections = {}
    for node in tree["nodes"]:
        atom = candidates["candidates_by_node"][node["node_id"]][0]
        selections[node["node_id"]] = {
            "considered_atom_ids": [item["atom_id"] for item in candidates["candidates_by_node"][node["node_id"]][:2]],
            "selected_atom_ids": [atom["atom_id"]], "proposition": atom["proposition"], "rationale": "Synthetic adapter selection for audit",
        }
    b3 = record_b3_selection(candidates, {"adapter_id": "FIXTURE-SELECTOR", "instruction_version": "test-v1", "intent_version": "test-v1", "selections": selections})
    requests = prepare_b4_requests(str(ROOT), tree, b3, intent_version="test-v1", criteria_version="test-v1")
    return admission, b1, tree, candidates, b3, requests


def response_for(request, disposition="PASS"):
    atom = request["selected_evidence"][0]
    return {
        "node_id": request["node_id"], "auditor_id": "FIXTURE-TRUTH-AUDITOR", "auditor_version": "test-only",
        "criteria_version": request["criteria_version"], "intent_version": request["intent_version"],
        "disposition": disposition, "reason": "Synthetic evidence-grounded fixture decision",
        "source_refs": [atom["evidence_provenance"]], "evidence_atom_refs": [atom["atom_id"]],
        "evidence_ceiling": atom["semantic_ceiling"], "verified_proposition": atom["proposition"],
        "unsupported_scope": [], "hard_gate_satisfied": disposition == "PASS",
        "decision_trace": {"material_evidence": [atom["atom_id"]], "selected_conclusion": disposition},
    }


class MaraBWorkbenchTest(unittest.TestCase):
    def test_boundary_b_admits_valid_release_and_rejects_tampering(self):
        release, sidecar, source = boundary_inputs()
        admitted = admit_boundary_b(release, sidecar, source)
        self.assertFalse(admitted["candidate_data_accessed"])
        release["authorized_observation_uuids"] = []
        with self.assertRaises(MaraBContractError):
            admit_boundary_b(release, sidecar, source)

    def test_b1_is_candidate_blind_and_validates_source_spans(self):
        release, sidecar, source = boundary_inputs()
        admission = admit_boundary_b(release, sidecar, source)
        b1 = validate_b1_decomposition(admission, b1_response())
        self.assertFalse(b1["candidate_data_accessed"])
        invalid = b1_response()
        invalid["primitives"][0]["span_start"] += 1
        with self.assertRaisesRegex(MaraBContractError, "source span"):
            validate_b1_decomposition(admission, invalid)

    def test_b1_records_origin_destination_malform(self):
        release, sidecar, source = boundary_inputs()
        admission = admit_boundary_b(release, sidecar, source)
        result = validate_b1_decomposition(admission, b1_response(destination=""))
        self.assertEqual("MALFORMED", result["status"])
        self.assertEqual("B1", result["malforms"][0]["stage"])

    def test_b2_addresses_are_stable_lowercase_and_complete(self):
        _, b1, tree, _, _, _ = stages_through_b3()
        self.assertEqual(2, len(tree["nodes"]))
        self.assertTrue(all(re.fullmatch(r"d\.\d+\.\d+", node["address"]) for node in tree["nodes"]))
        again = build_b2_tree(b1, {"adapter_id": "FIXTURE", "instruction_version": "v1", "intent_version": "v1", "domains": {"P-1": "Operations Leadership", "P-2": "Financial Discipline"}})
        self.assertEqual([n["address"] for n in tree["nodes"]], [n["address"] for n in again["nodes"]])

    def test_b3_is_target_driven_and_separates_considered_selected(self):
        _, _, tree, candidates, b3, _ = stages_through_b3()
        self.assertEqual({n["node_id"] for n in tree["nodes"]}, set(candidates["candidates_by_node"]))
        for record in b3["records"]:
            self.assertTrue(set(record["selected_atom_ids"]) < set(record["considered_atom_ids"]))
            self.assertEqual("NOT_AUDITED", record["truth_status"])

    def test_b3_rejects_selection_outside_considered_evidence(self):
        _, _, _, candidates, _, _ = stages_through_b3()
        selections = {node["node_id"]: {"considered_atom_ids": [], "selected_atom_ids": ["NOT-REAL"], "proposition": "Invented"} for node in candidates["nodes"]}
        with self.assertRaises(MaraBContractError):
            record_b3_selection(candidates, {"adapter_id": "FIXTURE", "instruction_version": "v1", "intent_version": "v1", "selections": selections})

    def test_b4_rejects_unselected_evidence_and_preserves_hard_gate(self):
        _, _, tree, _, b3, requests = stages_through_b3()
        responses = [response_for(request) for request in requests]
        responses[0]["evidence_atom_refs"] = ["UNSELECTED"]
        with self.assertRaisesRegex(MaraBContractError, "unselected"):
            reconcile_b4(tree, b3, requests, responses)
        responses = [response_for(request, "QUALIFIED") for request in requests]
        responses[0]["hard_gate_satisfied"] = True
        with self.assertRaisesRegex(MaraBContractError, "hard requirement"):
            reconcile_b4(tree, b3, requests, responses)

    def test_b4_reconciles_pass_bounded_unresolved_and_contradicted(self):
        _, _, tree, _, b3, requests = stages_through_b3()
        for disposition in ("PASS", "QUALIFIED", "UNRESOLVED", "CONTRADICTED"):
            responses = [response_for(request, disposition) for request in requests]
            for response, request in zip(responses, requests):
                if disposition != "PASS" and request["marker"] == "hard":
                    response["hard_gate_satisfied"] = False
            ledger = reconcile_b4(tree, b3, requests, responses)
            self.assertTrue(ledger["reconciliation"]["all_nodes_accounted_for"])
            self.assertFalse(ledger["handoff"]["b5_executed"])

    def test_b4_requires_exactly_one_record_per_node(self):
        _, _, tree, _, b3, requests = stages_through_b3()
        with self.assertRaisesRegex(MaraBContractError, "exactly one"):
            reconcile_b4(tree, b3, requests, [response_for(requests[0])])

    def test_segment_b_receipts_are_append_only_and_reference_only(self):
        envelope = {"schema": "SCOUT_TRAVELING_ENVELOPE_v1", "state": {"current_stage": "A5"}, "receipts": [{"stage": "A5"}]}
        original = copy.deepcopy(envelope)
        updated = append_b_receipt(envelope, stage="B1", artifact_ref="sha256:test", status="READY_FOR_B2")
        self.assertEqual(original, envelope)
        self.assertEqual(2, len(updated["receipts"]))
        self.assertFalse(updated["segment_b"]["full_evidence_embedded"])


if __name__ == "__main__":
    unittest.main()
