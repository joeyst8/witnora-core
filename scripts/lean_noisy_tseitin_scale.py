"""Bounded Lean source-to-G5 kernel proof size ladder for real noisy Tseitin CNF.

This is a capacity experiment. A successful native candidate does NOT imply
that Lean has checked it; only CI compilation changes that status.
"""
from __future__ import annotations
import argparse
from pathlib import Path

from scripts.experiment_noisy_tseitin_source_subset import (
    lean_source_for, make_case, source_subset_candidate,
)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--vertices", type=int, choices=(16, 32, 48), required=True)
    p.add_argument("--seed", type=int, default=307)
    p.add_argument("--noise", type=int, default=2)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    if not 0 <= a.noise <= 4:
        p.error("noise must stay within 0..4")
    formula = make_case(a.vertices, a.seed, a.noise, odd=True)
    candidate, subset, certificate = source_subset_candidate(
        formula, f"lean_scale_n{a.vertices}_s{a.seed}_noise{a.noise}")
    if candidate["status"] != "SOURCE_SUBSET_G5_NATIVE_UNSAT_CANDIDATE":
        raise AssertionError("source-subset G5 native certificate missing")
    generated = lean_source_for(formula, subset, certificate)
    a.out.write_text(generated, encoding="utf-8")
    print(f"vertices={a.vertices} vars={len(formula.variables)} clauses={len(formula.clauses)} "
          f"source_hash={formula.formula_hash} lean_file_bytes={len(generated)} "
          "native_status=NOT_LEAN_VERIFIED_PENDING_CI")


if __name__ == "__main__":
    main()
