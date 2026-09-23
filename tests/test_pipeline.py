import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sdna_px import SpatialDNAEngine
from sdna_px.demand import decompose_observation
from sdna_px.pipeline import compile_scout_observation


class PipelineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scout = json.loads((ROOT / "fixtures" / "job_002_scout_observation.json").read_text(encoding="utf-8"))
        cls.strategy = json.loads((ROOT / "strategies" / "hospitality_operations.json").read_text(encoding="utf-8"))
        cls.engine = SpatialDNAEngine.from_repo(ROOT)

    def test_scout_decomposition_preserves_all_verbatim_clauses(self):
        out = decompose_observation(self.scout)
        receptors = out["demand_envelope"]["receptors"]
        clauses = self.scout["demand_envelope"]["verbatim_clauses"]
        self.assertEqual(len(receptors), 5)
        self.assertEqual([r["receptor_id"] for r in receptors], ["D_01","D_02","D_03","D_04","D_05"])
        self.assertEqual([r["verbatim_text"] for r in receptors], [c["text"] for c in clauses])
        self.assertFalse(out["demand_envelope"]["decomposition_receipt"]["candidate_data_accessed"])

    def test_full_pipeline_produces_mara_payload(self):
        payload = compile_scout_observation(self.engine, self.scout, self.strategy)
        self.assertEqual(payload["contract_version"], "MARA_LAYOUT_PAYLOAD_v1")
        self.assertEqual(payload["metadata"]["target_job_id"], "JOB-002")
        self.assertEqual(len(payload["demand_envelope"]["receptors"]), 5)
        self.assertEqual(payload["strategy_lock"]["strategy_id"], "HOSPITALITY_OPERATIONS_LEADERSHIP")

    def test_decomposition_is_idempotent(self):
        once = decompose_observation(self.scout)
        twice = decompose_observation(once)
        self.assertEqual(once, twice)


if __name__ == "__main__":
    unittest.main()
