"""W027 deterministic, planted-SAT near-XOR negative controls.

Three signed literals form a vertex of a 3-cube. The only permitted
complete four-vertex sets for a source-derived XOR are the two parity
tetrahedra. These controls have repeated supports but neither tetrahedron.
No model-fitting or post hoc case filtering is used.
"""

import hashlib


N_VARS = 128
SPECS = (
    ("decoy_partial_64", "partial", 64, 0, 0x02700011),
    ("decoy_partial_256_noise4096", "partial", 256, 4096, 0x02700012),
    ("decoy_mixed_64", "mixed", 64, 0, 0x02700021),
    ("decoy_mixed_256_noise4096", "mixed", 256, 4096, 0x02700022),
)


def step(s):
    s ^= (s << 13) & 0xFFFFFFFF
    s ^= s >> 17
    s ^= (s << 5) & 0xFFFFFFFF
    return s & 0xFFFFFFFF


def clauses_for_spec(spec):
    _, kind, supports, filler, seed = spec
    state = seed
    used = set()
    clauses = []

    def fresh_triple():
        nonlocal state
        while True:
            vals = []
            for _ in range(3):
                state = step(state)
                vals.append(1 + state % N_VARS)
            triple = tuple(sorted(vals))
            if len(set(triple)) == 3 and triple not in used:
                used.add(triple)
                return triple

    def clause(triple, corner):
        row = [(-v if corner & (1 << j) else v)
               for j, v in enumerate(triple)]
        assert any(v < 0 for v in row), "all-false planted model"
        return row

    for j in range(supports):
        triple = fresh_triple()
        state = step(state)
        if kind == "partial":
            parity = state & 1
            candidates = [v for v in range(1, 8)
                          if v.bit_count() % 2 == parity]
            # Three corners, never a complete tetrahedron.
            if len(candidates) == 4:
                candidates.pop(state % 4)
            corners = candidates
        elif kind == "mixed":
            even, odd = (3, 5, 6), (1, 2, 4, 7)
            corners = [even[state % 3], even[(state + 1) % 3],
                       odd[state % 4], odd[(state + 2) % 4]]
        else:
            raise ValueError(kind)
        rows = [clause(triple, corner) for corner in corners]
        clauses.extend(rows)
        if j % 11 == 0:
            clauses.append(rows[0][:])  # source-duplicate robustness

    for _ in range(filler):
        triple = fresh_triple()
        state = step(state)
        clauses.append(clause(triple, 1 + state % 7))

    # A fixed deterministic permutation defeats positional sampling bias.
    for i in range(len(clauses) - 1, 0, -1):
        state = step(state)
        j = state % (i + 1)
        clauses[i], clauses[j] = clauses[j], clauses[i]

    assert all(any(lit < 0 for lit in row) for row in clauses)
    return clauses


def dimacs_bytes(clauses):
    body = [f"p cnf {N_VARS} {len(clauses)}"]
    body.extend(" ".join(map(str, row)) + " 0" for row in clauses)
    return ("\n".join(body) + "\n").encode("ascii")


def freeze_manifest():
    entries = []
    for spec in SPECS:
        clauses = clauses_for_spec(spec)
        entries.append({"case_id": spec[0], "kind": spec[1],
                        "support_count": spec[2], "filler": spec[3],
                        "seed": spec[4], "variables": N_VARS,
                        "clauses": len(clauses),
                        "cnf_sha256": hashlib.sha256(dimacs_bytes(clauses)).hexdigest(),
                        "expected": "SAT"})
    return {"study": "W-CROSSDOMAIN-027", "purpose": "frozen_near_xor_adversarial_controls",
            "generator": "scripts/w027_full_decoys.py", "entries": entries}
