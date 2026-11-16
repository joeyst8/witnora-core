#!/usr/bin/env python3
"""HV-008 admission smoke test for Cerbtora's published eight-state BTOR2 fixture.

This intentionally supports only the operators in the pinned example. It is
NOT an SMT solver, Cerbtora witness checker, or general hardware verifier.
Unknown operators fail closed. Use only as an independent finite-state control.

Provenance: Froleyks/cerbtora commit 983a21c440f8e4f25b1e8be8bd759332fee21e88
Example files: examples/model.btor2 and examples/witness.btor2 (MIT license).
"""

import argparse
import itertools
import json
from pathlib import Path


def parse(path):
    nodes, widths, states, inits, nexts, bads = {}, {}, [], {}, {}, []
    for raw_line in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw_line.split(";", 1)[0].strip()
        if not line:
            continue
        fields = line.split()
        ident, op, args = int(fields[0]), fields[1], fields[2:]
        if ident in nodes or ident in widths:
            raise ValueError(f"duplicate BTOR2 ID {ident}")
        if op == "sort":
            if args[0] != "bitvec":
                raise ValueError("only bitvec sort supported")
            widths[ident] = int(args[1])
            continue
        if op not in {"zero", "state", "init", "next", "neg", "not", "ite", "const", "eq", "or", "bad"}:
            raise ValueError(f"unsupported BTOR2 operator {op!r}")
        nodes[ident] = (op, args)
        if op == "state":
            states.append(ident)
        if op == "init":
            inits[int(args[1])] = int(args[2])
        if op == "next":
            nexts[int(args[1])] = int(args[2])
        if op == "bad":
            bads.append(int(args[0]))
    if set(states) != set(inits) or set(states) != set(nexts) or not bads:
        raise ValueError("only total initialization, total transition and >=1 bad supported")
    return {"nodes": nodes, "widths": widths, "states": states, "inits": inits, "nexts": nexts, "bads": bads}


def eval_expr(design, ident, state, memo=None):
    if memo is None:
        memo = {}
    if ident in memo:
        return memo[ident]
    op, args = design["nodes"][ident]

    def get(value):
        return eval_expr(design, int(value), state, memo)

    def mask():
        return (1 << design["widths"][int(args[0])]) - 1

    if op == "state":
        result = state[ident]
    elif op == "zero":
        result = 0
    elif op == "const":
        result = int(args[1], 2)
    elif op == "neg":
        result = (-get(args[1])) & mask()  # arithmetic two's-complement negation
    elif op == "not":
        result = (~get(args[1])) & mask()  # one's-complement bitwise negation
    elif op == "ite":
        result = get(args[2]) if get(args[1]) else get(args[3])
    elif op == "eq":
        result = int(get(args[1]) == get(args[2]))
    elif op == "or":
        result = get(args[1]) | get(args[2])
    else:
        raise ValueError(f"not a supported expression node: {ident}, {op}")
    memo[ident] = result
    return result


def state_key(design, state):
    return tuple(state[node] for node in design["states"])


def initial_state(design):
    return {node: eval_expr(design, expr, {}) for node, expr in design["inits"].items()}


def successor(design, state):
    return {node: eval_expr(design, expr, state) for node, expr in design["nexts"].items()}


def is_bad(design, state):
    return any(eval_expr(design, expr, state) != 0 for expr in design["bads"])


def enumerate_states(design):
    limits = [1 << design["widths"][int(design["nodes"][node][1][0])] for node in design["states"]]
    for values in itertools.product(*(range(size) for size in limits)):
        yield dict(zip(design["states"], values))


def inspect(design):
    states = list(enumerate_states(design))
    start = initial_state(design)
    seen, reached, current = set(), [], start
    while state_key(design, current) not in seen:
        seen.add(state_key(design, current))
        reached.append(state_key(design, current))
        current = successor(design, current)
    counterexamples = [(state_key(design, state), state_key(design, successor(design, state)))
                       for state in states if not is_bad(design, state) and is_bad(design, successor(design, state))]
    return {"total_states": len(states), "reachable_states": reached,
            "reachable_bad_count": sum(is_bad(design, dict(zip(design["states"], values))) for values in reached),
            "initial_safe": not is_bad(design, start),
            "one_step_inductive": not counterexamples,
            "induction_counterexamples": counterexamples}


def run(model_path, witness_path):
    model, witness = parse(model_path), parse(witness_path)
    if model["states"] != witness["states"] or model["widths"] != witness["widths"]:
        raise ValueError("fixture assumes identical state IDs, order, and sorts")
    states = list(enumerate_states(model))
    same_initial = initial_state(model) == initial_state(witness)
    same_transitions = all(successor(model, state) == successor(witness, state) for state in states)
    strengthened = all(not is_bad(model, state) or is_bad(witness, state) for state in states)
    model_out, witness_out = inspect(model), inspect(witness)
    expected = (model_out["total_states"] == 8 and
                len(model_out["reachable_states"]) == 2 and
                model_out["reachable_bad_count"] == 0 and
                not model_out["one_step_inductive"] and
                witness_out["one_step_inductive"] and
                witness_out["initial_safe"] and same_initial and same_transitions and strengthened)
    result = {"source": "Froleyks/cerbtora published BTOR2 example",
              "source_commit": "983a21c440f8e4f25b1e8be8bd759332fee21e88",
              "independent_exhaustive_semantic_control_passed": expected,
              "model": model_out, "witness": witness_out,
              "same_initial_state": same_initial,
              "same_transition_relation": same_transitions,
              "witness_bad_superset_of_original_bad": strengthened,
              "comment_mismatch": "neg of one-bit bitvector is identity, so state #5 stays 0; inline comment claims it flips",
              "caveat": "Subset interpreter / finite state model only; Cerbtora/Bitwuzla has NOT been executed or accepted this witness."}
    print(json.dumps(result, indent=2))
    return int(not expected)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("model", type=Path)
    parser.add_argument("witness", type=Path)
    args = parser.parse_args()
    raise SystemExit(run(args.model, args.witness))
