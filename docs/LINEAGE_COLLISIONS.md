# Lineage collision registry

## LC-001 — JOB-002 golden payload vs recovered 44-node ledger

The authoritative JOB-002 Dynamic Layout Sheet references two atom IDs that are absent from the recovered 44-node ledger:

- `PS-PRFL-001` — Leadership Traits
- `RF-REF-001` — Professional Reference / Charles Tolbert

The recovered ledger instead contains the current four psychometric atoms including `PS-AIREV-001`, and the current reference plane contains `RF-TWIN-001`, `RF-PAN-001`, `RF-PLAY-001`, and `RF-UNPOP-001`.

Drive revision history for `candidate_spatial_dna_nodes.jsonl` contains only one revision (2026-09-19), so the older 44-node revision used to generate the JOB-002 sheet is not recoverable from that document's version history.

### Rule

Do not silently alias, rename, or replace these IDs.

The repo therefore distinguishes:

1. **Current candidate substrate revision** — the recovered 44-node ledger committed under `data/`.
2. **Legacy JOB-002 golden excerpt** — preserved as a validation artifact showing historical behavior.
3. **Compatibility status** — structural contract and shared-atom behavior can be tested; byte-for-byte whole-run equivalence is blocked until the exact historical 44-node revision is recovered or an explicit migration map is authorized.

This is a lineage defect, not a reason to stop the executable build.
