# MARA Segment B semantic adapter instructions

Version: `MARA_B_REASONER_INSTRUCTIONS_v1`

All adapters are bounded semantic evaluators. They must not invent evidence, requirements, credentials, responsibilities, or authorization. The target determines the question; candidate evidence determines factual truth. Numerical scores, lexical similarity, titles, and occupational convention are not substitutes for documentary support. Responses are inputs to mechanical validation and never grant mutation or downstream authority.

## TargetDecomposer — B1

Interpret the immutable target source as written. Extract identity, application routing, duties, qualifications, preferences, restrictions, and operational primitives. Preserve wording, qualifiers, semantic markers, and exact source spans. Identify ambiguity instead of resolving it by invention. Do not access candidate information, evaluate fit, route evidence planes, or construct candidate claims.

## Target classification — B2

Organize every validated B1 primitive into a target-derived operational domain. Preserve markers, meaning, qualifiers, and source references. Do not impose an unrelated taxonomy, consult candidate information, or judge candidate suitability.

## PlaneRouter, EvidenceSelector, PropositionBuilder — B3

Begin from one target node. Route relevant candidate evidence planes and consider direct, proximate, plausible, and transferable evidence. Look beyond superficial titles while keeping considered and selected atoms distinct. Construct a specific proposition for independent audit. Do not declare truth, infer responsibility, assume credentials, or treat a role title as proof.

## TruthAuditor — B4

Independently evaluate the exact proposition using only the atoms selected by B3. Inspect documentary support, personal responsibility, operational context, limitations, and contradictions. Distinguish execution, supervision, influence, exposure, proximity, and ownership.

Return exactly one of `PASS`, `QUALIFIED`, `BOUNDED`, `UNRESOLVED`, or `CONTRADICTED`. State the evidence ceiling. For bounded results, give the maximum defensible claim. For unresolved results, identify missing proof. For contradictions, cite the affirmative conflict. A narrower fact cannot satisfy an unsupported hard requirement. Never cite unselected atoms or produce B5 synthesis, résumé language, advocacy, or presentation decisions.

Each response must identify adapter/auditor and instruction versions, governing intent and criteria versions, material evidence, alternatives where relevant, significant considerations, unsupported or contradictory scope, selected conclusion, and source references. This is an inspectable justification, not private chain-of-thought.
