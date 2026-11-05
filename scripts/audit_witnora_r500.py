"""Read-only R-500 research audit; no SAT theorem or production approval."""

from __future__ import annotations

import importlib
import inspect
import json
import re
import unittest

from scripts.audit_witnora_r180 import ROOT
from scripts.audit_witnora_r300 import (
    EXTERNAL_VERIFIER_REVISION, audit as r300_audit,
)


TEST_SUITES = (
    "tests.test_xor_syndrome_301_320",
    "tests.test_xor_hypergraph_adversarial_321_340",
    "tests.test_xor_geometry_341_360",
    "tests.test_xor_gauge_361_380",
    "tests.test_xor_resource_381_400",
    "tests.test_xor_heldout_401_460",
    "tests.test_xor_hostile_461_480",
    "tests.test_r500_manifest_audit",
)
BENCHMARK_SCRIPTS = (
    "scripts/benchmark_xor_syndrome_frontier.py",
    "scripts/benchmark_xor_constraint_geometry.py",
    "scripts/benchmark_xor_gauge_frontier.py",
    "scripts/benchmark_xor_resource_frontier.py",
    "scripts/benchmark_xor_heldout_401_460.py",
    "scripts/benchmark_xor_hostile_461_480.py",
)
DOCUMENTS = (
    "docs/RUST_301_320_GF2_SYNDROME.md",
    "docs/RUST_321_340_HYPERGRAPH_PROVENANCE.md",
    "docs/RUST_341_360_MATCHED_INTERACTION_GEOMETRY.md",
    "docs/RUST_361_380_GAUGE_METAMORPHIC.md",
    "docs/RUST_381_400_EXACT_RESOURCE_BOUNDARIES.md",
    "docs/RUST_401_460_HELDOUT_ORIGINAL_CNF.md",
    "docs/RUST_461_480_HOSTILE_PROOF_GATES.md",
    "docs/RUST_481_500_RESEARCH_SIGNOFF.md",
)


def named_gates():
    coverage = {}
    for suite in TEST_SUITES:
        module = importlib.import_module(suite)
        for obj in vars(module).values():
            if inspect.isclass(obj) and issubclass(obj, unittest.TestCase):
                for method in dir(obj):
                    # Grouped integration tests (test_r301_r320_...) are not
                    # individual numbered gates and must not double-count.
                    match = re.fullmatch(r"test_r(\d{3})_(?!r\d{3}_).*", method)
                    if match and 301 <= int(match.group(1)) <= 499:
                        milestone = int(match.group(1))
                        if milestone in coverage:
                            raise AssertionError(f"ambiguous duplicate research gate R-{milestone}")
                        coverage[milestone] = f"{suite}.{obj.__name__}.{method}"
    return coverage


def audit():
    baseline = r300_audit()
    if baseline["verified_xor_frontier"] != 500:
        raise AssertionError("the R-500 manifest is not gap-free through R-500")
    coverage = named_gates()
    if set(coverage) != set(range(301, 500)):
        missing = sorted(set(range(301, 500)) - set(coverage))
        raise AssertionError(f"R-301–R-499 named research gates missing: {missing}")
    missing_files = [p for p in (*BENCHMARK_SCRIPTS, *DOCUMENTS)
                     if not (ROOT / p).is_file()]
    if missing_files:
        raise AssertionError(f"research reproducibility files missing: {missing_files}")
    workflow = (ROOT / ".github/workflows/rust-migration-fast.yml").read_text(
        encoding="utf-8")
    required = (*TEST_SUITES, EXTERNAL_VERIFIER_REVISION, "--compare-rust",
                "--drat-trim", "WITNORA_DRAT_TRIM", "audit_witnora_r500")
    for token in required:
        if token not in workflow:
            raise AssertionError(f"R-500 required focused CI gate unwired: {token}")
    for script in BENCHMARK_SCRIPTS:
        dotted = script.replace("/", ".").removesuffix(".py")
        if dotted not in workflow:
            raise AssertionError(f"R-500 benchmark not executed in focused CI: {dotted}")
    manifest = json.loads((ROOT / "research/python_to_rust_manifest.json").read_text(
        encoding="utf-8"))
    xor = next(e for e in manifest["entries"] if e["path"] == "witnora_core/xor_drat.py")
    if xor["verified_milestone"] != "R-500" or xor["status"] != "partial_native_verified":
        raise AssertionError("the opt-in partial-native boundary was misreported")
    return {**baseline,
        "status": "R500_RESEARCH_AUDIT_PASSED_NOT_RELEASE_APPROVAL",
        "named_post_r300_gates": len(coverage),
        "all_post_r300_milestones_contiguous": True,
        "benchmarks_wired_in_focused_ci": len(BENCHMARK_SCRIPTS),
        "research_document_count": len(DOCUMENTS),
        "external_drat_trim_pinned_in_ci": EXTERNAL_VERIFIER_REVISION,
        "ci_run_verified_by_this_read_only_audit": False,
        "python_is_default": True,
        "new_original_python_files_migrated_by_research_gates": 0,
        "p_vs_np_or_general_sat_claim": False}


if __name__ == "__main__":
    print(json.dumps(audit(), sort_keys=True))
