from __future__ import annotations

import argparse
import json
from pathlib import Path

from scout_workbench import (
    compile_disks,
    freeze_a4_submission,
    initialize_a3,
    prepare_a5_request,
    process_a2_return,
)


def load_json_without_duplicate_keys(path: Path):
    def reject_duplicates(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON field {key!r} in {path}")
            result[key] = value
        return result

    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicates)


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the deterministic Scout A1-A4 path and prepare an A5 request.")
    parser.add_argument("scope", type=Path)
    parser.add_argument("records", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--runner-id", default="SIM-001")
    parser.add_argument("--dispatch-id", default="DSP-SIM-001")
    parser.add_argument("--criteria-version", default="SCOUT-A5-CRITERIA-v1")
    parser.add_argument("--intent-version", default="SCOUT-ETHOS-v1")
    parser.add_argument("--adapter", choices=("SIMULATED",), default="SIMULATED")
    args = parser.parse_args()

    scope = load_json_without_duplicate_keys(args.scope)
    records = load_json_without_duplicate_keys(args.records)
    compilation = compile_disks([scope])
    cartridge = compilation["disks"][0]["cartridge"]
    a2 = process_a2_return(
        cartridge,
        records,
        runner_id=args.runner_id,
        dispatch_id=args.dispatch_id,
        adapter=args.adapter,
    )
    a3 = initialize_a3(a2, sidecar_uri="local://artifacts/scout/sidecar.json")
    a4 = freeze_a4_submission(cartridge, a2, a3["sidecar"], a3["envelope"])
    request = prepare_a5_request(
        a4,
        a3["sidecar"],
        cartridge,
        criteria_version=args.criteria_version,
        intent_version=args.intent_version,
    )

    outputs = {
        "a1_compilation.json": compilation,
        "a2_intake.json": a2,
        "sidecar.json": a3["sidecar"],
        "traveling_envelope.json": a3["envelope"],
        "a4_submission.json": a4,
        "a5_reasoner_request.json": request,
    }
    for name, value in outputs.items():
        write_json(args.output_dir / name, value)
    print(json.dumps({
        "status": "A5_REQUEST_READY",
        "simulation": True,
        "submission_id": a4["submission_id"],
        "observation_count": len(request["observations"]),
        "output_dir": str(args.output_dir),
    }, indent=2))


if __name__ == "__main__":
    main()
