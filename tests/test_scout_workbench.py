from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from scout_workbench import (
    CANONICAL_OBSERVATION_CONTRACT_VERSION,
    CANONICAL_OBSERVATION_FIELDS,
    ScoutContractError,
    compile_disks,
    freeze_a4_submission,
    initialize_a3,
    prepare_a5_request,
    process_a2_return,
    record_a5_response,
)
from scripts.run_scout_workbench import load_json_without_duplicate_keys


FIELDS = list(CANONICAL_OBSERVATION_FIELDS)


def scope(disk_id: str = "DSK-000001") -> dict:
    return {
        "disk_id": disk_id,
        "label": "Hospitality leadership",
        "description": "Authorized synthetic test scope",
        "version": "1.0.0",
        "zip": "48226",
        "radius_miles": 25,
        "naics": [{"code": "722511", "label": "Full-Service Restaurants"}],
        "soc": [{"code": "11-9051", "label": "Food Service Managers"}],
        "include": ["general manager"],
        "exclude": ["commission only"],
        "limit": 10,
        "observation_contract": list(FIELDS),
        "classification_provenance": {"authority": "TEST_FIXTURE_ONLY"},
    }


def record(observation_id: str = "OBS-001") -> dict:
    return {
        "Observation_ID": observation_id,
        "Collection_Date": "2026-01-02",
        "Vendor": "Synthetic fixture",
        "Employer": "Example Hospitality",
        "Job_Title": "General Manager",
        "City": "Detroit",
        "State": "MI",
        "ZIP": "48226",
        "Industry": "Hospitality",
        "Employment_Type": "Full-time",
        "Compensation": "$1 synthetic",
        "Source_URL": f"https://example.invalid/jobs/{observation_id}",
        "Duplicate_Count": 0,
    }


def mechanical_path(records: list[dict] | None = None):
    compilation = compile_disks([scope()], compiled_at="2026-01-02T00:00:00Z")
    cartridge = compilation["disks"][0]["cartridge"]
    a2 = process_a2_return(
        cartridge,
        records or [record()],
        runner_id="SIM-001",
        dispatch_id="DSP-001",
        processed_at="2026-01-02T00:01:00Z",
    )
    a3 = initialize_a3(a2, sidecar_uri="memory://fixture", processed_at="2026-01-02T00:02:00Z")
    a4 = freeze_a4_submission(
        cartridge, a2, a3["sidecar"], a3["envelope"], frozen_at="2026-01-02T00:03:00Z"
    )
    request = prepare_a5_request(
        a4, a3["sidecar"], cartridge, criteria_version="TEST-1", intent_version="TEST-1"
    )
    return compilation, cartridge, a2, a3, a4, request


class ScoutWorkbenchTest(unittest.TestCase):
    def test_a1_compiles_one_to_three_and_rejects_four(self):
        for count in (1, 2, 3):
            result = compile_disks([scope(f"DSK-{n:06d}") for n in range(1, count + 1)])
            self.assertEqual(count, result["disk_count"])
            self.assertEqual("NOT_EXECUTED", result["execution_status"])
        with self.assertRaisesRegex(ScoutContractError, "one to three"):
            compile_disks([scope(f"DSK-{n:06d}") for n in range(1, 5)])

    def test_a1_requires_exact_canonical_contract(self):
        invalid = scope()
        invalid["observation_contract"] = FIELDS[:-1]
        with self.assertRaisesRegex(ScoutContractError, "exactly match"):
            compile_disks([invalid])
        reordered = scope()
        reordered["observation_contract"] = FIELDS[::-1]
        with self.assertRaisesRegex(ScoutContractError, "exactly match"):
            compile_disks([reordered])
        duplicate = scope()
        duplicate["observation_contract"][-1] = duplicate["observation_contract"][0]
        with self.assertRaisesRegex(ScoutContractError, "exactly match"):
            compile_disks([duplicate])
        cartridge = compile_disks([scope()])["disks"][0]["cartridge"]
        self.assertEqual(CANONICAL_OBSERVATION_CONTRACT_VERSION, cartridge["machine_payload"]["contract"]["version"])

    def test_a2_preserves_raw_and_rejects_malformed_return(self):
        cartridge = compile_disks([scope()])["disks"][0]["cartridge"]
        malformed = record()
        del malformed["Source_URL"]
        with self.assertRaisesRegex(ScoutContractError, "does not exactly match"):
            process_a2_return(cartridge, [malformed], runner_id="SIM-001", dispatch_id="DSP-001")
        unrecognized = record()
        unrecognized["Unexpected"] = "not permitted"
        with self.assertRaisesRegex(ScoutContractError, "unrecognized"):
            process_a2_return(cartridge, [unrecognized], runner_id="SIM-001", dispatch_id="DSP-001")
        valid = record()
        result = process_a2_return(cartridge, [valid], runner_id="SIM-001", dispatch_id="DSP-001")
        self.assertEqual(valid, result["raw_return"][0])
        self.assertEqual("PASS", result["coherence"]["status"])
        self.assertTrue(result["simulation"])

    def test_cli_loader_rejects_duplicate_json_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate.json"
            path.write_text('{"Observation_ID":"one","Observation_ID":"two"}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate JSON field"):
                load_json_without_duplicate_keys(path)

    def test_a3_identities_are_stable_and_receipts_append_only(self):
        _, cartridge, a2, a3_first, _, _ = mechanical_path()
        a3_second = initialize_a3(a2, sidecar_uri="memory://fixture", processed_at="2026-01-03T00:00:00Z")
        first = a3_first["envelope"]["lookup"]["observations"][0]["observation_uuid"]
        second = a3_second["envelope"]["lookup"]["observations"][0]["observation_uuid"]
        self.assertEqual(first, second)
        self.assertEqual("OBS-001", a3_first["sidecar"]["records"][0]["Observation_ID"])
        self.assertEqual("DSK-000001", cartridge["metadata"]["disk_id"])

    def test_a4_detects_mutated_sidecar_and_bad_pointer(self):
        _, cartridge, a2, a3, _, _ = mechanical_path()
        changed = copy.deepcopy(a3["sidecar"])
        changed["records"][0]["Employer"] = "Altered"
        with self.assertRaisesRegex(ScoutContractError, "SIDECAR_HASH_MISMATCH"):
            freeze_a4_submission(cartridge, a2, changed, a3["envelope"])
        bad_envelope = copy.deepcopy(a3["envelope"])
        bad_envelope["lookup"]["observations"][0]["record_index"] = 99
        with self.assertRaisesRegex(ScoutContractError, "BROKEN_RECORD_INDEX"):
            freeze_a4_submission(cartridge, a2, a3["sidecar"], bad_envelope)

    def test_a4_submission_is_copied_and_hash_reproducible(self):
        _, cartridge, a2, a3, a4, _ = mechanical_path()
        again = freeze_a4_submission(
            cartridge, a2, a3["sidecar"], a3["envelope"], frozen_at="2026-01-02T00:03:00Z"
        )
        self.assertEqual(a4["commitments"]["submission_sha256"], again["commitments"]["submission_sha256"])
        a3["envelope"]["lookup"]["observations"].clear()
        self.assertEqual(1, a4["verification"]["record_count"])

    def test_a5_isolation_and_mixed_release(self):
        records = [record("OBS-001"), record("OBS-002"), record("OBS-003")]
        _, _, _, a3, _, request = mechanical_path(records)
        ids = [item["pointer"]["observation_uuid"] for item in request["observations"]]
        refs = [item["pointer"]["source_key"] for item in request["observations"]]
        response = {
            "reasoner_id": "FIXTURE-REASONER",
            "reasoner_version": "test-only",
            "criteria_version": "TEST-1",
            "dispositions": [
                {"observation_uuid": ids[0], "decision": "ACCEPT", "reason": "Supported fixture", "evidence_refs": [refs[0]], "material_considerations": ["source support"]},
                {"observation_uuid": ids[1], "decision": "REJECT", "reason": "Irrelevant fixture", "evidence_refs": [refs[1]], "material_considerations": ["scope"]},
                {"observation_uuid": ids[2], "decision": "HOLD", "reason": "Uncertain fixture", "evidence_refs": [refs[2]], "material_considerations": ["uncertainty"]},
            ],
        }
        original_envelope = copy.deepcopy(a3["envelope"])
        result = record_a5_response(request, response, a3["envelope"], [], recorded_at="2026-01-02T00:04:00Z")
        self.assertEqual(original_envelope, a3["envelope"])
        self.assertEqual([ids[0]], result["release"]["authorized_observation_uuids"])
        self.assertEqual("AUTHORIZED", result["release"]["status"])
        self.assertEqual(1, len(result["ledger"]))

    def test_rejected_or_invalid_responses_cannot_advance(self):
        _, _, _, a3, _, request = mechanical_path()
        pointer = request["observations"][0]["pointer"]
        reject = {
            "reasoner_id": "FIXTURE-REASONER",
            "reasoner_version": "test-only",
            "criteria_version": "TEST-1",
            "dispositions": [{"observation_uuid": pointer["observation_uuid"], "decision": "REJECT", "reason": "Unsupported", "evidence_refs": [pointer["source_key"]], "material_considerations": ["support"]}],
        }
        result = record_a5_response(request, reject, a3["envelope"], [])
        self.assertEqual("BLOCKED", result["release"]["status"])
        invalid = copy.deepcopy(reject)
        invalid["dispositions"][0]["evidence_refs"] = []
        with self.assertRaises(ScoutContractError):
            record_a5_response(request, invalid, a3["envelope"], [])


if __name__ == "__main__":
    unittest.main()
