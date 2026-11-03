"""R-001: compare exact Python vs Rust VE including subprocess cost.

Rust and Python count identical normalized source-CNF components.
Independent Ganak timings are taken separately; no solver-wide
speed claim follows from this component-only pilot.
"""
from __future__ import annotations

import json
import os

from scripts.benchmark_crc_scaling import measured
from scripts.benchmark_crc_highcount import independent_ganak
from scripts.benchmark_crc_adversarial import chain_source, ring_source
from scripts.benchmark_crc_variable_elimination import fibonacci
from witnora_core.crc_boundary import _normalized_clauses
from witnora_core.crc_rust_bridge import count_component_by_rust_elimination
from witnora_core.crc_variable_elimination_indexed import (
    count_component_by_indexed_elimination,
)


def run(n, family):
    source = chain_source(n) if family == "chain" else ring_source(n)
    expected = (fibonacci(n + 2) if family == "chain"
                else fibonacci(n - 1) + fibonacci(n + 1))
    clauses = _normalized_clauses(source, tuple(range(1, n + 1)))
    boundary = tuple(range(1, n + 1))

    def direct(backend):
        result = backend(
            clauses, boundary, max_factor_variables=3,
            max_operations=200000)
        return None if result is None else (
            result.models, result.operations, result.max_factor_variables)
    python = measured(lambda: direct(count_component_by_indexed_elimination),
                      repeats=3, seconds=6)
    native = measured(lambda: direct(count_component_by_rust_elimination),
                      repeats=3, seconds=6)
    cli_binary = os.environ["WITNORA_RUST_VE_BIN"]
    def cli(clauses, boundary, *, max_factor_variables, max_operations):
        return count_component_by_rust_elimination(
            clauses, boundary, max_factor_variables=max_factor_variables,
            max_operations=max_operations, binary_path=cli_binary)
    rust_cli = measured(lambda: direct(cli), repeats=3, seconds=6)
    ganak = independent_ganak(source, n, seconds=6)
    if (python["status"] != native["status"] or
            python["status"] != rust_cli["status"] or
            python["status"] != "EXACT"):
        raise AssertionError(f"Rust/Python admission mismatch {family} n={n}")
    if (python["models"] != expected or native["models"] != expected or
            rust_cli["models"] != expected):
        raise AssertionError(f"model count mismatch {family} n={n}")
    if python["states"] != native["states"] or python["states"] != rust_cli["states"]:
        raise AssertionError(f"factor operation work mismatch {family} n={n}")
    if ganak["status"] != "EXACT" or ganak["models"] != expected:
        raise AssertionError(f"Ganak mismatch {family} n={n}")
    return {
        "family": family, "n": n, "clauses": len(source),
        "analytic_models": expected,
        "python": python, "rust_binding": native, "rust_cli": rust_cli,
        "ganak": ganak,
        "rust_binding_over_python_ms": round(
            native["median_ms"] / python["median_ms"], 3),
        "rust_cli_over_python_ms": round(
            rust_cli["median_ms"] / python["median_ms"], 3),
        "inprocess_binding_measured_separately": True,
    }


def main():
    rows = []
    for n in (16, 64, 128, 256):
        for family in ("chain", "ring"):
            row = run(n, family)
            rows.append(row)
            print(json.dumps(row, sort_keys=True), flush=True)
    print(json.dumps({
        "summary": "R-001 Rust indexed variable elimination migration pilot",
        "cases": len(rows), "matched_analytic_and_ganak": len(rows),
        "not_a_general_sat_improvement": True,
    }, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
