#!/usr/bin/env python3
"""HV-014: exact SHA-pinned one-hot FSM + H1 combined witness generator."""

import argparse
import hashlib
from pathlib import Path


SOURCE_SHA = "93fb87c152dc8b7fc3e709f1d56a6ab1178ac782340a1b84b86ee69f8fa40c49"
REQUIRED = {
    14: "14 state 12 ap_CS_fsm",
    22: "22 state 1 final_result_reg_160",
    27: "27 slice 1 14 5 5",
    99: "99 redor 1 98",
    100: "100 not 1 99",
    406: "406 bad 48",
}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("source", type=Path)
    p.add_argument("witness", type=Path)
    a = p.parse_args()
    data = a.source.read_bytes()
    h = hashlib.sha256(data).hexdigest()
    if h != SOURCE_SHA:
        raise SystemExit(f"Input hash mismatch: {h}")
    definitions = {}
    for line in data.decode().splitlines():
        if line and line[0].isdigit():
            id_string = line.split(maxsplit=1)[0]
            definitions[int(id_string)] = line
    for number, expected in REQUIRED.items():
        if definitions.get(number) != expected:
            raise SystemExit(f"Unexpected source node {number}: {definitions.get(number)}")
    if max(definitions) != 406 or not data.endswith(b"\n"):
        raise SystemExit("Source differs from frozen expected structure")
    additions = b"407 not 1 22\n408 and 1 27 407\n409 bad 100\n410 bad 408\n"
    result = data + additions
    a.witness.parent.mkdir(parents=True, exist_ok=True)
    a.witness.write_bytes(result)
    print("source_sha256=" + h)
    print("witness_sha256=" + hashlib.sha256(result).hexdigest())
    print("witness_bytes=" + str(len(result)))
    print("witness=" + str(a.witness))


if __name__ == "__main__":
    main()
