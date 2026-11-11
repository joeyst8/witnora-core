#!/usr/bin/env python3
"""Reproducible, SHA-pinned HV-010 development-only witness generator.

This does not edit the original benchmark; it appends one predeclared invariant
as a second bad property to a witness copy. Cerbtora checks the result.
"""

import argparse
import hashlib
from pathlib import Path


EXPECTED_SOURCE_SHA256 = "93fb87c152dc8b7fc3e709f1d56a6ab1178ac782340a1b84b86ee69f8fa40c49"
EXACT_NODES = {
    1: "1 sort bitvec 1",
    14: "14 state 12 ap_CS_fsm",
    22: "22 state 1 final_result_reg_160",
    27: "27 slice 1 14 5 5",
    406: "406 bad 48",
}


def sha256(contents: bytes) -> str:
    return hashlib.sha256(contents).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("witness", type=Path)
    parser.add_argument("--candidate", choices=("h1", "h2"), default="h1")
    args = parser.parse_args()

    original = args.source.read_bytes()
    actual_sha = sha256(original)
    if actual_sha != EXPECTED_SOURCE_SHA256:
        raise SystemExit(f"Source SHA mismatch: {actual_sha}")

    lines = original.decode("utf-8").splitlines()
    nodes = {}
    for line in lines:
        if line and line[0].isdigit():
            first, *_ = line.split(maxsplit=1)
            node_id = int(first)
            if node_id in nodes:
                raise SystemExit(f"Duplicate BTOR node {node_id}")
            nodes[node_id] = line
    for node_id, expected in EXACT_NODES.items():
        if nodes.get(node_id) != expected:
            raise SystemExit(f"Unexpected source node {node_id}: {nodes.get(node_id)}")
    if max(nodes) != 406:
        raise SystemExit(f"Unexpected last source node: {max(nodes)}")

    # In BTOR2, bad = violation of the proposed invariant.
    if args.candidate == "h1":
        # H1: !(FSM_bit5 && !final_result_latch).
        extra = "407 not 1 22\n408 and 1 27 407\n409 bad 408 ; HV-010 H1\n"
    else:
        # H2: complementary helper latches, XOR(43,45) == 1.
        extra = "407 xor 1 43 45\n408 not 1 407\n409 bad 408\n"
    if not original.endswith(b"\n"):
        raise SystemExit("Expected newline-terminated input")
    witness = original + extra.encode("utf-8")
    args.witness.parent.mkdir(parents=True, exist_ok=True)
    args.witness.write_bytes(witness)
    print(f"source_sha256={actual_sha}")
    print(f"witness_sha256={sha256(witness)}")
    print(f"witness_path={args.witness}")


if __name__ == "__main__":
    main()
