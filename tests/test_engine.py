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
        cls.payload = cls.engine.compile(cls.observation)

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
        second = self.engine.compile(self.observation)
        self.assertEqual(self.payload, second)
        self.assertEqual(self.payload["run_fingerprint_sha256"], second["run_fingerprint_sha256"])

    def test_work_history_is_active_for_job_002(self):
        active = [x["plane_id"] for x in self.payload["spatial_configuration"]["active_lateral_planes"]]
        self.assertIn("plane_02", active)

    def test_historical_baseline_is_comparison_not_override(self):
        comparison = self.payload["historical_baseline_comparison"]
        self.assertEqual(comparison["baseline_status"], "SOURCE_REPORTED_NOT_ASSUMED_AS_EXECUTION_TRUTH")
        self.assertIn("derived", comparison)


if __name__ == "__main__":
    unittest.main()
