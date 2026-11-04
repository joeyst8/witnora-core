"""W-CRC-003: high-model-count nonlinear CNF, with dedicated Ganak baseline.

The goal is to break cheap PySAT all-model enumeration. Ganak's
unweighted Counter uses integer arithmetic, but its default component
cache has a stated very small probability of hash-collision miscount.
The Ganak baseline runs in an isolated time-limited process. The
in-worker measured duration includes Counter creation, source loading
and counting; process startup duration is reported separately.

Run after installing python-sat and pyganak==2.8.0:
  python -m scripts.benchmark_crc_highcount
"""
from __future__ import annotations

import argparse
import json
import multiprocessing
import time

from scripts.benchmark_crc_scaling import (
    benchmark_case, overlapping_parity_source,
)
from scripts.benchmark_crc_vs_anf import dense_control


def _ganak_worker(clauses, nvars, sender):
    started = time.perf_counter()
    try:
        from pyganak import Counter
        counter = Counter(verbose=0, seed=0)
        counter.new_vars(nvars)
        counter.add_clauses(clauses)
        count = counter.count()
        sender.send(("EXACT", int(count),
                     round((time.perf_counter() - started) * 1000, 4)))
    except BaseException as exc:
        sender.send(("ERROR", type(exc).__name__ + ": " + str(exc), None))
    finally:
        sender.close()


def independent_ganak(clauses, nvars, *, seconds=2.5):
    """Complete integer result or timed failure; never infer UNSAT on timeout."""
    if seconds <= 0:
        raise ValueError("seconds must be positive")
    receiver, sender = multiprocessing.Pipe(duplex=False)
    worker = multiprocessing.Process(
        target=_ganak_worker, args=(clauses, nvars, sender),
        daemon=True,
    )
    started = time.perf_counter()
    worker.start()
    sender.close()
    worker.join(seconds)
    elapsed_ms = round((time.perf_counter() - started) * 1000, 4)
    if worker.is_alive():
        worker.kill()
        worker.join()
        receiver.close()
        return {"status": "TIMEOUT", "process_wall_ms": elapsed_ms}
    if not receiver.poll():
        receiver.close()
        return {
            "status": "ERROR", "process_wall_ms": elapsed_ms,
            "message": "Ganak process exited without a model count",
        }
    status, data, engine_ms = receiver.recv()
    receiver.close()
    if status != "EXACT":
        return {
            "status": "ERROR", "process_wall_ms": elapsed_ms,
            "message": str(data),
        }
    return {
        "status": "EXACT",
        "models": data,
        "counter_wall_ms": engine_ms,
        "process_wall_ms": elapsed_ms,
        "cache_guarantee": "probabilistic_default",
    }


def run_case(
    family, source, nvars, nonlinear, boundary, seed,
    *, repeats, seconds, max_states, max_models,
):
    row = benchmark_case(
        family, source, nvars, nonlinear, boundary, seed,
        repeats=repeats, seconds=seconds, max_states=max_states,
        max_models=max_models,
    )
    ganak = independent_ganak(source, nvars, seconds=seconds)
    for key in ("crc_ie", "crc_shannon", "structured_anf",
                "external_pysat_model_enumeration"):
        other = row[key]
        if ganak["status"] == other["status"] == "EXACT":
            if ganak["models"] != other["models"]:
                raise AssertionError(
                    f"Ganak {ganak['models']} disagrees with {key}: {other['models']}"
                )
    if ganak["status"] == "EXACT" and row["external_pysat_sat_decision"]["status"] == "EXACT":
        if (ganak["models"] > 0) != bool(
            row["external_pysat_sat_decision"]["models"]
        ):
            raise AssertionError("Ganak count disagrees with Glucose3 SAT decision")
    row["external_ganak_counter"] = ganak
    row["crc_over_ganak_engine_time_if_both_exact"] = (
        round(row["crc_shannon"]["median_ms"] / ganak["counter_wall_ms"], 3)
        if ganak["status"] == row["crc_shannon"]["status"] == "EXACT"
        and ganak["counter_wall_ms"] else None
    )
    return row


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--seconds", type=float, default=2.5)
    parser.add_argument("--max-states", type=int, default=3000)
    parser.add_argument("--max-models", type=int, default=1000)
    parser.add_argument("--ratio", type=float, default=2.4)
    options = parser.parse_args()
    if options.ratio <= 0 or options.repeats <= 0:
        parser.error("ratio and repeats must be positive")
    rows = []
    for k in (24, 32, 40):
        for offset in range(3):
            seed = 20261103 + offset
            source, nvars = dense_control(
                seed + 1000 * k, k, round(options.ratio * k),
            )
            rows.append(run_case(
                "highcount_dense_3cnf", source, nvars, source,
                tuple(range(1, k + 1)), seed,
                repeats=options.repeats, seconds=options.seconds,
                max_states=options.max_states, max_models=options.max_models,
            ))
            source, nvars, nonlinear = overlapping_parity_source(
                k, seed + 1000 * k, ratio=options.ratio,
            )
            rows.append(run_case(
                "highcount_mixed_xor_3cnf", source, nvars, nonlinear,
                tuple(range(1, k + 1)), seed,
                repeats=options.repeats, seconds=options.seconds,
                max_states=options.max_states, max_models=options.max_models,
            ))
    for row in rows:
        print(json.dumps(row, sort_keys=True), flush=True)
    print(json.dumps({
        "summary": "W-CRC-003",
        "cases": len(rows),
        "ganak_exact": sum(
            row["external_ganak_counter"]["status"] == "EXACT" for row in rows),
        "shannon_exact": sum(
            row["crc_shannon"]["status"] == "EXACT" for row in rows),
        "anf_exact": sum(
            row["structured_anf"]["status"] == "EXACT" for row in rows),
        "enumeration_capped": sum(
            row["external_pysat_model_enumeration"]["status"] == "MODEL_CAP_REACHED"
            for row in rows),
        "status": "pilot_only_no_general_sat_claim",
    }, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
