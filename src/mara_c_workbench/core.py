from __future__ import annotations

import copy
import hashlib
import html
import json
import math
from typing import Any, Mapping


class MaraCContractError(ValueError):
    pass


PRISMS = (
    "Sales Headhunter", "Sports Agent", "Discovery Scout",
    "Independent Staffing-Firm Owner", "Casting Director",
)
GEOMETRIES = {"Single Dominant", "Dual Dominant", "Dominant Plus Secondary", "Distributed"}
INCLUSION = {"foreground", "reinforcement", "background", "non-traveling"}
VALIDATION_PLANES = {
    "evidence", "prism", "expression", "structural", "chronological",
    "anti-pattern", "geometry", "extraction", "completeness", "provenance",
}


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def sha256(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _required(value: Mapping[str, Any], fields: tuple[str, ...], label: str) -> None:
    missing = [field for field in fields if value.get(field) in (None, "", [], {})]
    if missing:
        raise MaraCContractError(f"{label}: missing {missing}")


def _verify_hash(value: dict[str, Any], field: str) -> None:
    body = copy.deepcopy(value)
    expected = body.pop(field, None)
    if expected != sha256(body):
        raise MaraCContractError(f"invalid {field}")


def validate_b5_posture(b4: dict[str, Any], response: dict[str, Any]) -> dict[str, Any]:
    if b4.get("schema") != "MARA_B4_AUDITED_LEDGER_v1" or not b4.get("reconciliation", {}).get("all_nodes_accounted_for"):
        raise MaraCContractError("B5: incomplete B4 ledger")
    _verify_hash(b4, "ledger_sha256")
    _required(response, ("reasoner_id", "reasoner_version", "intent_version", "prisms", "owner_prism", "semantic_geometry", "narrative_posture", "prohibited_implications"), "B5 response")
    prisms = response["prisms"]
    if set(prisms) != set(PRISMS) or len(prisms) != 5:
        raise MaraCContractError("B5: all five established Prisms are required exactly once")
    if abs(sum(float(item["percentage"]) for item in prisms.values()) - 100.0) > 1e-9:
        raise MaraCContractError("B5: Prism distribution must total 100%")
    owner = response["owner_prism"]
    if owner not in PRISMS or float(prisms[owner]["percentage"]) != max(float(item["percentage"]) for item in prisms.values()):
        raise MaraCContractError("B5: owner must be a highest-ranked established Prism")
    if response["semantic_geometry"] not in GEOMETRIES:
        raise MaraCContractError("B5: invalid semantic geometry")
    atoms = {ref for node in b4["nodes"] for ref in node["selected_evidence_refs"]}
    for prism, item in prisms.items():
        _required(item, ("percentage", "prominence", "evidence_anchors"), f"B5 {prism}")
        if not set(item["evidence_anchors"]) <= atoms:
            raise MaraCContractError("B5: Prism cites evidence outside the audited ledger")
    core = {
        "schema": "MARA_B5_PRISM_POSTURE_v1", "b4_ledger_sha256": b4["ledger_sha256"],
        "prisms": copy.deepcopy(prisms), "owner_prism": owner,
        "supporting_prisms": copy.deepcopy(response.get("supporting_prisms", [])),
        "semantic_geometry": response["semantic_geometry"], "narrative_posture": response["narrative_posture"],
        "permissible_intensity": response.get("permissible_intensity", "evidence-bounded"),
        "prohibited_implications": copy.deepcopy(response["prohibited_implications"]),
        "reasoner": {key: response[key] for key in ("reasoner_id", "reasoner_version", "intent_version")},
    }
    core["b5_sha256"] = sha256(core)
    return core


def seal_boundary_c(b4: dict[str, Any], b5: dict[str, Any], envelope: dict[str, Any]) -> dict[str, Any]:
    if b5.get("b4_ledger_sha256") != b4.get("ledger_sha256"):
        raise MaraCContractError("Boundary C: B4/B5 commitment mismatch")
    if envelope.get("schema") != "SCOUT_TRAVELING_ENVELOPE_v1" or not isinstance(envelope.get("receipts"), list):
        raise MaraCContractError("Boundary C: invalid Traveling Envelope")
    out = copy.deepcopy(envelope)
    out["receipts"].append({"stage": "BOUNDARY_C", "status": "SEALED", "b4_ledger_sha256": b4["ledger_sha256"], "b5_sha256": b5["b5_sha256"]})
    out["state"] = {**out.get("state", {}), "current_stage": "C1", "status": "ADMITTED", "next_stage": "C1"}
    out["boundary_c"] = {"sidecar_lifecycle": "SEALED_STATIONARY", "sidecar_active": False, "b4_ledger_sha256": b4["ledger_sha256"], "b5_sha256": b5["b5_sha256"]}
    return out


def validate_c1_resolution(b4: dict[str, Any], b5: dict[str, Any], response: dict[str, Any]) -> dict[str, Any]:
    _required(response, ("adapter_id", "instruction_version", "intent_version", "content"), "C1 response")
    nodes = {node["node_id"]: node for node in b4["nodes"]}
    resolved = []
    seen: set[str] = set()
    for item in response["content"]:
        _required(item, ("content_id", "node_id", "inclusion", "evidence_refs", "semantic_ceiling", "provenance_label"), "C1 content")
        if item["content_id"] in seen or item["node_id"] not in nodes or item["inclusion"] not in INCLUSION:
            raise MaraCContractError("C1: invalid or duplicate content resolution")
        seen.add(item["content_id"])
        node = nodes[item["node_id"]]
        if not set(item["evidence_refs"]) <= set(node["selected_evidence_refs"]):
            raise MaraCContractError("C1: content exceeds audited evidence references")
        if item["semantic_ceiling"] != node["evidence_ceiling"]:
            raise MaraCContractError("C1: semantic ceiling changed")
        resolved.append(copy.deepcopy(item))
    core = {"schema": "MARA_C1_RESOLVED_SET_v1", "b4_ledger_sha256": b4["ledger_sha256"], "b5_sha256": b5["b5_sha256"], "content": resolved, "adapter": {k: response[k] for k in ("adapter_id", "instruction_version", "intent_version")}}
    core["c1_sha256"] = sha256(core)
    return core


def validate_c2_composition(c1: dict[str, Any], response: dict[str, Any]) -> dict[str, Any]:
    _required(response, ("adapter_id", "instruction_version", "intent_version"), "C2 response")
    if "expressions" not in response or not isinstance(response["expressions"], list):
        raise MaraCContractError("C2 response: expressions must be a list")
    authorized = {item["content_id"]: item for item in c1["content"] if item["inclusion"] != "non-traveling"}
    expressions = []
    if {item.get("content_id") for item in response["expressions"]} != set(authorized):
        raise MaraCContractError("C2: expressions must exactly cover traveling C1 content")
    for item in response["expressions"]:
        _required(item, ("content_id", "full", "compact", "agency", "chronology", "association"), "C2 expression")
        if not item["full"].strip() or not item["compact"].strip():
            raise MaraCContractError("C2: empty expression variant")
        expressions.append({**copy.deepcopy(item), "evidence_refs": copy.deepcopy(authorized[item["content_id"]]["evidence_refs"]), "semantic_ceiling": authorized[item["content_id"]]["semantic_ceiling"]})
    core = {"schema": "MARA_C2_COMPOSITION_v1", "c1_sha256": c1["c1_sha256"], "expressions": expressions, "adapter": {k: response[k] for k in ("adapter_id", "instruction_version", "intent_version")}}
    core["c2_sha256"] = sha256(core)
    return core


def construct_c3(b5: dict[str, Any], c1: dict[str, Any], c2: dict[str, Any], registry: dict[str, Any], selections: dict[str, str]) -> dict[str, Any]:
    _required(registry, ("registry_version", "surface", "layout_families"), "C3 registry")
    geometry = b5["semantic_geometry"]
    family = registry["layout_families"].get(geometry)
    if not family:
        raise MaraCContractError("C3: no verified layout family for semantic geometry")
    surface = registry["surface"]
    _required(surface, ("width_pt", "height_pt", "margin_pt", "line_height_pt", "avg_char_width_pt", "max_pages"), "C3 surface")
    expressions = {item["content_id"]: item for item in c2["expressions"]}
    included = [item for item in c1["content"] if item["inclusion"] != "non-traveling"]
    if set(selections) != {item["content_id"] for item in included}:
        raise MaraCContractError("C3: every included content object requires a selected variant")
    rank = {"foreground": 0, "reinforcement": 1, "background": 2}
    ordered = sorted(included, key=lambda item: (rank[item["inclusion"]], item["content_id"]))
    usable_width = float(surface["width_pt"]) - 2 * float(surface["margin_pt"])
    usable_height = float(surface["height_pt"]) - 2 * float(surface["margin_pt"])
    lines_per_page = math.floor(usable_height / float(surface["line_height_pt"]))
    items, demand = [], 0
    associations: dict[str, set[str]] = {}
    for item in ordered:
        variant = selections[item["content_id"]]
        if variant not in {"full", "compact"}:
            raise MaraCContractError("C3: unauthorized expression variant")
        expression = expressions[item["content_id"]]
        text = expression[variant]
        lines = max(1, math.ceil(len(text) * float(surface["avg_char_width_pt"]) / usable_width))
        demand += lines
        association = expression["association"]
        associations.setdefault(association, set()).add(expression["chronology"])
        items.append({"content_id": item["content_id"], "text": text, "variant": variant, "inclusion": item["inclusion"], "association": association, "chronology": expression["chronology"], "estimated_lines": lines})
    capacity = lines_per_page * int(surface["max_pages"])
    if demand > capacity:
        raise MaraCContractError(f"C3: OVERFLOW demand={demand} capacity={capacity}")
    audit = {
        "chronology_first_default": False, "template_sovereignty": False, "primary_evidence_buried": False,
        "equal_prominence_for_unequal_evidence": False, "false_single_dominance": False,
        "decorative_hierarchy": False, "secondary_evidence_suppression": False,
        "false_parallelism": False, "false_employment_association": False,
        "blanket_bullet_compression": False, "automatic_one_page_compression": False,
        "dense_narrow_rails": False, "empty_high_density_grid": False,
        "candidate_tier_layout_assignment": False, "keyword_visual_prominence": False,
        "extraction_order_corruption": False, "responsive_print_distortion": "REQUIRES_RENDER_INSPECTION",
        "unverified_capacity": False,
    }
    core = {
        "schema": "MARA_C3_CONSTRUCTED_MODEL_v1", "b5_sha256": b5["b5_sha256"], "c1_sha256": c1["c1_sha256"], "c2_sha256": c2["c2_sha256"],
        "semantic_geometry": geometry, "layout_family": family, "surface": copy.deepcopy(surface),
        "ordered_content": items, "reading_order": [item["content_id"] for item in items],
        "capacity": {"estimated_lines": demand, "lines_per_page": lines_per_page, "max_pages": surface["max_pages"], "fits": True, "metric_mode": "DECLARED_AVERAGE_FONT_METRIC"},
        "anti_pattern_audit": audit, "external_render_inspection": "NOT_RUN",
    }
    core["c3_sha256"] = sha256(core)
    return core


def validate_c4(c3: dict[str, Any], response: dict[str, Any]) -> dict[str, Any]:
    _required(response, ("validator_id", "validator_version", "intent_version", "disposition", "planes"), "C4 response")
    if "findings" not in response or not isinstance(response["findings"], list):
        raise MaraCContractError("C4 response: findings must be a list")
    if set(response["planes"]) != VALIDATION_PLANES:
        raise MaraCContractError("C4: every mandatory validation plane is required")
    if response["disposition"] not in {"PASS", "REWORK_REQUIRED"}:
        raise MaraCContractError("C4: invalid disposition")
    if response["disposition"] == "PASS" and (response["findings"] or any(value is not True for value in response["planes"].values())):
        raise MaraCContractError("C4: PASS requires all planes true and no findings")
    core = {"schema": "MARA_C4_RECEIPT_v1", "c3_sha256": c3["c3_sha256"], "disposition": response["disposition"], "planes": copy.deepcopy(response["planes"]), "findings": copy.deepcopy(response["findings"]), "validator": {k: response[k] for k in ("validator_id", "validator_version", "intent_version")}}
    core["c4_sha256"] = sha256(core)
    return core


def build_meta_request(c3: dict[str, Any], c4: dict[str, Any], b5: dict[str, Any]) -> dict[str, Any]:
    if c4.get("disposition") != "PASS" or c4.get("c3_sha256") != c3.get("c3_sha256"):
        raise MaraCContractError("C5: valid C4 approval is required")
    return {"schema": "MARA_META_RENDER_REQUEST_v1", "content": copy.deepcopy(c3["ordered_content"]), "reading_order": copy.deepcopy(c3["reading_order"]), "layout_family": c3["layout_family"], "surface": copy.deepcopy(c3["surface"]), "semantic_geometry": b5["semantic_geometry"], "c4_sha256": c4["c4_sha256"], "rewrite_authority": False}


def render_fixture_html(request: dict[str, Any]) -> dict[str, Any]:
    """Deterministic local fixture renderer; not evidence of browser/print geometry."""
    body = "".join(f'<section data-content-id="{html.escape(item["content_id"])}"><p>{html.escape(item["text"])}</p></section>' for item in request["content"])
    document = f'<!doctype html><html><head><meta charset="utf-8"><title>Resume</title></head><body><main>{body}</main></body></html>'
    return {"renderer_id": "LOCAL-FIXTURE-RENDERER", "html": document, "reading_order": copy.deepcopy(request["reading_order"]), "content": copy.deepcopy(request["content"]), "geometry_inspection": "NOT_RUN", "exceptions": []}


def finalize_c5(c3: dict[str, Any], c4: dict[str, Any], meta_request: dict[str, Any], meta_return: dict[str, Any]) -> dict[str, Any]:
    if c4.get("disposition") != "PASS" or meta_request.get("c4_sha256") != c4.get("c4_sha256"):
        raise MaraCContractError("C5: invalid C4 custody")
    if meta_return.get("content") != meta_request.get("content") or meta_return.get("reading_order") != meta_request.get("reading_order"):
        raise MaraCContractError("C5: render-time rewriting or order change detected")
    html_doc = meta_return.get("html", "")
    for content_id in meta_request["reading_order"]:
        if html_doc.count(f'data-content-id="{html.escape(content_id)}"') != 1:
            raise MaraCContractError("C5: HTML content-ID parity failed")
    markdown_parts = [f"- {item['text']} <!-- {item['content_id']} -->" for item in meta_request["content"]]
    markdown = "# Resume\n\n" + "\n".join(markdown_parts) + "\n"
    core = {
        "schema": "MARA_C5_FINAL_PACKAGE_v1", "c4_sha256": c4["c4_sha256"],
        "markdown": markdown, "html": html_doc, "content_ids": copy.deepcopy(meta_request["reading_order"]),
        "markdown_sha256": hashlib.sha256(markdown.encode()).hexdigest(), "html_sha256": hashlib.sha256(html_doc.encode()).hexdigest(),
        "renderer_id": meta_return.get("renderer_id"), "geometry_inspection": meta_return.get("geometry_inspection", "NOT_RUN"),
        "exceptions": copy.deepcopy(meta_return.get("exceptions", [])),
    }
    core["package_sha256"] = sha256(core)
    return core
