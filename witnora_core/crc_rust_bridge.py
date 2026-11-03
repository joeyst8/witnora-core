"""Native Rust indexed VE adapter, preserving exact Python count contracts.

Only the VE arithmetic moves to Rust. The Python reference remains as
an independent differential oracle during migration; the Lean checker
remains a separate, unmodified trust boundary.
"""
from __future__ import annotations

import os
from pathlib import Path
import subprocess

from witnora_core.crc_variable_elimination import VariableEliminationCount


def count_component_by_rust_elimination(
    violation_clauses,
    component_variables: tuple[int, ...],
    *,
    max_factor_variables: int = 6,
    max_operations: int = 1000000,
    binary_path: str | os.PathLike[str] | None = None,
    timeout_seconds: float = 20,
) -> VariableEliminationCount | None:
    """Exact native #SAT or None on a safe resource limit.

    Protocol is versioned by the compiled rust/witnora-ve executable.
    Absence of a binary is an explicit configuration error, never
    a hidden fallback to the Python reference.
    """
    if not 1 <= max_factor_variables <= 16 or max_operations < 1:
        raise ValueError("invalid Rust VE width or operation budget")
    if timeout_seconds <= 0:
        raise ValueError("timeout must be positive")
    variables = tuple(component_variables)
    if len(variables) != len(set(variables)) or any(
            not isinstance(v, int) or v < 1 or v > 2147483647
            for v in variables):
        raise ValueError("invalid component variable set")
    clauses = tuple(violation_clauses)
    allowed = sum(1 << (v - 1) for v in variables)
    source_lines = []
    for zeros, ones in clauses:
        if (not isinstance(zeros, int) or not isinstance(ones, int)
                or zeros < 0 or ones < 0 or zeros & ones
                or (zeros | ones) & ~allowed):
            raise ValueError("invalid normalized violation mask")
        literals = [str(v) for v in variables if zeros & (1 << (v - 1))]
        literals += [str(-v) for v in variables if ones & (1 << (v - 1))]
        source_lines.append(" ".join(literals + ["0"]))
    location = binary_path or os.environ.get("WITNORA_RUST_VE_BIN")
    if not location:
        raise RuntimeError("Rust VE binary not configured; build rust/witnora-ve")
    path = Path(location)
    if not path.is_file():
        raise RuntimeError(f"Rust VE binary unavailable: {path}")
    lines = [
        f"p witnora-ve {len(variables)} {len(clauses)} "
        f"{max_factor_variables} {max_operations}",
        " ".join(["v", *(str(v) for v in variables), "0"]),
        *source_lines,
    ]
    try:
        process = subprocess.run(
            [str(path)], input="\n".join(lines) + "\n",
            text=True, capture_output=True, check=False,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        return None
    if process.returncode:
        raise RuntimeError(
            f"Rust VE failed (code={process.returncode}): "
            + process.stderr.strip()[:400])
    fields = process.stdout.strip().split()
    if fields == ["INCOMPLETE"]:
        return None
    if len(fields) != 5 or fields[0] != "EXACT":
        raise RuntimeError("Rust VE returned malformed output")
    try:
        count, operations, width, eliminated = map(int, fields[1:])
    except ValueError as e:
        raise RuntimeError("Rust VE count output was not numeric") from e
    if count < 0 or operations < 0 or width < 0 or eliminated != len(variables):
        raise RuntimeError("Rust VE count invariants violated")
    if operations > max_operations or width > max_factor_variables:
        raise RuntimeError("Rust VE exceeded declared budgets")
    return VariableEliminationCount(count, operations, width, eliminated)
