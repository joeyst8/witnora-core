"""Fail-closed external SATLIB challenge, with full data provenance."""
from __future__ import annotations

import csv
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import tarfile
from time import perf_counter
from urllib.request import urlopen

from pysat.solvers import Glucose3
from witnora_core.dimacs import parse_dimacs
from witnora_core.experimental_operator_search import independent_sat
from witnora_core.incremental_separator import solve_incremental
from witnora_core.satlib_fingerprint import fingerprint

SOURCE_BASE = "https://www.cs.ubc.ca/~hoos/SATLIB/Benchmarks/SAT/RND3SAT/"
SUITES = (("uf125-538", True), ("uuf125-538", False))


def fetch_cases(suite: str, *, limit: int = 6):
    url = SOURCE_BASE + suite + ".tar.gz"
    with urlopen(url, timeout=30) as response:
        raw = response.read(20_000_001)
    if not raw or len(raw) > 20_000_000:
        raise ValueError("missing or oversized SATLIB archive")
    archive_hash = sha256(raw).hexdigest()
    cases = []
    with tarfile.open(fileobj=BytesIO(raw), mode="r:gz") as archive:
        members = sorted((member for member in archive.getmembers()
                          if member.isfile() and member.name.lower().endswith(".cnf")),
                         key=lambda m: m.name)
        for member in members[:limit]:
            if member.size > 2_000_000:
                raise ValueError("individual CNF exceeds cap")
            stream = archive.extractfile(member)
            if stream is None:
                raise ValueError("missing member bytes")
            data = stream.read()
            formula = parse_dimacs(data.decode("utf-8"))
            cases.append((member.name, sha256(data).hexdigest(), formula))
    if len(cases) < limit:
        raise ValueError("external benchmark missing requested instances")
    return url, archive_hash, cases


def direct(formula):
    with Glucose3(bootstrap_with=formula.to_clause_lists()) as solver:
        return bool(solver.solve())


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("satlib-external-study.csv"))
    args = parser.parse_args()
    rows = []
    for suite, expected_truth in SUITES:
        url, archive_sha, cases = fetch_cases(suite)
        for path, member_sha, formula in cases:
            structural = fingerprint(formula)
            before = perf_counter()
            direct_truth = direct(formula)
            direct_ms = (perf_counter() - before) * 1000
            before = perf_counter()
            candidate = solve_incremental(formula)
            candidate_ms = (perf_counter() - before) * 1000
            oracle = independent_sat(formula)
            if not (direct_truth == candidate["satisfiable"]
                    == oracle["glucose3"] == expected_truth):
                raise AssertionError(f"external SAT truth mismatch {suite} {path}")
            rows.append({
                "source_suite": suite, "archive_url": url,
                "archive_sha256": archive_sha, "member_path": path,
                "member_sha256": member_sha, **structural,
                "expected_satisfiable": expected_truth,
                "candidate_mode": candidate["mode"],
                "direct_glucose_ms": round(direct_ms, 6),
                "experimental_total_ms": round(candidate_ms, 6),
                "independent_solver_agreement": True,
            })
    with args.output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print({"source": "official SATLIB hosted at UBC",
           "cases": len(rows),
           "sat_cases": sum(row["expected_satisfiable"] for row in rows),
           "unsat_cases": sum(not row["expected_satisfiable"] for row in rows),
           "exact_xor_rows": sum(row["exact_xor_equations_detected"] > 0 for row in rows),
           "total_runtime_wins": sum(row["experimental_total_ms"] < row["direct_glucose_ms"] for row in rows),
           "all_truths_agree": True, "trusted": False})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
