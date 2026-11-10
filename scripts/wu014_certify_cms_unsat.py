"""Independently certify CryptoMiniSat UNSAT pilot cases with Cake XLRUP.

Only the rows already labeled UNSAT in a real execution pilot are retried.
Proof-generation and independent checker runtimes are separately recorded;
neither is falsely included in earlier no-proof solve times.
"""

import argparse
import csv
import hashlib
from pathlib import Path
import subprocess
import sys
import time


def timed(command, timeout):
    start = time.perf_counter()
    try:
        outcome = subprocess.run(command, capture_output=True, text=True,
                                 timeout=timeout, check=False)
    except subprocess.TimeoutExpired:
        return "TIMEOUT", time.perf_counter()-start, ""
    return str(outcome.returncode), time.perf_counter()-start, outcome.stdout


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pilot", required=True)
    ap.add_argument("--instances", required=True)
    ap.add_argument("--cms", required=True)
    ap.add_argument("--checker", required=True)
    ap.add_argument("--normalizer", required=True)
    ap.add_argument("--timeout", type=float, default=30)
    ap.add_argument("--proof-mode", choices=("1","2"), default="1",
                    help="CMS XLRUP output: 1=text, 2=binary")
    ap.add_argument("--max-cases", type=int, default=0)
    ap.add_argument("--results", required=True)
    args = ap.parse_args()
    root = Path(args.instances)
    with Path(args.pilot).open(newline="") as stream:
        to_check = [r for r in csv.DictReader(stream)
                    if r["solver"] == "cms" and r["status"] == "UNSAT"]
    if not to_check:
        raise ValueError("no published pilot UNSAT statuses to validate")
    if args.max_cases < 0:
        raise ValueError("max-cases cannot be negative")
    if args.max_cases:
        to_check = to_check[:args.max_cases]
    outcomes = []
    for row in to_check:
        if row["family"] != "unplanted":
            raise ValueError("UNSAT on a planted-witness instance contradicts generator validity")
        name = f"unplanted_n{row['n']}_seed{row['seed']}"
        original = root / f"{name}.xcnf"
        if not original.is_file():
            raise ValueError(f"source converted XNF not found: {original}")
        proof = root / f"{name}.mode{args.proof_mode}.xlrup"
        checked = root / f"{name}.check.xcnf"
        status, solve_s, answer = timed([args.cms,"--verb","0","--xlrup",args.proof_mode,
                                         str(original),str(proof)], args.timeout)
        if status != "20" or "s UNSATISFIABLE" not in answer:
            verified, check_s = "PROOF_GENERATION_FAILED", 0.
        else:
            subprocess.run([sys.executable,args.normalizer,str(original),str(checked)],
                           capture_output=True,text=True,check=True)
            checker_args = (["--no-binary"] if args.proof_mode == "1" else [])
            check_return, check_s, message = timed([args.checker,*checker_args,
                                                      str(checked),str(proof)],args.timeout)
            verified = "VERIFIED_UNSAT" if check_return == "0" and \
                "s VERIFIED UNSAT" in message else f"CHECK_FAILED:{check_return}"
        digest = hashlib.sha256(proof.read_bytes()).hexdigest() if proof.exists() else ""
        size = proof.stat().st_size if proof.exists() else 0
        outcomes.append({"family":row["family"],"n":row["n"],"seed":row["seed"],
                         "status":verified,"proof_mode":args.proof_mode,
                         "proof_bytes":size,"proof_sha256":digest,
                         "proof_solve_seconds":f"{solve_s:.6f}",
                         "proof_check_seconds":f"{check_s:.6f}"})
        print(f"WU-014 independent certificate {name} {verified} ",flush=True)
    with Path(args.results).open("w",newline="") as stream:
        writer = csv.DictWriter(stream,fieldnames=list(outcomes[0]))
        writer.writeheader()
        writer.writerows(outcomes)
    if any(r["status"] != "VERIFIED_UNSAT" for r in outcomes):
        return 3
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"WU-014 certifier rejected input: {exc}",file=sys.stderr)
        sys.exit(2)
