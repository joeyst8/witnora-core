"""Verification-kernel CLI for certificates, releases, and trust cards."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .verification_report import (
    render_trust_card_markdown,
    stable_json,
    trust_card_from_report,
    verification_report_for_certificate,
    verification_report_for_release,
    write_report_files,
)


def _write_trust_card(card: dict[str, object], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "trust_card.json").write_text(stable_json(card), encoding="utf-8")
    (out_dir / "trust_card.md").write_text(render_trust_card_markdown(card), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Witnora verification kernel")
    subparsers = parser.add_subparsers(dest="command", required=True)

    cert_parser = subparsers.add_parser("cert", help="verify a .wcert certificate bundle")
    cert_parser.add_argument("certificate", help=".wcert directory or .wcert.json file")
    cert_parser.add_argument("--out-dir", default=".", help="directory for verification_report.json/md")

    release_parser = subparsers.add_parser("release", help="verify a source/diagnostic release package")
    release_parser.add_argument("--source-zip", required=True)
    release_parser.add_argument("--diagnostic-zip", required=True)
    release_parser.add_argument("--manifest", required=True)
    release_parser.add_argument("--out-dir", default=".", help="directory for release_verification_report.json/md")

    card_parser = subparsers.add_parser("trust-card", help="create a trust card from a verification report")
    card_parser.add_argument("--report", required=True)
    card_parser.add_argument("--out-dir", default=".", help="directory for trust_card.json/md")

    args = parser.parse_args(argv)

    if args.command == "cert":
        out_dir = Path(args.out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        report = verification_report_for_certificate(args.certificate)
        write_report_files(report, out_dir / "verification_report.json", out_dir / "verification_report.md")
        print(stable_json(report), end="")
        return 0 if report.get("verdict") == "VERIFIED" else 1

    if args.command == "release":
        out_dir = Path(args.out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        report = verification_report_for_release(
            source_zip=args.source_zip,
            diagnostic_zip=args.diagnostic_zip,
            manifest=args.manifest,
        )
        write_report_files(
            report,
            out_dir / "release_verification_report.json",
            out_dir / "release_verification_report.md",
        )
        print(stable_json(report), end="")
        return 0 if report.get("verdict") in {"VERIFIED", "PARTIALLY_VERIFIED"} else 1

    if args.command == "trust-card":
        out_dir = Path(args.out_dir)
        report = json.loads(Path(args.report).read_text(encoding="utf-8"))
        card = trust_card_from_report(report)
        _write_trust_card(card, out_dir)
        print(stable_json(card), end="")
        return 0

    raise AssertionError(f"unhandled command {args.command!r}")


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
