"""Generate Lean checks of real Python G5 Gaussian trace payloads.

Lean replays the actual SWAP_ROWS/ADD_ROW_XOR operations and checks a bounded
UNSAT oracle over the *original* CNF. This is not a universal Python proof.
"""
from pathlib import Path

from witnora_core.operator_genesis import (
    AFFINE_RESIDUE_CERTIFICATE_VERIFIED,
    AFFINE_RESIDUE_UNSAT_NATIVE_CERTIFIED,
    build_affine_residue_certificate,
    make_affine_residue_instance,
)

CASES = ("parity_arity_7_unsat", "parity_arity_8_unsat")


def lean_bool(x):
    return "true" if x else "false"


def lean_cnf(formula):
    return "[" + ", ".join(
        "[" + ", ".join(
            f"({abs(lit)}, {lean_bool(lit > 0)})" for lit in clause
        ) + "]" for clause in formula.to_clause_lists()
    ) + "]"


def lean_rows(rows):
    return "[" + ", ".join(
        "{ coefficients := [" + ", ".join(map(str, row["coefficients"])) +
        "], rhs := " + lean_bool(bool(row["rhs"])) + " }"
        for row in rows
    ) + "]"


def lean_snapshots(snapshots):
    return "[" + ", ".join(lean_rows(rows) for rows in snapshots) + "]"


def python_snapshots(initial_rows, operations):
    """Serialize Python-recorded intermediate states; Lean replays independently."""
    current = [dict(row) for row in initial_rows]
    snapshots = []
    for op in operations:
        if op["operation"] == "SWAP_ROWS":
            current = [dict(row) for row in op["rows_after"]]
        elif op["operation"] == "ADD_ROW_XOR":
            target, source = op["target_row"], op["source_row"]
            if current[target] != op["before"] or current[source] != op["source"]:
                raise AssertionError("Python trace metadata inconsistent with previous rows")
            current = [dict(row) for row in current]
            current[target] = dict(op["after"])
        else:
            raise AssertionError(f"unknown op: {op}")
        snapshots.append(current)
    return snapshots


def lean_steps(operations):
    chunks = []
    for op in operations:
        if op["operation"] == "SWAP_ROWS":
            chunks.append(f".swap {op['row_a']} {op['row_b']}")
        elif op["operation"] == "ADD_ROW_XOR":
            chunks.append(f".addXor {op['target_row']} {op['source_row']}")
        else:
            raise RuntimeError(f"unrecognized operation: {op}")
    return "[" + ", ".join(chunks) + "]"


def lean_single_row(row):
    return ("{ coefficients := [" + ", ".join(map(str, row["coefficients"])) +
            "], rhs := " + lean_bool(bool(row["rhs"])) + " }")


def contradiction_derivation(initial_rows, operations, final_rows):
    """Compile indexed Python operations into independently checked XOR trees."""
    expressions = [f"(.input {lean_single_row(row)})" for row in initial_rows]
    for op in operations:
        if op["operation"] == "SWAP_ROWS":
            a, b = op["row_a"], op["row_b"]
            expressions[a], expressions[b] = expressions[b], expressions[a]
        elif op["operation"] == "ADD_ROW_XOR":
            target, source = op["target_row"], op["source_row"]
            if target == source:
                raise ValueError("self-XOR operation")
            expressions[target] = (
                f"(.xor {expressions[target]} {expressions[source]})"
            )
        else:
            raise ValueError("unrecognized G5 operation")
    candidates = [
        i for i, row in enumerate(final_rows)
        if row["coefficients"] == [] and bool(row["rhs"])
    ]
    if not candidates:
        raise ValueError("G5 trace has no contradiction row")
    expression = expressions[candidates[0]]
    if len(expression) > 120000:
        raise ValueError("G5 derivation tree too large; DAG format needed")
    return expression


def dag_refs_from_operations(input_rows, operations):
    """Compile mutable row indices into append-only checked DAG references.

    SWAP_ROWS changes the reference map; ADD_ROW_XOR appends a fresh node.
    Every DAG reference points to an original or previously appended row.
    """
    references = list(range(len(input_rows)))
    next_id = len(input_rows)
    steps = []
    for op in operations:
        if op["operation"] == "SWAP_ROWS":
            a, b = op["row_a"], op["row_b"]
            references[a], references[b] = references[b], references[a]
        elif op["operation"] == "ADD_ROW_XOR":
            target, source = op["target_row"], op["source_row"]
            if target == source:
                raise ValueError("self-XOR row operation is invalid")
            steps.append((references[target], references[source]))
            references[target] = next_id
            next_id += 1
        else:
            raise ValueError("unsupported G5 operation")
    return steps


def lean_dag_refs(steps):
    return "[" + ", ".join(f"({left}, {right})" for left, right in steps) + "]"


def main():
    lines = ["import Witnora.G5Trace", "import Witnora.G5Certificate", "import Witnora.G5Dag", "set_option maxRecDepth 16384", "set_option maxHeartbeats 0", "", "namespace Witnora.G5Generated"]
    for name in CASES:
        instance = make_affine_residue_instance(name)
        cert = build_affine_residue_certificate(instance)
        if (cert.checker_status != AFFINE_RESIDUE_CERTIFICATE_VERIFIED
                or cert.status != AFFINE_RESIDUE_UNSAT_NATIVE_CERTIFIED):
            raise RuntimeError(f"{name}: not a Python-verified G5 UNSAT certificate")
        trace = cert.gaussian_elimination_trace
        if trace[0].get("type") != "INITIAL_ROWS" or trace[-1].get("type") != "FINAL_ROWS":
            raise RuntimeError(f"{name}: malformed trace envelope")
        n = instance.formula.max_var
        if n > 8:
            raise RuntimeError("fixture exceeds exhaustive Lean budget")
        prefix = (
            f"Witnora.G5Trace.acceptsUnsat {n} "
            f"{lean_cnf(instance.formula)} "
            f"{lean_rows(trace[0]['rows'])} "
            f"{lean_steps(cert.row_operations)} "
        )
        lines.append(f"example : {prefix}{lean_rows(trace[-1]['rows'])} = true := by decide")
        proof_tree = contradiction_derivation(
            trace[0]["rows"], cert.row_operations, trace[-1]["rows"]
        )
        lines.append(
            "example : Witnora.G5Certificate.checkContradiction "
            f"{lean_rows(trace[0]['rows'])} {proof_tree} = true := by decide"
        )
        dag_ops = dag_refs_from_operations(
            trace[0]["rows"], cert.row_operations
        )
        lines.append(
            "example : Witnora.G5Dag.checkDagContradiction "
            f"{lean_rows(trace[0]['rows'])} {lean_dag_refs(dag_ops)} "
            "= true := by decide"
        )
        snapshots = python_snapshots(trace[0]["rows"], cert.row_operations)
        if not snapshots:
            raise AssertionError(f"{name}: expected nonempty Python row trace")
        snapshot_prefix = (
            f"Witnora.G5Trace.checkSnapshots "
            f"{lean_rows(trace[0]['rows'])} {lean_steps(cert.row_operations)} "
        )
        lines.append(
            f"example : {snapshot_prefix}{lean_snapshots(snapshots)} = true := by decide"
        )
        tampered = list(snapshots)
        tampered[0] = []
        lines.append(
            f"example : {snapshot_prefix}{lean_snapshots(tampered)} = false := by decide"
        )
        lines.append(f"example : {prefix}[] = false := by decide")
        lines.append(
            f"example : {prefix}[{{ coefficients := [0], rhs := true }}] "
            "= false := by decide"
        )
        lines.append(
            f"example : {prefix}[{{ coefficients := [1, 1], rhs := true }}] "
            "= false := by decide"
        )
    lines.extend(["", "end Witnora.G5Generated", ""])
    dest = Path("formal/Witnora/G5Generated.lean")
    dest.write_text("\n".join(lines), encoding="utf-8")
    print(f"Emitted {len(CASES)} Python G5 trace replay certificates and negative controls")


if __name__ == "__main__":
    main()
