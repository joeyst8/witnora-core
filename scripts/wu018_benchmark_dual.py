"""WU-018: paired runtime/correctness gate for a four-dual-mask XNF shortcut.

The baseline must be the pinned, unmodified Xorcle binary. Both solver
variants receive exactly the same options; timeout results are censored.
This is an engineering experiment, not a general-purpose SAT claim.
"""

import argparse
import csv
from pathlib import Path
import re
import subprocess
import sys
import time

if __package__:
    from .wu014_real_solver_pilot import check_model, parse_xnf, read_solution
    from .wu015_xorcle_ablation import collect_counters
else:
    from wu014_real_solver_pilot import check_model, parse_xnf, read_solution
    from wu015_xorcle_ablation import collect_counters

DUAL_KEYS = ("attempts", "eligible", "skipped", "rebuilds", "row_visits")
COUNTERS = ("conflicts", "propagations", "attempted_propagations", "watch_updates",
            "learned_clauses", "decisions")


def parse_dual_profile(stderr):
    latest = None
    for line in stderr.splitlines():
        if not line.startswith("WU018_DUAL "):
            continue
        items = dict(re.findall(r"([a-z0-9_]+)=([^\s]+)", line))
        if "stage" not in items or any(key not in items for key in DUAL_KEYS):
            raise ValueError("malformed WU018_DUAL snapshot")
        latest = {"dual_stage": items["stage"],
                  **{key: int(items[key]) for key in DUAL_KEYS}}
    return latest


def run_one(executable, options, instance, timeout, expect_dual):
    start = time.perf_counter()
    try:
        p = subprocess.run([str(executable), *options, str(instance)],
                           timeout=timeout, capture_output=True, text=True)
        elapsed = time.perf_counter() - start
        if p.returncode:
            raise ValueError(f"solver exit={p.returncode}; stderr={p.stderr[:300]}")
        status = "FINISHED"
        stdout, stderr = p.stdout, p.stderr
    except subprocess.TimeoutExpired as exc:
        elapsed = time.perf_counter() - start
        status = "TIMEOUT"
        stdout = exc.stdout.decode(errors="replace") if exc.stdout else ""
        stderr = exc.stderr.decode(errors="replace") if exc.stderr else ""
    return status, elapsed, stdout, stderr


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--instances", type=Path, required=True)
    p.add_argument("--baseline", type=Path, required=True)
    p.add_argument("--dual", type=Path, required=True)
    p.add_argument("--results", type=Path, required=True)
    p.add_argument("--timeout", type=float, default=3.5)
    p.add_argument("--max-cases", type=int, default=8)
    p.add_argument("--selection", choices=("cyclic", "leading_term_watchlist"),
                   default="cyclic")
    p.add_argument("--repetitions", type=int, default=1)
    args = p.parse_args()
    if not 0.1 <= args.timeout <= 60 or args.max_cases < 1 or args.repetitions < 1:
        p.error("invalid timing/case-count parameters")
    with (args.instances / "manifest.tsv").open(newline="") as f:
        cases = list(csv.DictReader(f, delimiter="\t"))[:args.max_cases]
    options = ("--selection=leading_term_watchlist",) if args.selection != "cyclic" else ()
    fields = ("family", "n", "seed", "repeat", "selection", "build", "status",
              "wall_seconds", "verification", *COUNTERS, "dual_stage", *DUAL_KEYS)
    args.results.parent.mkdir(parents=True, exist_ok=True)
    with args.results.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for rep in range(args.repetitions):
            for i, entry in enumerate(cases):
                instance = args.instances / entry["file"]
                if instance.resolve().parent != args.instances.resolve():
                    raise ValueError("invalid instance path")
                n, clauses = parse_xnf(instance)
                pair = (("baseline", args.baseline), ("dual", args.dual))
                if (rep + i) % 2:
                    pair = tuple(reversed(pair))
                complete = {}
                for name, executable in pair:
                    status, elapsed, stdout, stderr = run_one(executable, options,
                                                               instance, args.timeout,
                                                               name == "dual")
                    row = {"family": entry["family"], "n": n,
                           "seed": entry["seed"], "repeat": rep,
                           "selection": args.selection, "build": name,
                           "status": status, "wall_seconds": f"{elapsed:.6f}",
                           "verification": "none", "dual_stage": "",
                           **{key: "" for key in (*COUNTERS, *DUAL_KEYS)}}
                    if status == "FINISHED":
                        outcome, model = read_solution(stdout, n)
                        row["status"] = outcome
                        if outcome == "SAT":
                            if not check_model(n, clauses, model):
                                raise ValueError("invalid SAT model")
                            row["verification"] = "SAT_MODEL_OK"
                        else:
                            row["verification"] = "UNSAT_NOT_PROOF_CHECKED"
                        counters = collect_counters(stdout)
                        row.update(counters)
                        complete[name] = (outcome, counters)
                    if name == "dual":
                        observation = parse_dual_profile(stderr)
                        if observation is None:
                            raise ValueError("no WU018_DUAL observation")
                        row.update(observation)
                        if status == "FINISHED" and observation["attempts"] != row["attempted_propagations"]:
                            raise ValueError("dual counters mismatch")
                    writer.writerow(row)
                    f.flush()
                    print(f"WU018 {args.selection} rep={rep} case={i+1}/{len(cases)} "
                          f"seed={entry['seed']} {name}: {row['status']} {elapsed:.3f}s, "
                          f"skipped={row['skipped']}", flush=True)
                if len(complete) == 2:
                    if complete["baseline"][0] != complete["dual"][0]:
                        raise ValueError("solver outcome mismatch")
                    for key in COUNTERS:
                        if complete["baseline"][1][key] != complete["dual"][1][key]:
                            raise ValueError(f"solver search differed: {key}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError) as exc:
        print(f"WU018 error: {exc}", file=sys.stderr)
        sys.exit(2)
