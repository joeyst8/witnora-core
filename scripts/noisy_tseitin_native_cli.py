"""Fresh-process Witnora native check from the identical original DIMACS file.

For benchmark measurement only. It is NOT a per-instance Lean kernel proof.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

from pysat.formula import CNF

from witnora_core.cnf import CNFFormula
from scripts.experiment_noisy_tseitin_source_subset import source_subset_candidate


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--expected-hash", required=True)
    args = parser.parse_args()
    cnf = CNF(from_file=str(args.source))
    source = CNFFormula.from_raw_clauses(cnf.clauses)
    if source.formula_hash != args.expected_hash:
        raise AssertionError("DIMACS source checksum changed across independent input boundary")
    candidate, _, _ = source_subset_candidate(source, "fresh_process")
    print(json.dumps({"status": candidate["status"],
                      "source_hash": source.formula_hash,
                      "native_internal_ms": candidate["elapsed_ms"],
                      "lean_formal_status": "NOT_LEAN_VERIFIED"},
                     sort_keys=True))


if __name__ == "__main__":
    main()
