# Sdna-px

Executable reconstruction of the Spatial DNA candidate-evidence graph and projection pipeline.

## What is authoritative here

- `data/candidate_spatial_dna_nodes.jsonl`: the 44-atom candidate substrate recovered from Google Drive.
- `data/candidate_spatial_dna_edges.jsonl`: the 11-edge v2 graph recovered from Google Drive.
- `fixtures/job_002.json`: Method Hospitality JOB-002 demand-receptor fixture recovered from the Spatial DNA corpus.
- `src/sdna_px/`: deterministic traversal and payload compiler.
- `contracts/`: durable SCOUT input and MARA layout output schemas.
- `tests/`: regression checks for lineage, quarantine, bounds, determinism, and traceability.
- `viewer/`: passive zero-physics coordinate observer for generated projection artifacts.
- `docs/AUTHORITY_MANIFEST.json`: source-to-repository lineage receipt for the recovered Drive ledgers.

## Pipeline

`SCOUT_TARGET_OBSERVATION_v1 -> DEMAND RECEPTORS -> STRATEGY-LOCKED CANDIDATE GRAPH -> BINDING -> SPATIAL COORDINATES -> MARA_LAYOUT_PAYLOAD_v1 -> Resume Factory`

Chronology is metadata/lens, not the organizing axis of the candidate graph.

## Run

Requires Python 3.11+ and no third-party runtime dependencies.

```bash
python -m unittest discover -s tests -v
python scripts/run_job_002.py
python scripts/run_pipeline.py fixtures/job_002_scout_observation.json --strategy strategies/hospitality_operations.json -o artifacts/job_002_from_scout.json

# many Scout packets, one locked strategy
python scripts/run_batch.py scout_packets/ artifacts/batch --strategy strategies/hospitality_operations.json
```

The JOB-002 command writes `artifacts/job_002_projection.json`.

Two passive observers are included:

- `viewer/`: zero-build diagnostic observer.
- `web/`: React 19 + Three.js 0.185 observer. Run `cd web && npm install && npm run dev`, then load a `MARA_LAYOUT_PAYLOAD_v1` JSON artifact. OrbitControls change only the camera; coordinates and binding state remain immutable.

CI builds the Three.js observer and preserves `web/dist` as the `spatial-dna-observer` workflow artifact.

## Non-negotiable invariants

1. Candidate facts are never fabricated by traversal.
2. Every outward bullet is copied from a source atom proposition and carries `[Bound: ATOM_ID]`.
3. CONFLICTED / UNRESOLVED / PROVISIONAL atoms can be inspected but cannot occupy the Ceiling.
4. Coordinates remain inside X/Z [-10,10], Y [-5,5].
5. No physics, force layout, random placement, or LLM reasoning occurs in traversal.
6. Same input produces the same result.

See `docs/IMPLEMENTATION_DECISIONS.md` for the recovered-vs-resolved contract boundary.


## Throughput contract

Batch execution is not a bypass. Every packet runs through the same Scout observation decomposition, MARA strategy lock, Spatial DNA binding/geometry, and layout-payload compiler as the single-job path. A batch emits one projection per job plus `batch_manifest.json` with fingerprints and failures.

The repository CI executes on every push/PR and on an hourly schedule. It tests the current 44-node/11-edge graph, JOB-002 lineage compatibility, the pre-receptor Scout handoff, batch throughput, the passive observer syntax, provenance, containment, quarantine, and deterministic replay.


## Current executable boundary

Implemented now:

- Certified Scout packet intake.
- Deterministic verbatim-clause → demand-receptor decomposition.
- Explicit pre-envelope MARA strategy lock.
- 44-atom / 11-edge candidate graph loading and validation.
- DIRECT / TRANSFERABLE / NON_BIND classification.
- Conflict quarantine and bounded deterministic coordinates.
- Separate semantic match radius and geometric radius.
- Candidate graph relation rays and demand-centroid binding rays.
- Evidence-bound normalized projection.
- PIN-style deterministic layout packet for Resume Factory consumption.
- Single-job and multi-job batch execution.
- Structured batch receipts and structured single-run errors.
- Passive 2D diagnostic observer and compiled Three.js observer.
- Push/PR/hourly CI regression and external failure watch.

Known lineage boundary:

- The historical JOB-002 Sheet references `PS-PRFL-001` and `RF-REF-001`, which are absent from the recovered current 44-atom ledger. They are intentionally not aliased. See `docs/LINEAGE_COLLISIONS.md` and `docs/JOB_002_VALIDATION.md`.
