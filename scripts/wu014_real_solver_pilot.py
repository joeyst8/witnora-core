"""WU-014: timed, *real* Xorcle vs CryptoMiniSat pilot on fresh 2-XNF seeds.

Rust generates original input files; this harness only orchestrates external
unmodified solvers, the Xorcle upstream CNF-XOR converter, and SAT-model
verification. UNSAT is explicitly *unverified* unless checked separately.
"""

import argparse
import csv
from pathlib import Path
import subprocess
import sys
import time


def parse_xnf(path: Path):
    n = m = None
    clauses = []
    for source in path.read_text(encoding="ascii").splitlines():
        line = source.strip()
        if not line or line.startswith("c "):
            continue
        if line.startswith("p "):
            _, kind, n_raw, m_raw = line.split()
            if kind != "xnf" or n is not None:
                raise ValueError("invalid/duplicate XNF header")
            n, m = int(n_raw), int(m_raw)
            continue
        terms = line.split()
        if n is None or len(terms) != 3 or terms[-1] != "0":
            raise ValueError(f"invalid XNF clause: {line}")
        parsed = []
        for term in terms[:2]:
            neg = term.startswith("-")
            bits = tuple(int(v) for v in term.lstrip("-").split("+"))
            if not bits or len(set(bits)) != len(bits) or not all(1 <= v <= n for v in bits):
                raise ValueError("invalid XNF lineral")
            parsed.append((bits, neg))
        clauses.append(tuple(parsed))
    if not 21 <= n <= 40 or m != 3*n or len(clauses) != m:
        raise ValueError(f"inconsistent XNF source header/length: {path}")
    return n, clauses


def check_model(n, clauses, assignment):
    if any(v not in assignment for v in range(1, n+1)):
        return False
    for clause in clauses:
        def eval_lineral(x):
            values, neg = x
            parity = sum(assignment[v] for v in values) % 2
            return parity == (0 if neg else 1)
        if not any(eval_lineral(x) for x in clause):
            return False
    return True


def read_solution(output: str, n: int):
    statuses = [line.split(maxsplit=1)[1] for line in output.splitlines()
                if line.startswith("s ")]
    if len(statuses) != 1 or statuses[0] not in ("SATISFIABLE", "UNSATISFIABLE"):
        raise ValueError("missing/ambiguous SAT solver result")
    if statuses[0] == "UNSATISFIABLE":
        return "UNSAT", {}
    model = {}
    for line in output.splitlines():
        if line.startswith("v "):
            for token in line.split()[1:]:
                value = int(token)
                if value == 0:
                    continue
                v = abs(value)
                if v in model and model[v] != (value > 0):
                    raise ValueError("contradictory SAT model")
                if v <= n:
                    model[v] = value > 0
    return "SAT", model


def run_solver(command, deadline):
    start = time.perf_counter()
    try:
        run = subprocess.run(command, capture_output=True, text=True,
                             timeout=deadline, check=False)
    except subprocess.TimeoutExpired:
        return "TIMEOUT", time.perf_counter() - start, "", ""
    elapsed = time.perf_counter() - start
    if run.returncode not in (0, 10, 20):
        return "ERROR", elapsed, run.stdout, run.stderr[-600:]
    return "FINISHED", elapsed, run.stdout, run.stderr[-600:]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--instances", required=True)
    ap.add_argument("--xorcle", required=True)
    ap.add_argument("--cms", required=True)
    ap.add_argument("--converter", required=True)
    ap.add_argument("--timeout", type=float, default=2.0)
    ap.add_argument("--max-cases", type=int, default=0,
                    help="0 means every manifest case; otherwise take this many in order")
    ap.add_argument("--results", required=True)
    args = ap.parse_args()
    if not 0.1 <= args.timeout <= 60:
        raise ValueError("pilot wall-clock deadline must be 0.1..60 seconds")
    root = Path(args.instances)
    with (root / "manifest.tsv").open(newline="", encoding="utf-8") as file:
        instances = list(csv.DictReader(file, delimiter="\t"))
    if args.max_cases < 0:
        raise ValueError("max-cases cannot be negative")
    if args.max_cases:
        instances = instances[:args.max_cases]
    if not instances or len({r["file"] for r in instances}) != len(instances):
        raise ValueError("manifest empty or duplicated")
    rows = []
    for i, entry in enumerate(instances):
        original = root / entry["file"]
        if original.parent.resolve() != root.resolve():
            raise ValueError("manifest path escapes input directory")
        n, clauses = parse_xnf(original)
        if n != int(entry["variables"]):
            raise ValueError("manifest size mismatch")
        if entry["family"] == "planted":
            planted = int(entry["planted_witness_bits"], 16)
            witness = {v: bool(planted & (1 << (v-1))) for v in range(1, n+1)}
            if not check_model(n, clauses, witness):
                raise ValueError(f"generator failed planted witness validation: {original}")
        # Converter is independently published with Xorcle. For an honest CMS
        # end-to-end score, include its wall time in the reported duration.
        converted = root / (original.stem + ".xcnf")
        t0 = time.perf_counter()
        subprocess.run([sys.executable, args.converter, "cnf-xor", str(original),
                        str(converted)], check=True, capture_output=True, text=True)
        converter_seconds = time.perf_counter() - t0
        for name, command, setup in (
            ("xorcle", [args.xorcle, str(original)], 0.),
            ("cms", [args.cms, "--verb", "0", str(converted)], converter_seconds),
        ):
            status, seconds, stdout, stderr = run_solver(command, args.timeout)
            verified = "none"
            if status == "FINISHED":
                try:
                    status, model = read_solution(stdout, n)
                    if status == "SAT":
                        verified = "SAT_MODEL_OK" if check_model(n, clauses, model) else "INVALID_SAT_MODEL"
                        if verified != "SAT_MODEL_OK":
                            status = "ERROR"
                    else:
                        verified = "UNSAT_NOT_PROOF_CHECKED"
                except (ValueError, IndexError) as error:
                    status, verified = "ERROR", str(error)
            rows.append({"family":entry["family"], "n":n, "seed":entry["seed"],
                         "solver":name, "status":status,
                         "deadline_seconds":f"{args.timeout:.3f}",
                         "solver_seconds":f"{seconds:.6f}",
                         "conversion_seconds":f"{setup:.6f}",
                         "total_seconds":f"{seconds+setup:.6f}",
                         "verification":verified, "stderr":stderr.replace("\n", " ")})
        if (i+1) % 4 == 0 or i+1 == len(instances):
            c = rows[-8:]
            print(f"WU-014 real pilot progress {i+1}/{len(instances)} cases; "
                  f"latest statuses: {[x['solver']+':'+x['status'] for x in c]}", flush=True)
    path = Path(args.results)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"WU-014 wrote {len(rows)} actual solver records to {path}", flush=True)
    for name in ("xorcle", "cms"):
        subset = [r for r in rows if r["solver"] == name]
        counts = {state:sum(r["status"] == state for r in subset)
                  for state in ("SAT","UNSAT","TIMEOUT","ERROR")}
        print(f"WU-014 {name}: {counts} / {len(subset)}", flush=True)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, subprocess.CalledProcessError) as err:
        print(f"WU-014 pilot error: {err}", file=sys.stderr)
        sys.exit(2)
