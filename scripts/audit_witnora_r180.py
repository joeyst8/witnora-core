"""R-179 readiness audit: migration accounting and preserved proof boundaries.

This read-only audit never claims that the 560-file Python migration is done.
"""
from __future__ import annotations

import inspect
import json
from pathlib import Path

from witnora_core.xor_drat import export_xor_drat_for_path
from witnora_core.proof import export_certificate_bundle


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "research" / "python_to_rust_manifest.json"


def audit() -> dict:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    entries = manifest["entries"]
    total = manifest["total_python_files"]
    if total != 560 or len(entries) != total:
        raise AssertionError("Python source-file manifest total changed unexpectedly")
    expected_counts = manifest["current_status_counts"]
    actual_counts = {status: sum(row["status"] == status for row in entries)
                     for status in expected_counts}
    if actual_counts != expected_counts or sum(actual_counts.values()) != total:
        raise AssertionError("Python migration status accounting is inconsistent")
    if any(not (ROOT / row["path"]).is_file() for row in entries):
        raise AssertionError("an original Python source file is missing")
    if manifest["branch"] != "research/w-crc-001-asymmetric-v1":
        raise AssertionError("the migration manifest must remain research-scoped")
    xor = next(row for row in entries if row["path"] == "witnora_core/xor_drat.py")
    if xor["status"] != "partial_native_verified":
        raise AssertionError("XOR proof migration must remain partial")
    nums = {int(item[2:]) for item in xor["verified_milestones"]}
    frontier = max(nums)
    if set(range(132, frontier + 1)) != nums:
        raise AssertionError("XOR proof milestones contain an unverified gap")
    if frontier > 300:
        raise AssertionError("unexpected future milestone claimed")

    for fn, names in (
        (export_xor_drat_for_path, (
            "proof_backend", "require_dual_internal", "require_source_identity",
            "require_dual_source_parser", "require_native_proof_audit")),
        (export_certificate_bundle, (
            "xor_proof_backend", "xor_require_dual_internal",
            "xor_require_source_identity", "xor_require_dual_source_parser",
            "xor_require_native_proof_audit")),
    ):
        params = inspect.signature(fn).parameters
        for name in names:
            expected = "python" if name.endswith("backend") else False
            if params[name].default != expected:
                raise AssertionError(f"experimental option {name} is not opt-in")

    return {
        "status": "RESEARCH_AUDIT_PASSED_NOT_RELEASE_APPROVAL",
        "verified_xor_frontier": frontier,
        "original_python_files_preserved": total,
        "status_counts": actual_counts,
        "lean_kernel_unmodified_by_audit": True,
        "external_drat_trim_still_required": True,
        "full_python_to_rust_migration_complete": False,
    }


if __name__ == "__main__":
    print(json.dumps(audit(), sort_keys=True))
