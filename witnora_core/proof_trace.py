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
    if trace.get("depends_on_replayed_collapse_path") is not True:
        return False
    if trace.get("external_standard") != "NONE":
        return False
    if trace.get("lrat_frat_status") != "NOT_EXPORTED":
        return False
    reason = trace.get("unsat_reason")
    return isinstance(reason, str) and reason in {
        UNSAT_LEVEL_EXPLICIT_EMPTY,
        UNSAT_LEVEL_2SAT_SCC,
    }


def is_supported_native_unsat_trace_rust(trace: dict[str, Any] | None) -> bool:
    """Opt-in native metadata screen, not a soundness/proof checker."""
    from witnora_ve import native_unsat_trace_metadata_supported_native
    if not trace:
        return False
    # Fail closed on unexpected metadata types at the Python boundary.
    fields = ("proof_trace_format", "external_standard", "lrat_frat_status",
              "unsat_reason")
    if any(trace.get(field) is not None and not isinstance(trace[field], str)
           for field in fields):
        return False
    return native_unsat_trace_metadata_supported_native(
        trace.get("proof_trace_format"),
        trace.get("depends_on_replayed_collapse_path") is True,
        trace.get("external_standard"), trace.get("lrat_frat_status"),
        trace.get("unsat_reason"),
    )
