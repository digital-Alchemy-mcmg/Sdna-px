# Sdna-px

Executable reconstruction of the Spatial DNA candidate-evidence graph and projection pipeline.

## What is authoritative here

- `data/candidate_spatial_dna_nodes.jsonl`: the 44-atom candidate substrate recovered from Google Drive.
- `data/candidate_spatial_dna_edges.jsonl`: the 11-edge v2 graph recovered from Google Drive.
- `fixtures/job_002.json`: Method Hospitality JOB-002 demand-receptor fixture recovered from the Spatial DNA corpus.
- `src/sdna_px/`: deterministic traversal and payload compiler.
- `tests/`: regression checks for lineage, quarantine, bounds, determinism, and traceability.

## Pipeline

`JOB -> DEMAND RECEPTORS -> CANDIDATE GRAPH -> BINDING -> SPATIAL COORDINATES -> MARA_LAYOUT_PAYLOAD_v1`

Chronology is metadata/lens, not the organizing axis of the candidate graph.

## Run

Requires Python 3.11+ and no third-party runtime dependencies.

```bash
python -m unittest discover -s tests -v
python scripts/run_job_002.py
```

The JOB-002 command writes `artifacts/job_002_projection.json`.

## Non-negotiable invariants

1. Candidate facts are never fabricated by traversal.
2. Every outward bullet is copied from a source atom proposition and carries `[Bound: ATOM_ID]`.
3. CONFLICTED / UNRESOLVED / PROVISIONAL atoms can be inspected but cannot occupy the Ceiling.
4. Coordinates remain inside X/Z [-10,10], Y [-5,5].
5. No physics, force layout, random placement, or LLM reasoning occurs in traversal.
6. Same input produces the same result.

See `docs/IMPLEMENTATION_DECISIONS.md` for the recovered-vs-resolved contract boundary.
