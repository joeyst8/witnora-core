# Witnora Verification Report

## Claim Being Audited

Witnora-Core release evidence is available with source, diagnostic artifact,
paper PDF, and SHA256 hashes.

## Evidence Provided

- `witnora-core-v1.0-public-preprint-final.zip`
- `witnora-core-v0.9.8-full-tseitin-minfill-diagnostic.zip`
- `paper/witnora_tseitin_certified_collapse.pdf`
- `RELEASE_ASSETS_MANIFEST_v1.0-public-preprint.md`

## Checks Performed

- `source_archive_sha256`: pass (depth: `metadata_hash_checks_only`)
- `diagnostic_artifact_sha256`: pass (depth: `metadata_hash_checks_only`)
- `claim_boundary_scan`: pass (depth: `heuristic_text_scan`)

## Verification Depth

`metadata_hash_checks_only`

The artifact hashes match the manifest, required files are present, and the
claim-boundary scanner found no affirmative forbidden claims. This is a metadata
and artifact-integrity check. It does not rerun the scientific proofs, rerun
drat-trim on all proofs, or rerun the benchmark diagnostic.

## Evidence Checked

- `witnora-core-v1.0-public-preprint-final.zip` (source_archive): MATCH
- `witnora-core-v0.9.8-full-tseitin-minfill-diagnostic.zip` (diagnostic_artifact): MATCH

## External Verification

- none rerun by this metadata-only report

## Artifact Hashes

- `paper/witnora_tseitin_certified_collapse.pdf`: `A98910C817974D3D15F6847690CD197008362A06984FA38BE81194BE7D26DB9A`

## Certification Level

`RELEASE_ARTIFACT_INTEGRITY_VERIFIED`

## Claim Boundary Scanner Limitation

The claim-boundary scanner is a heuristic text safety net, not a proof of
absence of overclaims. It can miss paraphrases, ambiguous wording, or
context-sensitive claims. A human audit is still required before public release.

claim_scan_depth: `heuristic_text_scan`

## Allowed Claims

- Release artifacts can be checked against recorded SHA256 hashes.
- Trust is scoped to the evidence listed in the report.

## Forbidden Claims

- parity support
- broad XOR extraction
- competitive SAT solving
- P vs NP progress

## Risk Flags

- METADATA_ONLY
- DRAT_TRIM_NOT_RERUN
- INDEPENDENT_CHECKER_NOT_RERUN
- CLAIM_SCAN_HEURISTIC_ONLY

## Final Verdict

`ARTIFACT_INTEGRITY_VERIFIED`
