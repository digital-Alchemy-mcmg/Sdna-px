import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


class AuthorityManifestTest(unittest.TestCase):
    def test_candidate_ledgers_match_pinned_git_blobs(self):
        manifest = json.loads((ROOT / "docs" / "AUTHORITY_MANIFEST.json").read_text(encoding="utf-8"))
        for key in ("candidate_nodes", "candidate_edges"):
            entry = manifest[key]
            path = ROOT / entry["repo_path"]
            self.assertTrue(path.exists(), entry["repo_path"])
            self.assertEqual(git_blob_sha(path), entry["repo_blob_sha"], entry["repo_path"])

    def test_candidate_record_counts_match_authority_manifest(self):
        manifest = json.loads((ROOT / "docs" / "AUTHORITY_MANIFEST.json").read_text(encoding="utf-8"))
        for key in ("candidate_nodes", "candidate_edges"):
            entry = manifest[key]
            path = ROOT / entry["repo_path"]
            rows = [x for x in path.read_text(encoding="utf-8-sig").splitlines() if x.strip()]
            self.assertEqual(len(rows), entry["expected_records"], entry["repo_path"])


if __name__ == "__main__":
    unittest.main()
