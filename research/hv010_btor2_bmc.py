#!/usr/bin/env python3
"""Mechanical BTOR2 bounded safety checker input for HV-010.

Turns an original BTOR2 transition system into a *combinational* BTOR2
formula with time-indexed input/state variables, reset and transition
constraints, and a bad at each frame through the requested depth.
This is ordinary bounded model checking, not a proof of unbounded safety.
"""

import argparse
import hashlib
from pathlib import Path


SOURCE_SHA256 = "93fb87c152dc8b7fc3e709f1d56a6ab1178ac782340a1b84b86ee69f8fa40c49"
BINARY_OPS = {"add", "and", "concat", "eq", "or", "read"}
UNARY_OPS = {"not", "redor"}


def source_records(path: Path):
    raw = path.read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    if actual != SOURCE_SHA256:
        raise SystemExit(f"Source hash mismatch: {actual}")
    result = []
    for source_line in raw.decode().splitlines():
        if not source_line or source_line.lstrip().startswith(";"):
            continue
        tokens = source_line.split(";")[0].split()
        node = int(tokens[0])
        result.append((node, tokens[1], tokens[2:]))
    if len(set(x[0] for x in result)) != len(result):
        raise SystemExit("Duplicate BTOR2 node IDs")
    if [x[0] for x in result] != sorted(x[0] for x in result):
        raise SystemExit("Input BTOR2 IDs are not sorted")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--depth", type=int, required=True)
    parser.add_argument("--positive-control", action="store_true",
                        help="Add a SAT-expected bad for free input ap_start in t=0")
    args = parser.parse_args()
    if not 0 <= args.depth <= 64:
        raise SystemExit("Depth must be between 0 and 64")
    records = source_records(args.source)
    emitted = []
    next_id = 0

    def emit(operator, *parts):
        nonlocal next_id
        next_id += 1
        emitted.append(f"{next_id} {operator} {' '.join(str(p) for p in parts)}".rstrip())
        return next_id

    sorts = {}
    for source_id, operator, p in records:
        if operator != "sort":
            continue
        if p[0] == "bitvec":
            sorts[source_id] = emit("sort bitvec", p[1])
        elif p[0] == "array":
            sorts[source_id] = emit("sort array", sorts[int(p[1])], sorts[int(p[2])])
        else:
            raise ValueError(f"Unsupported sort {p[0]}")
    if 1 not in sorts:
        raise SystemExit("Original model is missing 1-bit sort")

    expr = {}
    init_relations = []
    next_relations = []
    bad_ids = []
    for original_id, op, p in records:
        if op == "init":
            init_relations.append((int(p[1]), int(p[2])))
        elif op == "next":
            next_relations.append((int(p[1]), int(p[2])))
        elif op == "bad":
            bad_ids.append(int(p[0]))
    if not init_relations or not next_relations or not bad_ids:
        raise SystemExit("Missing init/next/bad statements")

    for t in range(args.depth + 1):
        values = {}
        for original_id, op, p in records:
            if op in {"sort", "init", "next", "output", "bad"}:
                continue
            if op in {"input", "state"}:
                # State/input variables are unconstrained except for init/next
                # equalities added below. New fresh variables at every frame.
                values[original_id] = emit("input", sorts[int(p[0])], f"{op}_{original_id}_t{t}")
            elif op in {"const", "constd", "consth"}:
                values[original_id] = emit(op, sorts[int(p[0])], p[1])
            elif op in BINARY_OPS:
                values[original_id] = emit(op, sorts[int(p[0])], values[int(p[1])], values[int(p[2])])
            elif op == "write":
                values[original_id] = emit(op, sorts[int(p[0])], values[int(p[1])], values[int(p[2])], values[int(p[3])])
            elif op == "ite":
                values[original_id] = emit(op, sorts[int(p[0])], values[int(p[1])], values[int(p[2])], values[int(p[3])])
            elif op in UNARY_OPS:
                values[original_id] = emit(op, sorts[int(p[0])], values[int(p[1])])
            elif op == "slice":
                values[original_id] = emit(op, sorts[int(p[0])], values[int(p[1])], int(p[2]), int(p[3]))
            elif op == "uext":
                values[original_id] = emit(op, sorts[int(p[0])], values[int(p[1])], int(p[2]))
            else:
                raise SystemExit(f"Unsupported BTOR2 op {op} at node {original_id}")
        expr[t] = values

    n_constraints = 0
    for state, initial in init_relations:
        a = expr[0][state]
        b = expr[0][initial]
        emit("constraint", emit("eq", sorts[1], a, b))
        n_constraints += 1
    for t in range(args.depth):
        for state, rhs in next_relations:
            emit("constraint", emit("eq", sorts[1], expr[t + 1][state], expr[t][rhs]))
            n_constraints += 1

    for t in range(args.depth + 1):
        for bad in bad_ids:
            emit("bad", expr[t][bad])
    if args.positive_control:
        # Input 4 is ap_start: it is unconstrained at t=0, so an additional
        # bad on this input is a SAT-positive parser/solver sanity check.
        emit("bad", expr[0][4])

    args.output.parent.mkdir(parents=True, exist_ok=True)
    output = ("\n".join(emitted) + "\n").encode()
    args.output.write_bytes(output)
    print(f"depth={args.depth}")
    print(f"frames={args.depth + 1}")
    print(f"constraints={n_constraints}")
    print(f"bads={(args.depth + 1) * len(bad_ids) + int(args.positive_control)}")
    print(f"output_sha256={hashlib.sha256(output).hexdigest()}")
    print(f"output_bytes={len(output)}")
    print(f"output={args.output}")


if __name__ == "__main__":
    main()
