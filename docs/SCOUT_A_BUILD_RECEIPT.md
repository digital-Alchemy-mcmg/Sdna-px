# SCOUT Segment A development receipt

Status: development validation only

Branch: `codex/rw-a`

Contract source: Scout Disk Studio 2.2.0 reference export, as supplied by the operator

Contract version: `SCOUT_DISK_STUDIO_2.2.0_OBSERVATION_v1`

## Canonical observation fields

The implementation preserves this exact sequence:

1. `Observation_ID`
2. `Collection_Date`
3. `Vendor`
4. `Employer`
5. `Job_Title`
6. `City`
7. `State`
8. `ZIP`
9. `Industry`
10. `Employment_Type`
11. `Compensation`
12. `Source_URL`
13. `Duplicate_Count`

Validation policy: exact names, exact order, no additional fields, no missing fields, no duplicate JSON keys, and no silent repair. The synthetic fixture uses the same contract and remains labeled non-production.

## Validation evidence

- Baseline before implementation: 27 existing tests passed.
- Focused Scout workbench suite after canonical correction: 9 tests passed.
- The focused suite covers alternate, reordered, duplicate, missing, and unrecognized contract fields; A1 batch bounds; A2 preservation; stable A3 identity; A4 integrity and pointer failures; deterministic freezing; A5 isolation; mixed decisions; and accepted-only B1 release.

- Integrated repository suite: 36 tests passed after the duplicate-key check was added.
- Deterministic CLI fixture: completed through `A5_REQUEST_READY` with one synthetic observation.
- Notebook verification: all 7 code cells executed; A4 reached `READY_FOR_A5`; the A5 request used `SCOUT_A5_REASONER_REQUEST_v1`.
- All 11 JSON schema/contract documents parsed successfully.
- Python source compilation and passive observer syntax check passed.
- The React/Three.js production build passed with the existing non-blocking Vite chunk-size warning.

## Remaining integration issues

- The original Scout Disk Studio 2.2.0 export file is not present in this repository, so source-file hash comparison remains unverified even though the operator supplied the authoritative enumeration.
- Production taxonomy resolver authority and ring provenance are not connected.
- Only the explicitly labeled simulated runner adapter exists.
- No live independent reasoner has been invoked; response tests use fixtures only.
- External stationary-sidecar storage and its credential policy remain unconfigured.
