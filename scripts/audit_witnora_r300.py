"""Read-only R-300 research sign-off; never a production release approval."""

from __future__ import annotations

import importlib
import inspect
import json
from pathlib import Path
import re
import unittest

from scripts.audit_witnora_r180 import ROOT, audit as baseline_audit


TEST_SUITES = (
    "tests.test_xor_frontier_181_200",
    "tests.test_xor_external_201_220",
    "tests.test_xor_scaling_221_240",
    "tests.test_xor_chain_241_260",
    "tests.test_xor_cycles_261_280",
    "tests.test_xor_heldout_281_299",
)
BENCHMARK_SCRIPTS = (
    "scripts/benchmark_xor_frontier.py",
    "scripts/benchmark_xor_proof_scaling.py",
    "scripts/benchmark_xor_chain_frontier.py",
    "scripts/benchmark_xor_cycle_frontier.py",
    "scripts/benchmark_xor_heldout_281_299.py",
)
EXTERNAL_VERIFIER_REVISION = "2e3b2dc0ecf938addbd779d42877b6ed69d9a985"


def audit() -> dict:
    baseline = baseline_audit()
    if baseline["verified_xor_frontier"] < 300:
        raise AssertionError("the R-300 historical milestone ledger is incomplete")
    named = set()
    for suite in TEST_SUITES:
        module = importlib.import_module(suite)
        for obj in vars(module).values():
            if inspect.isclass(obj) and issubclass(obj, unittest.TestCase):
                for method in dir(obj):
                    match = re.fullmatch(r"test_r(\d{3})_.*", method)
                    if match:
                        milestone = int(match.group(1))
                        if 181 <= milestone <= 299:
                            named.add(milestone)
    if named != set(range(181, 300)):
        raise AssertionError(f"R-181–R-299 named gate coverage missing: {sorted(set(range(181,300))-named)}")
    missing = [path for path in BENCHMARK_SCRIPTS if not (ROOT / path).is_file()]
    if missing:
        raise AssertionError(f"research benchmark files missing: {missing}")
    workflow = (ROOT / ".github/workflows/rust-migration-fast.yml").read_text(encoding="utf-8")
    # Dotted unittest names appear in the workflow command; script paths are
    # checked separately. This is a static wiring audit, not proof CI ran.
    required = [EXTERNAL_VERIFIER_REVISION, "make -C", "--drat-trim", "--compare-rust", *TEST_SUITES]
    for item in required:
        if item not in workflow:
            raise AssertionError(f"required R-300 CI gate missing from workflow: {item}")
    for script in BENCHMARK_SCRIPTS:
        if script.replace("/", ".").removesuffix(".py") not in workflow:
            raise AssertionError(f"R-300 benchmark not executed in CI: {script}")
    return {
        **baseline,
        "status": "R300_RESEARCH_AUDIT_PASSED_NOT_RELEASE_APPROVAL",
        "named_post_r180_gate_count": len(named),
        "post_r180_milestones_contiguous": True,
        "external_checker_pinned_in_ci": EXTERNAL_VERIFIER_REVISION,
        "external_checker_ci_run_verified_by_this_read_only_audit": False,
        "source_files_migrated_by_test_milestones": 0,
    }


if __name__ == "__main__":
    print(json.dumps(audit(), sort_keys=True))
