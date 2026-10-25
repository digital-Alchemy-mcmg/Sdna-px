from __future__ import annotations

import copy
import hashlib
import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping


class ScoutContractError(ValueError):
    """Raised when a stage boundary cannot be admitted mechanically."""


_UUID_NAMESPACE = uuid.UUID("de642f7e-7511-4f01-a648-f59808676d69")
_DECISIONS = {"ACCEPT", "REJECT", "HOLD"}
CANONICAL_OBSERVATION_CONTRACT_VERSION = "SCOUT_DISK_STUDIO_2.2.0_OBSERVATION_v1"
CANONICAL_OBSERVATION_FIELDS = (
    "Observation_ID",
    "Collection_Date",
    "Vendor",
    "Employer",
    "Job_Title",
    "City",
    "State",
    "ZIP",
    "Industry",
    "Employment_Type",
    "Compensation",
    "Source_URL",
    "Duplicate_Count",
)


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _timestamp(value: str | None = None) -> str:
    return value or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _required(mapping: Mapping[str, Any], fields: Iterable[str], label: str) -> None:
    missing = [field for field in fields if mapping.get(field) in (None, "", [], {})]
    if missing:
        raise ScoutContractError(f"{label}: missing required fields {missing}")


def _safe_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value).replace("\u2014", " - ")).strip()


def compile_disks(scopes: list[dict[str, Any]], *, compiled_at: str | None = None) -> dict[str, Any]:
    """A1: compile one to three operator scopes without dispatching anything."""
    if not 1 <= len(scopes) <= 3:
        raise ScoutContractError("A1: a compilation batch must contain one to three Disks")
    compiled: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for scope in scopes:
        _required(
            scope,
            ("disk_id", "label", "version", "zip", "radius_miles", "naics", "soc", "include", "exclude", "limit", "observation_contract"),
            "A1 scope",
        )
        disk_id = str(scope["disk_id"])
        if disk_id in seen_ids:
            raise ScoutContractError(f"A1: duplicate disk_id {disk_id}")
        seen_ids.add(disk_id)
        observation_contract = list(scope["observation_contract"])
        if tuple(observation_contract) != CANONICAL_OBSERVATION_FIELDS:
            raise ScoutContractError(
                "A1: observation_contract must exactly match the ordered Scout Disk Studio 2.2.0 canonical contract"
            )
        definition = {
            "id": disk_id,
            "label": scope["label"],
            "description": scope.get("description", ""),
            "version": scope["version"],
            "territory": {"zip": str(scope["zip"]), "radius_miles": scope["radius_miles"]},
            "industry": copy.deepcopy(scope["naics"]),
            "roles": copy.deepcopy(scope["soc"]),
            "keywords": {"include": list(scope["include"]), "exclude": list(scope["exclude"])},
            "classification_provenance": copy.deepcopy(scope.get("classification_provenance", {})),
        }
        payload_id = f"PAY-{disk_id.removeprefix('DSK-')}"
        machine_payload = {
            "id": payload_id,
            "dsk": disk_id,
            "v": scope["version"],
            "obs_type": scope.get("observation_type", "EMPLOYMENT_OPPORTUNITY"),
            "loc": {"z": str(scope["zip"]), "r": scope["radius_miles"]},
            "tax": {"n": copy.deepcopy(scope["naics"]), "s": copy.deepcopy(scope["soc"])},
            "rng_provenance": copy.deepcopy(scope.get("classification_provenance", {})),
            "kw_rules": {"role_scopes": list(scope["include"]), "exclude": list(scope["exclude"])},
            "exec": {"limit": scope["limit"], "profile": scope.get("execution_profile", "MANUAL_AUTHORIZED_ADAPTER")},
            "contract": {
                "version": CANONICAL_OBSERVATION_CONTRACT_VERSION,
                "source": "Scout Disk Studio 2.2.0 reference export",
                "fields": observation_contract,
            },
        }
        cartridge_core = {
            "metadata": {
                "cartridge_id": f"CRT-{disk_id.removeprefix('DSK-')}",
                "disk_id": disk_id,
                "compilation_id": str(scope.get("compilation_id", "CMP-000001")),
                "payload_id": payload_id,
                "schema_version": "2.2.0",
            },
            "definition": definition,
            "machine_payload": machine_payload,
        }
        cartridge_hash = sha256(cartridge_core)
        compiled.append({
            "cartridge": {
                **cartridge_core,
                "certification": {"status": "CERTIFIED", "decision": "READY", "content_hash": cartridge_hash},
                "report": {"status": "SUCCESS", "metrics": {"observation_field_count": 13}},
            },
            "runner_ready": {
                "scout_disk_agent_prompt_ref": "config/scout_a5_reasoner_prompt.md",
                "cartridge_hash": cartridge_hash,
                "machine_payload": machine_payload,
                "dispatch_status": "NOT_DISPATCHED",
            },
        })
    return {
        "schema": "SCOUT_A1_COMPILATION_v1",
        "compiled_at": _timestamp(compiled_at),
        "disk_count": len(compiled),
        "disks": compiled,
        "execution_status": "NOT_EXECUTED",
    }


def process_a2_return(
    cartridge: dict[str, Any],
    records: list[dict[str, Any]],
    *,
    runner_id: str,
    dispatch_id: str,
    adapter: str = "SIMULATED",
    processed_at: str | None = None,
) -> dict[str, Any]:
    """A2: preserve raw records, create safe records, and report coherence."""
    cert = cartridge.get("certification", {})
    if cert.get("status") != "CERTIFIED" or cert.get("decision") != "READY":
        raise ScoutContractError("A2: cartridge is not certified and ready")
    expected_hash = sha256({k: cartridge[k] for k in ("metadata", "definition", "machine_payload")})
    if cert.get("content_hash") != expected_hash:
        raise ScoutContractError("A2: cartridge integrity commitment does not match")
    fields = cartridge["machine_payload"]["contract"]["fields"]
    exceptions: list[dict[str, Any]] = []
    safe_records: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        actual_fields = list(record.keys())
        if actual_fields != fields:
            missing = [field for field in fields if field not in record]
            unrecognized = [field for field in actual_fields if field not in fields]
            raise ScoutContractError(
                f"A2: record {index} does not exactly match canonical field order; "
                f"missing={missing}, unrecognized={unrecognized}"
            )
        safe_records.append({key: _safe_text(value) if isinstance(value, str) else copy.deepcopy(value) for key, value in record.items()})
    limit = int(cartridge["machine_payload"]["exec"]["limit"])
    if len(records) > limit:
        exceptions.append({"code": "RESULT_LIMIT_EXCEEDED", "limit": limit, "actual": len(records)})
    state = "EMPTY" if not records else "RECEIVED"
    return {
        "schema": "SCOUT_A2_INTAKE_v1",
        "adapter": adapter,
        "simulation": adapter == "SIMULATED",
        "processed_at": _timestamp(processed_at),
        "lineage": {
            "disk_id": cartridge["metadata"]["disk_id"],
            "cartridge_id": cartridge["metadata"]["cartridge_id"],
            "payload_id": cartridge["metadata"]["payload_id"],
            "runner_id": runner_id,
            "dispatch_id": dispatch_id,
        },
        "return_state": state,
        "raw_return": copy.deepcopy(records),
        "sidecar": {"format": "parsed-safe-json", "records": safe_records},
        "coherence": {"status": "PASS" if not exceptions else "EXCEPTION", "exceptions": exceptions},
    }


def initialize_a3(a2: dict[str, Any], *, sidecar_uri: str, processed_at: str | None = None) -> dict[str, Any]:
    """A3: assign stable identities and initialize an append-only envelope."""
    if a2.get("schema") != "SCOUT_A2_INTAKE_v1":
        raise ScoutContractError("A3: invalid A2 intake schema")
    records = copy.deepcopy(a2["sidecar"]["records"])
    sidecar_id = f"SID-{sha256(records)[:16]}"
    sidecar = {"sidecar_id": sidecar_id, "uri": sidecar_uri, "format": "parsed-safe-json", "records": records}
    sidecar_hash = sha256(sidecar)
    lineage = copy.deepcopy(a2["lineage"])
    lookup = []
    for index, record in enumerate(records):
        observation_id = str(record.get("Observation_ID", ""))
        source_url = str(record.get("Source_URL", ""))
        if not observation_id:
            raise ScoutContractError(f"A3: record {index} has no Observation_ID")
        stable_key = f"{lineage['disk_id']}|{lineage['dispatch_id']}|{observation_id}|{source_url}"
        lookup.append({
            "observation_uuid": str(uuid.uuid5(_UUID_NAMESPACE, stable_key)),
            "observation_id": observation_id,
            "record_index": index,
            "source_key": source_url,
        })
    if len({item["observation_uuid"] for item in lookup}) != len(lookup):
        raise ScoutContractError("A3: duplicate evidence identity")
    job_uuid = str(uuid.uuid5(_UUID_NAMESPACE, f"job|{lineage['dispatch_id']}"))
    envelope_uuid = str(uuid.uuid5(_UUID_NAMESPACE, f"envelope|{lineage['dispatch_id']}"))
    receipt = {"stage": "A3", "action": "INITIALIZE_ENVELOPE", "status": "RECORDED", "at": _timestamp(processed_at)}
    envelope = {
        "schema": "SCOUT_TRAVELING_ENVELOPE_v1",
        "envelope_uuid": envelope_uuid,
        "job_uuid": job_uuid,
        "state": {"origin_stage": "A3", "current_stage": "A3", "status": "INITIALIZED", "next_stage": "A4"},
        "lineage": lineage,
        "sidecar": {"sidecar_id": sidecar_id, "uri": sidecar_uri, "sha256": sidecar_hash, "format": "parsed-safe-json"},
        "lookup": {"observations": lookup},
        "receipts": [receipt],
        "upstream_exceptions": copy.deepcopy(a2["coherence"]["exceptions"]),
    }
    return {"sidecar": sidecar, "envelope": envelope, "receipt": receipt}


def freeze_a4_submission(
    cartridge: dict[str, Any],
    a2: dict[str, Any],
    sidecar: dict[str, Any],
    envelope: dict[str, Any],
    *,
    frozen_at: str | None = None,
) -> dict[str, Any]:
    """A4: reconcile identities and freeze an inspection-only submission."""
    failures: list[dict[str, Any]] = []
    current_sidecar_hash = sha256(sidecar)
    if envelope["sidecar"]["sha256"] != current_sidecar_hash:
        failures.append({"code": "SIDECAR_HASH_MISMATCH"})
    disk_ids = {cartridge["metadata"]["disk_id"], a2["lineage"]["disk_id"], envelope["lineage"]["disk_id"]}
    if len(disk_ids) != 1:
        failures.append({"code": "DISK_LINEAGE_MISMATCH"})
    seen: set[str] = set()
    for pointer in envelope["lookup"]["observations"]:
        obs_uuid = pointer["observation_uuid"]
        if obs_uuid in seen:
            failures.append({"code": "DUPLICATE_OBSERVATION_UUID", "observation_uuid": obs_uuid})
        seen.add(obs_uuid)
        index = pointer["record_index"]
        if not isinstance(index, int) or index < 0 or index >= len(sidecar["records"]):
            failures.append({"code": "BROKEN_RECORD_INDEX", "observation_uuid": obs_uuid})
            continue
        record = sidecar["records"][index]
        if record.get("Observation_ID") != pointer["observation_id"] or record.get("Source_URL") != pointer["source_key"]:
            failures.append({"code": "MISDIRECTED_POINTER", "observation_uuid": obs_uuid})
    if failures:
        raise ScoutContractError(f"A4: blocking mechanical failures {failures}")
    frozen_envelope = copy.deepcopy(envelope)
    envelope_hash = sha256(frozen_envelope)
    core = {
        "schema": "SCOUT_A4_SUBMISSION_v1",
        "submission_id": f"A4-SUB-{sha256([current_sidecar_hash, envelope_hash])[:16]}",
        "state": "READY_FOR_A5",
        "identity": {
            "job_uuid": envelope["job_uuid"],
            "envelope_uuid": envelope["envelope_uuid"],
            "disk_id": cartridge["metadata"]["disk_id"],
        },
        "artifacts": {
            "disk_content_hash": cartridge["certification"]["content_hash"],
            "a2_dispatch_id": a2["lineage"]["dispatch_id"],
            "sidecar_id": sidecar["sidecar_id"],
        },
        "inspection": {"lookup": copy.deepcopy(envelope["lookup"]), "exceptions": copy.deepcopy(envelope.get("upstream_exceptions", []))},
        "verification": {"integrity": "PASS", "reconciliation": "PASS", "traversal": "PASS", "record_count": len(sidecar["records"]), "exceptions": []},
        "commitments": {"sidecar_sha256": current_sidecar_hash, "envelope_sha256": envelope_hash},
        "handoff": {"destination": "A5", "authorization": "INSPECTION_ONLY"},
        "frozen_at": _timestamp(frozen_at),
    }
    core["commitments"]["submission_sha256"] = sha256(core)
    return core


def prepare_a5_request(
    submission: dict[str, Any],
    sidecar: dict[str, Any],
    cartridge: dict[str, Any],
    *,
    criteria_version: str,
    intent_version: str,
) -> dict[str, Any]:
    """Prepare immutable evidence copies for an independently invoked reasoner."""
    if submission.get("state") != "READY_FOR_A5":
        raise ScoutContractError("A5: submission is not ready")
    committed = submission["commitments"].get("submission_sha256")
    check = copy.deepcopy(submission)
    del check["commitments"]["submission_sha256"]
    if committed != sha256(check):
        raise ScoutContractError("A5: submission commitment is invalid")
    if submission["commitments"]["sidecar_sha256"] != sha256(sidecar):
        raise ScoutContractError("A5: sidecar commitment is invalid")
    observations = []
    for pointer in submission["inspection"]["lookup"]["observations"]:
        observations.append({"pointer": copy.deepcopy(pointer), "evidence": copy.deepcopy(sidecar["records"][pointer["record_index"]])})
    return {
        "schema": "SCOUT_A5_REASONER_REQUEST_v1",
        "submission_id": submission["submission_id"],
        "submission_sha256": committed,
        "intent_version": intent_version,
        "criteria_version": criteria_version,
        "certified_disk": copy.deepcopy(cartridge["definition"]),
        "observations": observations,
        "allowed_decisions": sorted(_DECISIONS),
        "write_access": False,
    }


def record_a5_response(
    request: dict[str, Any],
    response: dict[str, Any],
    envelope: dict[str, Any],
    ledger: list[dict[str, Any]],
    *,
    recorded_at: str | None = None,
) -> dict[str, Any]:
    """Validate an independent response and append decisions without mutation."""
    _required(response, ("reasoner_id", "reasoner_version", "criteria_version", "dispositions"), "A5 response")
    if response["criteria_version"] != request["criteria_version"]:
        raise ScoutContractError("A5: criteria version mismatch")
    expected = {item["pointer"]["observation_uuid"] for item in request["observations"]}
    dispositions = response["dispositions"]
    actual = {item.get("observation_uuid") for item in dispositions}
    if actual != expected or len(dispositions) != len(expected):
        raise ScoutContractError("A5: every submitted observation requires exactly one disposition")
    evidence_refs = {
        item["pointer"]["observation_uuid"]: item["pointer"]["source_key"] for item in request["observations"]
    }
    normalized = []
    for item in dispositions:
        decision = item.get("decision")
        if decision not in _DECISIONS:
            raise ScoutContractError(f"A5: unsupported decision {decision!r}")
        _required(item, ("reason", "evidence_refs", "material_considerations"), "A5 disposition")
        if evidence_refs[item["observation_uuid"]] not in item["evidence_refs"]:
            raise ScoutContractError("A5: disposition does not cite its submitted source")
        normalized.append(copy.deepcopy(item))
    decision_core = {
        "schema": "SCOUT_A5_DISPOSITION_v1",
        "decision_id": f"A5-DEC-{sha256([request['submission_sha256'], normalized])[:16]}",
        "submission": {"a4_submission_ref": request["submission_id"], "a4_submission_sha256": request["submission_sha256"], "envelope_uuid": envelope["envelope_uuid"]},
        "evaluation": {"reasoner_id": response["reasoner_id"], "reasoner_version": response["reasoner_version"], "criteria_version": response["criteria_version"], "intent_version": request["intent_version"]},
        "dispositions": normalized,
        "recorded_at": _timestamp(recorded_at),
    }
    decision_hash = sha256(decision_core)
    ledger_out = copy.deepcopy(ledger)
    ledger_out.append({**decision_core, "disposition_sha256": decision_hash})
    accepted = sorted(item["observation_uuid"] for item in normalized if item["decision"] == "ACCEPT")
    envelope_out = copy.deepcopy(envelope)
    envelope_out["receipts"].append({"stage": "A5", "action": "RECORD_DISPOSITION", "status": "RECORDED", "decision_id": decision_core["decision_id"], "at": decision_core["recorded_at"]})
    envelope_out["state"] = {"origin_stage": "A3", "current_stage": "A5", "status": "DISPOSITION_RECORDED", "next_stage": "B1" if accepted else None}
    envelope_out["a5"] = {"decision_id": decision_core["decision_id"], "disposition_sha256": decision_hash, "authorized_observation_uuids": accepted}
    release = {
        "schema": "SCOUT_B1_RELEASE_v1",
        "status": "AUTHORIZED" if accepted else "BLOCKED",
        "destination": "B1",
        "a4_submission_sha256": request["submission_sha256"],
        "a5_decision_id": decision_core["decision_id"],
        "a5_disposition_sha256": decision_hash,
        "authorized_observation_uuids": accepted,
        "sidecar_lookup": [item["pointer"] for item in request["observations"] if item["pointer"]["observation_uuid"] in accepted],
    }
    release["release_sha256"] = sha256(release)
    return {"ledger": ledger_out, "envelope": envelope_out, "release": release}
