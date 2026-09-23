import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sdna_px import SpatialDNAEngine


class SpatialDNATest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = SpatialDNAEngine.from_repo(ROOT)
        cls.observation = json.loads((ROOT / "fixtures" / "job_002.json").read_text(encoding="utf-8"))
        cls.strategy = json.loads((ROOT / "strategies" / "hospitality_operations.json").read_text(encoding="utf-8"))
        cls.payload = cls.engine.compile(cls.observation, cls.strategy)

    def test_recovered_graph_cardinality(self):
        self.assertEqual(len(self.engine.nodes), 44)
        self.assertEqual(len(self.engine.edges), 11)

    def test_edge_endpoints_exist(self):
        ids = {n["atom_id"] for n in self.engine.nodes}
        for edge in self.engine.edges:
            self.assertIn(edge["source"], ids)
            self.assertIn(edge["target"], ids)

    def test_projection_evaluates_all_atoms(self):
        atoms = self.payload["spatial_atoms_projection"]
        self.assertEqual(len(atoms), 44)
        self.assertEqual(self.payload["spatial_configuration"]["counts"]["total_atoms_evaluated"], 44)

    def test_coordinates_are_bounded(self):
        for atom in self.payload["spatial_atoms_projection"]:
            self.assertGreaterEqual(atom["x"], -10)
            self.assertLessEqual(atom["x"], 10)
            self.assertGreaterEqual(atom["y"], -5)
            self.assertLessEqual(atom["y"], 5)
            self.assertGreaterEqual(atom["z"], -10)
            self.assertLessEqual(atom["z"], 10)

    def test_geometric_radius_is_geometry(self):
        for atom in self.payload["spatial_atoms_projection"]:
            expected = (atom["x"] ** 2 + atom["z"] ** 2) ** 0.5
            self.assertAlmostEqual(atom["geometric_radius"], expected, places=5)

    def test_conflicted_or_unresolved_never_reaches_ceiling(self):
        forbidden = {"CONFLICTED", "UNRESOLVED", "PROVISIONAL"}
        for atom in self.payload["spatial_atoms_projection"]:
            if atom["evidence_state"] in forbidden:
                self.assertEqual(atom["polarity_zone"], "FLOOR")

    def test_nonbinds_are_not_authorized_claims(self):
        claim_ids = {c["atom_id"] for c in self.payload["normalized_projection"]["claims"]}
        for atom in self.payload["spatial_atoms_projection"]:
            if atom["binding_class"] == "NON_BIND":
                self.assertNotIn(atom["atom_id"], claim_ids)

    def test_claims_cannot_strengthen_source_atoms(self):
        by_id = {n["atom_id"]: n for n in self.engine.nodes}
        for claim in self.payload["normalized_projection"]["claims"]:
            source = by_id[claim["atom_id"]]
            self.assertEqual(claim["authorized_expression"], source["proposition"])
            self.assertEqual(claim["semantic_ceiling"], source["semantic_ceiling"])
            self.assertEqual(claim["provenance"], source["evidence_provenance"])
            self.assertEqual(
                claim["rendered_with_trace"],
                f"{source['proposition']} [Bound: {source['atom_id']}]",
            )

    def test_replay_is_deterministic(self):
        second = self.engine.compile(self.observation, self.strategy)
        self.assertEqual(self.payload, second)
        self.assertEqual(self.payload["run_fingerprint_sha256"], second["run_fingerprint_sha256"])

    def test_work_history_is_active_for_job_002(self):
        active = [x["plane_id"] for x in self.payload["spatial_configuration"]["active_lateral_planes"]]
        self.assertEqual(active, ["plane_02", "plane_01", "plane_06", "plane_05"])
        self.assertEqual(self.payload["spatial_configuration"]["counts"]["non_bind_count"], 16)

    def test_historical_baseline_is_comparison_not_override(self):
        comparison = self.payload["historical_baseline_comparison"]
        self.assertEqual(comparison["baseline_status"], "SOURCE_REPORTED_NOT_ASSUMED_AS_EXECUTION_TRUTH")
        self.assertIn("derived", comparison)

    def test_semantic_match_radius_uses_recovered_contract(self):
        for atom in self.payload["spatial_atoms_projection"]:
            expected = min(10.0, max(3.0, 11.0 - atom["relevance"] * 7.0))
            self.assertAlmostEqual(atom["match_radius"], expected, places=6)

    def test_angular_azimuth_is_injected(self):
        active = {p["plane_id"] for p in self.payload["spatial_configuration"]["active_lateral_planes"]}
        for atom in self.payload["spatial_atoms_projection"]:
            if atom["plane_id"] in active:
                self.assertIsNotNone(atom["angular_azimuth_degrees"])
                self.assertGreaterEqual(atom["angular_azimuth_degrees"], 0.0)
                self.assertLess(atom["angular_azimuth_degrees"], 360.0)
            else:
                self.assertIsNone(atom["angular_azimuth_degrees"])

    def test_observation_provenance_survives_payload(self):
        self.assertEqual(self.payload["provenance"], self.observation["provenance"])

    def test_dynamic_layout_contract_is_emitted(self):
        layout = self.payload["dynamic_layout_elements"]
        self.assertEqual(layout["persona_surface"], self.strategy["persona_surface"])
        ids = [c["container_id"] for c in layout["layout_containers"]]
        self.assertEqual(ids, ["HEADER", "EXECUTIVE_PROJECTION", "TARGETED_WORK_HISTORY", "COMPETENCY_MATRIX"])

    def test_layout_bound_atoms_exist_and_floor_is_excluded_from_projection_sections(self):
        atom_by_id = {a["atom_id"]: a for a in self.payload["spatial_atoms_projection"]}
        layout = self.payload["dynamic_layout_elements"]
        containers = {c["container_id"]: c for c in layout["layout_containers"]}
        for atom_id in containers["EXECUTIVE_PROJECTION"]["bound_atoms"]:
            self.assertIn(atom_id, atom_by_id)
            self.assertNotEqual(atom_by_id[atom_id]["polarity_zone"], "FLOOR")
        for role in containers["TARGETED_WORK_HISTORY"]["roles"]:
            for atom_id in role["bound_atoms"]:
                self.assertIn(atom_id, atom_by_id)
                self.assertNotEqual(atom_by_id[atom_id]["polarity_zone"], "FLOOR")
        for atom_id in containers["COMPETENCY_MATRIX"]["bound_atoms"]:
            self.assertIn(atom_id, atom_by_id)
            self.assertNotEqual(atom_by_id[atom_id]["polarity_zone"], "FLOOR")

    def test_nonbind_has_explicit_non_invented_suppression_signature(self):
        for atom in self.payload["spatial_atoms_projection"]:
            sig = atom["suppression_signature"]
            if atom["binding_class"] == "NON_BIND":
                self.assertEqual(sig["mode"], "NO_POSITIVE_BIND")
                self.assertEqual(sig["triggered_constraints"], [])
            else:
                self.assertIsNone(sig)


if __name__ == "__main__":
    unittest.main()
