"""Reproducible, read-only TC-063 separator-policy experiment.

Four distinct policies on the SAME source formula:
  production: archived pre-cache behavior (rebuild graph and test non-cuts)
  production_cached: current production recognizer (one graph per invocation)
  cached_first: cache primal graph once, validate cuts in current order
  cached_balanced: cache graph, rank all actual cuts by largest component,
                   then apply the SAME exact-affine validation as first-valid

Build and independently verify the normal G14 certificate for accepted cuts.
The experimental cached policies do not mutate the production recognizer.

Usage:
  python -B -m research.pr119_separator_selection_benchmark --trials 2 --permutations 3
"""

import argparse
from itertools import combinations
import json
from pathlib import Path
import platform
import random
import statistics
import time

from witnora_core.cnf import CNFFormula, formula_satisfied
from witnora_core.separator_affine_family_theorem import (
    AFFINE_RESIDUE_CERTIFICATE_VERIFIED,
    DIAGNOSTIC_ONLY,
    SAT_CERTIFIED,
    SEPARATOR_AFFINE_CERTIFICATE_VERIFIED,
    SEPARATOR_AFFINE_FAMILY_RECOGNIZED,
    UNSAT_CERTIFIED,
    SeparatorAffineFamilyInstance,
    _affine_component_certificate,
    _affine_source_clause_coverage,
    _all_assignments,
    _assignment_from_payload,
    _component_dicts,
    _components_after_removing,
    _condition_by_separator,
    build_separator_affine_certificate,
    check_affine_residue_certificate,
    check_separator_affine_certificate,
    primal_graph,
    recognize_separator_affine_family,
)
from witnora_core.obstruction_dual import stable_json


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "research" / "PR119_DUBOIS20_SOURCE_XOR_CERTIFICATE.json"
POLICIES = ("production", "production_cached", "cached_first", "cached_balanced")


def source_formula() -> CNFFormula:
    archive = json.loads(SOURCE.read_text())
    assert archive["source_sha256"] == (
        "82059aba0e5773644b386eb6bcbe53680655390cb041873a3cb3e93f7bd896a7"
    )
    formula = CNFFormula.from_raw_clauses(
        clause for equation in archive["proof_equations"]
        for clause in equation["source_clauses"]
    )
    assert len(formula.clauses) == 160 and len(formula.variables) == 60
    return formula


def relabel_formula(formula: CNFFormula, seed: int) -> CNFFormula:
    rng = random.Random(seed)
    labels = list(range(1, 61))
    rng.shuffle(labels)
    mapping = dict(zip(range(1, 61), labels))
    return CNFFormula.from_raw_clauses(
        [mapping[abs(lit)] if lit > 0 else -mapping[abs(lit)] for lit in clause]
        for clause in formula.clauses
    )


def random_three_sat_control(seed: int) -> CNFFormula:
    rng = random.Random(seed)
    rows = []
    for _ in range(160):
        variables = rng.sample(range(1, 61), 3)
        rows.append([v if rng.getrandbits(1) else -v for v in variables])
    return CNFFormula.from_raw_clauses(rows)


def exact_affine_candidate(formula: CNFFormula, cut: tuple[int, ...], r: int) -> bool:
    """Mirror the production recognizer's fail-closed per-branch checks."""
    components = _component_dicts(formula, list(cut))
    if len(components) < 2:
        return False
    return _exact_affine_residuals(formula, cut, components, r)


def _exact_affine_residuals(formula: CNFFormula, cut: tuple[int, ...], components: list[dict], r: int) -> bool:
    for assignment in _all_assignments(cut):
        _, residuals, errors = _condition_by_separator(formula, assignment, components)
        if errors:
            return False
        for cid, residual in residuals.items():
            cert = _affine_component_certificate("policy_probe_" + cid, residual, max_arity=r)
            check = check_affine_residue_certificate(residual, cert, max_arity=r)
            coverage = _affine_source_clause_coverage(cert)
            expected = set(range(1, len(residual.clauses) + 1))
            witness_ok = (
                check.get("gf2_status") != "SAT"
                or formula_satisfied(residual, _assignment_from_payload(cert.get("solution")))
            )
            if (check["status"] != AFFINE_RESIDUE_CERTIFICATE_VERIFIED
                    or coverage != expected or not witness_ok):
                return False
    return True


def legacy_uncached_cut(formula: CNFFormula, c: int, r: int) -> dict:
    """Reproduce pre-cache selection: validate even candidates with one component.

    Previously `ok = len(components) >= 2` was evaluated before the
    expensive residual validation but did not prevent executing it.
    """
    seen = 0
    graph_cuts = 0
    for size in range(1, min(c, len(formula.variables)) + 1):
        for cut in combinations(formula.variables, size):
            seen += 1
            components = _component_dicts(formula, list(cut))
            is_cut = len(components) >= 2
            if is_cut:
                graph_cuts += 1
            affine = _exact_affine_residuals(formula, cut, components, r)
            if is_cut and affine:
                return {"cut": list(cut), "candidate_count": seen,
                        "graph_cuts": graph_cuts, "affine_attempts": graph_cuts}
    return {"cut": [], "candidate_count": seen,
            "graph_cuts": graph_cuts, "affine_attempts": graph_cuts}


def cached_cut(formula: CNFFormula, policy: str, c: int, r: int) -> dict:
    graph = primal_graph(formula)
    seen = 0
    graph_cuts = []
    for size in range(1, min(c, len(formula.variables)) + 1):
        for cut in combinations(formula.variables, size):
            seen += 1
            components = _components_after_removing(graph, set(cut))
            if len(components) < 2:
                continue
            graph_cuts.append((cut, tuple(sorted((len(x) for x in components), reverse=True))))
            if policy == "cached_first" and exact_affine_candidate(formula, cut, r):
                return {"cut": list(cut), "candidate_count": seen,
                        "graph_cuts": len(graph_cuts), "affine_attempts": len(graph_cuts)}

    if policy == "cached_first":
        return {"cut": [], "candidate_count": seen,
                "graph_cuts": len(graph_cuts), "affine_attempts": len(graph_cuts)}

    # Balance is a mathematical hypothesis to benchmark, not a claim of
    # optimal certificate cost or an oracle that knows which cut works.
    graph_cuts.sort(key=lambda row: (row[1][0], sum(x*x for x in row[1]), len(row[0]), row[0]))
    attempts = 0
    for cut, _ in graph_cuts:
        attempts += 1
        if exact_affine_candidate(formula, cut, r):
            return {"cut": list(cut), "candidate_count": seen,
                    "graph_cuts": len(graph_cuts), "affine_attempts": attempts}
    return {"cut": [], "candidate_count": seen,
            "graph_cuts": len(graph_cuts), "affine_attempts": attempts}


def measure(formula: CNFFormula, label: str, policy: str, *, c: int, r: int) -> dict:
    start = time.perf_counter()
    if policy == "production":
        detail = legacy_uncached_cut(formula, c, r)
        selected = detail["cut"]
    elif policy == "production_cached":
        recognition = recognize_separator_affine_family(formula, c=c, r=r)
        selected = list(recognition["separator_variables"])
        detail = {"cut": selected, "candidate_count": len(recognition["trace"]),
                  "graph_cuts": sum(row["component_count"] >= 2 for row in recognition["trace"]),
                  "affine_attempts": sum(row["component_count"] >= 2 for row in recognition["trace"])}
        recognized = recognition["status"] == SEPARATOR_AFFINE_FAMILY_RECOGNIZED
        assert recognized == bool(selected)
    else:
        detail = cached_cut(formula, policy, c, r)
        selected = detail["cut"]
    select_s = time.perf_counter() - start

    result = {"case": label, "policy": policy, "separator": selected,
              "selection_s": round(select_s, 6), **{k: v for k, v in detail.items() if k != "cut"}}
    if not selected:
        result.update({"status": DIAGNOSTIC_ONLY, "component_sizes": [],
                       "build_s": 0.0, "verify_s": 0.0,
                       "total_s": round(select_s, 6), "certificate_bytes": 0})
        return result

    instance = SeparatorAffineFamilyInstance(
        instance_id="pr119_" + label,
        formula=formula,
        separator_variables=selected,
        separator_bound_c=c,
        affine_arity_bound_r=r,
        expected_result=UNSAT_CERTIFIED,
        family="archived-dubois20-policy-experiment",
        n=len(formula.variables),
    )
    begin = time.perf_counter()
    certificate = build_separator_affine_certificate(instance)
    build_s = time.perf_counter() - begin
    begin = time.perf_counter()
    verification = check_separator_affine_certificate(formula, certificate)
    verify_s = time.perf_counter() - begin
    if (certificate.checker_status != SEPARATOR_AFFINE_CERTIFICATE_VERIFIED
            or verification["checker_status"] != SEPARATOR_AFFINE_CERTIFICATE_VERIFIED
            or certificate.final_result not in (SAT_CERTIFIED, UNSAT_CERTIFIED)):
        raise AssertionError(f"fail-closed certificate mismatch: {label} {policy}: {verification['errors']}")
    result.update({
        "status": certificate.final_result,
        "component_sizes": [len(row["variables"]) for row in
                            certificate.separator_verification["components_after_removal"]],
        "build_s": round(build_s, 6),
        "verify_s": round(verify_s, 6),
        "total_s": round(select_s + build_s + verify_s, 6),
        "certificate_bytes": len(stable_json(certificate.to_dict()).encode()),
    })
    return result


def summarize(measurements: list[dict]) -> list[dict]:
    groups = {}
    for row in measurements:
        groups.setdefault((row["case"], row["policy"]), []).append(row)
    summary = []
    for (case, policy), rows in sorted(groups.items()):
        summary.append({
            "case": case, "policy": policy, "separator": rows[0]["separator"],
            "component_sizes": rows[0]["component_sizes"],
            "status": rows[0]["status"],
            "candidates": rows[0]["candidate_count"],
            "graph_cuts_seen": rows[0]["graph_cuts"],
            "affine_attempts": rows[0]["affine_attempts"],
            "median_selection_s": round(statistics.median(r["selection_s"] for r in rows), 6),
            "median_build_s": round(statistics.median(r["build_s"] for r in rows), 6),
            "median_verify_s": round(statistics.median(r["verify_s"] for r in rows), 6),
            "median_total_s": round(statistics.median(r["total_s"] for r in rows), 6),
            "min_total_s": round(min(r["total_s"] for r in rows), 6),
            "max_total_s": round(max(r["total_s"] for r in rows), 6),
            "certificate_bytes": rows[0]["certificate_bytes"],
        })
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=2)
    parser.add_argument("--permutations", type=int, default=3)
    parser.add_argument("--control-trials", type=int, default=1)
    parser.add_argument("--no-control", action="store_true")
    args = parser.parse_args()
    if args.trials < 1 or args.control_trials < 1 or not 0 <= args.permutations <= 10:
        parser.error("trials must be positive and permutations between 0 and 10")
    original = source_formula()
    cases = [("dubois20", original)] + [
        (f"relabel_{seed}", relabel_formula(original, seed))
        for seed in (11, 29, 47, 73, 101, 131, 157, 181, 211, 239)[:args.permutations]
    ]
    if not args.no_control:
        cases.append(("random3sat_negative", random_three_sat_control(20261102)))
    measurements = []
    policy_rng = random.Random(54321)
    for label, formula in cases:
        n_trials = args.control_trials if label == "random3sat_negative" else args.trials
        for trial in range(n_trials):
            order = list(POLICIES)
            policy_rng.shuffle(order)
            for policy in order:
                row = measure(formula, label, policy, c=2, r=3)
                row["trial"] = trial
                measurements.append(row)
    results = {
        "kind": "PR119_TC063_SEPARATOR_POLICY_BENCHMARK",
        "scope": "bounded c=2 r=3, archived Dubois20 and variable relabels; one random 3-SAT negative control",
        "python": platform.python_version(),
        "machine": platform.machine(),
        "trial_count": args.trials,
        "control_trial_count": args.control_trials if not args.no_control else 0,
        "permutation_count": args.permutations,
        "control_included": not args.no_control,
        "note": "Single-machine wall-clock medians; selection cost is included. Historical 'production' means the pre-cache rebuild-per-candidate path; 'production_cached' is the real current implementation. Built certificates are independently rechecked. This is an implementation speedup, not a new algorithmic complexity result.",
        "summary": summarize(measurements),
        "samples": measurements,
    }
    print(json.dumps(results, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
