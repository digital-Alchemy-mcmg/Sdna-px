# SDNA B5 Airtable Overnight Control

## Objective
Build a durable Airtable landing zone for the actual baseline-ranking model outputs and preserve the B–B4 architecture state without inventing B5 architecture.

## Source-of-truth constraints
- The finalized B–B4 control document is authoritative for B through B4.
- B5 is still experimental and must not be canonized.
- The Airtable schema must be derived from the actual baseline-ranking outputs, not from imagined future fields.
- Raw model outputs must be preserved unchanged.

## Airtable ingestion contract
Normalize to one record per:
`run_id + job_id + rank`

Required normalized fields:
- model
- run_id
- job_id
- job_title
- rank
- candidate_uuid_raw
- candidate_uuid_resolved
- candidate_name_raw
- evidence_basis
- rankable_status
- source_artifact
- ingest_status

Rules:
- Never guess or silently expand a truncated UUID.
- Resolve shortened UUIDs only against the canonical applicant dataset.
- If ambiguous, leave candidate_uuid_resolved blank and mark unresolved.
- rankable_status: RANKED | NOT_RANKABLE | UNRESOLVED
- Keep source-model/run provenance intact.
- Do not bake consensus into source records.
- Re-ingestion must be idempotent and must not duplicate or overwrite another model/run.

## Cross-comparison requirement
Airtable must support direct comparison by Job ID and Rank across Qwen, Perplexity, GLM, and later Gemini/prism runs, including:
- same/different Rank 1 selections
- same/different Rank 2 selections
- top-two overlap
- NOT_RANKABLE disagreements
- candidate recurrence across models

## Durable repository outputs
Store:
1. raw model return artifacts
2. parser/import logic
3. Airtable schema/mapping
4. ingestion receipts
5. comparison-query/view definition
6. validation tests

## B–B4 durability
Preserve current canonical B–B4 materials. Do not reopen or silently rewrite B–B4 architecture. If an older artifact conflicts with the current control document, mark it historical/deprecated rather than merging the old rule back into canon.

## Stop conditions
Before writing model results into Airtable:
1. inspect the actual supplied return artifacts;
2. show/prove the exact source-field → Airtable-field mapping;
3. verify every source value has a deterministic landing place;
4. stop on unmapped or ambiguous values instead of inventing fields or guesses.

## Verification receipt
Return:
- branch and HEAD
- changed files
- Airtable base/table IDs or exact external blocker
- jobs found per model
- normalized ranking rows
- full UUIDs accepted
- truncated UUIDs resolved
- unresolved UUIDs
- NOT_RANKABLE rows
- parse failures
- tests run/results
- remaining blockers

Do not expand scope beyond this control document.
