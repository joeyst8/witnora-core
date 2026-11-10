"""WU-018: independent LRUP(+) checks for the native dual-mask experiment.

Generates proofs in scratch only. Uses published Xorcle's separate proof
checker (not the modified solver itself) and records solve + check costs.
"""

import argparse
import csv
import hashlib
from pathlib import Path
import subprocess
import sys
import time

if __package__:
    from .wu015_xorcle_ablation import collect_counters
else:
    from wu015_xorcle_ablation import collect_counters


def timed(cmd):
    start = time.perf_counter()
    result = subprocess.run(cmd, text=True, capture_output=True, timeout=60)
    return result, time.perf_counter() - start


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--instances", type=Path, required=True)
    ap.add_argument("--baseline", type=Path, required=True)
    ap.add_argument("--dual", type=Path, required=True)
    ap.add_argument("--checker", type=Path, required=True)
    ap.add_argument("--scratch", type=Path, required=True)
    ap.add_argument("--results", type=Path, required=True)
    args = ap.parse_args()
    args.scratch.mkdir(parents=True, exist_ok=True)
    with (args.instances / "manifest.tsv").open() as stream:
        cases = [row for row in csv.DictReader(stream, delimiter="\t")
                 if row["family"] == "unplanted"]
    if not cases:
        raise ValueError("no unplanted candidate UNSAT cases")
    rows = []
    for case in cases:
        instance = args.instances / case["file"]
        for selection in ("cyclic", "leading_term_watchlist"):
            same_instance = []
            for build, exe in (("baseline", args.baseline), ("dual", args.dual)):
                proof = args.scratch / (f"{case['seed']}_{selection}_{build}.lrup")
                run, solve_s = timed([str(exe), "--compact=false",
                                      f"--selection={selection}", f"--proof={proof}",
                                      str(instance)])
                if run.returncode or "s UNSATISFIABLE" not in run.stdout:
                    raise ValueError(f"not UNSAT: {case['seed']} {selection} {build}")
                check, check_s = timed([sys.executable, str(args.checker),
                                        str(instance), str(proof)])
                if check.returncode or "OK:" not in check.stdout:
                    raise ValueError(f"proof rejected: {case['seed']} {selection} {build}: {check.stdout[:200]}")
                counters = collect_counters(run.stdout)
                row = {"seed": case["seed"], "n": case["variables"],
                       "selection": selection, "build": build,
                       "status": "CHECKED_UNSAT", "solve_seconds": f"{solve_s:.6f}",
                       "check_seconds": f"{check_s:.6f}",
                       "proof_bytes": proof.stat().st_size,
                       "proof_sha256": hashlib.sha256(proof.read_bytes()).hexdigest(),
                       **counters}
                same_instance.append(row)
                rows.append(row)
                print(f"WU018 proof {case['seed']} {selection} {build}: "
                      f"solve={solve_s:.3f}s check={check_s:.3f}s", flush=True)
            a, b = same_instance
            for key in (*counters, "proof_sha256", "proof_bytes"):
                if a[key] != b[key]:
                    raise ValueError(f"proof/search mismatch {case['seed']}: {key}")
    args.results.parent.mkdir(parents=True, exist_ok=True)
    with args.results.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError, subprocess.TimeoutExpired) as exc:
        print(f"WU018 proof failure: {exc}", file=sys.stderr)
        sys.exit(2)
