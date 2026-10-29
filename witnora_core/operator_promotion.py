"""Fail-closed research operator promotion gate.

Discovery alone never proves UNSAT. This module re-discovers evidence from
the supplied CNF, then invokes the *real* source-bound G5 Lean gate; it does
not accept caller-supplied verification status or performance assertions.

Even a successful Lean check yields PROOF_VERIFIED only. Promotion additionally
requires independent, reproducible performance/novelty review, deliberately
outside this soundness gate. This prevents premature claims of invention.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from .cnf import CNFFormula
from .lean_g5_gate import verify_g5_certificate_with_lean
from .spoke_discovery import discover_parity_spoke_conflicts


CANDIDATE_ONLY = "RESEARCH_CANDIDATE_ONLY"
PROOF_REJECTED = "SOURCE_BOUND_LEAN_PROOF_REJECTED"
PROOF_VERIFIED = "PROOF_VERIFIED_PER_INSTANCE_BENCHMARK_PENDING"
NO_DISCOVERY = "NO_SUPPORTED_OPERATOR_DISCOVERED"


def assess_parity_spoke_operator(
    formula: CNFFormula,
    certificate: Any | None = None,
    *,
    raw_clauses: object | None = None,
    source_tokens: object | None = None,
    source_spellings: object | None = None,
    source_text: object | None = None,
    timeout_seconds: int = 120,
    project_root: Path | None = None,
) -> dict[str, Any]:
    """Only fresh source-bound Lean acceptance upgrades discovered evidence.

    A successful result does not certify algorithmic novelty, competitive
    performance, or universal correctness of the Python generator.
    """
    candidates = discover_parity_spoke_conflicts(formula)
    discovery_digest = sha256(json.dumps(
        {"cnf": formula.to_clause_lists(), "candidates": candidates},
        sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")).hexdigest()
    base = {
        "operator": "PARITY_SPOKE_SYNDROME",
        "discovery_sha256": discovery_digest,
        "candidate_count": len(candidates),
        "promoted": False,
        "novelty_verified": False,
        "performance_advantage_verified": False,
    }
    if not candidates:
        return {**base, "status": NO_DISCOVERY}
    if (certificate is None or raw_clauses is None or source_tokens is None
            or source_spellings is None or source_text is None):
        return {**base, "status": CANDIDATE_ONLY,
                "reason": "original source document and G5 proof required"}
    try:
        checked = verify_g5_certificate_with_lean(
            formula, certificate, raw_clauses=raw_clauses,
            source_tokens=source_tokens, source_spellings=source_spellings,
            source_text=source_text, timeout_seconds=timeout_seconds,
            project_root=project_root,
        )
    except (ValueError, TypeError, OSError, AttributeError) as exc:
        return {**base, "status": PROOF_REJECTED,
                "reason": type(exc).__name__}

    if (checked.get("verified") is not True
            or checked.get("lean_formal_status") != "LEAN_VERIFIED"
            or checked.get("source_document_verified") is not True
            or checked.get("source_normalization_verified") is not True
            or checked.get("source_tokens_verified") is not True
            or checked.get("source_lexemes_verified") is not True
            or not isinstance(checked.get("normalization_check"), dict)
            or checked["normalization_check"].get("verified") is not True):
        return {**base, "status": PROOF_REJECTED,
                "lean_check": checked}
    return {
        **base,
        "status": PROOF_VERIFIED,
        "proof_source_sha256": checked.get("proof_source_sha256"),
        "lean_input_sha256": checked.get("input_sha256"),
        "claim_boundary": (
            "per-instance original-document G5 UNSAT proof only; "
            "promotion requires independent performance and novelty review"
        ),
    }
