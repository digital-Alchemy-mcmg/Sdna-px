from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .engine import SpatialDNAEngine, SpatialDNAError
from .pipeline import compile_scout_observation


def compile_batch(
    repo_root: Path,
    input_dir: Path,
    output_dir: Path,
    strategy_path: Path,
) -> dict[str, Any]:
    strategy = json.loads(strategy_path.read_text(encoding="utf-8"))
    engine = SpatialDNAEngine.from_repo(repo_root)
    output_dir.mkdir(parents=True, exist_ok=True)

    jobs = []
    failures = []
    for path in sorted(input_dir.glob("*.json")):
        try:
            observation = json.loads(path.read_text(encoding="utf-8"))
            payload = compile_scout_observation(engine, observation, strategy)
            job_id = payload["metadata"]["target_job_id"] or path.stem
            out = output_dir / f"{job_id}.projection.json"
            body = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
            out.write_text(body, encoding="utf-8")
            jobs.append({
                "source": path.name,
                "job_id": job_id,
                "output": out.name,
                "run_fingerprint_sha256": payload["run_fingerprint_sha256"],
                "counts": payload["spatial_configuration"]["counts"],
            })
        except Exception as exc:
            failures.append({
                "source": path.name,
                "error_type": type(exc).__name__,
                "error": str(exc),
            })

    manifest_core = {
        "contract_version": "SDNA_BATCH_RECEIPT_v1",
        "strategy_id": strategy["strategy_id"],
        "input_count": len(list(input_dir.glob("*.json"))),
        "success_count": len(jobs),
        "failure_count": len(failures),
        "jobs": jobs,
        "failures": failures,
    }
    canonical = json.dumps(manifest_core, sort_keys=True, separators=(",", ":")).encode("utf-8")
    manifest = dict(manifest_core)
    manifest["batch_fingerprint_sha256"] = hashlib.sha256(canonical).hexdigest()
    (output_dir / "batch_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return manifest
