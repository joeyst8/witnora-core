#!/usr/bin/env python3
"""HV-019: first-step original safety property strengthened by legal FSM only."""

import argparse
import hashlib
from pathlib import Path


SOURCE_SHA = "93fb87c152dc8b7fc3e709f1d56a6ab1178ac782340a1b84b86ee69f8fa40c49"
UNROLLER_SHA = "51d1fd32b8bd7c70ab437daed7ed1bd0d419326ce7b9a6b50792529850e9d94b"


def data_rows(data):
    return [line.split() for line in data.decode().splitlines() if line and line[0].isdigit()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source", type=Path)
    ap.add_argument("unrolled_depth1", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    sr = args.source.read_bytes()
    br = args.unrolled_depth1.read_bytes()
    for data, expected, name in [(sr, SOURCE_SHA, "source"), (br, UNROLLER_SHA, "unrolled")]:
        actual = hashlib.sha256(data).hexdigest()
        if actual != expected:
            raise SystemExit(f"{name} hash mismatch: {actual}")

    source = data_rows(sr)
    nodes = {int(row[0]): row for row in source}
    for ident, line in {
        48: "48 and 1 45 47",
        99: "99 redor 1 98",
        100: "100 not 1 99",
        406: "406 bad 48",
    }.items():
        if " ".join(nodes[ident]) != line:
            raise SystemExit(f"Unexpected source line {ident}")
    num_sorts = sum(row[1] == "sort" for row in source)
    expr_ids = [
        int(row[0]) for row in source
        if row[1] not in {"sort", "init", "next", "output", "bad"}
    ]

    def at(source_id, frame):
        return num_sorts + frame * len(expr_ids) + expr_ids.index(source_id) + 1

    model = data_rows(br)
    ids = [int(row[0]) for row in model]
    if ids != sorted(ids) or len(set(ids)) != len(ids):
        raise SystemExit("Original unroller node IDs are unsorted or duplicate")
    for frame in (0, 1):
        bad = at(48, frame)
        if model[bad - 1] != [
            str(bad), "and", "1", str(at(45, frame)), str(at(47, frame))
        ]:
            raise SystemExit("Original property mapping mismatch")
        illegal = at(100, frame)
        if model[illegal - 1] != [str(illegal), "not", "1", str(at(99, frame))]:
            raise SystemExit("Controller onehot mapping mismatch")
    original_bads = [row for row in model if row[1] == "bad"]
    if original_bads != [
        [original_bads[0][0], "bad", str(at(48, 0))],
        [original_bads[1][0], "bad", str(at(48, 1))],
    ]:
        raise SystemExit("Unexpected original bad records")

    constraints_seen = 0
    kept = []
    for row in model:
        if row[1] == "bad":
            continue
        if row[1] == "constraint":
            constraints_seen += 1
            if constraints_seen <= 7:
                continue
        kept.append(row)
    if constraints_seen != 33:
        raise SystemExit("Expected exactly 7 init + 26 transition equalities")
    newest = ids[-1]
    kept.extend([
        [str(newest + 1), "not", "1", str(at(48, 0))],
        [str(newest + 2), "constraint", str(newest + 1)],
        [str(newest + 3), "not", "1", str(at(100, 0))],
        [str(newest + 4), "constraint", str(newest + 3)],
        [str(newest + 5), "bad", str(at(48, 1))],
    ])
    output = ("\n".join(" ".join(row) for row in kept) + "\n").encode()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output)
    print(f"output_sha256={hashlib.sha256(output).hexdigest()}")
    print(f"output_bytes={len(output)}")
    print(f"original_bad_t0={at(48, 0)} original_bad_t1={at(48, 1)}")
    print(f"controller_illegal_t0={at(100, 0)}")
    print("retained_transition_constraints=26; dropped_init_constraints=7")


if __name__ == "__main__":
    main()
