"""Prepare the standalone Witnora Verify marketplace action repository package.

This script performs local packaging only. It does not create repositories,
push commits, publish marketplace listings, or contact GitHub.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil
import zipfile


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ACTION_DIR = REPO_ROOT / "marketplace-action"
DEFAULT_DIST_DIR = REPO_ROOT / "dist" / "witnora-verify-action"


README_TEXT = """# Witnora Verify Action

Witnora Verify is a scoped GitHub Action for release artifact integrity checks,
claim-boundary scanning, selected proof-evidence replay, and trust-card
generation.

Witnora Verify checks release artifact integrity and optionally replays selected
proof evidence. It does not rerun the solver, regenerate benchmark instances,
regenerate DRAT proofs, or replace human review.

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

## Install Witnora-Core

The action is a thin wrapper around `python -m witnora_core.ci`. For this MVP,
install Witnora-Core before invoking the action:

```yaml
- name: Install Witnora-Core
  run: python -m pip install git+https://github.com/joeyst8/witnora-core.git@v1.5.1-release-trust-polish
```

If `python -m witnora_core.ci` is unavailable, the action reports a setup error
equivalent to `WITNORA_CORE_NOT_INSTALLED`. This repository does not claim a PyPI package exists.

## Inputs

- `source-zip`: source archive path.
- `diagnostic-zip`: diagnostic artifact path.
- `manifest`: release asset manifest path.
- `depth`: `metadata` or `partial`, default `metadata`.
- `select`: `largest`, `first`, `all`, or `instance`.
- `select-instance`: selected row, for example `tseitin_20:c=2`.
- `rerun-drat-trim`: optional selected proof replay with drat-trim.
- `drat-trim`: path to drat-trim.
- `max-replay-proofs`: cap for optional drat-trim replay.
- `replay-timeout-seconds`: timeout for optional drat-trim replay.
- `fail-on-risk-flags`: comma-separated risk flags that fail the action.
- `fail-on-verdict`: comma-separated verdicts that fail the action.
- `out-dir`: output directory.
- `upload-artifacts`: upload report and trust card as workflow artifacts.

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

## Selection Policies

- `largest`: deterministic selection of the externally verified row with the
  largest recorded proof size, then variables, clauses, instance suffix, c
  value, and cap profile as tie-breakers.
- `first`: first externally verified row in deterministic sorted order.
- `all`: all externally verified rows for syntax/log/checker replay. Optional
  drat-trim replay remains bounded by `max-replay-proofs`.
- `instance`: selected by `select-instance`, for example `tseitin_20:c=2`.

Selected evidence is not all evidence unless `select: all` is used. Partial
replay never implies full benchmark replay.

## Risk Flags

| Risk flag | Meaning | Recommended action |
| --- | --- | --- |
| `METADATA_ONLY` | Metadata checks only were performed. | Use partial mode for selected replay. |
| `DRAT_TRIM_NOT_RERUN` | drat-trim was not rerun. | Enable selected drat-trim replay if required. |
| `INDEPENDENT_CHECKER_NOT_RERUN` | Independent checker did not rerun. | Use partial mode with valid evidence. |
| `CLAIM_SCAN_HEURISTIC_ONLY` | Claim scan is heuristic. | Keep human review. |
| `PROOF_SELECTION_LIMITED` | Only selected proofs were replayed. | Use `select: all` if appropriate. |
| `PROOF_SELECTION_NONE` | No proof evidence was selected. | Check selection inputs. |
| `PROOF_FILE_MISSING` | Selected proof file is absent. | Rebuild or reattach artifact. |
| `DRAT_TRIM_TIMEOUT` | Optional drat-trim replay timed out. | Increase timeout or replay fewer proofs. |
| `ACTION_INPUT_MISMATCH` | Input asset names do not match manifest. | Use manifest-listed assets. |
| `CHECKER_VERSION_NOT_RECORDED` | Checker version unavailable. | Record checker build details. |
| `UNVERIFIED_CLAIM` | Claim or manifest evidence gap. | Fix manifest or claim text. |
| `HASH_MISMATCH` | Asset hash differs from manifest. | Use the correct release asset. |
| `MISSING_FILE` | Required file is absent. | Attach or download the missing asset. |
| `GITHUB_CLI_NOT_AVAILABLE` | Release helper could not find gh. | Install gh or use dry-run output. |
| `RELEASE_TAG_NOT_FOUND` | Target release tag was not found. | Create release first or fix tag. |

## Fail-On Policies

Strict artifact integrity:

```yaml
fail-on-risk-flags: HASH_MISMATCH,MISSING_FILE,ACTION_INPUT_MISMATCH,UNVERIFIED_CLAIM
```

Require partial replay:

```yaml
fail-on-verdict: NOT_VERIFIED,PARTIALLY_VERIFIED
```

Require drat-trim rerun:

```yaml
fail-on-risk-flags: DRAT_TRIM_NOT_RERUN,DRAT_TRIM_TIMEOUT
```

Require full proof selection:

```yaml
fail-on-risk-flags: PROOF_SELECTION_LIMITED,PROOF_SELECTION_NONE
```

## Release Trust-Card Automation

Generate report and trust card with the action, then prepare upload plans with
the Witnora-Core helper:

```powershell
python scripts/attach_release_trust_card.py --release-tag v1 --trust-card trust_card.md --report release_verification_report.json --manifest RELEASE_ASSETS_MANIFEST.md --out-dir release-trust-plan
```

Upload mode is optional and uses `gh release view <tag>` before any upload. If
the release tag does not exist, it reports `RELEASE_TAG_NOT_FOUND` and does not
attempt upload. The helper does not use `--clobber` by default.

## What This Action Verifies

- artifact hashes
- required file presence
- manifest consistency
- claim-boundary scan
- selected proof syntax in partial mode
- existing drat-trim logs in partial mode
- selected independent checker replay in partial mode
- optional selected drat-trim replay

## What This Action Does Not Verify

- does not rerun the solver
- does not regenerate benchmark instances
- does not regenerate DRAT proofs
- does not rerun the full benchmark diagnostic
- does not prove claims outside selected evidence
- does not replace human review

## Example Workflows

See `examples/metadata.yml`, `examples/partial-replay.yml`,
`examples/partial-replay-drat.yml`, and `examples/release-trust-card.yml`.

## Security / Trust Model

This action reports scoped evidence checks. It can block workflows on configured
risk flags or verdicts. It is not a complete security audit, not a general proof
verifier, and not a competitive SAT solver.

## Limitations

No general SAT solving claim, no parity support claim, no broad XOR extraction
claim, no competitive SAT solver claim, no P vs NP claim, and no HARD or UNKNOWN
status claims are made by this action.

## Versioning

Use pinned tags such as `joeyst8/witnora-verify-action@v1`. The package is
prepared from Witnora-Core v1.6 marketplace distribution files.
"""


RELEASE_NOTES = """# Release Notes

Initial dedicated marketplace action package for Witnora Verify.

- Root `action.yml` for Marketplace-compatible repository layout.
- Product-facing README with scoped trust semantics.
- Example workflows for metadata, partial replay, drat-trim replay, and release
  trust-card planning.
- Self-test workflow for package-level CI.

This release does not add solver logic, benchmark solving logic, proof-export
logic, XOR-solving logic, or new benchmark claims.
"""


CLAIM_BOUNDARY = """# Claim Boundary

Allowed:

- Witnora Verify checks release artifact integrity.
- Witnora Verify can partially replay selected proof evidence already present in
  diagnostic artifacts.
- Witnora Verify can generate scoped verification reports and trust cards.

Forbidden:

- no general SAT solving claim
- no parity support claim
- no broad XOR extraction claim
- no competitive SAT solver claim
- no industrial benchmark claim
- no full DRAT/RAT/LRAT/FRAT support claim
- no P vs NP claim
- no HARD or UNKNOWN status claim

Witnora Verify does not rerun the solver, regenerate benchmark instances,
regenerate DRAT proofs, rerun the full benchmark diagnostic, or replace human
review.
"""


CHECKLIST = """# Marketplace Release Checklist

1. Create public repo `joeyst8/witnora-verify-action`.
2. Copy `dist/witnora-verify-action/*` to the repository root.
3. Confirm `action.yml` is at the repository root.
4. Confirm `README.md` and `LICENSE` are present.
5. Commit and push the repository.
6. Push tag `v1`.
7. Create a GitHub Release for `v1`.
8. Check the GitHub Marketplace publish prompt.
9. Accept the Marketplace Developer Agreement if required.
10. Verify the action appears in Marketplace.
11. Test usage:

```yaml
uses: joeyst8/witnora-verify-action@v1
```
"""


SELF_TEST = """name: Self Test

on:
  workflow_dispatch:
  pull_request:
  push:

jobs:
  metadata-fixture:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install Witnora-Core from source tag
        run: python -m pip install git+https://github.com/joeyst8/witnora-core.git@v1.5.1-release-trust-polish
      - name: Create metadata fixtures
        run: |
          python - <<'PY'
          import hashlib, zipfile
          from pathlib import Path
          Path('fixtures').mkdir(exist_ok=True)
          with zipfile.ZipFile('fixtures/source.zip', 'w') as z:
              z.writestr('README.md', 'source fixture\\n')
          with zipfile.ZipFile('fixtures/diagnostic.zip', 'w') as z:
              z.writestr('manifest.json', '{}\\n')
          def sha(p):
              return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
          Path('fixtures/manifest.md').write_text(
              '# Fixture Manifest\\n\\n'
              '| asset | SHA256 | status |\\n'
              '| --- | --- | --- |\\n'
              f'| `source.zip` | `{sha("fixtures/source.zip")}` | source archive |\\n'
              f'| `diagnostic.zip` | `{sha("fixtures/diagnostic.zip")}` | diagnostic artifact |\\n'
              '\\nThis release does not claim parity support, broad XOR extraction, or P vs NP progress.\\n',
              encoding='utf-8',
          )
          PY
      - name: Run action in metadata mode
        uses: ./
        with:
          source-zip: fixtures/source.zip
          diagnostic-zip: fixtures/diagnostic.zip
          manifest: fixtures/manifest.md
          depth: metadata
          out-dir: witnora-verify-out
"""


def sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def copy_tree(source: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_manifest(dist_dir: Path) -> dict[str, object]:
    files = sorted(path for path in dist_dir.rglob("*") if path.is_file())
    records = []
    for path in files:
        if path.name == "ACTION_PACKAGE_MANIFEST.json":
            continue
        records.append(
            {
                "path": path.relative_to(dist_dir).as_posix(),
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
            }
        )
    return {
        "package": "witnora-verify-action",
        "source": "marketplace-action",
        "intended_repository": "joeyst8/witnora-verify-action",
        "install_usage": "uses: joeyst8/witnora-verify-action@v1",
        "files": records,
    }


def create_zip(dist_dir: Path, zip_path: Path) -> None:
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(dist_dir.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(dist_dir.parent).as_posix())


def prepare_package(*, dist_dir: Path = DEFAULT_DIST_DIR, create_package_zip: bool = True) -> dict[str, object]:
    copy_tree(SOURCE_ACTION_DIR, dist_dir)
    write_text(dist_dir / "README.md", README_TEXT)
    write_text(dist_dir / "RELEASE_NOTES.md", RELEASE_NOTES)
    write_text(dist_dir / "CLAIM_BOUNDARY.md", CLAIM_BOUNDARY)
    write_text(dist_dir / "MARKETPLACE_RELEASE_CHECKLIST.md", CHECKLIST)
    write_text(dist_dir / ".github" / "workflows" / "self-test.yml", SELF_TEST)

    manifest = build_manifest(dist_dir)
    manifest_path = dist_dir / "ACTION_PACKAGE_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest = build_manifest(dist_dir)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    zip_info = None
    if create_package_zip:
        zip_path = REPO_ROOT / "witnora-verify-action-v1-package.zip"
        create_zip(dist_dir, zip_path)
        zip_info = {"path": str(zip_path), "sha256": sha256_file(zip_path)}
    return {
        "dist_dir": str(dist_dir),
        "manifest_path": str(manifest_path),
        "file_count": len(manifest["files"]),
        "zip": zip_info,
    }


def validate_required_files(dist_dir: Path = DEFAULT_DIST_DIR) -> list[str]:
    required = [
        "action.yml",
        "README.md",
        "LICENSE",
        "examples/metadata.yml",
        "examples/partial-replay.yml",
        "examples/partial-replay-drat.yml",
        "examples/release-trust-card.yml",
        ".github/workflows/self-test.yml",
        "RELEASE_NOTES.md",
        "CLAIM_BOUNDARY.md",
        "MARKETPLACE_RELEASE_CHECKLIST.md",
        "ACTION_PACKAGE_MANIFEST.json",
    ]
    return [item for item in required if not (dist_dir / item).is_file()]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare standalone Witnora Verify action repo package")
    parser.add_argument("--dist-dir", default=str(DEFAULT_DIST_DIR))
    parser.add_argument("--no-zip", action="store_true")
    args = parser.parse_args(argv)
    result = prepare_package(dist_dir=Path(args.dist_dir), create_package_zip=not args.no_zip)
    missing = validate_required_files(Path(args.dist_dir))
    result["missing_required_files"] = missing
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if missing else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
