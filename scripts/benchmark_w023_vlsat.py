"""W023 external holdout: signed gauge-deflated geometry and pinned Kissat."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time

from scripts.benchmark_w022_vlsat import download, independent_dimacs_check, kissat_verdict


FROZEN = [
    ("vlsat2_798_17543", "UNSAT"),
    ("vlsat2_1022_14955", "UNSAT"),
    ("vlsat2_1134_26703", "UNSAT"),
    ("vlsat2_1155_42917", "UNSAT"),
    ("vlsat2_7452_334035", "SAT"),
    ("vlsat2_11130_1186888", "SAT"),
]


def run():
    rust = os.environ["WITNORA_RUST_DEFLATED_BIN"]
    kissat = os.environ["W023_KISSAT_BIN"]
    report = Path(os.environ["W023_REPORT_PATH"])
    cases=[]
    with tempfile.TemporaryDirectory(prefix="witnora-w023-") as folder:
        for name, label in FROZEN:
            raw, compressed_hash=download(name)
            edges=independent_dimacs_check(raw,name)
            filename=Path(folder)/(name+".cnf")
            filename.write_bytes(raw)
            features=json.loads(subprocess.run([rust,str(filename)],text=True,
                        capture_output=True,timeout=60,check=True).stdout)
            n,m=map(int,name.split("_")[1:])
            if (features["variables"],features["clauses"],
                features["literal_occurrences"])!=(n,m,edges):
                raise AssertionError("W023 source identity disagreement")
            start=time.perf_counter_ns()
            try:
                done=subprocess.run([kissat,str(filename)],text=True,
                                    capture_output=True,timeout=15)
                elapsed=time.perf_counter_ns()-start
                status=kissat_verdict(done)
            except subprocess.TimeoutExpired:
                elapsed=time.perf_counter_ns()-start
                status="TIMEOUT"
            if status=="ERROR" or (status in {"SAT","UNSAT"} and status!=label):
                raise AssertionError(f"Kissat contradiction/exit failure {name}: {status}")
            cases.append({"id":name,"publisher_label":label,
                          "compressed_sha256":compressed_hash,
                          "cnf_sha256":hashlib.sha256(raw).hexdigest(),
                          "kissat_status":status,"kissat_wall_ns":elapsed,
                          "rust_features":features})
            print(f"{name}: kissat={status}, gauge={features['gauge_frustration']}, "
                  f"deflated={features['deflated_rayleigh']}, "
                  f"polarity={features['polarity_conflict_fraction']:.6f}",flush=True)
    result={"research_id":"W-CROSSDOMAIN-023", "cases":cases,
            "source":"INRIA VLSAT-2: frozen distinct W023 holdout",
            "kissat_tag":"rel-4.0.4",
            "kissat_resolved_commit":os.environ["W023_KISSAT_COMMIT"],
            "kissat_timeout_seconds":15,
            "claim":"descriptive spectral features; no validated solver speedup or UNSAT proof"}
    report.parent.mkdir(parents=True,exist_ok=True)
    report.write_text(json.dumps(result,indent=2,sort_keys=True),encoding="utf-8")
    print(f"W023 archived {len(cases)} held-out results: {report}")


if __name__=="__main__":
    run()
