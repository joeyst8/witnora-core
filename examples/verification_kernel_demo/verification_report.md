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

- `sha256_manifest_match`: pass
- `claim_boundary_scan`: pass

## External Verification

- `SHA256 archive checks`
- `unit test suite`
- `drat-trim`

## Artifact Hashes

- `paper/witnora_tseitin_certified_collapse.pdf`: `A98910C817974D3D15F6847690CD197008362A06984FA38BE81194BE7D26DB9A`

## Certification Level

`RELEASE_EVIDENCE_VERIFIED`

## Allowed Claims

- Release artifacts can be checked against recorded SHA256 hashes.
- Trust is scoped to the evidence listed in the report.

## Forbidden Claims

- parity support
- broad XOR extraction
- competitive SAT solving
- P vs NP progress

## Risk Flags

- none

## Final Verdict

`VERIFIED`
