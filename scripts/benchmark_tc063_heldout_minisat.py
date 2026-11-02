"""Held-out TC-063 native certificate pipeline versus an independent MiniSat solver.

This is NOT a comparison of Lean kernel-check time or a claim about general SAT.
The solver gets the same CNF without requiring a proof-producing certificate.
Run after installing python-sat==1.8.dev24.

python -m scripts.benchmark_tc063_heldout_minisat --trials 2 --output tc063_heldout_minisat.json
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from itertools import product
import json
from pathlib import Path
import random
import statistics
import time

from pysat.solvers import Minisat22

from witnora_core.cnf import CNFFormula
from witnora_core.separator_affine_family_theorem import (
    SAT_CERTIFIED,
    UNSAT_CERTIFIED,
    DIAGNOSTIC_ONLY,
    SEPARATOR_AFFINE_CERTIFICATE_VERIFIED,
    SEPARATOR_AFFINE_FAMILY_RECOGNIZED,
    SeparatorAffineFamilyInstance,
    build_separator_affine_certificate,
    check_separator_affine_certificate,
    make_separator_affine_instance,
    recognize_separator_affine_family,
)


FAMILIES = ("saf_sat_chain", "saf_unsat_cover", "saf_balanced_sat")
SIZES = (4, 8, 16)
SEEDS = (23, 59)


def permute_with_sign_flips(formula: CNFFormula, seed: int) -> CNFFormula:
    """A held-out isomorphism: variable names, polarities, clause/literal order."""
    rng = random.Random(seed)
    original = list(formula.variables)
    shuffled = original[:]
    rng.shuffle(shuffled)
    renaming = dict(zip(original, shuffled))
    flip = {v: bool(rng.getrandbits(1)) for v in original}
    clauses = []
    for clause in formula.to_clause_lists():
        mapped = []
        for literal in clause:
            sign = (1 if literal > 0 else -1) * (-1 if flip[abs(literal)] else 1)
            mapped.append(sign * renaming[abs(literal)])
        rng.shuffle(mapped)
        clauses.append(mapped)
    rng.shuffle(clauses)
    return CNFFormula.from_raw_clauses(clauses)


def minisat_answer(formula: CNFFormula) -> tuple[str, float]:
    t0 = time.perf_counter_ns()
    with Minisat22(bootstrap_with=formula.to_clause_lists()) as solver:
        sat = solver.solve()
    elapsed_ms = (time.perf_counter_ns() - t0) / 1_000_000
    return SAT_CERTIFIED if sat else UNSAT_CERTIFIED, elapsed_ms


def witnora_native_answer(formula: CNFFormula, label: str) -> tuple[str, float, int, list[int]]:
    t0 = time.perf_counter_ns()
    recognition = recognize_separator_affine_family(formula, c=1, r=2)
    if recognition["status"] != SEPARATOR_AFFINE_FAMILY_RECOGNIZED:
        elapsed_ms = (time.perf_counter_ns() - t0) / 1_000_000
        return DIAGNOSTIC_ONLY, elapsed_ms, 0, []
    separator = recognition["separator_variables"]
    instance = SeparatorAffineFamilyInstance(
        instance_id="heldout_" + label,
        formula=formula,
        separator_variables=separator,
        separator_bound_c=1,
        affine_arity_bound_r=2,
        expected_result="benchmark",
        family="heldout-guarded-affine",
        n=len(formula.variables),
    )
    certificate = build_separator_affine_certificate(instance)
    verified = check_separator_affine_certificate(formula, certificate)
    if (verified["checker_status"] != SEPARATOR_AFFINE_CERTIFICATE_VERIFIED
            or certificate.checker_status != SEPARATOR_AFFINE_CERTIFICATE_VERIFIED
            or certificate.final_result not in (SAT_CERTIFIED, UNSAT_CERTIFIED)):
        raise AssertionError(f"native certificate rejected: {label}: {verified.get('errors')}")
    elapsed_ms = (time.perf_counter_ns() - t0) / 1_000_000
    data = json.dumps(certificate.to_dict(), sort_keys=True, separators=(",", ":"))
    return certificate.final_result, elapsed_ms, len(data.encode("utf-8")), separator


def measure(trials: int) -> dict:
    rows = []
    for family, size, seed in product(FAMILIES, SIZES, SEEDS):
        original = make_separator_affine_instance(f"{family}_{size}")
        formula = permute_with_sign_flips(original.formula, seed)
        label = f"{family}_{size}_seed{seed}"
        for trial in range(trials):
            # Reverse measurement order every other trial to reduce order bias.
            if trial % 2:
                ours = witnora_native_answer(formula, label)
                oracle = minisat_answer(formula)
            else:
                oracle = minisat_answer(formula)
                ours = witnora_native_answer(formula, label)
            if ours[0] != oracle[0] and ours[0] != DIAGNOSTIC_ONLY:
                raise AssertionError(f"independent SAT answer mismatch: {label} {ours[0]} != {oracle[0]}")
            rows.append({
                "family": family, "components": size, "seed": seed, "trial": trial,
                "variables": len(formula.variables), "clauses": len(formula.clauses),
                "answer": oracle[0], "native_status": ours[0], "separator": ours[3],
                "minisat_total_ms": round(oracle[1], 6),
                "witnora_native_total_ms": round(ours[1], 6),
                "certificate_bytes": ours[2],
                "native_certificate_verified": ours[0] != DIAGNOSTIC_ONLY,
            })
    groups = defaultdict(list)
    for row in rows:
        groups[(row["family"], row["components"], row["seed"])].append(row)
    summaries = []
    for (family, size, seed), selected in sorted(groups.items()):
        mini = statistics.median(r["minisat_total_ms"] for r in selected)
        ours = statistics.median(r["witnora_native_total_ms"] for r in selected)
        summaries.append({
            "family": family, "components": size, "seed": seed,
            "variables": selected[0]["variables"], "clauses": selected[0]["clauses"],
            "answer": selected[0]["answer"], "native_status": selected[0]["native_status"],
            "minisat_median_ms": round(mini, 6),
            "witnora_native_median_ms": round(ours, 6),
            "native_over_minisat_ratio": round(ours / mini, 3) if mini > 0 and selected[0]["native_certificate_verified"] else None,
            "certificate_bytes": selected[0]["certificate_bytes"],
        })
    return {
        "kind": "TC063_HELDOUT_GUARDED_AFFINE_MINISAT_BENCHMARK",
        "scope": "Independent MiniSat22 vs native G14 recognizer + certificate builder + checker",
        "limitations": [
            "Synthetic guarded-affine families, not industrial SAT benchmarks",
            "MiniSat returns an answer; Witnora additionally produces and checks a native certificate",
            "Lean kernel checking excluded from Witnora timings",
            "Wall-clock timings are short; environment and noise strongly affect ratios",
            "A native certificate check is not a universal Python-to-Lean refinement proof",
        ],
        "trial_count": trials,
        "case_count": len(summaries),
        "certified_answer_agreement": sum(row["native_certificate_verified"] for row in rows),
        "diagnostic_only_count": sum(not row["native_certificate_verified"] for row in rows),
        "all_emitted_certificates_accepted": True,
        "native_total_wins": sum(row["native_certificate_verified"] and row["witnora_native_total_ms"] < row["minisat_total_ms"] for row in rows),
        "summary": summaries,
        "samples": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=2)
    parser.add_argument("--output", default="tc063_heldout_minisat.json")
    args = parser.parse_args()
    if not 1 <= args.trials <= 10:
        parser.error("trials must be between 1 and 10")
    result = measure(args.trials)
    Path(args.output).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "cases": result["case_count"],
        "certified_agreement": result["certified_answer_agreement"],
        "diagnostic_only": result["diagnostic_only_count"],
        "all_emitted_certificates_accepted": result["all_emitted_certificates_accepted"],
        "native_total_wins": result["native_total_wins"],
        "output": args.output,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
