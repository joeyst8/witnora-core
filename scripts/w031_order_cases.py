"""W031 frozen 16-seed clause-order robustness challenge for Rust XOR proof.

Exactly matched SAT/UNSAT source CNFs share the *same* clause permutation;
the only changing constraint is the signed parity of the W026 core.
"""

from __future__ import annotations

import hashlib

from scripts.w027_full_decoys import SPECS, clauses_for_spec
from scripts.w030_smoke_cases import source_bytes
from tests.test_mixed_xor_recovery_rust import SAT, UNSAT, core, fingerprint, make_noise


NOISE = 8192
REPLICATES = 16
ORDERS = ("corefirst", "corelast", "shuffled")
DECOYS = {spec[0] for spec in SPECS}


def xorshift32(state):
    state ^= (state << 13) & 0xffffffff
    state ^= state >> 17
    state ^= (state << 5) & 0xffffffff
    return state & 0xffffffff


def permutation(replicate, order):
    count = NOISE + 20
    if order == "corefirst":
        return list(range(count))
    if order == "corelast":
        return list(range(20, count)) + list(range(20))
    if order != "shuffled":
        raise ValueError(order)
    indices = list(range(count))
    state = (0x03103100 ^ (replicate * 0x9e3779b9)) & 0xffffffff
    if state == 0:
        state = 0xa59301
    for i in range(len(indices) - 1, 0, -1):
        state = xorshift32(state)
        j = state % (i + 1)
        indices[i], indices[j] = indices[j], indices[i]
    return indices


def cases():
    entries = []
    for replicate in range(REPLICATES):
        seed, noise = make_noise(NOISE, replicate)
        noise_hash = fingerprint(noise)
        for order in ORDERS:
            perm = permutation(replicate, order)
            # This geometric support-position feature does not use truth labels.
            core_positions = [i for i, old_idx in enumerate(perm) if old_idx < 20]
            for parity, expected in ((SAT, "SAT"), (UNSAT, "UNSAT")):
                source = core(parity) + noise
                ordered = [source[idx] for idx in perm]
                entries.append({
                    "case_id": f"w031_d{NOISE}_r{replicate}_{expected.lower()}_{order}",
                    "expected": expected, "stratum": "matched_w026_order",
                    "variables": 64, "clauses": ordered, "order": order,
                    "replicate": replicate, "noise_seed": seed,
                    "noise_fingerprint_fnv64": noise_hash,
                    "first_core_position_zero_based": min(core_positions),
                    "last_core_position_zero_based": max(core_positions),
                })
    for spec in SPECS:
        entries.append({"case_id": spec[0], "expected": "SAT",
                        "stratum": "adversarial_sat_decoy", "variables": 128,
                        "clauses": clauses_for_spec(spec), "order": "fixed_decoy"})
    return entries


def manifest():
    rows = []
    for case in cases():
        encoded = source_bytes(case["variables"], case["clauses"])
        row = {"case_id": case["case_id"], "expected": case["expected"],
               "stratum": case["stratum"], "order": case["order"],
               "variables": case["variables"], "clauses": len(case["clauses"]),
               "cnf_sha256": hashlib.sha256(encoded).hexdigest()}
        for feature in ("replicate", "noise_seed", "noise_fingerprint_fnv64",
                        "first_core_position_zero_based", "last_core_position_zero_based"):
            if feature in case:
                row[feature] = case[feature]
        rows.append(row)
    return {"study": "W-CROSSDOMAIN-031", "protocol": "docs/W_CROSSDOMAIN_031_ORDER_ROBUSTNESS_PROTOCOL.md",
            "generator": "scripts/w031_order_cases.py", "entries": rows}
