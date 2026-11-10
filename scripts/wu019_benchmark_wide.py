"""WU-019 paired untouched Xorcle versus experimental wide-dual-mask gate.

General XNF source validation (including unary linear clauses) is independent
of the earlier fixed 3n, n<=40 WU-014 pilot. Censored runs are never solved.
"""

import argparse
import csv
from pathlib import Path
import re
import subprocess
import sys
import time

from scripts.wu014_real_solver_pilot import read_solution
from scripts.wu015_xorcle_ablation import collect_counters

METRICS = ("attempts", "eligible", "skipped", "rebuilds", "row_visits",
           "wide_eligible", "wide_skipped", "wide_rebuilds", "wide_row_words")
COUNTERS = ("conflicts", "propagations", "attempted_propagations",
            "watch_updates", "learned_clauses", "decisions")


def parse_xnf(path):
    n = expected = None
    clauses = []
    for raw in path.read_text(encoding="ascii").splitlines():
        line = raw.strip()
        if not line or line.startswith("c "):
            continue
        if line.startswith("p "):
            _, kind, n, expected = line.split()
            if kind != "xnf":
                raise ValueError("non-XNF input")
            n, expected = int(n), int(expected)
            continue
        tokens = line.split()
        if n is None or tokens[-1:] != ["0"] or len(tokens) not in (2, 3):
            raise ValueError("bad XNF clause")
        clause = []
        for token in tokens[:-1]:
            rhs = not token.startswith("-")
            idxs = tuple(int(v) for v in token.lstrip("-").split("+"))
            if not idxs or len(set(idxs)) != len(idxs) or not all(1 <= v <= n for v in idxs):
                raise ValueError("bad XNF lineral")
            clause.append((idxs, rhs))
        clauses.append(clause)
    if n is None or expected != len(clauses):
        raise ValueError("XNF header/length mismatch")
    return n, clauses


def validates_model(n, clauses, bits):
    if len(bits) != n:
        return False
    return all(any((sum(bits[i - 1] for i in idxs) % 2 == int(rhs))
                   for idxs, rhs in clause) for clause in clauses)


def profile(stderr):
    last = None
    for line in stderr.splitlines():
        if not line.startswith("WU018_DUAL "):
            continue
        parsed = dict(re.findall(r"([a-z0-9_]+)=([^\s]+)", line))
        if "stage" not in parsed or not all(key in parsed for key in METRICS):
            raise ValueError("corrupted WU-019 gate profile")
        last = {"profile_stage": parsed["stage"],
                **{key: int(parsed[key]) for key in METRICS}}
    return last


def run(executable, options, instance, limit):
    start = time.perf_counter()
    p = subprocess.Popen([str(executable), *options, str(instance)],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    peak_rss = 0
    status = "FINISHED"
    try:
        import psutil  # Optional; sampling is a lower bound on actual peak RSS.
        process = psutil.Process(p.pid)
    except ImportError:
        process = None
    while True:
        try:
            stdout, stderr = p.communicate(timeout=0.025)
            break
        except subprocess.TimeoutExpired:
            if process is not None:
                try:
                    peak_rss = max(peak_rss, process.memory_info().rss)
                except (OSError, psutil.NoSuchProcess):
                    pass
            if time.perf_counter() - start >= limit:
                p.kill()
                stdout, stderr = p.communicate()
                status = "TIMEOUT"
                break
    elapsed = time.perf_counter() - start
    if status != "TIMEOUT" and p.returncode not in (0, 10, 20):
        raise ValueError(f"solver exited {p.returncode}: {stderr[:300]}")
    return status, elapsed, stdout, stderr, peak_rss


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--instances", type=Path, required=True)
    ap.add_argument("--baseline", type=Path, required=True)
    ap.add_argument("--wide", type=Path, required=True)
    ap.add_argument("--results", type=Path, required=True)
    ap.add_argument("--timeout", type=float, default=6)
    ap.add_argument("--family", default="embedded_unplanted,embedded_planted,dense_planted,sparse_planted")
    ap.add_argument("--widths", default="80,129,192", help="Comma-separated widths to benchmark")
    ap.add_argument("--selection", choices=("cyclic", "leading_term_watchlist"), default="cyclic")
    ap.add_argument("--repetitions", type=int, default=1)
    ap.add_argument("--compact", action="store_true", help="Enable default compaction; otherwise pin full wide dimension")
    args = ap.parse_args()
    if args.timeout < 0.1 or args.timeout > 60 or args.repetitions < 1:
        ap.error("invalid limits")
    widths = {int(v) for v in args.widths.split(",")}
    with (args.instances / "manifest.tsv").open(newline="") as f:
        cases = [r for r in csv.DictReader(f, delimiter="\t")
                 if r["family"] in args.family.split(",") and int(r["variables"]) in widths]
    if not cases:
        ap.error("no matching cases")
    options = [] if args.compact else ["--compact=false"]
    if args.selection == "leading_term_watchlist":
        options.append("--selection=leading_term_watchlist")
    fields = ("seed", "family", "n", "selection", "compact", "rep", "build", "status",
              "seconds", "sampled_rss_kb", "verification", *COUNTERS,
              "profile_stage", *METRICS)
    args.results.parent.mkdir(parents=True, exist_ok=True)
    with args.results.open("w", newline="") as f:
        out = csv.DictWriter(f, fieldnames=fields)
        out.writeheader()
        for rep in range(args.repetitions):
            for i, case in enumerate(cases):
                instance = args.instances / case["file"]
                if instance.resolve().parent != args.instances.resolve():
                    raise ValueError("manifest path escape")
                n, clauses = parse_xnf(instance)
                if n != int(case["variables"]):
                    raise ValueError("manifest width mismatch")
                if case["planted_witness_bits"]:
                    witness = int(case["planted_witness_bits"], 16)
                    if not validates_model(n, clauses, [(witness >> j) & 1 for j in range(n)]):
                        raise ValueError("invalid planted witness in manifest")
                pair = (("baseline", args.baseline), ("wide", args.wide))
                if (rep + i) % 2:
                    pair = tuple(reversed(pair))
                complete = {}
                for build, executable in pair:
                    status, seconds, stdout, stderr, rss = run(executable, options, instance,
                                                               args.timeout)
                    row = {"seed": case["seed"], "family": case["family"], "n": n,
                           "selection": args.selection, "compact": bool(args.compact),
                           "rep": rep, "build": build, "status": status,
                           "seconds": f"{seconds:.6f}", "sampled_rss_kb": rss // 1024,
                           "verification": "none", "profile_stage": "",
                           **{key: "" for key in (*COUNTERS, *METRICS)}}
                    if status == "FINISHED":
                        sat_status, assignment = read_solution(stdout, n)
                        row["status"] = sat_status
                        if sat_status == "SAT":
                            bits = [int(assignment.get(v, False)) for v in range(1, n+1)]
                            if len(assignment) != n or not validates_model(n, clauses, bits):
                                raise ValueError("invalid returned SAT assignment")
                            row["verification"] = "SAT_MODEL_OK"
                        else:
                            row["verification"] = "UNSAT_NEEDS_PROOF"
                        counters = collect_counters(stdout)
                        row.update(counters)
                        complete[build] = (sat_status, counters)
                    if build == "wide":
                        observed = profile(stderr)
                        if observed is None:
                            raise ValueError("no wide observation")
                        row.update(observed)
                        if status == "FINISHED" and observed["attempts"] != row["attempted_propagations"]:
                            raise ValueError("inconsistent wide counters")
                    out.writerow(row)
                    f.flush()
                    print(f"WU019 {args.selection} {case['family']} n={n} rep={rep} "
                          f"{build} {row['status']} {seconds:.3f}s "
                          f"wide_skips={row['wide_skipped']}", flush=True)
                if len(complete) == 2:
                    a, b = complete["baseline"], complete["wide"]
                    if a[0] != b[0] or any(a[1][key] != b[1][key] for key in COUNTERS):
                        raise ValueError(f"search divergence at {case['seed']}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError) as exc:
        print(f"WU019 failed: {exc}", file=sys.stderr)
        sys.exit(2)
