from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sdna_px import SpatialDNAEngine
from sdna_px.pipeline import compile_scout_observation


def main() -> None:
    p = argparse.ArgumentParser(description="Scout observation -> demand receptors -> Spatial DNA -> MARA layout payload")
    p.add_argument("observation", type=Path)
    p.add_argument("--strategy", type=Path, required=True)
    p.add_argument("-o", "--output", type=Path, required=True)
    args = p.parse_args()

    try:
        observation = json.loads(args.observation.read_text(encoding="utf-8"))
        strategy = json.loads(args.strategy.read_text(encoding="utf-8"))
        payload = compile_scout_observation(SpatialDNAEngine.from_repo(ROOT), observation, strategy)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps({
            "status": "OK",
            "job_id": payload["metadata"]["target_job_id"],
            "receptors": len(payload["demand_envelope"]["receptors"]),
            "fingerprint": payload["run_fingerprint_sha256"],
            "output": str(args.output),
        }, indent=2))
    except Exception as exc:
        print(json.dumps({
            "status": "ERROR",
            "error_code": "HARNESS_VALIDATION_ERROR",
            "stage": "SCOUT_TO_MARA_PIPELINE",
            "details": str(exc),
        }, indent=2))
        raise SystemExit(2)


if __name__ == "__main__":
    main()
