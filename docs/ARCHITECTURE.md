# Spatial DNA executable architecture

## Ownership boundaries

### Scout
Scout observes the target. It emits `SCOUT_TARGET_OBSERVATION_v1` with provenance, entity metadata, verbatim requirement clauses, and negative-space constraints. Scout cannot read candidate evidence and cannot bind candidate atoms.

### Demand decomposition
`sdna_px.demand` turns Scout's verbatim clauses into addressable `D_01...D_n` receptors by deterministic structural tagging. It preserves the clause text byte-for-byte after whitespace normalization and records that candidate data was not accessed.

### MARA strategy lock
A strategy must exist before binding. The strategy selects exactly four candidate evidence planes and supplies the persona surface. The job envelope cannot choose or rewrite the candidate strategy.

### Spatial DNA
The candidate substrate is the recovered 44-atom evidence graph plus 11 v2 relations. Chronology is metadata, not the organizing axis. Evidence state, provenance, conflicts, proposition text, and semantic ceilings survive traversal.

### Binding and geometry
Candidate atoms in inactive planes are NON_BIND for the locked strategy. Active-plane atoms are evaluated against the demand receptors and become DIRECT_BIND or TRANSFERABLE_BIND. Conflicted/provisional/unresolved evidence stays on the Floor. Geometry is deterministic and bounded.

Two radii are retained because the historical corpus used one name for two different concepts:

- `match_radius`: semantic distance from the target centroid.
- `geometric_radius`: `sqrt(x²+z²)`.

### Projection transducer
The engine emits `MARA_LAYOUT_PAYLOAD_v1`, including:

- original observation/provenance;
- explicit strategy-lock receipt;
- demand receptors;
- all projected atoms;
- graph relation rays;
- demand binding rays;
- bounded claims copied from source propositions;
- layout containers;
- Resume Factory handoff lists;
- deterministic run fingerprint.

### Resume Factory boundary
The harness does not invent polished résumé claims. Resume Factory receives authorized expressions and bound atom IDs. An outward statement may not exceed the atom's semantic ceiling.

### Passive observers
`viewer/` and `web/` consume projection payloads only. They may change camera/view state and inspect atoms. They cannot calculate, relax, rebind, or rewrite coordinates.

## Execution surfaces

Single packet:

`scripts/run_pipeline.py <SCOUT_PACKET> --strategy <STRATEGY> -o <OUTPUT>`

Batch:

`scripts/run_batch.py <SCOUT_PACKET_DIR> <OUTPUT_DIR> --strategy <STRATEGY>`

Regression:

`python -m unittest discover -s tests -v`

The GitHub Actions workflow runs all three execution paths and builds the Three.js observer on push, pull request, manual dispatch, and hourly schedule.
