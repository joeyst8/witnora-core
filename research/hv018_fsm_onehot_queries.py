#!/usr/bin/env python3
"""HV-018: isolate a one-hot FSM induction lemma from frozen HV-010 unrollings."""

import argparse
import hashlib
from pathlib import Path


SOURCE_SHA = "93fb87c152dc8b7fc3e709f1d56a6ab1178ac782340a1b84b86ee69f8fa40c49"


def parsed(path):
    lines = path.read_text().splitlines()
    return [line.split() for line in lines if line and line[0].isdigit()]


def render(lines):
    return ("\n".join(" ".join(tokens) for tokens in lines) + "\n").encode()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("bmc0", type=Path)
    parser.add_argument("bmc1", type=Path)
    parser.add_argument("outdir", type=Path)
    args = parser.parse_args()

    actual = hashlib.sha256(args.source.read_bytes()).hexdigest()
    if actual != SOURCE_SHA:
        raise SystemExit("Frozen source SHA mismatch: " + actual)
    source = parsed(args.source)
    source_nodes = {int(row[0]): row for row in source}
    for node, expected in {
        99: "99 redor 1 98",
        100: "100 not 1 99",
        406: "406 bad 48",
    }.items():
        if " ".join(source_nodes[node]) != expected:
            raise SystemExit(f"Unexpected source node {node}")

    num_sorts = sum(row[1] == "sort" for row in source)
    expr_nodes = [
        int(row[0]) for row in source
        if row[1] not in {"sort", "init", "next", "output", "bad"}
    ]
    if 100 not in expr_nodes or 99 not in expr_nodes:
        raise SystemExit("Missing source one-hot expression")
    expr_per_frame = len(expr_nodes)

    def emitted_id(source_id, frame):
        return num_sorts + frame * expr_per_frame + expr_nodes.index(source_id) + 1

    args.outdir.mkdir(parents=True, exist_ok=True)
    for depth, input_path in [(0, args.bmc0), (1, args.bmc1)]:
        rows = parsed(input_path)
        ids = [int(row[0]) for row in rows]
        if ids != sorted(ids) or len(set(ids)) != len(ids):
            raise SystemExit("Invalid unrolling node IDs")
        assert rows[0] == ["1", "sort", "bitvec", "1"]
        if sum(row[1] == "sort" for row in rows) != num_sorts:
            raise SystemExit("Unexpected sort count")
        if sum(row[1] == "bad" for row in rows) != depth + 1:
            raise SystemExit("Unexpected original bad count")
        if sum(row[1] == "constraint" for row in rows) != 7 + 26 * depth:
            raise SystemExit("Unexpected init/transition constraint count")
        for frame in range(depth + 1):
            illegal, legal = emitted_id(100, frame), emitted_id(99, frame)
            if rows[illegal - 1] != [str(illegal), "not", "1", str(legal)]:
                raise SystemExit(f"One-hot expression mismatch at frame {frame}")

        head = [row for row in rows if row[1] != "bad"]
        if depth == 0:
            base = head + [[str(ids[-1] + 1), "bad", str(emitted_id(100, 0))]]
            name = "base"
            sets = [(name, base)]
        else:
            clean = []
            dropped = 0
            for row in head:
                if row[1] == "constraint" and dropped < 7:
                    dropped += 1
                    continue
                clean.append(row)
            if dropped != 7:
                raise SystemExit("Did not drop exactly seven init constraints")
            next_id = ids[-1] + 1
            step = clean + [
                [str(next_id), "not", "1", str(emitted_id(100, 0))],
                [str(next_id + 1), "constraint", str(next_id)],
                [str(next_id + 2), "bad", str(emitted_id(100, 1))],
            ]
            positive = clean + [
                [str(next_id), "bad", str(emitted_id(100, 0))],
            ]
            sets = [("step", step), ("positive", positive)]
        for suffix, query in sets:
            query_ids = [int(row[0]) for row in query]
            if query_ids != sorted(query_ids) or len(set(query_ids)) != len(query_ids):
                raise SystemExit("Derived query IDs not ordered and unique")
            output = render(query)
            target = args.outdir / f"hv018_onehot_{suffix}.btor2"
            target.write_bytes(output)
            print(f"{suffix}: sha256={hashlib.sha256(output).hexdigest()} bytes={len(output)} path={target}")

    print(f"source_sha256={actual}")
    print(f"num_source_sorts={num_sorts} expressions_per_frame={expr_per_frame}")
    print(f"fsm_onehot_violation_ids=({emitted_id(100, 0)},{emitted_id(100, 1)})")


if __name__ == "__main__":
    main()
