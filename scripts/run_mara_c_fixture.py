from __future__ import annotations

import argparse
import json
from pathlib import Path

from mara_c_workbench import (
    build_meta_request, construct_c3, finalize_c5, render_fixture_html,
    validate_b5_posture, validate_c1_resolution, validate_c2_composition, validate_c4,
)
try:
    from scripts.run_mara_b_fixture import run_fixture as run_b_fixture
except ModuleNotFoundError:  # Direct `python scripts/run_mara_c_fixture.py` execution.
    from run_mara_b_fixture import run_fixture as run_b_fixture


PRISMS = ("Sales Headhunter", "Sports Agent", "Discovery Scout", "Independent Staffing-Firm Owner", "Casting Director")


def run_fixture(repo_root: Path) -> dict:
    b4 = run_b_fixture(repo_root)["b4"]
    atom = b4["nodes"][0]["selected_evidence_refs"][0]
    b5 = validate_b5_posture(b4, {
        "reasoner_id": "SIMULATED-B5", "reasoner_version": "fixture", "intent_version": "fixture-v1",
        "prisms": {name: {"percentage": pct, "prominence": "owner" if index == 0 else "support", "evidence_anchors": [atom]} for index, (name, pct) in enumerate(zip(PRISMS, (40, 25, 15, 10, 10)))},
        "owner_prism": PRISMS[0], "supporting_prisms": list(PRISMS[1:]), "semantic_geometry": "Dominant Plus Secondary",
        "narrative_posture": "Lead with documented production and reinforce transferable operations.",
        "permissible_intensity": "documented", "prohibited_implications": ["No unsupported ownership"],
    })
    content = [{"content_id": f"C-{i}", "node_id": node["node_id"], "inclusion": "foreground" if i == 1 else "reinforcement", "evidence_refs": node["selected_evidence_refs"], "semantic_ceiling": node["evidence_ceiling"], "provenance_label": f"Work {i}", "dependencies": []} for i, node in enumerate(b4["nodes"], 1)]
    c1 = validate_c1_resolution(b4, b5, {"adapter_id": "SIMULATED-C1", "instruction_version": "fixture", "intent_version": "fixture-v1", "content": content})
    expressions = [{"content_id": item["content_id"], "full": f"Documented contribution for {item['content_id']} with bounded responsibility.", "compact": f"Bounded contribution {item['content_id']}.", "agency": "contribution", "chronology": "2024", "association": item["provenance_label"]} for item in content]
    c2 = validate_c2_composition(c1, {"adapter_id": "SIMULATED-C2", "instruction_version": "fixture", "intent_version": "fixture-v1", "expressions": expressions})
    registry = {"registry_version": "fixture-v1", "surface": {"width_pt": 612, "height_pt": 792, "margin_pt": 54, "line_height_pt": 12, "avg_char_width_pt": 6, "max_pages": 1}, "layout_families": {"Single Dominant": "single-center", "Dual Dominant": "dual-center", "Dominant Plus Secondary": "lead-plus-support", "Distributed": "distributed"}}
    c3 = construct_c3(b5, c1, c2, registry, {item["content_id"]: "full" for item in content})
    plane_names = ("evidence", "prism", "expression", "structural", "chronological", "anti-pattern", "geometry", "extraction", "completeness", "provenance")
    c4 = validate_c4(c3, {"validator_id": "SIMULATED-C4", "validator_version": "fixture", "intent_version": "fixture-v1", "disposition": "PASS", "planes": {name: True for name in plane_names}, "findings": []})
    meta_request = build_meta_request(c3, c4, b5)
    meta_return = render_fixture_html(meta_request)
    c5 = finalize_c5(c3, c4, meta_request, meta_return)
    return {"b5": b5, "c1": c1, "c2": c2, "c3": c3, "c4": c4, "meta_request": meta_request, "meta_return": meta_return, "c5": c5, "simulation": True}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    outputs = run_fixture(args.repo_root)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, value in outputs.items():
        if isinstance(value, (dict, list)):
            (args.output_dir / f"{name}.json").write_text(json.dumps(value, indent=2) + "\n")
    print(json.dumps({"status": "C5_PACKAGE_READY", "simulation": True, "geometry_inspection": outputs["c5"]["geometry_inspection"], "content_count": len(outputs["c5"]["content_ids"])}, indent=2))


if __name__ == "__main__":
    main()
