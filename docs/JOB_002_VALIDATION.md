# JOB-002 validation authority

JOB-002 has two distinct historical authorities that must not be collapsed:

1. **Dynamic Layout Sheet excerpt** — 12 explicitly projected rows: 9 DIRECT_BIND and 3 TRANSFERABLE_BIND.
2. **Bootstrap aggregate statement** — 44 total atoms: 12 DIRECT_BIND, 16 TRANSFERABLE_BIND, 16 NON_BIND.

These are not the same thing. The Sheet is a selected projection excerpt, while the bootstrap claims whole-graph aggregate counts. In addition, the Sheet references `PS-PRFL-001` and `RF-REF-001`, which do not exist in the recovered current 44-node ledger.

The executable acceptance rule is therefore:

- Exact-match the binding class and polarity of every Sheet row whose atom exists in the recovered current ledger.
- Reject silent aliases for missing legacy atom IDs.
- Preserve the bootstrap aggregate as historical reported data, but do not force the current ledger to reproduce it unless the historical ledger revision is recovered.
- Validate current whole-graph invariants independently: 44 nodes, 11 edges, four strategy-locked active planes, 16 inactive-plane NON_BIND atoms for the Hospitality strategy, deterministic replay, provenance, quarantine, and containment.

This prevents a contradictory historical aggregate from becoming a hidden hard-coded override.
