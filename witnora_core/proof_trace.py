"""Witnora-native proof-trace metadata.

This module intentionally does not export DRAT, LRAT, or FRAT. The native trace
is a compact, replay-auditable explanation for UNSAT cases already supported by
Witnora's internal and independent checkers.
"""

from __future__ import annotations

from typing import Any

from .certificate import (
    CollapsePath,
    NATIVE_UNSAT_TRACE_FORMAT,
    UNSAT_LEVEL_2SAT_SCC,
    UNSAT_LEVEL_EXPLICIT_EMPTY,
)


def native_unsat_trace(path: CollapsePath) -> dict[str, Any] | None:
    """Return a supported native UNSAT trace for ``path``, if one exists."""

    return path.native_proof_trace


def is_supported_native_unsat_trace(trace: dict[str, Any] | None) -> bool:
    if not trace:
        return False
    if trace.get("proof_trace_format") != NATIVE_UNSAT_TRACE_FORMAT:
        return False
    if trace.get("external_standard") != "NONE":
        return False
    if trace.get("lrat_frat_status") != "NOT_EXPORTED":
        return False
    return trace.get("unsat_reason") in {
        UNSAT_LEVEL_EXPLICIT_EMPTY,
        UNSAT_LEVEL_2SAT_SCC,
    }
