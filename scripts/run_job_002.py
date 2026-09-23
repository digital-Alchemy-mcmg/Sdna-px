from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sdna_px import SpatialDNAEngine

obs = json.loads((ROOT / "fixtures" / "job_002.json").read_text(encoding="utf-8"))
strategy = json.loads((ROOT / "strategies" / "hospitality_operations.json").read_text(encoding="utf-8"))
payload = SpatialDNAEngine.from_repo(ROOT).compile(obs, strategy)
out = ROOT / "artifacts" / "job_002_projection.json"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"wrote {out}")
print(json.dumps(payload["spatial_configuration"]["counts"], indent=2))
print("active_planes:", [p["plane_id"] for p in payload["spatial_configuration"]["active_lateral_planes"]])
print("fingerprint:", payload["run_fingerprint_sha256"])
