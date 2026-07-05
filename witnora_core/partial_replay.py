"""Partial replay checks for Witnora release diagnostic artifacts."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import tempfile
import time
import zipfile
from typing import Any

from .drat_trim import find_drat_trim, run_drat_trim
from .independent_check import parse_dimacs_raw, verify_wcert_raw


PUBLIC_CATEGORY_UNSAT_DRAT = "UNSAT_DRAT_EXPORTED_VERIFIED"


@dataclass(frozen=True)
class DiagnosticEntryIndex:
    entries: set[str]

    def find(self, artifact_path: str | None) -> str | None:
        if not artifact_path:
            return None
        normalized = artifact_path.replace("\\", "/").lstrip("./")
        if normalized in self.entries:
            return normalized
        suffix_matches = sorted(entry for entry in self.entries if entry.endswith(normalized))
        return suffix_matches[0] if suffix_matches else None


def _read_json_from_zip(archive: zipfile.ZipFile, entry: str) -> Any:
    with archive.open(entry) as handle:
        return json.loads(handle.read().decode("utf-8"))


def _read_text_from_zip(archive: zipfile.ZipFile, entry: str) -> str:
    with archive.open(entry) as handle:
        return handle.read().decode("utf-8", errors="replace")


def _find_first(entries: set[str], suffix: str) -> str | None:
    matches = sorted(entry for entry in entries if entry.endswith(suffix))
    return matches[0] if matches else None


def _candidate_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates = []
    for row in rows:
        if row.get("public_category") != PUBLIC_CATEGORY_UNSAT_DRAT:
            continue
        if not row.get("proof_drat_path") or not row.get("certificate_path"):
            continue
        candidates.append(row)
    return sorted(candidates, key=_row_sort_key)


def _instance_number(instance_id: str) -> int:
    digits = "".join(ch if ch.isdigit() else " " for ch in instance_id).split()
    return int(digits[-1]) if digits else -1


def _row_sort_key(row: dict[str, Any]) -> tuple[int, int, int, str, str]:
    return (
        int(row.get("original_num_vars") or 0),
        int(row.get("original_num_clauses") or 0),
        _instance_number(str(row.get("instance_id", ""))),
        f"c{row.get('c', '')}",
        str(row.get("cap_profile", "")),
    )


def select_rows(rows: list[dict[str, Any]], selection_policy: str) -> list[dict[str, Any]]:
    candidates = _candidate_rows(rows)
    if not candidates:
        return []
    if selection_policy == "all":
        return candidates
    if selection_policy == "first":
        return [candidates[0]]
    if selection_policy == "largest":
        return [candidates[-1]]
    if selection_policy.startswith("instance:"):
        parts = selection_policy.split(":")
        instance = parts[1] if len(parts) > 1 else ""
        c_value = None
        if len(parts) >= 4 and parts[2] == "c":
            c_value = parts[3]
        selected = [
            row
            for row in candidates
            if row.get("instance_id") == instance
            and (c_value is None or str(row.get("c")) == str(c_value))
        ]
        return selected[:1]
    return [candidates[-1]]


def _zip_structure_checks(entries: set[str]) -> list[dict[str, Any]]:
    checks = []
    required_suffixes = [
        "manifest.json",
        "per_instance_results.json",
        "FULL_TSEITIN_MINFILL_DIAGNOSTIC_REPORT.md",
    ]
    for suffix in required_suffixes:
        found = _find_first(entries, suffix)
        checks.append(
            {
                "name": f"diagnostic_structure_{suffix}",
                "status": "PASS" if found else "FAIL",
                "depth": "partial_replay",
                "evidence_path": found or suffix,
                "message": "present" if found else "missing",
            }
        )
    for folder in ["certs/", "drat_logs/", "independent_checks/"]:
        found = any(folder in entry for entry in entries)
        checks.append(
            {
                "name": f"diagnostic_structure_{folder.strip('/')}",
                "status": "PASS" if found else "FAIL",
                "depth": "partial_replay",
                "evidence_path": folder,
                "message": "present" if found else "missing",
            }
        )
    return checks


def _validate_proof_syntax(
    archive: zipfile.ZipFile,
    index: DiagnosticEntryIndex,
    row: dict[str, Any],
) -> dict[str, Any]:
    proof_entry = index.find(str(row.get("proof_drat_path") or ""))
    original_entry = index.find(str(row.get("certificate_path") or "").rstrip("\\/") + "/original.dimacs")
    if not original_entry:
        original_entry = index.find(str(row.get("original_dimacs_path") or ""))
    if not original_entry:
        original_entry = index.find(str(row.get("certificate_path") or "").rstrip("\\/") + "\\original.dimacs")

    messages: list[str] = []
    passed = True
    proof_line_count = 0
    has_empty_clause = False

    if not proof_entry:
        passed = False
        messages.append("proof.drat missing")
    else:
        proof_text = _read_text_from_zip(archive, proof_entry)
        proof_lines = [line.strip() for line in proof_text.splitlines() if line.strip()]
        proof_line_count = len(proof_lines)
        if not proof_lines:
            passed = False
            messages.append("proof.drat empty")
        for line in proof_lines:
            if line.startswith("c"):
                continue
            tokens = line.split()
            if not tokens or tokens[-1] != "0":
                passed = False
                messages.append(f"proof line does not end in 0: {line[:80]}")
                break
            if line == "0":
                has_empty_clause = True
        if not has_empty_clause:
            passed = False
            messages.append("final empty clause line 0 missing")

    if not original_entry:
        passed = False
        messages.append("original.dimacs missing")
    else:
        try:
            parse_dimacs_raw(_read_text_from_zip(archive, original_entry))
        except Exception as exc:  # pragma: no cover - defensive detail in report
            passed = False
            messages.append(f"original.dimacs parse failed: {exc}")

    return {
        "name": "proof_drat_syntax",
        "status": "PASS" if passed else "FAIL",
        "depth": "partial_replay",
        "instance_id": row.get("instance_id"),
        "c": row.get("c"),
        "proof_path": proof_entry,
        "original_dimacs_path": original_entry,
        "proof_line_count": proof_line_count,
        "has_final_empty_clause": has_empty_clause,
        "message": "; ".join(messages) if messages else "proof.drat and original.dimacs syntax checks passed",
    }


def _validate_drat_log(
    archive: zipfile.ZipFile,
    index: DiagnosticEntryIndex,
    row: dict[str, Any],
) -> dict[str, Any]:
    log_entry = index.find(str(row.get("drat_trim_log_path") or ""))
    passed = False
    message = "drat-trim log missing"
    excerpt = ""
    if log_entry:
        text = _read_text_from_zip(archive, log_entry)
        passed = "s VERIFIED" in text
        message = "s VERIFIED found" if passed else "s VERIFIED not found"
        excerpt = "\n".join(text.splitlines()[:12])
    return {
        "name": "drat_trim_log_verified",
        "status": "PASS" if passed else "FAIL",
        "depth": "partial_replay",
        "instance_id": row.get("instance_id"),
        "c": row.get("c"),
        "evidence_path": log_entry,
        "message": message,
        "stdout_excerpt": excerpt,
    }


def _safe_extract_prefix(archive: zipfile.ZipFile, prefix: str, target_root: Path) -> Path:
    normalized_prefix = prefix.replace("\\", "/").rstrip("/") + "/"
    cert_root = target_root / Path(normalized_prefix).name
    for entry in archive.namelist():
        if not entry.startswith(normalized_prefix) or entry.endswith("/"):
            continue
        relative = entry[len(normalized_prefix):]
        destination = cert_root / Path(relative)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with archive.open(entry) as src, destination.open("wb") as dst:
            dst.write(src.read())
    return cert_root


def _independent_checker_replay(
    archive: zipfile.ZipFile,
    index: DiagnosticEntryIndex,
    row: dict[str, Any],
) -> dict[str, Any]:
    cert_entry = index.find(str(row.get("certificate_path") or "").rstrip("\\/") + "/manifest.json")
    if not cert_entry:
        cert_entry = index.find(str(row.get("certificate_path") or "").rstrip("\\/") + "\\manifest.json")
    if not cert_entry:
        return {
            "name": "independent_checker_replay",
            "status": "SKIP",
            "depth": "partial_replay",
            "instance_id": row.get("instance_id"),
            "c": row.get("c"),
            "message": "certificate bundle not present",
        }
    cert_prefix = cert_entry.rsplit("/", 1)[0]
    start = time.perf_counter()
    with tempfile.TemporaryDirectory() as tmp:
        cert_dir = _safe_extract_prefix(archive, cert_prefix, Path(tmp))
        result = verify_wcert_raw(cert_dir)
    runtime = time.perf_counter() - start
    return {
        "name": "independent_checker_replay",
        "status": "PASS" if result.get("verified") else "FAIL",
        "depth": "partial_replay",
        "instance_id": row.get("instance_id"),
        "c": row.get("c"),
        "evidence_path": cert_prefix,
        "runtime_seconds": runtime,
        "checker": result.get("checker"),
        "public_category": result.get("public_category"),
        "message": "independent checker replay verified" if result.get("verified") else str(result.get("error", "independent checker failed")),
    }


def _extract_zip_file(archive: zipfile.ZipFile, entry: str, target: Path) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    with archive.open(entry) as src, target.open("wb") as dst:
        dst.write(src.read())
    return target


def _drat_trim_replay(
    archive: zipfile.ZipFile,
    index: DiagnosticEntryIndex,
    row: dict[str, Any],
    drat_trim_path: str | Path | None,
    timeout_seconds: float | None,
) -> dict[str, Any]:
    checker = find_drat_trim(drat_trim_path)
    if checker is None:
        return {
            "name": "drat_trim_replay",
            "status": "SKIP",
            "depth": "partial_replay",
            "instance_id": row.get("instance_id"),
            "c": row.get("c"),
            "message": "drat-trim executable unavailable",
        }
    proof_entry = index.find(str(row.get("proof_drat_path") or ""))
    original_entry = index.find(str(row.get("certificate_path") or "").rstrip("\\/") + "/original.dimacs")
    if not proof_entry or not original_entry:
        return {
            "name": "drat_trim_replay",
            "status": "FAIL",
            "depth": "partial_replay",
            "instance_id": row.get("instance_id"),
            "c": row.get("c"),
            "message": "proof.drat or original.dimacs missing",
        }
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)
        proof_path = _extract_zip_file(archive, proof_entry, tmp_root / "proof.drat")
        original_path = _extract_zip_file(archive, original_entry, tmp_root / "original.dimacs")
        start = time.perf_counter()
        result = run_drat_trim(original_path, proof_path, checker, timeout_seconds=timeout_seconds)
        runtime = time.perf_counter() - start
    verified = bool(result.get("external_checker_verified"))
    timed_out = bool(result.get("timeout"))
    return {
        "name": "drat_trim_replay",
        "status": "PASS" if verified else "FAIL",
        "depth": "partial_replay",
        "instance_id": row.get("instance_id"),
        "c": row.get("c"),
        "evidence_path": proof_entry,
        "runtime_seconds": runtime,
        "exit_code": result.get("exit_code"),
        "timeout": timed_out,
        "checker_version": None,
        "stdout_excerpt": str(result.get("stdout", ""))[:1000],
        "stderr_excerpt": str(result.get("stderr", ""))[:1000],
        "message": "drat-trim replay verified" if verified else str(result.get("error", "drat-trim replay failed")),
    }


def partial_replay_diagnostic_artifact(
    diagnostic_zip: str | Path,
    *,
    selection_policy: str = "largest",
    rerun_drat_trim: bool = False,
    drat_trim_path: str | Path | None = None,
    max_replay_proofs: int = 3,
    replay_timeout_seconds: float | None = None,
) -> dict[str, Any]:
    zip_path = Path(diagnostic_zip)
    if not zip_path.is_file():
        return {
            "passed": False,
            "error": "diagnostic artifact missing",
            "selection_policy": selection_policy,
            "selected_evidence": [],
            "structure_checks": [],
            "proof_syntax_checks": [],
            "drat_trim_log_checks": [],
            "independent_checker_replay": [],
            "drat_trim_replay": [],
        }

    with zipfile.ZipFile(zip_path, "r") as archive:
        entries = set(archive.namelist())
        index = DiagnosticEntryIndex(entries)
        structure_checks = _zip_structure_checks(entries)
        per_instance_entry = _find_first(entries, "per_instance_results.json")
        rows: list[dict[str, Any]] = []
        if per_instance_entry:
            payload = _read_json_from_zip(archive, per_instance_entry)
            rows = list(payload.get("rows", []))
        selected_rows = select_rows(rows, selection_policy)
        selected_evidence = [
            {
                "instance_id": row.get("instance_id"),
                "c": row.get("c"),
                "cap_profile": row.get("cap_profile"),
                "public_category": row.get("public_category"),
                "certificate_path": row.get("certificate_path"),
                "proof_drat_path": row.get("proof_drat_path"),
                "drat_trim_log_path": row.get("drat_trim_log_path"),
                "independent_checker_path": row.get("independent_checker_path"),
            }
            for row in selected_rows
        ]
        proof_checks = [_validate_proof_syntax(archive, index, row) for row in selected_rows]
        log_checks = [_validate_drat_log(archive, index, row) for row in selected_rows]
        independent_replays = [_independent_checker_replay(archive, index, row) for row in selected_rows]
        replay_rows = selected_rows[: max(0, max_replay_proofs)] if rerun_drat_trim else []
        drat_replays = [
            _drat_trim_replay(archive, index, row, drat_trim_path, replay_timeout_seconds)
            for row in replay_rows
        ]

    all_required = structure_checks + proof_checks + log_checks
    passed = bool(selected_rows) and all(check.get("status") == "PASS" for check in all_required)
    independent_passed = bool(independent_replays) and all(
        check.get("status") == "PASS" for check in independent_replays
    )
    drat_replay_attempted = bool(drat_replays)
    drat_replay_passed = drat_replay_attempted and all(
        check.get("status") == "PASS" for check in drat_replays
    )
    return {
        "passed": passed,
        "selection_policy": selection_policy,
        "selected_evidence": selected_evidence,
        "structure_checks": structure_checks,
        "proof_syntax_checks": proof_checks,
        "drat_trim_log_checks": log_checks,
        "independent_checker_replay": independent_replays,
        "drat_trim_replay": drat_replays,
        "independent_checker_passed": independent_passed,
        "drat_trim_replay_attempted": drat_replay_attempted,
        "drat_trim_replay_passed": drat_replay_passed,
        "candidate_count": len(_candidate_rows(rows)),
    }
