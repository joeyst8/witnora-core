"""CI wrapper for Witnora release verification.

This module is intentionally a thin product-facing layer over the verification
kernel. It does not rerun the solver or alter proof/XOR logic.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from .verification_report import (
    VERDICT_ARTIFACT_INTEGRITY_VERIFIED,
    VERDICT_PARTIAL_REPLAY_VERIFIED,
    render_trust_card_markdown,
    stable_json,
    trust_card_from_report,
    verification_report_for_release,
    write_report_files,
)


DEFAULT_FAIL_ON = "hash_mismatch,overclaim,missing_file"
SCOPE_LOG_TEXT = (
    "Witnora Verify did not rerun the solver, regenerate CNFgen instances, "
    "regenerate DRAT proofs, or rerun the full benchmark diagnostic."
)


def _parse_fail_on(value: str) -> set[str]:
    return {item.strip().lower() for item in value.split(",") if item.strip()}


def _check_status_failed(items: list[dict[str, Any]]) -> bool:
    return any(str(item.get("status", "")).upper() in {"FAIL", "SKIP"} for item in items)


def evaluate_fail_conditions(report: dict[str, Any], fail_on: set[str]) -> list[str]:
    """Return CI failure reasons selected by ``fail_on``."""

    risk_flags = set(report.get("risk_flags", []))
    verdict = str(report.get("verdict", ""))
    reasons: list[str] = []

    if "hash_mismatch" in fail_on and "HASH_MISMATCH" in risk_flags:
        reasons.append("hash_mismatch")
    if "missing_file" in fail_on and "MISSING_FILE" in risk_flags:
        reasons.append("missing_file")
    if "overclaim" in fail_on and (verdict == "OVERCLAIM" or "UNVERIFIED_CLAIM" in risk_flags):
        reasons.append("overclaim")
    if "partial_or_not_verified" in fail_on:
        positive = {VERDICT_ARTIFACT_INTEGRITY_VERIFIED, VERDICT_PARTIAL_REPLAY_VERIFIED}
        if verdict not in positive or "UNVERIFIED_CLAIM" in risk_flags:
            reasons.append("partial_or_not_verified")
    if "drat_replay_failed" in fail_on:
        if "DRAT_TRIM_REPLAY_FAILED_OR_SKIPPED" in risk_flags or _check_status_failed(report.get("drat_trim_replay", [])):
            reasons.append("drat_replay_failed")
    if "independent_checker_failed" in fail_on and _check_status_failed(report.get("independent_checker_replay", [])):
        reasons.append("independent_checker_failed")
    return reasons


def evaluate_marketplace_fail_conditions(
    report: dict[str, Any],
    *,
    fail_on_risk_flags: set[str],
    fail_on_verdict: set[str],
) -> list[str]:
    risk_flags = {str(flag).upper() for flag in report.get("risk_flags", [])}
    verdict = str(report.get("verdict", "")).upper()
    reasons = [f"risk_flag:{flag}" for flag in sorted(fail_on_risk_flags & risk_flags)]
    if verdict in fail_on_verdict:
        reasons.append(f"verdict:{verdict}")
    return reasons


def _json_compact(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _selection_policy(select: str, select_instance: str | None) -> str:
    if select_instance:
        parts = select_instance.split(":c=")
        if len(parts) == 2:
            return f"instance:{parts[0]}:c:{parts[1]}"
        return f"instance:{select_instance}"
    if select == "instance":
        return "instance:"
    return select


def render_ci_log_summary(report: dict[str, Any], failure_reasons: list[str]) -> str:
    selected = report.get("selected_evidence", [])
    selected_lines = [
        f"- {item.get('instance_id')} c={item.get('c')} ({item.get('public_category')})"
        for item in selected
    ] or ["- none"]
    checks = report.get("checks_performed", [])
    checked_names = [str(check.get("name", "check")) for check in checks[:12]]
    if len(checks) > 12:
        checked_names.append(f"... {len(checks) - 12} more")
    checked_lines = [f"- {name}" for name in checked_names] or ["- none"]
    risk_lines = [f"- {flag}" for flag in report.get("risk_flags", [])] or ["- none"]
    failure_lines = [f"- {reason}" for reason in failure_reasons] or ["- none"]
    lines = [
        "Witnora Verify CI Summary",
        f"Verdict: {report.get('verdict')}",
        f"Verification depth: {report.get('verification_depth')}",
        f"Replay depth: {report.get('replay_depth')}",
        "Selected evidence:",
        *selected_lines,
        "Risk flags:",
        *risk_lines,
        "Checks performed:",
        *checked_lines,
        "What was not checked:",
        f"- {SCOPE_LOG_TEXT}",
        "Failure reasons:",
        *failure_lines,
    ]
    return "\n".join(lines) + "\n"


def _write_trust_card(card: dict[str, Any], out_dir: Path) -> tuple[Path, Path]:
    json_path = out_dir / "trust_card.json"
    md_path = out_dir / "trust_card.md"
    json_path.write_text(stable_json(card), encoding="utf-8")
    md_path.write_text(render_trust_card_markdown(card), encoding="utf-8")
    return json_path, md_path


def _write_github_outputs(outputs: dict[str, str]) -> None:
    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        return
    with Path(output_path).open("a", encoding="utf-8") as handle:
        for key, value in outputs.items():
            handle.write(f"{key}={value}\n")


def run_ci(args: argparse.Namespace) -> tuple[int, dict[str, Any], dict[str, Any], list[str]]:
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    report = verification_report_for_release(
        source_zip=args.source_zip,
        diagnostic_zip=args.diagnostic_zip,
        manifest=args.manifest,
        depth=args.depth,
        selection_policy=_selection_policy(args.select, args.select_instance),
        rerun_drat_trim=args.rerun_drat_trim,
        drat_trim_path=args.drat_trim,
        max_replay_proofs=args.max_replay_proofs,
        replay_timeout_seconds=args.replay_timeout_seconds,
    )
    report_json = out_dir / "release_verification_report.json"
    report_md = out_dir / "release_verification_report.md"
    write_report_files(report, report_json, report_md)

    card = trust_card_from_report(report)
    trust_json, trust_md = _write_trust_card(card, out_dir)

    failure_reasons = evaluate_fail_conditions(report, _parse_fail_on(args.fail_on))
    failure_reasons.extend(
        evaluate_marketplace_fail_conditions(
            report,
            fail_on_risk_flags={item.upper() for item in _parse_fail_on(args.fail_on_risk_flags)},
            fail_on_verdict={item.upper() for item in _parse_fail_on(args.fail_on_verdict)},
        )
    )
    failure_reasons = sorted(set(failure_reasons))
    _write_github_outputs(
        {
            "verdict": str(report.get("verdict", "")),
            "certification_level": str(report.get("certification_level", "")),
            "verification_depth": str(report.get("verification_depth", "")),
            "replay_depth": str(report.get("replay_depth") or ""),
            "risk_flags": _json_compact(report.get("risk_flags", [])),
            "selected_evidence": _json_compact(report.get("selected_evidence", [])),
            "report_path": str(report_json),
            "trust_card_path": str(trust_md),
        }
    )

    summary = {
        "verdict": report.get("verdict"),
        "certification_level": report.get("certification_level"),
        "verification_depth": report.get("verification_depth"),
        "replay_depth": report.get("replay_depth"),
        "risk_flags": report.get("risk_flags", []),
        "report_path": str(report_json),
        "trust_card_path": str(trust_md),
        "failure_reasons": failure_reasons,
        "trust_card_json_path": str(trust_json),
    }
    print(render_ci_log_summary(report, failure_reasons))
    print(stable_json(summary), end="")
    return (1 if failure_reasons else 0), report, card, failure_reasons


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Witnora Verify CI wrapper")
    parser.add_argument("--source-zip", required=True)
    parser.add_argument("--diagnostic-zip", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--depth", choices=["metadata", "partial", "full"], default="metadata")
    parser.add_argument("--select", choices=["largest", "first", "all", "instance"], default="largest")
    parser.add_argument("--select-instance", default=None, help="selected instance, for example tseitin_20:c=2")
    parser.add_argument("--rerun-drat-trim", action="store_true")
    parser.add_argument("--drat-trim", default=None)
    parser.add_argument("--max-replay-proofs", type=int, default=1)
    parser.add_argument("--replay-timeout-seconds", type=float, default=120.0)
    parser.add_argument("--fail-on", default=DEFAULT_FAIL_ON)
    parser.add_argument("--fail-on-risk-flags", default="")
    parser.add_argument("--fail-on-verdict", default="")
    parser.add_argument("--out-dir", default="witnora-verify-out")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    exit_code, _report, _card, _reasons = run_ci(args)
    return exit_code


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
