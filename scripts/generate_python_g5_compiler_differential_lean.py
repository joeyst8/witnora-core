"""Generate independently Lean-checked Python G5 compiler differential cases.

For every emitted case, the expected DAG comes from the actual production
Python _compile_dag implementation. The checked proposition independently
reruns Witnora.G5IndexedBridge.compile on the same source instructions.

This is a deterministic finite differential test, NOT a universal theorem
about Python/CPython execution or serialization.
"""
from __future__ import annotations

import random

from witnora_core.lean_g5_gate import _compile_dag, _serialize_indexed_operations


def _swap(i: int, j: int) -> dict[str, object]:
    return {"operation": "SWAP_ROWS", "row_a": i, "row_b": j}


def _xor(i: int, j: int) -> dict[str, object]:
    return {"operation": "ADD_ROW_XOR", "target_row": i, "source_row": j}


def _cases():
    yield 0, []
    for n in range(4):
        yield n, []
        for i in range(n + 2):
            for j in range(n + 2):
                yield n, [_swap(i, j)]
                yield n, [_xor(i, j)]

    rng = random.Random(630121)
    for n in (2, 3, 4, 6):
        for _ in range(22):
            operations = []
            for _ in range(rng.randint(4, 24)):
                i = rng.randrange(n)
                j = rng.randrange(n)
                if rng.random() < 0.3:
                    operations.append(_swap(i, j))
                else:
                    if i == j:
                        j = (j + 1) % n
                    operations.append(_xor(i, j))
            yield n, operations

    for _ in range(160):
        n = rng.randrange(8)
        operations = []
        for _ in range(rng.randrange(15)):
            i = rng.choice((rng.randrange(n + 3), rng.randrange(n + 3),
                            1048576, 0))
            j = rng.choice((rng.randrange(n + 3), rng.randrange(n + 3),
                            1048576, 0))
            operations.append((_swap if rng.random() < 0.5 else _xor)(i, j))
        yield n, operations


def emit() -> str:
    lines = [
        "import Witnora.G5IndexedBridge",
        "namespace Witnora.GeneratedPythonG5CompilerDifferential",
        "set_option maxRecDepth 8192",
        "set_option maxHeartbeats 4000000",
    ]
    valid = rejected = 0
    for index, (n, operations) in enumerate(_cases()):
        trace = _serialize_indexed_operations(operations)
        try:
            dag = _compile_dag([{} for _ in range(n)], operations)
            expected = f"some {dag}"
            valid += 1
        except ValueError:
            expected = "none"
            rejected += 1
        lines.extend([
            f"-- Python runtime case {index}, initial rows {n}, operations {len(operations)}",
            f"example : Witnora.G5IndexedBridge.compile {n} {trace} =",
            f"    {expected} := by decide",
        ])
    lines.extend([
        f"-- Total {valid + rejected} cases: {valid} accepted, {rejected} rejected",
        "end Witnora.GeneratedPythonG5CompilerDifferential",
        "",
    ])
    return "\n".join(lines)


if __name__ == "__main__":
    print(emit(), end="")
