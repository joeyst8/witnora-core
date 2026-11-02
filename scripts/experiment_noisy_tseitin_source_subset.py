"""Falsifiable source-subset G5 experiment on noisy cubic-graph Tseitin CNFs.

All odd-charge Tseitin cores are UNSAT, even-charge cores SAT. Noise clauses
have a fresh always-true guard literal, so do not alter satisfiability.
This is known GF(2) reasoning, NOT a mathematical-novelty claim.

A candidate UNSAT only passes if exact full XOR-CNF clauses are present in
the source, a separately rebuilt subset has a native checked G5 contradiction,
and a small instance's entire source-subset claim is kernel-checked by Lean.
The Python-native status alone is never labelled LEAN_VERIFIED.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from itertools import product
import json
from multiprocessing import get_context
from pathlib import Path
import random
from statistics import median
from time import perf_counter_ns

from witnora_core.cnf import CNFFormula
from witnora_core.operator_genesis import (
    AFFINE_RESIDUE_CERTIFICATE_VERIFIED,
    AFFINE_RESIDUE_UNSAT_NATIVE_CERTIFIED,
    AffineResidueInstance,
    build_affine_residue_certificate,
    check_affine_residue_certificate,
)
from witnora_core.xor import canonical_xor_cnf_clauses, detect_cnf_xor_patterns


def cubic_edges(vertices: int, seed: int) -> list[tuple[int, int]]:
    if vertices < 8 or vertices % 2:
        raise ValueError("requires an even number of vertices >= 8")
    rng = random.Random(seed)
    cycle = {tuple(sorted((i, (i + 1) % vertices))) for i in range(vertices)}
    matching = None
    for _ in range(200):
        order = list(range(vertices))
        rng.shuffle(order)
        pairs = {tuple(sorted((order[j], order[j + 1])))
                 for j in range(0, vertices, 2)}
        if all(pair not in cycle for pair in pairs):
            matching = pairs
            break
    if matching is None:
        raise AssertionError("failed to construct disjoint random matching")
    edges = sorted(cycle | matching)
    assert len(edges) == 3 * vertices // 2
    return edges


def make_case(vertices: int, seed: int, noise_per_vertex: int, *, odd: bool) -> CNFFormula:
    edges = cubic_edges(vertices, seed)
    incidents = [[] for _ in range(vertices)]
    for variable, (left, right) in enumerate(edges, start=1):
        incidents[left].append(variable)
        incidents[right].append(variable)
    raw = []
    for vertex, variables in enumerate(incidents):
        if len(variables) != 3:
            raise AssertionError("not cubic")
        raw.extend(canonical_xor_cnf_clauses(variables, int(odd and vertex == 0)))
    guard = len(edges) + 1
    rng = random.Random(seed * 1009 + vertices * 17 + noise_per_vertex)
    for _ in range(vertices * noise_per_vertex):
        chosen = rng.sample(range(1, len(edges) + 1), 3)
        raw.append((guard, *(v if rng.getrandbits(1) else -v for v in chosen)))
    rng.shuffle(raw)
    return CNFFormula.from_raw_clauses(raw)


def drop_one_xor_clause(formula: CNFFormula, vertices: int, seed: int) -> CNFFormula:
    """Remove one clause from the first vertex parity encoding."""
    incident = [index for index, edge in enumerate(cubic_edges(vertices, seed), start=1)
                if 0 in edge]
    target = sorted(canonical_xor_cnf_clauses(incident, 1))[0]
    remaining = [clause.to_list() for clause in formula.clauses
                 if tuple(clause.literals) != target]
    if len(remaining) != len(formula.clauses) - 1:
        raise AssertionError("expected exactly one source clause deletion")
    return CNFFormula.from_raw_clauses(remaining)


def extract_source_subset(formula: CNFFormula):
    """Return an exact source-clause subset and source IDs, or no candidate."""
    detected = detect_cnf_xor_patterns(formula, max_k=3)
    source_ids = {tuple(clause.literals): index
                  for index, clause in enumerate(formula.clauses, start=1)}
    selected = set()
    equations = 0
    for eq in detected.equations:
        if not (eq.safe_use and eq.exact_full_encoding and len(eq.variables) == 3):
            continue
        clauses = {tuple(clause) for clause in eq.source_clauses}
        if clauses != canonical_xor_cnf_clauses(eq.variables, eq.rhs):
            raise AssertionError("exact XOR encoding mismatch")
        if not clauses.issubset(source_ids):
            raise AssertionError("source clause not present")
        equations += 1
        selected.update(clauses)
    if not selected:
        return None, [], 0
    subset = CNFFormula.from_raw_clauses(selected)
    if not {tuple(c.literals) for c in subset.clauses}.issubset(source_ids):
        raise AssertionError("normalized subset not contained in source")
    return subset, sorted(source_ids[c] for c in selected), equations


def source_subset_candidate(formula: CNFFormula, label: str):
    """Recheck both source inclusion and the extracted G5 certificate."""
    begin = perf_counter_ns()
    subset, clause_ids, equation_count = extract_source_subset(formula)
    if subset is None:
        return {"status": "DIAGNOSTIC_ONLY", "elapsed_ms": (perf_counter_ns() - begin) / 1e6,
                "equations": 0, "subset_clauses": 0}, None, None
    instance = AffineResidueInstance(
        instance_id="noisy_tseitin_" + label, equations=(), formula=subset,
        family="source-subset-g5", expected_outcome="unknown",
        description="Only clauses independently found in full source CNF",
    )
    cert = build_affine_residue_certificate(instance, max_arity=3)
    verified = check_affine_residue_certificate(subset, cert, max_arity=3)
    source_keys = {tuple(c.literals) for c in formula.clauses}
    inclusion = all(tuple(c.literals) in source_keys for c in subset.clauses)
    native_unsat = (
        inclusion
        and verified["status"] == AFFINE_RESIDUE_CERTIFICATE_VERIFIED
        and cert.checker_status == AFFINE_RESIDUE_CERTIFICATE_VERIFIED
        and cert.status == AFFINE_RESIDUE_UNSAT_NATIVE_CERTIFIED
    )
    elapsed_ms = (perf_counter_ns() - begin) / 1e6
    return {
        "status": "SOURCE_SUBSET_G5_NATIVE_UNSAT_CANDIDATE" if native_unsat else "DIAGNOSTIC_ONLY",
        "elapsed_ms": round(elapsed_ms, 6),
        "equations": equation_count, "subset_clauses": len(subset.clauses),
        "source_clauses": len(formula.clauses),
        "source_hash": formula.formula_hash,
        "subset_hash": subset.formula_hash,
        "clause_ids": clause_ids,
        "subset_membership_rechecked": inclusion,
        "native_g5_verified": native_unsat,
        "lean_formal_status": "NOT_LEAN_VERIFIED",
    }, subset, cert


def _solver_worker(clauses, solver_name, out):
    from pysat import solvers
    try:
        solver_type = getattr(solvers, solver_name)
        start = perf_counter_ns()
        with solver_type(bootstrap_with=clauses) as solver:
            result = bool(solver.solve())
        out.put(("SAT" if result else "UNSAT", (perf_counter_ns() - start) / 1e6))
    except Exception as exc:
        out.put(("ERROR", str(exc)))


def bounded_solver(formula: CNFFormula, solver_name: str, limit_s: float):
    if solver_name not in ("Minisat22", "Cadical195"):
        raise ValueError("invalid independent solver")
    ctx = get_context("fork")
    queue = ctx.Queue()
    worker = ctx.Process(target=_solver_worker,
                         args=(formula.to_clause_lists(), solver_name, queue))
    start = perf_counter_ns()
    worker.start()
    worker.join(limit_s)
    if worker.is_alive():
        worker.terminate()
        worker.join(2)
        if worker.is_alive():
            worker.kill()
            worker.join(2)
        queue.close()
        return {"status": "UNKNOWN_TIMEOUT", "wall_ms": (perf_counter_ns() - start) / 1e6}
    if queue.empty():
        queue.close()
        return {"status": "ERROR", "error": "missing independent answer"}
    status, worker_ms = queue.get()
    queue.close()
    return {"status": status,
            "worker_ms": worker_ms,
            "wall_ms": round((perf_counter_ns() - start) / 1e6, 6)}


def lean_source_for(formula: CNFFormula, subset: CNFFormula, certificate) -> str:
    """Construct a closed proposition; Lean evaluates and proves it itself."""
    from witnora_core.lean_g5_gate import _compile_dag, _serialize_cnf, _serialize_rows
    payload = certificate.to_dict()
    trace = payload.get("gaussian_elimination_trace") or []
    if not trace or trace[0].get("type") != "INITIAL_ROWS":
        raise AssertionError("missing independently checked G5 initial rows")
    rows = trace[0]["rows"]
    source = _serialize_cnf(formula)
    chosen = _serialize_cnf(subset)
    bound = subset.max_var + 1
    body = [
        "import Witnora.SourceSubsetG5",
        "set_option maxRecDepth 16384",
        "set_option maxHeartbeats 0",
        "example : Witnora.SignedSerialization.decodeCNF "
        + str(formula.to_clause_lists()) + " = " + source + " := by decide",
        "example : Witnora.SourceSubsetG5.checkSourceSubsetG5 "
        + str(bound) + " " + source + " " + chosen
        + " " + _serialize_rows(rows) + " " + _compile_dag(rows, payload.get("row_operations"))
        + " = true := by decide",
        "example : ¬ ∃ a, Witnora.G5Extraction.CNFHolds " + source + " a := by",
        "  exact Witnora.SourceSubsetG5.checkSourceSubsetG5_unsat "
        + str(bound) + " " + source + " " + chosen
        + " " + _serialize_rows(rows) + " " + _compile_dag(rows, payload.get("row_operations"))
        + " (by decide)",
    ]
    return "\n".join(body) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=1)
    parser.add_argument("--limit-s", type=float, default=1.5)
    parser.add_argument("--out", type=Path, default=Path("noisy_tseitin_result.json"))
    parser.add_argument("--lean-smoke", type=Path, default=None)
    args = parser.parse_args()
    if not 1 <= args.trials <= 3 or not 0.2 <= args.limit_s <= 5:
        parser.error("invalid safe benchmark bound")
    rows = []
    for vertices, seed, noise in product((16, 32, 48), (11, 29), (0, 2)):
        formula = make_case(vertices, seed, noise, odd=True)
        for trial in range(args.trials):
            candidate, subset, cert = source_subset_candidate(formula, f"n{vertices}_s{seed}_noise{noise}")
            if candidate["status"] != "SOURCE_SUBSET_G5_NATIVE_UNSAT_CANDIDATE":
                raise AssertionError("expected exact source-subset G5 contradiction")
            baselines = {name: bounded_solver(formula, name, args.limit_s)
                         for name in ("Minisat22", "Cadical195")}
            if any(x["status"] not in ("UNSAT", "UNKNOWN_TIMEOUT")
                   for x in baselines.values()):
                raise AssertionError("independent solver contradicted UNSAT or errored")
            rows.append({
                "vertices": vertices, "seed": seed, "noise_per_vertex": noise,
                "trial": trial, "variables": len(formula.variables),
                "clauses": len(formula.clauses), "candidate": candidate,
                "baselines": baselines,
            })
    # SAT and incomplete-XOR controls must never receive an UNSAT claim.
    controls = []
    for label, formula in (
        ("even_charge_sat", make_case(16, 101, 2, odd=False)),
        ("broken_source_encoding", drop_one_xor_clause(
            make_case(16, 101, 2, odd=True), 16, 101)),
    ):
        candidate, _, _ = source_subset_candidate(formula, label)
        baseline = bounded_solver(formula, "Minisat22", args.limit_s)
        if baseline["status"] != "SAT":
            raise AssertionError("SAT adversarial control was not confirmed by MiniSat")
        if candidate["status"] != "DIAGNOSTIC_ONLY":
            raise AssertionError("SAT source falsely certified as UNSAT")
        controls.append({"label": label, "candidate": candidate["status"],
                         "minisat": baseline["status"]})
    if args.lean_smoke:
        small = make_case(8, 307, 2, odd=True)
        result, subset, cert = source_subset_candidate(small, "lean_smoke")
        if result["status"] != "SOURCE_SUBSET_G5_NATIVE_UNSAT_CANDIDATE":
            raise AssertionError("Lean smoke fixture lacks native proof")
        args.lean_smoke.write_text(lean_source_for(small, subset, cert), encoding="utf-8")
    output = {
        "kind": "NOISY_TSEITIN_SOURCE_SUBSET_G5_PROTOTYPE",
        "scope": "random Hamiltonian cubic graphs; exact XOR subset; satisfiability-preserving guarded non-affine noise",
        "prior_art": "Tseitin contradictions and Gaussian elimination are established techniques; no novelty claim",
        "lean_claim": "small generated fixture must be separately kernel-checked in CI; native rows alone are not Lean status",
        "trials": args.trials, "solver_limit_s": args.limit_s,
        "rows": rows, "controls": controls,
        "summary": {
            "cases": len(rows),
            "native_unsat_candidates": sum(row["candidate"]["native_g5_verified"] for row in rows),
            "minisat_unsat": sum(row["baselines"]["Minisat22"]["status"] == "UNSAT" for row in rows),
            "minisat_timeout": sum(row["baselines"]["Minisat22"]["status"] == "UNKNOWN_TIMEOUT" for row in rows),
            "cadical_unsat": sum(row["baselines"]["Cadical195"]["status"] == "UNSAT" for row in rows),
            "cadical_timeout": sum(row["baselines"]["Cadical195"]["status"] == "UNKNOWN_TIMEOUT" for row in rows),
        }
    }
    args.out.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(output["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
