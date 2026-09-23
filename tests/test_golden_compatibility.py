import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sdna_px import SpatialDNAEngine


class GoldenCompatibilityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = SpatialDNAEngine.from_repo(ROOT)
        cls.obs = json.loads((ROOT / "fixtures" / "job_002.json").read_text(encoding="utf-8"))
        cls.strategy = json.loads((ROOT / "strategies" / "hospitality_operations.json").read_text(encoding="utf-8"))
        cls.golden = json.loads((ROOT / "fixtures" / "job_002_golden_excerpt.json").read_text(encoding="utf-8"))
        cls.payload = cls.engine.compile(cls.obs, cls.strategy)
        cls.projected = {a["atom_id"]: a for a in cls.payload["spatial_atoms_projection"]}

    def test_all_recoverable_golden_rows_match_binding_and_polarity(self):
        checked = 0
        for row in self.golden["golden_rows"]:
            atom_id = row["atom_id"]
            if atom_id not in self.projected:
                continue
            atom = self.projected[atom_id]
            self.assertEqual(atom["binding_class"], row["binding_class"], atom_id)
            self.assertEqual(atom["polarity_zone"], row["polarity"], atom_id)
            checked += 1
        self.assertEqual(checked, 10)

    def test_legacy_missing_ids_are_not_silently_aliased(self):
        missing = [
            row["atom_id"]
            for row in self.golden["golden_rows"]
            if row["atom_id"] not in self.engine.node_by_id
        ]
        self.assertEqual(sorted(missing), ["PS-PRFL-001", "RF-REF-001"])

    def test_reported_aggregate_is_not_misrepresented_as_sheet_rows(self):
        rows = self.golden["golden_rows"]
        direct_rows = sum(r["binding_class"] == "DIRECT_BIND" for r in rows)
        transferable_rows = sum(r["binding_class"] == "TRANSFERABLE_BIND" for r in rows)
        # The preserved sheet excerpt itself has 9/3; the separate bootstrap reports 12/16/16.
        # This assertion intentionally preserves the contradiction instead of normalizing it away.
        self.assertEqual((direct_rows, transferable_rows), (9, 3))
        self.assertEqual(self.golden["expected_counts_reported"]["direct_bind_count"], 12)
        self.assertEqual(self.golden["expected_counts_reported"]["transferable_bind_count"], 16)


if __name__ == "__main__":
    unittest.main()
