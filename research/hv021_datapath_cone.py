#!/usr/bin/env python3
"""HV-021: static BTOR2 fan-in / sequential next-state closure, no solving.

Only the Github mirror admitted by the full two-frame digest test is accepted.
Each state edge consumes one unit of sequential-depth budget.
"""

import argparse
import hashlib
import json
from pathlib import Path


MIRROR_SHA256 = "cfa12d67ca508b686e2c2609962fac74919e7448ca8a379d2527cdeba65d58bc"
EXPR_BINARY = {"add", "and", "concat", "eq", "or", "read"}
EXPR_UNARY = {"not", "redor", "uext", "slice"}


def load(path):
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != MIRROR_SHA256:
        raise SystemExit(f"mirror source hash mismatch: {digest}")
    records = {}
    nxt = {}
    for line in raw.decode().splitlines():
        parts = line.split(";")[0].split()
        if not parts:
            continue
        ident = int(parts[0])
        if ident in records:
            raise SystemExit(f"duplicate node {ident}")
        op, args = parts[1], parts[2:]
        records[ident] = (op, args)
        if op == "next":
            nxt[int(args[1])] = int(args[2])
    assert len(nxt) == 26
    assert records[265] == ("next", ["1", "22", "264"])
    assert records[166] == ("eq", ["1", "165", "164"])
    assert records[319][0] == "state"
    assert records[320] == ("read", ["6", "319", "194"])
    assert records[397] == ("read", ["6", "319", "194"])
    assert records[405] == ("next", ["318", "319", "404", "mem_V_U.top_mem_V_ram_U.ram"])
    return records, nxt


def references(op, a):
    if op in EXPR_BINARY:
        return [int(a[1]), int(a[2])]
    if op == "write":
        return [int(a[1]), int(a[2]), int(a[3])]
    if op == "ite":
        return [int(a[1]), int(a[2]), int(a[3])]
    if op in EXPR_UNARY:
        return [int(a[1])]
    if op in {"sort", "state", "input", "const", "constd", "consth"}:
        return []
    raise SystemExit(f"unexpected operator in expression: {op}")


def cone(records, nxt, root, steps):
    visited = set()
    nodes = set()
    state_leaves = set()
    input_leaves = set()
    reads, writes = set(), set()
    queue = [(root, steps)]
    while queue:
        node, budget = queue.pop()
        if (node, budget) in visited:
            continue
        visited.add((node, budget))
        op, args = records[node]
        nodes.add(node)
        if op == "state":
            state_leaves.add(node)
            if budget > 0 and node in nxt:
                queue.append((nxt[node], budget - 1))
        elif op == "input":
            input_leaves.add(node)
        else:
            if op == "read":
                reads.add(node)
            if op == "write":
                writes.add(node)
            queue.extend((ref, budget) for ref in references(op, args))
    return {
        "visited_node_count": len(nodes),
        "state_ids": sorted(state_leaves),
        "input_ids": sorted(input_leaves),
        "read_ids": sorted(reads),
        "write_ids": sorted(writes),
        "contains_array_ram_state_319": 319 in state_leaves,
        "contains_q0_phi_equality_166": 166 in nodes,
        "contains_result_register_22": 22 in state_leaves,
        "contains_fsm_state_14": 14 in state_leaves,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    args = parser.parse_args()
    records, nxt = load(args.source)
    layers = {str(k): cone(records, nxt, 264, k) for k in (0, 1, 2)}
    assert layers["0"]["contains_q0_phi_equality_166"]
    assert not layers["0"]["contains_array_ram_state_319"]
    assert layers["1"]["contains_array_ram_state_319"]
    assert 320 in layers["1"]["read_ids"]
    assert 397 in layers["2"]["read_ids"]
    assert 402 in layers["2"]["write_ids"]
    print(json.dumps({
        "experiment": "HV-021",
        "source": "GitHub mirror independently admitted by equality of depth1 unroll SHA",
        "mirror_sha256": MIRROR_SHA256,
        "unbounded_safety_proved": False,
        "algorithm_novelty": False,
        "result_reg_next_node": 264,
        "sequential_dependency_layers": layers,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
