"""W022 frozen external VLSAT-2 pilot; orchestration only, algorithms in Rust.

Downloads original publisher CNFs, runs Rust profiler and pinned Kissat.
It does not claim a checked UNSAT proof or solver improvement.
"""
import bz2
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
from urllib.request import Request, urlopen


INSTANCES = [
    ("vlsat2_544_8738", "UNSAT"),
    ("vlsat2_600_11440", "UNSAT"),
    ("vlsat2_684_9417", "UNSAT"),
    ("vlsat2_684_13953", "UNSAT"),
    ("vlsat2_708_10259", "UNSAT"),
    ("vlsat2_736_11022", "UNSAT"),
    ("vlsat2_1000_22250", "SAT"),
    ("vlsat2_3456_192912", "SAT"),
]
SOURCE = "https://cadp.inria.fr/ftp/benchmarks/vlsat/"


def download(name):
    url = SOURCE + name + ".cnf.bz2"
    # Fail closed: no synthetic substitute if an upstream source is missing.
    error = None
    for _ in range(3):
        try:
            with urlopen(Request(url, headers={"User-Agent": "Witnora-research-W022/1.0"}),
                         timeout=45) as stream:
                compressed = stream.read(20_000_001)
            if not compressed or len(compressed) > 20_000_000:
                raise ValueError("compressed source exceeds pilot cap")
            raw = bz2.decompress(compressed)
            if len(raw) > 35_000_000:
                raise ValueError("decompressed source exceeds pilot cap")
            return raw, hashlib.sha256(compressed).hexdigest()
        except Exception as exc:
            error = exc
    raise RuntimeError(f"unavailable frozen VLSAT2 input {name}: {error}")


def independent_dimacs_check(raw, expected_name):
    expected_n, expected_m = (int(x) for x in expected_name.split("_")[1:])
    seen_header = False
    current = 0
    nclauses = 0
    edges = 0
    for line in raw.decode("ascii").splitlines():
        text = line.strip()
        if not text or text.startswith("c"):
            continue
        if text.startswith("p"):
            parts = text.split()
            if seen_header or parts != ["p", "cnf", str(expected_n), str(expected_m)]:
                raise ValueError("DIMACS identity mismatch: " + expected_name)
            seen_header = True
            continue
        if not seen_header:
            raise ValueError("DIMACS clause precedes header")
        for token in text.split():
            lit = int(token)
            if lit == 0:
                nclauses += 1
                current = 0
            else:
                if abs(lit) > expected_n:
                    raise ValueError("DIMACS out-of-universe literal")
                edges += 1
                current += 1
    if not seen_header or nclauses != expected_m or current:
        raise ValueError("DIMACS final clause count mismatch")
    return edges


def kissat_verdict(result):
    if result.returncode == 10 and "s SATISFIABLE" in result.stdout:
        return "SAT"
    if result.returncode == 20 and "s UNSATISFIABLE" in result.stdout:
        return "UNSAT"
    return "ERROR"


def run():
    profile_bin = os.environ["WITNORA_RUST_SPECTRAL_BIN"]
    kissat_bin = os.environ["W022_KISSAT_BIN"]
    report_path = Path(os.environ["W022_REPORT_PATH"])
    kissat_source = os.environ["W022_KISSAT_COMMIT"]
    cases = []
    with tempfile.TemporaryDirectory(prefix="witnora-w022-") as folder:
        for name, expected in INSTANCES:
            raw, compressed_sha = download(name)
            edges = independent_dimacs_check(raw, name)
            filename = Path(folder) / (name + ".cnf")
            filename.write_bytes(raw)
            feature_result = subprocess.run([profile_bin, str(filename)],
                                            capture_output=True, text=True,
                                            timeout=30, check=True)
            features = json.loads(feature_result.stdout)
            if (features["variables"], features["clauses"],
                features["literal_occurrences"]) != (*[int(x) for x in name.split("_")[1:]], edges):
                raise AssertionError("independent Rust DIMACS size mismatch")
            start = time.perf_counter_ns()
            try:
                result = subprocess.run([kissat_bin, str(filename)],
                                        capture_output=True, text=True, timeout=15)
                elapsed = time.perf_counter_ns() - start
                status = kissat_verdict(result)
            except subprocess.TimeoutExpired:
                elapsed = time.perf_counter_ns() - start
                status = "TIMEOUT"
            if status == "ERROR" or status in {"SAT", "UNSAT"} and status != expected:
                raise AssertionError(f"Kissat result inconsistent for {name}: {status}; expected {expected}")
            cases.append({
                "id": name, "publisher_label": expected,
                "compressed_sha256": compressed_sha,
                "cnf_sha256": hashlib.sha256(raw).hexdigest(),
                "kissat_status": status, "kissat_wall_ns": elapsed,
                "rust_features": features,
            })
            print(f"{name}: label={expected} kissat={status}, "
                  f"wall={elapsed/1e9:.3f}s, spectral={features['spectral_rayleigh']:.6f}",
                  flush=True)

    output = {
        "research_id": "W-CROSSDOMAIN-022", "cases": cases,
        "source": "INRIA VLSAT-2", "kissat_tag": "rel-4.0.4",
        "kissat_resolved_commit": kissat_source,
        "kissat_timeout_seconds": 15,
        "conclusion": "diagnostic profiling only; no solver speedup or checked UNSAT proof claimed",
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(output, indent=2, sort_keys=True), encoding="utf-8")
    print(f"W022 wrote {len(cases)} frozen-source results: {report_path}")


if __name__ == "__main__":
    run()
