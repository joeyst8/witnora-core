"""WU-019: independently verify paired untouched and wide-mask Xorcle UNSAT proofs."""

import argparse
import csv
import hashlib
from pathlib import Path
import subprocess
import sys
import time

from scripts.wu015_xorcle_ablation import collect_counters


def timed(command, timeout):
    start = time.perf_counter()
    result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    return result, time.perf_counter() - start


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--instances", type=Path, required=True)
    ap.add_argument("--baseline", type=Path, required=True)
    ap.add_argument("--wide", type=Path, required=True)
    ap.add_argument("--checker", type=Path, required=True)
    ap.add_argument("--scratch", type=Path, required=True)
    ap.add_argument("--results", type=Path, required=True)
    ap.add_argument("--width", type=int, default=80)
    ap.add_argument("--selection", choices=("cyclic", "leading_term_watchlist"), default="cyclic")
    ap.add_argument("--timeout", type=float, default=35)
    args = ap.parse_args()
    if not 0.1 <= args.timeout <= 120:
        ap.error("timeout outside 0.1..120")
    with (args.instances / "manifest.tsv").open(newline="") as f:
        cases = [r for r in csv.DictReader(f, delimiter="\t")
                 if r["family"] == "embedded_unplanted" and int(r["variables"]) == args.width]
    if len(cases) != 1:
        raise ValueError("expected one selected embedded unplanted case")
    args.scratch.mkdir(parents=True, exist_ok=True)
    rows = []
    for case in cases:
        instance = args.instances / case["file"]
        for build, binary in (("baseline", args.baseline), ("wide", args.wide)):
            proof = args.scratch / f"wu019_n{args.width}_{args.selection}_{build}.lrup"
            result, solve_s = timed([str(binary), "--compact=false",
                                     f"--selection={args.selection}", f"--proof={proof}",
                                     str(instance)], args.timeout)
            if result.returncode not in (0, 20) or "s UNSATISFIABLE" not in result.stdout:
                raise ValueError(f"{build} did not produce UNSAT proof")
            checked, check_s = timed([sys.executable, str(args.checker),
                                      str(instance), str(proof)], args.timeout)
            if checked.returncode or "OK:" not in checked.stdout:
                raise ValueError(f"{build} independent proof checker failed: {checked.stdout}")
            rows.append({"family": case["family"], "n": args.width,
                         "seed": case["seed"], "selection": args.selection,
                         "build": build, "status": "CHECKED_UNSAT",
                         "solver_seconds": f"{solve_s:.6f}",
                         "checker_seconds": f"{check_s:.6f}",
                         "proof_bytes": proof.stat().st_size,
                         "proof_sha256": hashlib.sha256(proof.read_bytes()).hexdigest(),
                         **collect_counters(result.stdout)})
            print(f"WU019 native proof {args.width} {args.selection} {build}: "
                  f"{solve_s:.3f}s + checker {check_s:.3f}s", flush=True)
    left, right = rows
    for key in ("proof_sha256", "proof_bytes", "conflicts", "propagations",
                "attempted_propagations", "watch_updates", "learned_clauses", "decisions"):
        if left[key] != right[key]:
            raise ValueError(f"proof/search differed on {key}")
    args.results.parent.mkdir(parents=True, exist_ok=True)
    with args.results.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError, subprocess.TimeoutExpired) as error:
        print(f"WU019 independent native proof failure: {error}", file=sys.stderr)
        sys.exit(2)
