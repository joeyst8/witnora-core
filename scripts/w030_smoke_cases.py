"""Frozen W030 exploratory cases, stressing clause-order sensitivity.

Source-exact DIMACS is constructed from the pre-existing verified W026 core,
W026 noise generator, and W027 source-audited planted-SAT decoys.
"""

from __future__ import annotations

import hashlib

from scripts.w027_full_decoys import SPECS, clauses_for_spec, dimacs_bytes
from tests.test_mixed_xor_recovery_rust import SAT, UNSAT, core, fingerprint, make_noise


def source_bytes(variables, clauses):
    return (f"p cnf {variables} {len(clauses)}\n" + "".join(
        " ".join(map(str, clause)) + " 0\n" for clause in clauses
    )).encode("ascii")


def cases():
    prepared = []
    for noise_size in (0, 8192):
        seed, noise = make_noise(noise_size, 0)
        for parity, expected in ((SAT, "SAT"), (UNSAT, "UNSAT")):
            for arrangement in (("corefirst", "corelast") if noise_size else ("corefirst",)):
                clauses = (core(parity) + noise) if arrangement == "corefirst" else (noise + core(parity))
                case_id = f"w030_d{noise_size}_r0_{expected.lower()}_{arrangement}"
                prepared.append({"case_id": case_id, "expected": expected,
                                 "stratum": f"w026_{arrangement}",
                                 "clauses": clauses, "variables": 64,
                                 "noise_seed": seed, "noise_fingerprint_fnv64": fingerprint(noise)})

    for spec in SPECS:
        if spec[0] in ("decoy_partial_256_noise4096", "decoy_mixed_256_noise4096"):
            prepared.append({"case_id": spec[0], "expected": "SAT", "stratum": "near_xor_decoy",
                             "clauses": clauses_for_spec(spec), "variables": 128})
    return prepared


def manifest():
    entries = []
    for case in cases():
        encoded = source_bytes(case["variables"], case["clauses"])
        entry = {"case_id": case["case_id"], "expected": case["expected"],
                 "stratum": case["stratum"], "variables": case["variables"],
                 "clauses": len(case["clauses"]), "cnf_sha256": hashlib.sha256(encoded).hexdigest()}
        if "noise_seed" in case:
            entry.update(noise_seed=case["noise_seed"],
                         noise_fingerprint_fnv64=case["noise_fingerprint_fnv64"])
        entries.append(entry)
    return {"study": "W-CROSSDOMAIN-030", "phase": "preregistered_exploratory_smoke",
            "generator": "scripts/w030_smoke_cases.py", "entries": entries}
