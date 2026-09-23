from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sdna_px.batch import compile_batch


def main() -> None:
    p = argparse.ArgumentParser(description="Compile many Scout observation packets through one locked Spatial DNA strategy.")
    p.add_argument("input_dir", type=Path)
    p.add_argument("output_dir", type=Path)
    p.add_argument("--strategy", type=Path, required=True)
    args = p.parse_args()

    manifest = compile_batch(ROOT, args.input_dir, args.output_dir, args.strategy)
    print(json.dumps(manifest, indent=2))
    if manifest["failure_count"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
