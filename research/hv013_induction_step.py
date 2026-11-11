#!/usr/bin/env python3
"""HV-013 standard k-induction *step* query from an exact BTOR2 unrolling.

The original unroller emits 7 init equalities, then 26*k transition
equalities, then k+1 original bad properties. This transformation deletes
only the 7 init *constraints*, assumes previous safety, and asks whether
the last-frame bad is reachable from an otherwise arbitrary start state.
"""

import argparse
import hashlib
from pathlib import Path


NUM_INITS = 7
NUM_NEXT = 26


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("original", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--k", type=int, required=True)
    args = parser.parse_args()
    if not 1 <= args.k <= 64:
        raise SystemExit("k outside permitted predeclared range")

    original = args.original.read_bytes()
    parsed = [line.split() for line in original.decode().splitlines()]
    if not parsed or parsed[0] != ["1", "sort", "bitvec", "1"]:
        raise SystemExit("Missing expected Boolean sort")
    ids = [int(t[0]) for t in parsed]
    if ids != sorted(ids) or len(ids) != len(set(ids)):
        raise SystemExit("BTOR2 IDs not sorted and unique")

    max_id = max(ids)
    retained = []
    previous_bad_predicates = []
    all_bad_predicates = []
    constraint_index = 0
    seen_bad = False
    for t in parsed:
        node_op = t[1]
        if node_op == "bad":
            seen_bad = True
            if len(t) != 3:
                raise SystemExit("Malformed bad")
            all_bad_predicates.append(int(t[2]))
            continue
        if seen_bad:
            raise SystemExit("Bads must be last in the original unroller")
        if node_op == "constraint":
            if constraint_index >= NUM_INITS:
                retained.append(" ".join(t))
            constraint_index += 1
        else:
            retained.append(" ".join(t))

    if constraint_index != NUM_INITS + NUM_NEXT * args.k:
        raise SystemExit(f"Unexpected constraint count {constraint_index}")
    if len(all_bad_predicates) != args.k + 1:
        raise SystemExit(f"Expected {args.k + 1} original bad predicates")
    previous_bad_predicates = all_bad_predicates[:-1]

    for bad_id in previous_bad_predicates:
        max_id += 1
        negative = max_id
        retained.append(f"{negative} not 1 {bad_id}")
        max_id += 1
        retained.append(f"{max_id} constraint {negative}")
    max_id += 1
    retained.append(f"{max_id} bad {all_bad_predicates[-1]}")

    output = ("\n".join(retained) + "\n").encode()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output)
    print(f"k={args.k}")
    print(f"original_sha256={digest(original)}")
    print(f"step_sha256={digest(output)}")
    print(f"dropped_init_constraints={NUM_INITS}")
    print(f"preserved_transition_constraints={NUM_NEXT * args.k}")
    print(f"assumed_safe_frames={len(previous_bad_predicates)}")
    print(f"step_bad_frame={args.k}")
    print(f"output_bytes={len(output)}")


if __name__ == "__main__":
    main()
