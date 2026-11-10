"""WU-015: controlled source-option ablation of the pinned Xorcle executable.

This is diagnostic profiling, not a new solver. Original 2-XNF inputs and
their independent model checker are inherited from WU-014. Timeouts are
censored. Xorcle's existing public counters record completed runs only.
"""

import argparse
import csv
from pathlib import Path
import re
import sys

if __package__:
    from .wu014_real_solver_pilot import check_model, parse_xnf, read_solution, run_solver
else:
    from wu014_real_solver_pilot import check_model, parse_xnf, read_solution, run_solver


VARIANTS = {
    "default": (),
    "watchlist": ("--selection=leading_term_watchlist",),
    "sparse": ("--equation-repr=sparse",),
    "sparse_watchlist": ("--equation-repr=sparse", "--selection=leading_term_watchlist"),
    "no_compaction": ("--compact=false",),
}

COUNTERS = {
    "conflicts": "Conflicts",
    "propagations": "Propagations",
    "attempted_propagations": "Attempted propagations",
    "watch_updates": "Watch updates",
    "learned_clauses": "Learned clauses",
    "decisions": "Decisions",
}


def collect_counters(stdout):
    observed = dict(re.findall(r"^c ([^:]+): ([^\n]+)$", stdout, flags=re.MULTILINE))
    if not all(v in observed for v in COUNTERS.values()):
        raise ValueError("completed run lacked solver counters")
    return {key: int(observed[label]) for key, label in COUNTERS.items()}


def run_one(xorcle, instance, name, options, deadline):
    n, clauses = parse_xnf(instance)
    outcome, elapsed, stdout, stderr = run_solver([str(xorcle), *options, str(instance)], deadline)
    result = {"status": outcome, "elapsed_seconds": f"{elapsed:.6f}",
              "verification": "none", "stderr": stderr.replace("\n", " ")}
    result.update({key: "" for key in COUNTERS})
    if outcome == "FINISHED":
        try:
            status, model = read_solution(stdout, n)
            result["status"] = status
            result.update(collect_counters(stdout))
            if status == "SAT":
                result["verification"] = "SAT_MODEL_OK" if check_model(n, clauses, model) else "INVALID_SAT_MODEL"
                if result["verification"] != "SAT_MODEL_OK":
                    result["status"] = "ERROR"
            else:
                result["verification"] = "UNSAT_NOT_PROOF_CHECKED"
        except (ValueError, KeyError, IndexError) as exc:
            result["status"] = "ERROR"
            result["verification"] = str(exc)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instances", type=Path, required=True)
    parser.add_argument("--xorcle", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--max-cases", type=int, default=8)
    parser.add_argument("--timeout", type=float, default=3.5)
    parser.add_argument("--variants", default=",".join(VARIANTS))
    args = parser.parse_args()
    if args.timeout < 0.1 or args.timeout > 60 or args.max_cases < 1:
        parser.error("timeout must be 0.1..60s and max-cases must be positive")
    names = args.variants.split(",")
    if not names or len(set(names)) != len(names) or not all(v in VARIANTS for v in names):
        parser.error("variants must be a unique comma-separated subset of " + ",".join(VARIANTS))

    with (args.instances / "manifest.tsv").open(encoding="utf-8", newline="") as f:
        corpus = list(csv.DictReader(f, delimiter="\t"))[:args.max_cases]
    if not corpus:
        parser.error("no inputs selected")
    args.results.parent.mkdir(parents=True, exist_ok=True)
    fields = ["family", "n", "seed", "variant", "deadline_seconds", "status",
              "elapsed_seconds", "verification", *COUNTERS, "stderr"]
    with args.results.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for index, entry in enumerate(corpus):
            instance = args.instances / entry["file"]
            if instance.resolve().parent != args.instances.resolve():
                raise ValueError("manifest path escapes corpus directory")
            # Rotate variant order to reduce a fixed warm-up / thermal bias.
            rotated = names[index % len(names):] + names[:index % len(names)]
            for name in rotated:
                result = run_one(args.xorcle, instance, name, VARIANTS[name], args.timeout)
                writer.writerow({"family": entry["family"], "n": entry["variables"],
                                 "seed": entry["seed"], "variant": name,
                                 "deadline_seconds": f"{args.timeout:.3f}", **result})
                file.flush()
                print(f"WU-015 {index+1}/{len(corpus)} {entry['seed']} "
                      f"{name}: {result['status']} {result['elapsed_seconds']}s", flush=True)
                if result["status"] == "ERROR":
                    raise RuntimeError("unvalidated solver result, aborting")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"WU-015 ablation error: {exc}", file=sys.stderr)
        sys.exit(2)
