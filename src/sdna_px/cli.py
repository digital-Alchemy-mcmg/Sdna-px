from __future__ import annotations

import argparse
import json
from pathlib import Path

from sdna_px import SpatialDNAEngine


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("observation", type=Path)
    ap.add_argument("-o", "--output", type=Path)
    ap.add_argument("--strategy", type=Path, required=True)
    ap.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    args = ap.parse_args()

    observation = json.loads(args.observation.read_text(encoding="utf-8"))
    strategy = json.loads(args.strategy.read_text(encoding="utf-8"))
    engine = SpatialDNAEngine.from_repo(args.repo_root)
    payload = engine.compile(observation, strategy)
    body = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(body, encoding="utf-8")
    else:
        print(body, end="")


if __name__ == "__main__":
    main()
