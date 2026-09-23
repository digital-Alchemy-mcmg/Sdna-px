import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sdna_px.batch import compile_batch


class BatchTest(unittest.TestCase):
    def test_batch_compiles_multiple_observations_and_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            inp = td / "in"
            out = td / "out"
            inp.mkdir()
            source = (ROOT / "fixtures" / "job_002.json").read_text(encoding="utf-8")
            one = json.loads(source)
            two = json.loads(source)
            two["observation_id"] = "JOB-002-B"
            (inp / "a.json").write_text(json.dumps(one), encoding="utf-8")
            (inp / "b.json").write_text(json.dumps(two), encoding="utf-8")

            manifest = compile_batch(
                ROOT,
                inp,
                out,
                ROOT / "strategies" / "hospitality_operations.json",
            )
            self.assertEqual(manifest["input_count"], 2)
            self.assertEqual(manifest["success_count"], 2)
            self.assertEqual(manifest["failure_count"], 0)
            self.assertTrue((out / "JOB-002.projection.json").exists())
            self.assertTrue((out / "JOB-002-B.projection.json").exists())
            self.assertTrue((out / "batch_manifest.json").exists())


if __name__ == "__main__":
    unittest.main()
