#!/usr/bin/env python3
"""HV-012: mechanically combine all terminal BTOR2 bads into one OR-bad.

This is a standard, semantics-preserving finite-horizon BMC encoding change.
All time-unrolled signal definitions and transition/reset constraints remain
unchanged. The original benchmark is not modified.
"""

import argparse
import hashlib
from pathlib import Path


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="Unrolled combinational BTOR2 file")
    parser.add_argument("output", type=Path)
    parser.add_argument("--expected-bads", type=int, required=True)
    args = parser.parse_args()

    original = args.input.read_bytes()
    lines = original.decode().splitlines()
    ids = []
    bad_predicates = []
    retained = []
    seen_bad = False

    for line in lines:
        fields = line.split()
        if len(fields) < 3 or not fields[0].isdigit():
            raise SystemExit(f"Unexpected line format: {line[:90]}")
        original_id = int(fields[0])
        ids.append(original_id)
        if fields[1] == "bad":
            if len(fields) != 3:
                raise SystemExit("Expected one Boolean expression per bad")
            seen_bad = True
            bad_predicates.append(int(fields[2]))
        else:
            if seen_bad:
                raise SystemExit("Expected all bad declarations to be at end")
            retained.append(line)

    if ids != sorted(ids) or len(ids) != len(set(ids)):
        raise SystemExit("BTOR2 node IDs must be unique and increasing")
    if len(bad_predicates) != args.expected_bads:
        raise SystemExit(f"Bad-count mismatch: {len(bad_predicates)} != {args.expected_bads}")
    if not bad_predicates:
        raise SystemExit("No original bad declarations")

    # Original BTOR2 input's Boolean sort is first, with generated ID 1.
    if retained[0] != "1 sort bitvec 1":
        raise SystemExit(f"Unexpected Boolean sort: {retained[0]}")

    max_id = int(retained[-1].split()[0])
    combined = bad_predicates[0]
    for current in bad_predicates[1:]:
        max_id += 1
        retained.append(f"{max_id} or 1 {combined} {current}")
        combined = max_id
    max_id += 1
    retained.append(f"{max_id} bad {combined}")

    output = ("\n".join(retained) + "\n").encode()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output)
    print(f"original_sha256={sha256(original)}")
    print(f"combined_sha256={sha256(output)}")
    print(f"original_bad_count={len(bad_predicates)}")
    print(f"combined_bad_count=1")
    print(f"output_bytes={len(output)}")
    print(f"output={args.output}")


if __name__ == "__main__":
    main()
