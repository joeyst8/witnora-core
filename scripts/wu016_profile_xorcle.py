"""WU-016: paired unmodified/instrumented Xorcle profiling on native XNF.

Instrumented source is a separate reproducible patch of pinned upstream
solver.cpp. Profile fields are sampled timings, *not* precise full-run CPU
attribution. Timeout rows preserve the latest progress snapshot only.
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


PROFILE_KEYS = ("attempts", "propagations", "conflicts", "watch_updates",
                "select_calls", "select_samples", "select_ns",
                "probe_calls", "probe_samples", "probe_ns",
                "post_calls", "post_samples", "post_ns",
                "analysis_calls", "analysis_samples", "analysis_ns",
                "gate_eligible", "gate_independent", "gate_counterexamples")


def decode_output(value):
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value or ""


def last_profile(stderr):
    observations = []
    for line in stderr.splitlines():
        if not line.startswith("WU016_PROFILE "):
            continue
        pairs = dict(re.findall(r"([a-z_]+)=([^\s]+)", line))
        if not all(key in pairs for key in (*PROFILE_KEYS, "stage")):
            raise ValueError("incomplete instrumentation record")
        observations.append({"profile_stage": pairs["stage"],
                             **{key: int(pairs[key]) for key in PROFILE_KEYS}})
    return observations[-1] if observations else None


def run_one(executable, instance, timeout):
    start = time.perf_counter()
    try:
        process = subprocess.run([str(executable), str(instance)], timeout=timeout,
                                 text=True, capture_output=True, check=False)
        elapsed = time.perf_counter() - start
        if process.returncode != 0:
            raise ValueError(f"solver failed: exit {process.returncode}")
        return "FINISHED", elapsed, process.stdout, process.stderr
    except subprocess.TimeoutExpired as exc:
        elapsed = time.perf_counter() - start
        return "TIMEOUT", elapsed, decode_output(exc.stdout), decode_output(exc.stderr)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--instances", type=Path, required=True)
    ap.add_argument("--baseline", type=Path, required=True)
    ap.add_argument("--profiled", type=Path, required=True)
    ap.add_argument("--results", type=Path, required=True)
    ap.add_argument("--max-cases", type=int, default=8)
    ap.add_argument("--timeout", type=float, default=2.0)
    args = ap.parse_args()
    if args.max_cases < 1 or not 0.1 <= args.timeout <= 60:
        ap.error("max-cases must be positive and timeout must be 0.1..60s")
    with (args.instances / "manifest.tsv").open(encoding="utf-8", newline="") as f:
        cases = list(csv.DictReader(f, delimiter="\t"))[:args.max_cases]
    if not cases:
        ap.error("no cases")
    fields = ("family", "n", "seed", "build", "deadline_seconds", "status",
              "wall_seconds", "verification", "reported_attempts", "reported_conflicts",
              "reported_watch_updates", "profile_stage", *PROFILE_KEYS)
    args.results.parent.mkdir(parents=True, exist_ok=True)
    with args.results.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for index, entry in enumerate(cases):
            instance = args.instances / entry["file"]
            if instance.resolve().parent != args.instances.resolve():
                raise ValueError("manifest path escapes selected corpus")
            n, clauses = parse_xnf(instance)
            previous = {}
            # Alternate order to limit fixed-order thermal/caching bias.
            pair = (("baseline", args.baseline), ("profiled", args.profiled))
            if index % 2:
                pair = tuple(reversed(pair))
            for build, executable in pair:
                status, elapsed, stdout, stderr = run_one(executable, instance, args.timeout)
                row = {"family": entry["family"], "n": n, "seed": entry["seed"],
                       "build": build, "deadline_seconds": f"{args.timeout:.3f}",
                       "wall_seconds": f"{elapsed:.6f}", "status": status,
                       "verification": "none", "reported_attempts": "",
                       "reported_conflicts": "", "reported_watch_updates": "",
                       "profile_stage": "", **{key: "" for key in PROFILE_KEYS}}
                if status == "FINISHED":
                    solved_status, model = read_solution(stdout, n)
                    row["status"] = solved_status
                    if solved_status == "SAT":
                        if not check_model(n, clauses, model):
                            raise ValueError("incorrect SAT model")
                        row["verification"] = "SAT_MODEL_OK"
                    else:
                        row["verification"] = "UNSAT_NOT_PROOF_CHECKED"
                    counters = collect_counters(stdout)
                    row["reported_attempts"] = counters["attempted_propagations"]
                    row["reported_conflicts"] = counters["conflicts"]
                    row["reported_watch_updates"] = counters["watch_updates"]
                    previous[build] = counters
                if build == "profiled":
                    observation = last_profile(stderr)
                    if not observation:
                        raise ValueError("instrumented run has no profile (even at deadline)")
                    row.update(observation)
                    if status == "FINISHED" and (
                        row["reported_attempts"] != observation["attempts"] or
                        row["reported_conflicts"] != observation["conflicts"]):
                        raise ValueError("inconsistent instrumented internal counters")
                writer.writerow(row)
                f.flush()
                print(f"WU-016 {index+1}/{len(cases)} {entry['seed']} "
                      f"{build}: {row['status']} {elapsed:.3f}s, "
                      f"last_profile_at={row['attempts']}", flush=True)
            if all(key in previous for key in ("baseline", "profiled")):
                for key in ("attempted_propagations", "conflicts", "propagations",
                            "watch_updates", "decisions"):
                    if previous["baseline"][key] != previous["profiled"][key]:
                        raise ValueError(f"instrumentation altered complete-run {key}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError) as exc:
        print(f"WU-016 profiler error: {exc}", file=sys.stderr)
        sys.exit(2)
