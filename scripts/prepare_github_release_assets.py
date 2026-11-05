"""Prepare a GitHub release asset checklist from a Witnora manifest.

This helper performs no upload and does not require a GitHub token. It only
checks local files listed in a manifest table and emits Markdown for release
preparation.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from witnora_core.verification_report import parse_manifest_hash_table, sha256_file


def build_checklist(manifest_path: Path, asset_root: Path) -> str:
    manifest_text = manifest_path.read_text(encoding="utf-8")
    manifest_hashes = parse_manifest_hash_table(manifest_text)
    lines = [
        "# GitHub Release Asset Checklist",
        "",
        f"Manifest: `{manifest_path}`",
        f"Asset root: `{asset_root}`",
        "",
        "| asset | expected SHA256 | actual SHA256 | status |",
        "| --- | --- | --- | --- |",
    ]
    for asset, expected in sorted(manifest_hashes.items()):
        candidate = asset_root / asset
        if candidate.is_file():
            actual = sha256_file(candidate)
            status = "MATCH" if actual == expected else "MISMATCH"
        else:
            actual = ""
            status = "MISSING"
        lines.append(f"| `{asset}` | `{expected}` | `{actual}` | {status} |")
    lines.extend(
        [
            "",
            "## Release Notes Asset Block",
            "",
        ]
    )
    for asset, expected in sorted(manifest_hashes.items()):
        lines.extend([f"- `{asset}`", f"  SHA256: `{expected}`"])
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare Witnora GitHub release asset checklist")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--asset-root", default=".")
    parser.add_argument("--out", default="github_release_asset_checklist.md")
    args = parser.parse_args(argv)

    output = build_checklist(Path(args.manifest), Path(args.asset_root))
    Path(args.out).write_text(output, encoding="utf-8")
    print(output, end="")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
