from __future__ import annotations

import copy
import unittest
from pathlib import Path

from mara_c_workbench import (
    MaraCContractError, build_meta_request, construct_c3, finalize_c5,
    render_fixture_html, seal_boundary_c, validate_b5_posture,
    validate_c1_resolution, validate_c2_composition, validate_c4,
)
from scripts.run_mara_b_fixture import run_fixture


ROOT = Path(__file__).resolve().parents[1]


def prism_response(b4, geometry="Dominant Plus Secondary"):
    atom = b4["nodes"][0]["selected_evidence_refs"][0]
    percentages = [40, 25, 15, 10, 10]
    names = ["Sales Headhunter", "Sports Agent", "Discovery Scout", "Independent Staffing-Firm Owner", "Casting Director"]
    return {
        "reasoner_id": "SIMULATED-B5", "reasoner_version": "fixture", "intent_version": "fixture-v1",
        "prisms": {name: {"percentage": percentage, "prominence": "owner" if index == 0 else "support", "evidence_anchors": [atom]} for index, (name, percentage) in enumerate(zip(names, percentages))},
        "owner_prism": names[0], "supporting_prisms": names[1:], "semantic_geometry": geometry,
        "narrative_posture": "Lead with documented production and reinforce transferable operations.",
        "permissible_intensity": "documented", "prohibited_implications": ["No unsupported ownership"],
    }


def pipeline():
    b4 = run_fixture(ROOT)["b4"]
    b5 = validate_b5_posture(b4, prism_response(b4))
    content = []
    for index, node in enumerate(b4["nodes"], 1):
        content.append({"content_id": f"C-{index}", "node_id": node["node_id"], "inclusion": "foreground" if index == 1 else "reinforcement", "evidence_refs": node["selected_evidence_refs"], "semantic_ceiling": node["evidence_ceiling"], "provenance_label": f"Work {index}", "dependencies": []})
    c1 = validate_c1_resolution(b4, b5, {"adapter_id": "SIMULATED-C1", "instruction_version": "fixture", "intent_version": "fixture-v1", "content": content})
    expressions = []
    for item in content:
        expressions.append({"content_id": item["content_id"], "full": f"Documented contribution for {item['content_id']} with bounded responsibility.", "compact": f"Bounded contribution {item['content_id']}.", "agency": "contribution", "chronology": "2024", "association": item["provenance_label"]})
    c2 = validate_c2_composition(c1, {"adapter_id": "SIMULATED-C2", "instruction_version": "fixture", "intent_version": "fixture-v1", "expressions": expressions})
    registry = {"registry_version": "fixture-v1", "surface": {"width_pt": 612, "height_pt": 792, "margin_pt": 54, "line_height_pt": 12, "avg_char_width_pt": 6, "max_pages": 1}, "layout_families": {"Single Dominant": "single-center", "Dual Dominant": "dual-center", "Dominant Plus Secondary": "lead-plus-support", "Distributed": "distributed"}}
    c3 = construct_c3(b5, c1, c2, registry, {item["content_id"]: "full" for item in content})
    planes = {name: True for name in ("evidence", "prism", "expression", "structural", "chronological", "anti-pattern", "geometry", "extraction", "completeness", "provenance")}
    c4 = validate_c4(c3, {"validator_id": "SIMULATED-C4", "validator_version": "fixture", "intent_version": "fixture-v1", "disposition": "PASS", "planes": planes, "findings": []})
    request = build_meta_request(c3, c4, b5)
    meta = render_fixture_html(request)
    c5 = finalize_c5(c3, c4, request, meta)
    return b4, b5, c1, c2, registry, c3, c4, request, meta, c5


class MaraCWorkbenchTest(unittest.TestCase):
    def test_b5_requires_locked_five_prisms_totaling_100(self):
        b4 = run_fixture(ROOT)["b4"]
        valid = validate_b5_posture(b4, prism_response(b4))
        self.assertEqual(5, len(valid["prisms"]))
        invalid = prism_response(b4)
        invalid["prisms"]["Sales Headhunter"]["percentage"] = 39
        with self.assertRaisesRegex(MaraCContractError, "100"):
            validate_b5_posture(b4, invalid)

    def test_b5_rejects_unaudited_anchor_and_supports_all_geometries(self):
        b4 = run_fixture(ROOT)["b4"]
        invalid = prism_response(b4)
        invalid["prisms"]["Casting Director"]["evidence_anchors"] = ["NOT-AUDITED"]
        with self.assertRaisesRegex(MaraCContractError, "outside"):
            validate_b5_posture(b4, invalid)
        for geometry in ("Single Dominant", "Dual Dominant", "Dominant Plus Secondary", "Distributed"):
            self.assertEqual(geometry, validate_b5_posture(b4, prism_response(b4, geometry))["semantic_geometry"])

    def test_boundary_c_seals_sidecar_and_appends_envelope(self):
        b4, b5, *_ = pipeline()
        envelope = {"schema": "SCOUT_TRAVELING_ENVELOPE_v1", "state": {}, "receipts": [{"stage": "B4"}]}
        original = copy.deepcopy(envelope)
        sealed = seal_boundary_c(b4, b5, envelope)
        self.assertEqual(original, envelope)
        self.assertFalse(sealed["boundary_c"]["sidecar_active"])

    def test_c1_preserves_evidence_and_ceiling(self):
        b4, b5, c1, *_ = pipeline()
        self.assertEqual(b4["ledger_sha256"], c1["b4_ledger_sha256"])
        response = {"adapter_id": "bad", "instruction_version": "v", "intent_version": "v", "content": [copy.deepcopy(c1["content"][0])]}
        response["content"][0]["semantic_ceiling"] = "inflated"
        with self.assertRaisesRegex(MaraCContractError, "ceiling"):
            validate_c1_resolution(b4, b5, response)

    def test_c2_exactly_covers_traveling_content(self):
        _, _, c1, *_ = pipeline()
        with self.assertRaisesRegex(MaraCContractError, "exactly cover"):
            validate_c2_composition(c1, {"adapter_id": "bad", "instruction_version": "v", "intent_version": "v", "expressions": []})

    def test_c3_rejects_overflow_and_unregistered_geometry(self):
        _, b5, c1, c2, registry, *_ = pipeline()
        small = copy.deepcopy(registry)
        small["surface"]["height_pt"] = 100
        with self.assertRaisesRegex(MaraCContractError, "OVERFLOW"):
            construct_c3(b5, c1, c2, small, {item["content_id"]: "full" for item in c1["content"]})
        missing = copy.deepcopy(registry)
        del missing["layout_families"][b5["semantic_geometry"]]
        with self.assertRaisesRegex(MaraCContractError, "layout family"):
            construct_c3(b5, c1, c2, missing, {item["content_id"]: "full" for item in c1["content"]})

    def test_c3_preserves_semantic_order_and_flags_render_inspection(self):
        *_, c3, c4, request, meta, c5 = pipeline()
        self.assertEqual("foreground", c3["ordered_content"][0]["inclusion"])
        self.assertEqual("REQUIRES_RENDER_INSPECTION", c3["anti_pattern_audit"]["responsive_print_distortion"])
        self.assertEqual("NOT_RUN", c5["geometry_inspection"])

    def test_c4_requires_all_independent_planes(self):
        *_, c3, _, _, _, _ = pipeline()
        with self.assertRaisesRegex(MaraCContractError, "every mandatory"):
            validate_c4(c3, {"validator_id": "bad", "validator_version": "v", "intent_version": "v", "disposition": "PASS", "planes": {"evidence": True}, "findings": []})

    def test_c5_requires_c4_and_rejects_renderer_rewrite(self):
        _, _, _, _, _, c3, c4, request, meta, _ = pipeline()
        bad_c4 = copy.deepcopy(c4)
        bad_c4["disposition"] = "REWORK_REQUIRED"
        with self.assertRaisesRegex(MaraCContractError, "approval"):
            build_meta_request(c3, bad_c4, pipeline()[1])
        changed = copy.deepcopy(meta)
        changed["content"][0]["text"] = "rewritten"
        with self.assertRaisesRegex(MaraCContractError, "rewriting"):
            finalize_c5(c3, c4, request, changed)

    def test_c5_outputs_have_distinct_reproducible_commitments(self):
        *_, c5 = pipeline()
        again = pipeline()[-1]
        self.assertNotEqual(c5["markdown_sha256"], c5["html_sha256"])
        self.assertEqual(c5["package_sha256"], again["package_sha256"])


if __name__ == "__main__":
    unittest.main()
