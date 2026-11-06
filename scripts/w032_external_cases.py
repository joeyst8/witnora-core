"""W032 immutable official VLSAT2 inputs and frozen parity/decoy controls."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.benchmark_w022_vlsat import INSTANCES
from scripts.w027_full_decoys import N_VARS, SPECS, clauses_for_spec, dimacs_bytes
from scripts.w030_smoke_cases import source_bytes
from tests.test_mixed_xor_recovery_rust import SAT, UNSAT, core, make_noise


def cases_metadata():
    earlier = json.loads(Path("research/results/w022_external_vlsat2.json").read_text())
    known = {row["id"]: row for row in earlier["cases"]}
    entries = []
    for name, expected in INSTANCES:
        source = known[name]
        if source["publisher_label"] != expected:
            raise ValueError("publisher label changed")
        _, variables, clauses = name.split("_")
        entries.append({"case_id": name, "expected": expected,
                        "stratum": "official_external_vlsat2", "variables": int(variables),
                        "clauses": int(clauses), "cnf_sha256": source["cnf_sha256"],
                        "compressed_sha256": source["compressed_sha256"]})

    for spec in SPECS:
        clauses = clauses_for_spec(spec)
        encoded = dimacs_bytes(clauses)
        entries.append({"case_id": spec[0], "expected": "SAT",
                        "stratum": "frozen_adversarial_sat_decoy", "variables": N_VARS,
                        "clauses": len(clauses),
                        "cnf_sha256": hashlib.sha256(encoded).hexdigest()})

    _, noise = make_noise(8192, 0)
    for parity, expected in ((SAT, "SAT"), (UNSAT, "UNSAT")):
        clauses = core(parity) + noise
        entries.append({"case_id": f"w032_w026_r0_{expected.lower()}_sanity",
                        "expected": expected, "stratum": "synthetic_sanity_only",
                        "variables": 64, "clauses": len(clauses),
                        "cnf_sha256": hashlib.sha256(source_bytes(64, clauses)).hexdigest()})
    return entries


def manifest():
    return {"study": "W-CROSSDOMAIN-032", "phase": "frozen_external_domain_pilot",
            "source": "INRIA VLSAT2 publisher plus W027/W026 controls",
            "protocol": "docs/W_CROSSDOMAIN_032_EXTERNAL_DOMAIN_PROTOCOL.md",
            "entries": cases_metadata()}
