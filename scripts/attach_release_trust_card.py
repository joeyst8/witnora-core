"""Prepare or upload Witnora release trust-card assets.

The default mode is dry-run planning. Optional upload mode uses:

    gh release upload <tag> <files>...

Do not use ``--clobber`` by default: GitHub CLI deletes and re-uploads existing
assets of the same name when clobbering. This helper keeps that as an explicit
operator decision outside the default path.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from witnora_core.verification_report import parse_manifest_hash_table, sha256_file, stable_json, utc_timestamp


def _asset_record(path: Path, *, kind: str) -> dict[str, Any]:
    exists = path.is_file()
    return {
        "path": str(path),
        "name": path.name,
        "kind": kind,
        "exists": exists,
        "sha256": sha256_file(path) if exists else None,
    }


def _release_notes_snippet(tag: str, assets: list[dict[str, Any]]) -> str:
    lines = [
        "## Witnora Verification Trust Assets",
        "",
        f"Release tag: `{tag}`",
        "",
        "| asset | kind | SHA256 |",
        "| --- | --- | --- |",
    ]
    for asset in assets:
        digest = asset.get("sha256") or "MISSING"
        lines.append(f"| `{asset['name']}` | {asset['kind']} | `{digest}` |")
    return "\n".join(lines) + "\n"


def _render_plan_markdown(plan: dict[str, Any]) -> str:
    lines = [
        "# Witnora Release Trust-Card Upload Plan",
        "",
        f"Release tag: `{plan['release_tag']}`",
        f"Mode: `{plan['mode']}`",
        f"Upload status: `{plan['upload_status']}`",
        "",
        "## Assets",
        "",
        "| asset | kind | exists | SHA256 |",
        "| --- | --- | --- | --- |",
    ]
    for asset in plan["assets"]:
        lines.append(
            f"| `{asset['name']}` | {asset['kind']} | {asset['exists']} | `{asset.get('sha256') or ''}` |"
        )
    lines.extend(["", "## Release Notes Snippet", "", plan["release_notes_snippet"]])
    if plan.get("messages"):
        lines.extend(["", "## Messages", ""])
        lines.extend(f"- {message}" for message in plan["messages"])
    return "\n".join(lines) + "\n"


def build_upload_plan(
    *,
    release_tag: str,
    trust_card_path: str | Path,
    report_path: str | Path,
    manifest_path: str | Path,
    mode: str = "dry-run",
    gh_cli: str = "gh",
) -> dict[str, Any]:
    trust_card = Path(trust_card_path)
    report = Path(report_path)
    manifest = Path(manifest_path)
    assets = [
        _asset_record(trust_card, kind="trust_card"),
        _asset_record(report, kind="verification_report"),
        _asset_record(manifest, kind="asset_manifest"),
    ]
    messages: list[str] = []
    upload_status = "DRY_RUN"
    if manifest.is_file():
        manifest_hashes = parse_manifest_hash_table(manifest.read_text(encoding="utf-8"))
        messages.append(f"manifest_hash_entries={len(manifest_hashes)}")
    else:
        messages.append("manifest missing")

    gh_path = shutil.which(gh_cli) if mode == "upload" else None
    if mode == "upload" and gh_path is None:
        upload_status = "GITHUB_CLI_NOT_AVAILABLE"
        messages.append("gh CLI was not available; no upload attempted")
    elif mode == "upload":
        missing_assets = [asset["path"] for asset in assets if not asset["exists"]]
        if missing_assets:
            upload_status = "MISSING_ASSET"
            messages.append("missing upload asset(s): " + ", ".join(missing_assets))
        else:
            view_command = [gh_path, "release", "view", release_tag]
            view_completed = subprocess.run(view_command, capture_output=True, text=True, check=False)
            if view_completed.returncode != 0:
                return {
                    "release_tag": release_tag,
                    "mode": mode,
                    "generated_at": utc_timestamp(),
                    "assets": assets,
                    "upload_status": "RELEASE_TAG_NOT_FOUND",
                    "risk_flags": ["RELEASE_TAG_NOT_FOUND"],
                    "messages": messages + [
                        "GitHub release tag was not found; no upload attempted.",
                        f"gh_release_view_exit_code={view_completed.returncode}",
                    ],
                    "release_notes_snippet": _release_notes_snippet(release_tag, assets),
                }
            command = [gh_path, "release", "upload", release_tag, *[asset["path"] for asset in assets]]
            completed = subprocess.run(command, capture_output=True, text=True, check=False)
            upload_status = "UPLOADED" if completed.returncode == 0 else "UPLOAD_FAILED"
            messages.append(f"gh_exit_code={completed.returncode}")
            if completed.stdout:
                messages.append("gh_stdout=" + completed.stdout[:500])
            if completed.stderr:
                messages.append("gh_stderr=" + completed.stderr[:500])

    return {
        "release_tag": release_tag,
        "mode": mode,
        "generated_at": utc_timestamp(),
        "assets": assets,
        "upload_status": upload_status,
        "risk_flags": [] if upload_status in {"DRY_RUN", "UPLOADED"} else [upload_status],
        "messages": messages,
        "release_notes_snippet": _release_notes_snippet(release_tag, assets),
    }


def write_upload_plan(plan: dict[str, Any], out_dir: str | Path) -> tuple[Path, Path, Path]:
    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / "release_upload_plan.json"
    markdown_path = output / "release_upload_plan.md"
    snippet_path = output / "release_notes_snippet.md"
    json_path.write_text(stable_json(plan), encoding="utf-8")
    markdown_path.write_text(_render_plan_markdown(plan), encoding="utf-8")
    snippet_path.write_text(plan["release_notes_snippet"], encoding="utf-8")
    return json_path, markdown_path, snippet_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare Witnora release trust-card upload plan")
    parser.add_argument("--tag", "--release-tag", dest="tag", required=True, help="GitHub Release tag")
    parser.add_argument("--trust-card", required=True, help="trust_card.md path")
    parser.add_argument("--report", required=True, help="release_verification_report.json path")
    parser.add_argument("--manifest", required=True, help="release asset manifest path")
    parser.add_argument("--out-dir", default="release-trust-upload-plan")
    parser.add_argument("--upload", action="store_true", help="attempt gh release upload")
    parser.add_argument("--gh-cli", default="gh", help="gh executable name or path")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    plan = build_upload_plan(
        release_tag=args.tag,
        trust_card_path=args.trust_card,
        report_path=args.report,
        manifest_path=args.manifest,
        mode="upload" if args.upload else "dry-run",
        gh_cli=args.gh_cli,
    )
    json_path, markdown_path, _snippet_path = write_upload_plan(plan, args.out_dir)
    print(f"release_upload_plan_json={json_path}")
    print(f"release_upload_plan_md={markdown_path}")
    print(f"upload_status={plan['upload_status']}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
