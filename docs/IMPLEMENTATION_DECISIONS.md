# Implementation decisions and authority boundary

This file records where the executable reconstruction follows recovered authority and where it resolves contradictions that were present in the transferred corpus.

## Recovered authority

- Candidate substrate: 44 immutable evidence atoms recovered from Drive.
- Graph: 11 v2 edges recovered from Drive.
- Candidate graph is atemporal by default. Chronology remains atom metadata and may be used as a lens; traversal does not rank evidence by recency unless a future receptor explicitly requires freshness.
- Scout ends at structured target observation. Scout does not bind candidate evidence.
- FISSION is an internal MARA compiler layer. It cannot invent candidate facts or strengthen evidence.
- Binding classes: DIRECT_BIND, TRANSFERABLE_BIND, NON_BIND.
- Conflicts are preserved, never silently normalized.
- Canvas/renderer is a passive observer. It does not calculate or alter coordinates.
- Coordinate bounds: X/Z [-10, 10], Y [-5, 5].
- No force layout, gravity, springs, collision solvers, or random placement.
- Every downstream claim retains the atom ID and provenance.

## Resolved contradictions

### R had two meanings in the historical corpus

The recovered material used R both as semantic match radius and as geometric sqrt(X^2+Z^2), including center-axis examples with non-zero R. This implementation keeps both:

- `match_radius`: semantic distance from target demand, derived from match relevance.
- `geometric_radius`: actual sqrt(X^2+Z^2).

This preserves information instead of forcing incompatible meanings into one field.

### Angular jitter used an unstable runtime hash in reported script-era notes

Python's built-in hash is process-salted and therefore violates replay determinism. This implementation derives angular dispersion from SHA-256(atom_id), preserving the stated bounded jitter while making replay stable.

### Historical JOB-002 counts are not treated as proof

The source copy reports 12 direct / 16 transferable / 16 non-bind and 11 ceiling / 1 floor. Those values are retained in the fixture as a historical baseline. The executable engine independently derives its result and reports a baseline comparison. It does not force classifications merely to reproduce a prior narrative.

### FISSION input

The recovered 44-node ledger is already atomized. This implementation does not split those propositions further during traversal. A future source-ingestion compiler may create new atoms, but it must do so before graph binding and retain source provenance.

## Output boundary

The engine emits evidence-bound projection data for Resume Factory. It does not fabricate polished résumé prose. Resume Factory may render only expressions authorized by the projection packet and must preserve bound atom IDs.
