"""Frozen symbolic-syndrome transfer on independent original PARITY sources.

This is a **cross-instance negative/positive gate**, not an optimization
target. The par32-2-c holdout is sealed. The algorithmic primitives, width
caps, and resource budgets come unchanged from the successful par32-1-c gate.
Only structural dimensions and the minimum separator-side size scale with
the number of source residual variables; these are not fitted to timings.
"""
from __future__ import annotations

import argparse
import json
from hashlib import sha256
from multiprocessing import get_context
from subprocess import run
from time import perf_counter
from urllib.request import urlopen

from scripts.benchmark_real_satlib_parity_gate import BASE, fetch_file
from scripts.experiment_satlib_cryptominisat_gate import bounded_cms
from scripts.experiment_satlib_residual_fourier import _bits, source_residual_parity_rows
from scripts.experiment_satlib_syndrome_mitm import (
    candidate_natural_separators, exact_separator_counts,
    lift_original_xor_variables, parity_columns, split_local_factors,
)
from scripts.experiment_satlib_symbolic_syndrome_bdd import (
    SymbolicLimit, sparse_side_syndromes, symbolic_side_syndromes,
)
from scripts.experiment_satlib_incremental_syndrome_oracle import (
    assumptions_for_syndrome, make_syndrome_oracle,
)
from witnora_core.dimacs import parse_dimacs_with_raw


FROZEN_VALIDATION_SOURCES = {
    "par16-1-c.cnf.Z": "33691e8d6a59db323b77240ae6319353f3adc0738c36e7a3e1e9f3efaa182d8a",
    "par16-2-c.cnf.Z": "d85df8f9275977bbeb1e50fb2a3b8bce59fb6e0158dbde0b0ec33fb8faa30560",
    "par32-3-c.cnf.Z": "fe096410a048413b6279239143bab90bb5fb54037f7ac38d431cf81e892c12b6",
}


def fetch_validation_source(name):
    """Pin original archive SHA before the worker; never fetch sealed holdout."""
    if name not in FROZEN_VALIDATION_SOURCES:
        raise ValueError("unapproved validation source or sealed holdout")
    if name != "par32-3-c.cnf.Z":
        return fetch_file(name, True)
    # The shared historical fetcher has a separate, deliberately frozen name
    # allowlist. Extend only this validation gate without broadening it.
    with urlopen(BASE + name, timeout=25) as response:
        compressed = response.read(3_000_001)
    if not compressed or len(compressed) > 3_000_000:
        raise ValueError("missing or oversized official archive object")
    uncompressed = run(["uncompress", "-c"], input=compressed,
                       capture_output=True, check=True, timeout=12).stdout
    if not uncompressed or len(uncompressed) > 12_000_000:
        raise ValueError("missing or oversized official DIMACS")
    formula, clauses = parse_dimacs_with_raw(uncompressed.decode("ascii"))
    return {"dimacs_sha256": sha256(uncompressed).hexdigest(),
            "variables": formula.max_var, "clauses": len(clauses),
            "clause_lists": clauses}


def cross_instance_symbolic_search(raw_clauses, nvars, *, budget_s=30,
                                   node_cap=500_000, state_cap=100_000,
                                   sparse_entry_cap=250_000):
    """Source-exact model search; `UNKNOWN` is the only incomplete outcome."""
    if not (0 < budget_s <= 60 and 100 <= node_cap <= 2_000_000
            and 10 <= sparse_entry_cap <= 1_000_000):
        raise ValueError("unsupported frozen resource cap")
    start = perf_counter()
    deadline = start + budget_s
    try:
        residual, variables, rows, info, equations = source_residual_parity_rows(
            raw_clauses, nvars, return_source_equations=True)
        local = [(tuple(_bits(mask)), rhs) for mask, rhs in rows
                 if mask.bit_count() == 3]
        global_rows = [(tuple(_bits(mask)), rhs) for mask, rhs in rows
                       if mask.bit_count() > 3]
        if len(local) + len(global_rows) != len(rows) or not (1 <= len(global_rows) <= 32):
            return {"status": "UNSUPPORTED_SOURCE_STRUCTURE", "xor_info": info,
                    "elapsed_ms": round((perf_counter() - start) * 1000, 2)}
        candidates = candidate_natural_separators(
            variables, residual, local, min_side=max(8, len(variables) // 4))
        if not candidates or candidates[0]["boundary_size"] > 10:
            return {"status": "UNSUPPORTED_SEPARATOR", "xor_info": info,
                    "elapsed_ms": round((perf_counter() - start) * 1000, 2)}
        split = split_local_factors(residual, variables, local, candidates[0])
        source_ms = round((perf_counter() - start) * 1000, 2)
        counts = exact_separator_counts(split)
        count_ms = round((perf_counter() - start) * 1000 - source_ms, 2)
        columns, target = parity_columns(global_rows)
        batches = sorted(counts["conditional_model_counts"],
                         key=lambda r: (-(r["left"] * r["right"]), r["boundary_bits"]))
        records = []
        for batch in batches:
            b = batch["boundary_bits"]
            small = "left" if batch["left"] <= batch["right"] else "right"
            large = "right" if small == "left" else "left"
            if min(batch["left"], batch["right"]) > 50_000:
                records.append({"boundary_bits": b, "status": "SKIP_SMALL_SIDE_CAP"})
                continue
            if perf_counter() > deadline:
                raise SymbolicLimit("CROSS_INSTANCE_TIME_BUDGET")
            compile_start = perf_counter()
            bdd, root, bdd_stats = symbolic_side_syndromes(
                split, large, b, columns, width=len(global_rows),
                deadline=deadline, node_cap=node_cap, state_cap=state_cap)
            bdd_ms = round((perf_counter() - compile_start) * 1000, 2)
            if bdd_stats["models"] != batch[large]:
                raise AssertionError("BDD local count disagrees with exact DP")
            sparse_start = perf_counter()
            sparse, sparse_stats = sparse_side_syndromes(
                split, small, b, columns, deadline=deadline,
                entry_cap=sparse_entry_cap)
            if sparse_stats["models"] != batch[small]:
                raise AssertionError("sparse local count disagrees with exact DP")
            boundary_mask = 0
            boundary_signature = 0
            for j, v in enumerate(split["boundary"]):
                if b & (1 << j):
                    boundary_mask |= 1 << (v - 1)
                    boundary_signature ^= columns.get(v, 0)
            needed = target ^ boundary_signature
            chosen = next(((leftsig, witness, leftsig ^ needed)
                           for leftsig, witness in sparse.items()
                           if bdd.contains(root, leftsig ^ needed)), None)
            if chosen is None:
                records.append({"boundary_bits": b, "status": "EXACT_NO_JOIN",
                                "bdd_models": bdd_stats["models"],
                                "sparse_models": sparse_stats["models"]})
                continue
            _, smallmask, wanted = chosen
            large_solver, indicators = make_syndrome_oracle(
                split, large, b, global_rows, nvars)
            sat_large, model = large_solver.solve(
                assumptions=assumptions_for_syndrome(indicators, wanted))
            if not sat_large:
                raise AssertionError("exact BDD membership contradicted source side")
            combined = boundary_mask | smallmask
            for v in split[f"{large}_vars"]:
                if v not in split["boundary"] and model[v]:
                    combined |= 1 << (v - 1)
            assignment = {v: bool(combined & (1 << (v - 1))) for v in variables}
            full = lift_original_xor_variables(raw_clauses, nvars, assignment,
                                               source_equations=equations)
            digest = sha256(bytes(int(full[v]) for v in range(1, nvars + 1))).hexdigest()
            return {"status": "SAT_VERIFIED_ORIGINAL", "model_sha256": digest,
                    "separator": candidates[0], "matched_boundary_bits": b,
                    "xor_info": info, "exact_counts": counts,
                    "large_bdd": bdd_stats, "small_sparse": sparse_stats,
                    "source_ms": source_ms, "exact_count_ms": count_ms,
                    "bdd_compile_ms": bdd_ms,
                    "sparse_join_verify_ms": round((perf_counter() - sparse_start) * 1000, 2),
                    "right_oracle_queries": 1,
                    "elapsed_ms": round((perf_counter() - start) * 1000, 2),
                    "records": records}
    except SymbolicLimit as exc:
        return {"status": "UNKNOWN_RESOURCE_CAP", "reason": str(exc),
                "elapsed_ms": round((perf_counter() - start) * 1000, 2),
                "no_unsat_inference": True}
    except ValueError as exc:
        return {"status": "UNSUPPORTED_OPERATOR_WIDTH", "reason": str(exc),
                "elapsed_ms": round((perf_counter() - start) * 1000, 2),
                "no_unsat_inference": True}
    return {"status": "UNKNOWN_INCOMPLETE", "records": records,
            "elapsed_ms": round((perf_counter() - start) * 1000, 2),
            "no_unsat_inference": True}


def _worker(clauses, nvars, budget_s, queue):
    try:
        queue.put(cross_instance_symbolic_search(clauses, nvars, budget_s=budget_s))
    except Exception as exc:
        queue.put({"status": "ERROR", "error": repr(exc)})


def bounded_cross_instance(clauses, nvars, *, budget_s=30):
    if not (0 < budget_s <= 60):
        raise ValueError("invalid bounded worker budget")
    ctx = get_context("fork")
    queue = ctx.Queue()
    worker = ctx.Process(target=_worker, args=(clauses, nvars, budget_s, queue))
    start = perf_counter()
    worker.start()
    worker.join(budget_s)
    if worker.is_alive():
        worker.terminate()
        worker.join(2)
        if worker.is_alive():
            worker.kill()
            worker.join(2)
        queue.close()
        return {"status": "UNKNOWN_TIMEOUT", "wall_ms": round((perf_counter() - start) * 1000, 2),
                "no_unsat_inference": True}
    if queue.empty():
        queue.close()
        return {"status": "ERROR", "error": "cross-instance worker returned no data"}
    result = queue.get()
    queue.close()
    result["wall_ms"] = round((perf_counter() - start) * 1000, 2)
    return result


def benchmark(*, names=("par16-1-c.cnf.Z", "par16-2-c.cnf.Z", "par32-3-c.cnf.Z"), repeats=2,
              budget_s=30):
    if not names or any(n not in FROZEN_VALIDATION_SOURCES for n in names):
        raise ValueError("unapproved source or sealed holdout")
    if repeats not in (1, 2, 3):
        raise ValueError("unsupported repeat count")
    results = []
    for name in names:
        source = fetch_validation_source(name)
        if source["dimacs_sha256"] != FROZEN_VALIDATION_SOURCES[name]:
            raise AssertionError("external source digest changed")
        trials = []
        for i in range(repeats):
            trials.append({"trial": i + 1,
                           "symbolic": bounded_cross_instance(
                               source["clause_lists"], source["variables"],
                               budget_s=budget_s),
                           "raw_cms": bounded_cms(
                               source["clause_lists"], source["variables"],
                               "raw_cnf", timeout_s=12)})
        results.append({"source": name, "sha256": source["dimacs_sha256"],
                        "nvars": source["variables"], "clauses": source["clauses"],
                        "trials": trials})
    return {"gate": "frozen symbolic cross-instance validation",
            "source_download_excluded": True,
            "source_model_verification_required": True,
            "sealed_holdout_untouched": True,
            "results": results}


def compact_benchmark(result):
    """Only display metrics; leave the full verification record intact."""
    return {"sealed_holdout_untouched": result["sealed_holdout_untouched"],
            "results": [{"source": record["source"], "sha256": record["sha256"],
                         "trials": [{"trial": t["trial"],
                                     "symbolic_status": t["symbolic"]["status"],
                                     "symbolic_ms": t["symbolic"].get("elapsed_ms"),
                                     "symbolic_wall_ms": t["symbolic"].get("wall_ms"),
                                     "cms_status": t["raw_cms"]["status"],
                                     "cms_ms": t["raw_cms"].get("total_worker_ms"),
                                     "cms_wall_ms": t["raw_cms"].get("wall_ms"),
                                     "bdd_reachable_nodes": t["symbolic"].get(
                                         "large_bdd", {}).get("bdd_nodes_reachable"),
                                     "sparse_unique_syndromes": t["symbolic"].get(
                                         "small_sparse", {}).get("unique_syndromes"),
                                     "model_sha256": t["symbolic"].get("model_sha256")}
                                    for t in record["trials"]]}
                        for record in result["results"]]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, choices=(1, 2, 3), default=2)
    parser.add_argument("--budget", type=float, default=30)
    parser.add_argument("--names", nargs="+", default=list(FROZEN_VALIDATION_SOURCES),
                        choices=list(FROZEN_VALIDATION_SOURCES))
    parser.add_argument("--compact", action="store_true")
    args = parser.parse_args()
    result = benchmark(names=tuple(args.names), repeats=args.repeats,
                       budget_s=args.budget)
    print(json.dumps(compact_benchmark(result) if args.compact else result, indent=2))
