# Witnora Verify Docker Action

Witnora Verify Docker is a self-contained GitHub Action package for scoped
release artifact verification, claim-boundary scanning, selected proof-evidence
replay, and trust-card generation.

The Docker package reduces external setup friction by installing Witnora-Core
inside the action image from a tagged source ref. It is heavier than the
composite action, but more reproducible for repositories that do not want to
prepare Python and Witnora-Core before verification.

Witnora Verify checks release artifact integrity and optionally replays selected
proof evidence. It does not rerun the solver, does not regenerate benchmark
instances, does not regenerate DRAT proofs, does not rerun the full benchmark
diagnostic, and does not replace human review.

## Quick Start

```yaml
- uses: joeyst8/witnora-verify-action@v1
  with:
    source-zip: witnora-core-v1.0-public-preprint.zip
    diagnostic-zip: witnora-core-v0.9.8-full-tseitin-minfill-diagnostic.zip
    manifest: RELEASE_ASSETS_MANIFEST_v1.0-public-preprint.md
    depth: partial
    select: largest
    fail-on-risk-flags: HASH_MISMATCH,MISSING_FILE,ACTION_INPUT_MISMATCH,UNVERIFIED_CLAIM
    fail-on-verdict: NOT_VERIFIED,PARTIALLY_VERIFIED,OVERCLAIM
```

## Docker Image Dependency

The Dockerfile installs Witnora-Core from:

```text
git+https://github.com/joeyst8/witnora-core.git@v1.7-docker-action-runner
```

This package does not claim a PyPI package exists. Override the build arg
`WITNORA_CORE_REF` only when deliberately testing another frozen Witnora-Core
tag:

```bash
docker build --build-arg WITNORA_CORE_REF=<tag> -t witnora-verify-action .
```

The default ref is `v1.7-docker-action-runner`. That tag must be available from
the repository used by the Docker build before external Docker publication.

## Inputs

- `source-zip`: source archive path.
- `diagnostic-zip`: diagnostic artifact path.
- `manifest`: release asset manifest path.
- `depth`: `metadata` or `partial`, default `metadata`.
- `select`: `largest`, `first`, `all`, or `instance`.
- `select-instance`: selected row, for example `tseitin_20:c=2`.
- `rerun-drat-trim`: optional selected proof replay with drat-trim.
- `drat-trim`: path to drat-trim inside the container.
- `max-replay-proofs`: cap for optional drat-trim replay.
- `replay-timeout-seconds`: timeout for optional drat-trim replay.
- `fail-on`: backward-compatible fail policy.
- `fail-on-risk-flags`: comma-separated risk flags that fail the action.
- `fail-on-verdict`: comma-separated verdicts that fail the action.
- `out-dir`: output directory.
- `upload-artifacts`: retained for input parity. Docker actions write output
  files; upload them with a separate `actions/upload-artifact` step.

## Outputs

- `verdict`
- `certification_level`
- `verification_depth`
- `replay_depth`
- `risk_flags`
- `selected_evidence`
- `trust_card_path`
- `report_path`

## Depth Modes

- `metadata`: artifact hashes, file presence, manifest consistency, and
  claim-boundary scan.
- `partial`: selected proof syntax, existing drat-trim logs, selected
  independent checker replay, and optional selected drat-trim replay.
- `full`: not supported yet.

## What This Action Verifies

Metadata mode verifies artifact hashes, file presence, manifest consistency,
and the heuristic claim-boundary scan.

Partial replay verifies selected evidence already present in the diagnostic
artifact: proof syntax, existing drat-trim log status, independent checker
replay, and optional selected drat-trim replay.

## What This Action Does Not Verify

- It does not rerun the solver.
- It does not regenerate benchmark instances.
- It does not regenerate CNFgen instances.
- It does not rerun the full benchmark diagnostic.
- It does not regenerate DRAT proofs.
- It does not prove claims outside selected evidence.
- It does not replace human review.

## Composite vs Docker

- Composite action: lighter, faster to inspect, but requires Python and
  Witnora-Core setup in the caller's runner.
- Docker action: self-contained and more reproducible at runtime, but heavier,
  slower to start, and requires a Docker-capable runner.

Composite action requires Python and Witnora-Core setup in the caller's runner.

The Docker action should not be treated as externally validated until the Docker
build/run self-test passes in GitHub Actions or another Docker-capable
environment.

## Claim Boundary

This package does not claim parity support, broad XOR extraction,
CryptoMiniSat-style extraction, competitive SAT solving, industrial benchmark
performance, full DRAT/RAT/LRAT/FRAT support, P vs NP progress, or HARD/UNKNOWN
status claims.
