from __future__ import annotations

import hashlib
import json
import math
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class SpatialDNAError(ValueError):
    pass


CONCEPTS: dict[str, tuple[str, ...]] = {
    "operations": ("operations", "operational", "execution", "workflow", "runbook"),
    "leadership": ("leadership", "leader", "managed", "manager", "management", "directed", "supervised", "supervision"),
    "shift": ("shift", "multi-shift", "scheduling", "labor balancing"),
    "hospitality": ("hospitality", "restaurant", "dining", "front-of-house", "foh", "back-of-house", "boh", "bar", "guest"),
    "financial": ("p&l", "financial", "prime cost", "margin", "cost variance", "sales", "underwriting"),
    "inventory": ("inventory", "reconciliation", "ordering", "stock"),
    "training": ("training", "trained", "train", "onboard", "onboarding", "develop", "development"),
    "workforce": ("workforce", "team", "staff", "staffing", "retention", "recruit", "recruiting"),
    "compliance": ("compliance", "audit", "health department", "ecosure", "mlcc", "liquor", "servsafe", "tips", "safety"),
    "service": ("service", "guest", "customer", "escalation", "culture"),
    "multiunit": ("multi-unit", "multi-location", "multiple markets", "new store", "nso", "regional"),
    "systems": ("systems", "system", "architecture", "pipeline", "deterministic", "serializer", "software", "three.js", "webgl"),
    "analytics": ("analytics", "analysis", "forecast", "forecasting", "data", "variance"),
    "identity": ("identity", "professional archetype", "operations systems leader"),
    "corroboration": ("corroborated", "entrustment", "advancement", "selected", "promotion", "reference"),
}


PLANE_META = {
    "plane_01": ("Identity", "#3B82F6"),
    "plane_02": ("Work History", "#F59E0B"),
    "plane_03": ("Education & Technical Competency", "#64748B"),
    "plane_04": ("Creative Works & Projects", "#EC4899"),
    "plane_05": ("Psychometric & Cognitive Profile", "#8B5CF6"),
    "plane_06": ("References & Testimony", "#10B981"),
}

AZIMUTHS = [
    ("Lateral North (+Z)", 0.0),
    ("Lateral East (+X)", 90.0),
    ("Lateral South (-Z)", 180.0),
    ("Lateral West (-X)", 270.0),
]

FLOOR_STATES = {"CONFLICTED", "UNRESOLVED", "PROVISIONAL"}


def _concepts(text: str) -> set[str]:
    t = re.sub(r"\s+", " ", text.lower())
    found: set[str] = set()
    for concept, terms in CONCEPTS.items():
        if any(term in t for term in terms):
            found.add(concept)
    return found


def _stable_jitter(atom_id: str) -> float:
    n = int(hashlib.sha256(atom_id.encode("utf-8")).hexdigest()[:8], 16)
    return float((n % 3001) / 100.0 - 15.0)


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for line_no, raw in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        if not raw.strip():
            continue
        try:
            out.append(json.loads(raw))
        except json.JSONDecodeError as exc:
            raise SpatialDNAError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
    return out


@dataclass(frozen=True)
class Binding:
    atom_id: str
    binding_class: str
    relevance: float
    matched_receptors: tuple[str, ...]
    matched_concepts: tuple[str, ...]


class SpatialDNAEngine:
    def __init__(self, nodes: list[dict[str, Any]], edges: list[dict[str, Any]]):
        self.nodes = nodes
        self.edges = edges
        self.node_by_id = {n["atom_id"]: n for n in nodes}
        self.adjacency: dict[str, set[str]] = defaultdict(set)
        for e in edges:
            self.adjacency[e["source"]].add(e["target"])
            self.adjacency[e["target"]].add(e["source"])
        self.validate_graph()

    @classmethod
    def from_repo(cls, root: str | Path) -> "SpatialDNAEngine":
        root = Path(root)
        return cls(
            _load_jsonl(root / "data" / "candidate_spatial_dna_nodes.jsonl"),
            _load_jsonl(root / "data" / "candidate_spatial_dna_edges.jsonl"),
        )

    def validate_graph(self) -> None:
        ids = [n.get("atom_id") for n in self.nodes]
        if len(ids) != len(set(ids)):
            raise SpatialDNAError("Duplicate atom_id detected")
        required = {
            "atom_id", "candidate", "domain", "plane_assignment", "branch_provenance",
            "evidence_provenance", "evidence_state", "semantic_ceiling", "proposition",
        }
        for n in self.nodes:
            missing = required - n.keys()
            if missing:
                raise SpatialDNAError(f"{n.get('atom_id', '<unknown>')}: missing {sorted(missing)}")
            if n["plane_assignment"] not in PLANE_META:
                raise SpatialDNAError(f"{n['atom_id']}: unknown plane {n['plane_assignment']}")
        for e in self.edges:
            if e["source"] not in self.node_by_id or e["target"] not in self.node_by_id:
                raise SpatialDNAError(f"{e.get('edge_id')}: edge endpoint absent from node ledger")

    def _raw_binding(self, atom: dict[str, Any], receptors: list[dict[str, Any]]) -> Binding:
        atom_text = " ".join(str(atom.get(k, "")) for k in (
            "domain", "branch_provenance", "category", "semantic_ceiling", "proposition"
        ))
        atom_concepts = _concepts(atom_text)
        matched_receptors: list[str] = []
        all_hits: set[str] = set()
        weighted = 0.0
        for receptor in receptors:
            receptor_text = f"{receptor.get('category', '')} {receptor.get('verbatim_text', receptor.get('verbatim_clause', ''))}"
            hits = atom_concepts & _concepts(receptor_text)
            if hits:
                matched_receptors.append(receptor["receptor_id"])
                all_hits |= hits
                weighted += len(hits) * float(receptor.get("weight", 1))

        hit_count = len(all_hits)
        relevance = min(1.0, 0.20 + 0.11 * hit_count + 0.025 * weighted) if hit_count else 0.0

        # Direct requires multiple independent semantic hinges or broad receptor coverage.
        if hit_count >= 3 or (hit_count >= 2 and len(matched_receptors) >= 2):
            cls = "DIRECT_BIND"
        elif hit_count >= 1:
            cls = "TRANSFERABLE_BIND"
        else:
            cls = "NON_BIND"

        return Binding(
            atom_id=atom["atom_id"],
            binding_class=cls,
            relevance=round(relevance, 6),
            matched_receptors=tuple(sorted(set(matched_receptors))),
            matched_concepts=tuple(sorted(all_hits)),
        )

    def bind(self, receptors: list[dict[str, Any]]) -> dict[str, Binding]:
        bindings = {n["atom_id"]: self._raw_binding(n, receptors) for n in self.nodes}

        # One-hop graph propagation can establish transferability, never direct evidence.
        upgraded: dict[str, Binding] = dict(bindings)
        for atom_id, b in bindings.items():
            if b.binding_class != "NON_BIND":
                continue
            direct_neighbors = [
                nid for nid in self.adjacency.get(atom_id, ())
                if bindings[nid].binding_class == "DIRECT_BIND"
            ]
            if direct_neighbors:
                upgraded[atom_id] = Binding(
                    atom_id=atom_id,
                    binding_class="TRANSFERABLE_BIND",
                    relevance=0.25,
                    matched_receptors=(),
                    matched_concepts=("graph_corroboration",),
                )
        return upgraded

    def _plane_scores(self, bindings: dict[str, Binding]) -> dict[str, float]:
        scores = defaultdict(float)
        for n in self.nodes:
            b = bindings[n["atom_id"]]
            weight = {"DIRECT_BIND": 3.0, "TRANSFERABLE_BIND": 1.0, "NON_BIND": 0.0}[b.binding_class]
            scores[n["plane_assignment"]] += weight * (0.5 + b.relevance)
        return {p: round(scores[p], 6) for p in PLANE_META}

    def _coordinates(
        self,
        atom: dict[str, Any],
        binding: Binding,
        plane_azimuth: dict[str, float],
    ) -> dict[str, Any]:
        # Recovered semantic-distance contract: R = clamp(11 - 7*match_strength, 3, 10).
        match_radius = min(10.0, max(3.0, 11.0 - binding.relevance * 7.0))
        plane = atom["plane_assignment"]
        if plane in plane_azimuth:
            theta = math.radians(plane_azimuth[plane] + _stable_jitter(atom["atom_id"]))
            x = math.sin(theta) * match_radius
            z = math.cos(theta) * match_radius
        else:
            x = z = 0.0

        state = str(atom.get("evidence_state", "")).upper()
        if state in FLOOR_STATES:
            y = -2.8
            zone = "FLOOR"
        elif binding.binding_class == "DIRECT_BIND":
            y = min(5.0, 2.0 + binding.relevance * 2.5)
            zone = "CEILING"
        else:
            y = (binding.relevance - 0.5) * 0.8
            zone = "BASELINE"

        x, y, z = round(x, 6), round(y, 6), round(z, 6)
        geom_radius = round(math.sqrt(x * x + z * z), 6)
        angular_azimuth = None if geom_radius == 0 else round((math.degrees(math.atan2(x, z)) + 360.0) % 360.0, 6)
        if not (-10 <= x <= 10 and -5 <= y <= 5 and -10 <= z <= 10):
            raise SpatialDNAError(f"OUT_OF_BOUNDS_ERROR: {atom['atom_id']} -> {(x, y, z)}")
        return {
            "x": x, "y": y, "z": z,
            "match_radius": round(match_radius, 6),
            "geometric_radius": geom_radius,
            "angular_azimuth_degrees": angular_azimuth,
            "polarity_zone": zone,
        }

    def compile(self, observation: dict[str, Any]) -> dict[str, Any]:
        receptors = observation["demand_envelope"]["receptors"]
        bindings = self.bind(receptors)
        scores = self._plane_scores(bindings)
        active = sorted(scores, key=lambda p: (-scores[p], p))[:4]
        plane_azimuth = {plane: AZIMUTHS[i][1] for i, plane in enumerate(active)}

        atoms: list[dict[str, Any]] = []
        for n in self.nodes:
            b = bindings[n["atom_id"]]
            coords = self._coordinates(n, b, plane_azimuth)
            atoms.append({
                "atom_id": n["atom_id"],
                "plane_id": n["plane_assignment"],
                "domain": n["domain"],
                "branch_provenance": n["branch_provenance"],
                "evidence_provenance": n["evidence_provenance"],
                "evidence_state": n["evidence_state"],
                "conflict_flag": n.get("conflict_flag"),
                "semantic_ceiling": n["semantic_ceiling"],
                "proposition": n["proposition"],
                "binding_class": b.binding_class,
                "relevance": b.relevance,
                "matched_receptors": list(b.matched_receptors),
                "matched_concepts": list(b.matched_concepts),
                "quarantine_action": ("PRESERVE_CONFLICT_ON_FLOOR" if str(n.get("evidence_state", "")).upper() in FLOOR_STATES else None),
                "suppression_signature": ({
                    "mode": "NO_POSITIVE_BIND",
                    "negative_space_constraints": list(observation["demand_envelope"].get("negative_space_constraints", [])),
                    "triggered_constraints": [],
                    "note": "NON_BIND reflects absence of positive receptor binding; no negative constraint is asserted without a deterministic trigger rule.",
                } if b.binding_class == "NON_BIND" else None),
                **coords,
            })

        claims = []
        for a in atoms:
            if a["binding_class"] == "NON_BIND" or a["evidence_state"] == "UNRESOLVED":
                continue
            claims.append({
                "claim_id": f"CLAIM-{a['atom_id']}",
                "atom_id": a["atom_id"],
                "binding_class": a["binding_class"],
                "authorized_expression": a["proposition"],
                "semantic_ceiling": a["semantic_ceiling"],
                "evidence_state": a["evidence_state"],
                "conflict_flag": a["conflict_flag"],
                "provenance": a["evidence_provenance"],
                "rendered_with_trace": f"{a['proposition']} [Bound: {a['atom_id']}]",
            })

        counts = {
            "total_atoms_evaluated": len(atoms),
            "direct_bind_count": sum(a["binding_class"] == "DIRECT_BIND" for a in atoms),
            "transferable_bind_count": sum(a["binding_class"] == "TRANSFERABLE_BIND" for a in atoms),
            "non_bind_count": sum(a["binding_class"] == "NON_BIND" for a in atoms),
            "ceiling_polarity_count": sum(a["polarity_zone"] == "CEILING" for a in atoms),
            "floor_polarity_count": sum(a["polarity_zone"] == "FLOOR" for a in atoms),
        }

        active_planes = []
        for i, p in enumerate(active):
            domain_name, color = PLANE_META[p]
            active_planes.append({
                "plane_id": p,
                "domain_name": domain_name,
                "azimuth": AZIMUTHS[i][0],
                "azimuth_degrees": AZIMUTHS[i][1],
                "color_hex": color,
                "domain_alignment_score": scores[p],
            })

        # Surface Transducer: deterministic layout packet for Resume Factory.
        safe_claims = [
            c for c in claims
            if next(a for a in atoms if a["atom_id"] == c["atom_id"])["polarity_zone"] != "FLOOR"
        ]
        safe_claims.sort(
            key=lambda c: (
                -next(a for a in atoms if a["atom_id"] == c["atom_id"])["relevance"],
                c["atom_id"],
            )
        )

        header_atoms = [atom_id for atom_id in ("ID-001", "ID-002", "ID-003") if atom_id in self.node_by_id]
        identity_name = self.node_by_id.get("ID-001", {}).get("candidate", "Christopher Flournoy")
        identity_location = self.node_by_id.get("ID-002", {}).get("proposition", "")

        executive_claims = [c for c in safe_claims if c["binding_class"] == "DIRECT_BIND"][:4]
        executive_bound = [c["atom_id"] for c in executive_claims]
        executive_content = " ".join(c["rendered_with_trace"] for c in executive_claims)

        roles = []
        work_atoms = [
            a for a in atoms
            if a["domain"] == "Work History"
            and a["binding_class"] != "NON_BIND"
            and a["polarity_zone"] != "FLOOR"
        ]
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for atom in work_atoms:
            grouped[atom["branch_provenance"]].append(atom)
        for company in sorted(grouped):
            group = sorted(grouped[company], key=lambda a: (-a["relevance"], a["atom_id"]))
            roles.append({
                "company": company,
                "location": "",
                "title": group[0]["semantic_ceiling"],
                "tenure": self.node_by_id[group[0]["atom_id"]].get("chronology", ""),
                "bound_atoms": [a["atom_id"] for a in group],
                "bullets": [f'{a["proposition"]} [Bound: {a["atom_id"]}]' for a in group],
            })

        competency_atoms = [
            a for a in atoms
            if a["domain"] in {"Education and Technical Competency", "Creative Works and Projects"}
            and a["binding_class"] != "NON_BIND"
            and a["polarity_zone"] != "FLOOR"
        ]
        competency_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for atom in competency_atoms:
            competency_groups[self.node_by_id[atom["atom_id"]].get("category", atom["domain"])].append(atom)
        bound_categories = []
        for category in sorted(competency_groups):
            group = sorted(competency_groups[category], key=lambda a: (-a["relevance"], a["atom_id"]))
            bound_categories.append({
                "category": category,
                "items": [f'{a["proposition"]} [Bound: {a["atom_id"]}]' for a in group],
            })

        dynamic_layout_elements = {
            "persona_surface": "TARGET_BOUNDED_EVIDENCE_PROJECTION",
            "transducer_profile": "ATS_COMPLIANT_LINEAR",
            "layout_containers": [
                {
                    "container_id": "HEADER",
                    "order": 1,
                    "content": {
                        "name": identity_name,
                        "title": observation["entity_metadata"].get("job_title", ""),
                        "location": identity_location,
                    },
                    "bound_atoms": header_atoms,
                },
                {
                    "container_id": "EXECUTIVE_PROJECTION",
                    "order": 2,
                    "receptor_alignment": sorted({
                        rid
                        for c in executive_claims
                        for rid in next(a for a in atoms if a["atom_id"] == c["atom_id"])["matched_receptors"]
                    }),
                    "content": executive_content,
                    "bound_atoms": executive_bound,
                },
                {
                    "container_id": "TARGETED_WORK_HISTORY",
                    "order": 3,
                    "roles": roles,
                },
                {
                    "container_id": "COMPETENCY_MATRIX",
                    "order": 4,
                    "bound_categories": bound_categories,
                    "bound_atoms": [a["atom_id"] for a in competency_atoms],
                },
            ],
        }

        entity = observation["entity_metadata"]
        canonical = {
            "contract_version": "MARA_LAYOUT_PAYLOAD_v1",
            "source_observation_contract": observation.get("contract_version"),
            "source_observation_id": observation.get("observation_id"),
            "timestamp": observation.get("timestamp"),
            "provenance": dict(observation.get("provenance", {})),
            "metadata": {
                "target_job_id": observation.get("observation_id"),
                "target_title": entity.get("job_title"),
                "target_company": entity.get("employer"),
                "target_location": entity.get("location"),
                "target_compensation": entity.get("compensation"),
                "employment_type": entity.get("employment_type"),
                "industry": entity.get("industry"),
            },
            "demand_envelope": observation["demand_envelope"],
            "spatial_configuration": {
                "active_lateral_planes": active_planes,
                "plane_scores": scores,
                "counts": counts,
            },
            "spatial_atoms_projection": atoms,
            "normalized_projection": {
                "claims": claims,
                "projection_rule": "No expression may exceed its source atom semantic ceiling.",
            },
            "dynamic_layout_elements": dynamic_layout_elements,
            "resume_factory_handoff": {
                "claims": claims,
                "prohibited_atom_ids": [a["atom_id"] for a in atoms if a["binding_class"] == "NON_BIND"],
                "quarantined_atom_ids": [a["atom_id"] for a in atoms if a["polarity_zone"] == "FLOOR"],
            },
        }
        fingerprint_input = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
        canonical["run_fingerprint_sha256"] = hashlib.sha256(fingerprint_input).hexdigest()
        baseline = observation.get("historical_baseline")
        if baseline:
            canonical["historical_baseline_comparison"] = {
                "baseline_status": baseline.get("status"),
                "reported": {k: v for k, v in baseline.items() if k != "status"},
                "derived": {
                    "active_planes": active,
                    "direct_bind_count": counts["direct_bind_count"],
                    "transferable_bind_count": counts["transferable_bind_count"],
                    "non_bind_count": counts["non_bind_count"],
                    "ceiling_count": counts["ceiling_polarity_count"],
                    "floor_count": counts["floor_polarity_count"],
                },
            }
        return canonical
