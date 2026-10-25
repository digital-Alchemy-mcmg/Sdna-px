from __future__ import annotations

import copy
import hashlib
import json
import re
import uuid
from typing import Any, Mapping

from sdna_px import SpatialDNAEngine


class MaraBContractError(ValueError):
    pass


_NAMESPACE = uuid.UUID("80a51577-2ea6-49d8-8255-c7c4baec03cc")
_MARKERS = {"hard", "soft", "unmarked"}
_DISPOSITIONS = {"PASS", "QUALIFIED", "BOUNDED", "UNRESOLVED", "CONTRADICTED"}


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def sha256(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _verify_embedded_hash(value: dict[str, Any], field: str) -> None:
    expected = value.get(field)
    body = copy.deepcopy(value)
    body.pop(field, None)
    if expected != sha256(body):
        raise MaraBContractError(f"invalid {field}")


def _required(value: Mapping[str, Any], fields: tuple[str, ...], label: str) -> None:
    missing = [field for field in fields if value.get(field) in (None, "", [], {})]
    if missing:
        raise MaraBContractError(f"{label}: missing {missing}")


def finding(stage: str, affected: str, reason: str, correction: str) -> dict[str, Any]:
    return {"stage": stage, "affected_object": affected, "reason": reason, "permitted_correction": correction}


def append_b_receipt(envelope: dict[str, Any], *, stage: str, artifact_ref: str, status: str, findings: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Return a new envelope with a compact Segment B receipt; never embed evidence."""
    if envelope.get("schema") != "SCOUT_TRAVELING_ENVELOPE_v1" or not isinstance(envelope.get("receipts"), list):
        raise MaraBContractError("Segment B receipt: invalid Traveling Envelope")
    if stage not in {"BOUNDARY_B", "B1", "B2", "B3", "B4"}:
        raise MaraBContractError("Segment B receipt: invalid stage")
    out = copy.deepcopy(envelope)
    previous_count = len(out["receipts"])
    out["receipts"].append({"stage": stage, "artifact_ref": artifact_ref, "status": status, "findings": copy.deepcopy(findings or [])})
    out["state"] = {**out.get("state", {}), "current_stage": stage, "status": status}
    out["segment_b"] = {"receipt_count_added": len(out["receipts"]) - previous_count, "full_evidence_embedded": False}
    return out


def admit_boundary_b(
    release: dict[str, Any],
    sidecar: dict[str, Any],
    source_artifact: dict[str, Any],
) -> dict[str, Any]:
    """Admit an authorized A5 release without performing B1 decomposition."""
    if release.get("schema") != "SCOUT_B1_RELEASE_v1" or release.get("status") != "AUTHORIZED":
        raise MaraBContractError("Boundary B: Scout release is not authorized")
    _verify_embedded_hash(release, "release_sha256")
    authorized = release.get("authorized_observation_uuids", [])
    if not authorized:
        raise MaraBContractError("Boundary B: no authorized observations")
    pointers = {item["observation_uuid"]: item for item in release.get("sidecar_lookup", [])}
    if set(authorized) != set(pointers):
        raise MaraBContractError("Boundary B: authorization and lookup identities differ")
    source_uuid = source_artifact.get("observation_uuid")
    if len(authorized) != 1 or source_uuid != authorized[0]:
        raise MaraBContractError("Boundary B: source artifact identity is not the authorized target")
    _required(source_artifact, ("observation_uuid", "source_text", "source_ref"), "Boundary B source")
    if source_artifact.get("source_sha256") != sha256(source_artifact["source_text"]):
        raise MaraBContractError("Boundary B: source artifact hash mismatch")
    pointer = pointers[source_uuid]
    index = pointer["record_index"]
    if index < 0 or index >= len(sidecar.get("records", [])):
        raise MaraBContractError("Boundary B: sidecar lookup is broken")
    if sidecar["records"][index].get("Observation_ID") != pointer["observation_id"]:
        raise MaraBContractError("Boundary B: sidecar lookup is misdirected")
    core = {
        "schema": "MARA_BOUNDARY_B_ADMISSION_v1",
        "session_uid": str(uuid.uuid5(_NAMESPACE, release["release_sha256"])),
        "target_uuid": source_uuid,
        "source": copy.deepcopy(source_artifact),
        "a5_release_sha256": release["release_sha256"],
        "status": "ADMITTED_FOR_B1",
        "candidate_data_accessed": False,
    }
    core["admission_sha256"] = sha256(core)
    return core


def validate_b1_decomposition(admission: dict[str, Any], response: dict[str, Any]) -> dict[str, Any]:
    """Validate an injected TargetDecomposer response against immutable source spans."""
    if admission.get("status") != "ADMITTED_FOR_B1" or admission.get("candidate_data_accessed") is not False:
        raise MaraBContractError("B1: invalid candidate-blind admission")
    _required(response, ("adapter_id", "instruction_version", "intent_version", "primitives", "application_routing"), "B1 response")
    source = admission["source"]["source_text"]
    primitives = copy.deepcopy(response["primitives"])
    seen: set[str] = set()
    malforms: list[dict[str, Any]] = []
    for primitive in primitives:
        _required(primitive, ("primitive_id", "text", "marker", "span_start", "span_end", "kind"), "B1 primitive")
        if primitive["primitive_id"] in seen:
            raise MaraBContractError("B1: duplicate primitive identity")
        seen.add(primitive["primitive_id"])
        if primitive["marker"] not in _MARKERS:
            raise MaraBContractError("B1: invalid semantic marker")
        start, end = primitive["span_start"], primitive["span_end"]
        if not isinstance(start, int) or not isinstance(end, int) or source[start:end] != primitive["text"]:
            raise MaraBContractError(f"B1: invalid source span for {primitive['primitive_id']}")
    routing = response["application_routing"]
    if not routing.get("origin"):
        malforms.append(finding("B1", admission["target_uuid"], "application origin missing", "reprocess B1 or preserve source deficiency"))
    if not routing.get("destination"):
        malforms.append(finding("B1", admission["target_uuid"], "application destination missing", "reprocess B1 or preserve source deficiency"))
    core = {
        "schema": "MARA_B1_DECOMPOSITION_v1",
        "session_uid": admission["session_uid"],
        "target_uuid": admission["target_uuid"],
        "source_sha256": admission["source"]["source_sha256"],
        "application_routing": copy.deepcopy(routing),
        "primitives": primitives,
        "ambiguities": copy.deepcopy(response.get("ambiguities", [])),
        "malforms": malforms,
        "status": "MALFORMED" if malforms else "READY_FOR_B2",
        "candidate_data_accessed": False,
        "adapter": {key: response[key] for key in ("adapter_id", "instruction_version", "intent_version")},
    }
    core["b1_sha256"] = sha256(core)
    return core


def build_b2_tree(b1: dict[str, Any], classifications: dict[str, Any]) -> dict[str, Any]:
    """Build stable lowercase addresses from complete B1 primitives."""
    if b1.get("status") != "READY_FOR_B2" or b1.get("candidate_data_accessed") is not False:
        raise MaraBContractError("B2: B1 is not candidate-blind and ready")
    _required(classifications, ("adapter_id", "instruction_version", "intent_version", "domains"), "B2 classifications")
    domain_by_primitive: dict[str, str] = classifications["domains"]
    primitive_ids = {item["primitive_id"] for item in b1["primitives"]}
    if set(domain_by_primitive) != primitive_ids:
        raise MaraBContractError("B2: every B1 primitive requires exactly one domain classification")
    normalized = {pid: re.sub(r"[^a-z0-9]+", "-", domain.strip().lower()).strip("-") for pid, domain in domain_by_primitive.items()}
    if any(not domain for domain in normalized.values()):
        raise MaraBContractError("B2: empty operational domain")
    ordered_domains = sorted(set(normalized.values()))
    counters = {domain: 0 for domain in ordered_domains}
    nodes = []
    for primitive in b1["primitives"]:
        domain = normalized[primitive["primitive_id"]]
        counters[domain] += 1
        address = f"d.{ordered_domains.index(domain) + 1}.{counters[domain]}"
        nodes.append({
            "node_id": str(uuid.uuid5(_NAMESPACE, f"{b1['b1_sha256']}|{primitive['primitive_id']}|{domain}")),
            "address": address,
            "operational_domain": domain,
            "requirement": primitive["text"],
            "marker": primitive["marker"],
            "kind": primitive["kind"],
            "qualifiers": copy.deepcopy(primitive.get("qualifiers", [])),
            "source_span": {"start": primitive["span_start"], "end": primitive["span_end"]},
            "primitive_id": primitive["primitive_id"],
        })
    core = {
        "schema": "MARA_B2_TARGET_TREE_v1",
        "target_uuid": b1["target_uuid"],
        "b1_sha256": b1["b1_sha256"],
        "nodes": nodes,
        "address_to_primitive": {node["address"]: node["primitive_id"] for node in nodes},
        "primitive_to_address": {node["primitive_id"]: node["address"] for node in nodes},
        "candidate_data_accessed": False,
        "adapter": {key: classifications[key] for key in ("adapter_id", "instruction_version", "intent_version")},
    }
    core["b2_sha256"] = sha256(core)
    return core


def prepare_b3_candidates(root: str, tree: dict[str, Any], routes: dict[str, Any]) -> dict[str, Any]:
    """Expose real eligible atoms for target-driven semantic selection."""
    if tree.get("candidate_data_accessed") is not False:
        raise MaraBContractError("B3: invalid tree custody")
    _required(routes, ("adapter_id", "instruction_version", "intent_version", "planes_by_node"), "B3 routes")
    engine = SpatialDNAEngine.from_repo(root)
    planes_by_node = routes["planes_by_node"]
    node_ids = {node["node_id"] for node in tree["nodes"]}
    if set(planes_by_node) != node_ids:
        raise MaraBContractError("B3: every target node requires a plane route")
    valid_planes = {node["plane_assignment"] for node in engine.nodes}
    candidates = {}
    for node in tree["nodes"]:
        planes = list(planes_by_node[node["node_id"]])
        if not planes or not set(planes) <= valid_planes:
            raise MaraBContractError("B3: route contains an invalid evidence plane")
        candidates[node["node_id"]] = [copy.deepcopy(atom) for atom in engine.nodes if atom["plane_assignment"] in planes]
    return {
        "schema": "MARA_B3_CANDIDATE_SET_v1",
        "target_uuid": tree["target_uuid"],
        "b2_sha256": tree["b2_sha256"],
        "nodes": copy.deepcopy(tree["nodes"]),
        "candidates_by_node": candidates,
        "routes": copy.deepcopy(planes_by_node),
        "adapter": {key: routes[key] for key in ("adapter_id", "instruction_version", "intent_version")},
    }


def record_b3_selection(candidate_set: dict[str, Any], response: dict[str, Any]) -> dict[str, Any]:
    _required(response, ("adapter_id", "instruction_version", "intent_version", "selections"), "B3 selection")
    selections = response["selections"]
    node_ids = {node["node_id"] for node in candidate_set["nodes"]}
    if set(selections) != node_ids:
        raise MaraBContractError("B3: every node requires a selection record")
    ledger = []
    for node in candidate_set["nodes"]:
        selected = selections[node["node_id"]]
        _required(selected, ("considered_atom_ids", "proposition"), "B3 node selection")
        eligible = {atom["atom_id"] for atom in candidate_set["candidates_by_node"][node["node_id"]]}
        considered = list(selected["considered_atom_ids"])
        selected_ids = list(selected.get("selected_atom_ids", []))
        if not set(considered) <= eligible or not set(selected_ids) <= set(considered):
            raise MaraBContractError("B3: selected evidence must be eligible and considered")
        ledger.append({
            "node_id": node["node_id"], "target_address": node["address"], "requirement": node["requirement"],
            "marker": node["marker"], "considered_atom_ids": considered, "selected_atom_ids": selected_ids,
            "proposition": selected["proposition"], "selection_rationale": selected.get("rationale", ""),
            "truth_status": "NOT_AUDITED",
        })
    core = {
        "schema": "MARA_B3_BINDING_LEDGER_v1", "target_uuid": candidate_set["target_uuid"],
        "b2_sha256": candidate_set["b2_sha256"], "records": ledger,
        "adapter": {key: response[key] for key in ("adapter_id", "instruction_version", "intent_version")},
    }
    core["b3_sha256"] = sha256(core)
    return core


def prepare_b4_requests(root: str, tree: dict[str, Any], b3: dict[str, Any], *, intent_version: str, criteria_version: str) -> list[dict[str, Any]]:
    if b3.get("b2_sha256") != tree.get("b2_sha256"):
        raise MaraBContractError("B4: tree and binding ledger differ")
    engine = SpatialDNAEngine.from_repo(root)
    atoms = {atom["atom_id"]: atom for atom in engine.nodes}
    requests = []
    for record in b3["records"]:
        selected = record["selected_atom_ids"]
        if any(atom_id not in atoms for atom_id in selected):
            raise MaraBContractError("B4: selected atom is absent")
        requests.append({
            "schema": "MARA_B4_TRUTH_REQUEST_v1", "target_uuid": tree["target_uuid"],
            "node_id": record["node_id"], "target_address": record["target_address"],
            "requirement": record["requirement"], "marker": record["marker"],
            "proposition": record["proposition"], "selected_evidence": [copy.deepcopy(atoms[atom_id]) for atom_id in selected],
            "selected_evidence_refs": selected, "intent_version": intent_version, "criteria_version": criteria_version,
            "b3_sha256": b3["b3_sha256"], "write_access": False,
        })
    return requests


def reconcile_b4(tree: dict[str, Any], b3: dict[str, Any], requests: list[dict[str, Any]], responses: list[dict[str, Any]]) -> dict[str, Any]:
    by_node = {response.get("node_id"): response for response in responses}
    expected = {node["node_id"] for node in tree["nodes"]}
    if set(by_node) != expected or len(responses) != len(expected):
        raise MaraBContractError("B4: exactly one current response is required per B2 node")
    request_by_node = {request["node_id"]: request for request in requests}
    records = []
    for node in tree["nodes"]:
        request = request_by_node[node["node_id"]]
        response = by_node[node["node_id"]]
        _required(response, ("auditor_id", "auditor_version", "criteria_version", "intent_version", "disposition", "reason", "source_refs", "evidence_ceiling"), "B4 response")
        if response["criteria_version"] != request["criteria_version"] or response["intent_version"] != request["intent_version"]:
            raise MaraBContractError("B4: governance version mismatch")
        disposition = response["disposition"]
        if disposition not in _DISPOSITIONS:
            raise MaraBContractError("B4: invalid disposition")
        selected = set(request["selected_evidence_refs"])
        if not set(response.get("evidence_atom_refs", [])) <= selected:
            raise MaraBContractError("B4: auditor cited unselected evidence")
        hard_gate = response.get("hard_gate_satisfied")
        if node["marker"] == "hard" and disposition != "PASS" and hard_gate is not False:
            raise MaraBContractError("B4: non-PASS hard requirement must remain unsatisfied")
        if disposition == "PASS" and not request["selected_evidence_refs"]:
            raise MaraBContractError("B4: PASS requires selected documentary evidence")
        records.append({
            "node_id": node["node_id"], "target_address": node["address"], "marker": node["marker"],
            "requirement": node["requirement"], "proposition": request["proposition"],
            "selected_evidence_refs": request["selected_evidence_refs"], "disposition": disposition,
            "verified_proposition": response.get("verified_proposition"), "evidence_ceiling": response["evidence_ceiling"],
            "unsupported_scope": copy.deepcopy(response.get("unsupported_scope", [])),
            "hard_gate_satisfied": hard_gate, "reason": response["reason"], "source_refs": copy.deepcopy(response["source_refs"]),
            "evidence_atom_refs": copy.deepcopy(response.get("evidence_atom_refs", [])),
            "decision_trace": copy.deepcopy(response.get("decision_trace", {})),
        })
    core = {
        "schema": "MARA_B4_AUDITED_LEDGER_v1", "target_uuid": tree["target_uuid"],
        "b2_tree_ref": tree["b2_sha256"], "b3_ledger_ref": b3["b3_sha256"], "nodes": records,
        "reconciliation": {"b2_node_count": len(tree["nodes"]), "current_b4_record_count": len(records), "all_nodes_accounted_for": True},
        "handoff": {"destination": "B5_ENTRY", "status": "READY_FOR_B5_SEMANTIC_CORE", "b5_executed": False},
    }
    core["ledger_sha256"] = sha256(core)
    return core
