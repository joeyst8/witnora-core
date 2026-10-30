"""Kernel-check discovered parity-spoke contradictions against original DIMACS.

This gate does not trust the discovered XOR equations. It serializes their
proposed endpoints and verifies with Lean that all four complete binary
patterns follow from the *actual* signed clauses parsed from source text.
Only accepted closed source-to-UNSAT propositions receive formal status.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import subprocess
from typing import Any

from .cnf import CNFFormula
from .lean_cnf_gate import _lean_rows, _strict_rows
from .spoke_discovery import (discover_parity_spoke_conflicts,
                              extract_binary_xor_equations, extract_spoke_paths)


def _spoke_literal(path: dict[str, Any], x: int, z: int) -> str:
    mid = path["middle"]
    if type(mid) is not int or mid <= 0 or mid in (x, z):
        raise ValueError("invalid intermediate variable")
    equations = path["equations"]
    if not isinstance(equations, list) or len(equations) != 2:
        raise ValueError("incomplete two-equation path")
    by_vars = {}
    for item in equations:
        vs, rhs = item["variables"], item["rhs"]
        if (not isinstance(vs, list) or len(vs) != 2
                or any(type(v) is not int or v <= 0 for v in vs)
                or type(rhs) is not int or rhs not in (0, 1)):
            raise ValueError("invalid source equation")
        by_vars[frozenset(vs)] = rhs
    left = by_vars[frozenset((x, mid))]
    right = by_vars[frozenset((mid, z))]
    return f"({{ middle := {mid}, left := {'true' if left else 'false'}, right := {'true' if right else 'false'} }})"


def verify_discovered_spoke_with_lean(
    formula: CNFFormula,
    *,
    raw_clauses: object,
    source_tokens: object,
    source_text: object,
    timeout_seconds: int = 120,
    project_root: Path | None = None,
) -> dict[str, Any]:
    failure = {"verified": False, "lean_formal_status": "NOT_LEAN_VERIFIED"}
    try:
        if (type(source_text) is not str or not source_text.isascii()
                or len(source_text) > 65536):
            raise ValueError("unsupported ASCII source")
        if (type(source_tokens) not in (list, tuple)
                or any(type(v) is not int for v in source_tokens)):
            raise ValueError("invalid source tokens")
        raw = _lean_rows(_strict_rows(raw_clauses))
        candidates = discover_parity_spoke_conflicts(formula)
        if not candidates:
            return {**failure, "reason": "NO_DISCOVERED_CONTRADICTION"}
        candidate = candidates[0]
        x, z = candidate["endpoints"]
        first, second = candidate["paths"]
        s, t = _spoke_literal(first, x, z), _spoke_literal(second, x, z)
        source_bytes = [ord(c) for c in source_text]
        ids = sorted(formula.variables)
        if len(ids) > 24:
            raise ValueError("full binary-extraction equality exceeds the supported variable cap")
        if len(ids) > 6:
            raise ValueError("full spoke-path equality exceeds the supported variable cap")
        proposed_equations = extract_binary_xor_equations(formula)
        emitted_equations = "[" + ", ".join(
            "{ u := " + str(u) + ", v := " + str(v) +
            ", rhs := " + ("true" if rhs else "false") + " }"
            for u, v, rhs in proposed_equations
        ) + "]"
        emitted_paths = "[" + ", ".join(
            "{ x := " + str(x) + ", z := " + str(z) +
            ", middle := " + str(m) +
            ", left := " + ("true" if l else "false") +
            ", right := " + ("true" if r else "false") + " }"
            for x, z, m, l, r in extract_spoke_paths(formula)
        ) + "]"
        # This example has *no assumed correctness of Python's discovery*.
        # The kernel checks each complete pattern against raw source clauses.
        proof = (
            "import Witnora.SpokeDiscoverySpec\n"
            "set_option maxRecDepth 16384\n"
            "set_option maxHeartbeats 0\n"
            "example : Witnora.BinaryXorDiscovery.extract "
            f"(Witnora.SignedSerialization.decodeCNF {raw}) {ids} "
            f"= {emitted_equations} := by decide\n"
            "example : Witnora.SpokePathDiscovery.extract "\n            f"(Witnora.SignedSerialization.decodeCNF {raw}) {ids} "\n            f"= {emitted_paths} := by decide\n"\n            "example : Witnora.SpokeDiscoverySpec.discoverFrom "
            f"(Witnora.SignedSerialization.decodeCNF {raw}) "
            f"[{{ x := {x}, z := {z}, first := {s}, second := {t} }}] "
            f"= [{{ x := {x}, z := {z}, first := {s}, second := {t} }}] "
            ":= by decide\n"
            "example : Witnora.DIMACSDocument.parseDocument "
            f"{source_bytes} = some (Witnora.DIMACSTokens.serialize {raw}) "
            "∧ ¬ ∃ a, Witnora.SignedSerialization.signedCNFHolds "
            f"{raw} a := by\n"
            "  exact Witnora.SpokeSourceBridge.checked_ascii_dimacs_spoke_unsat "
            f"{source_bytes} {list(source_tokens)} {raw} "
            f"(by decide) (by decide) {x} {z} {s} {t} (by decide)\n"
        )
        root = Path(project_root) if project_root is not None else Path(__file__).resolve().parents[1]
        formal_dir = root / "formal"
        if not (formal_dir / "lakefile.toml").is_file():
            raise ValueError("Lean project unavailable")
        with TemporaryDirectory(prefix="witnora_spoke_source_") as temp:
            path = Path(temp) / "SpokeSourceProof.lean"
            path.write_text(proof, encoding="utf-8")
            result = subprocess.run(
                ["lake", "env", "lean", str(path)], cwd=formal_dir,
                capture_output=True, text=True,
                timeout=timeout_seconds, check=False,
            )
        if result.returncode != 0:
            raise ValueError("Lean rejected source-bound spoke proof: " +
                             (result.stdout + result.stderr)[-1000:])
        return {
            "binary_extraction_exact_checked": True,
            "spoke_path_extraction_exact_checked": True,
            "verified": True,
            "lean_formal_status": "LEAN_SOURCE_SPOKE_UNSAT_VERIFIED",
            "proof_source_sha256": sha256(proof.encode("utf-8")).hexdigest(),
            "operator": "PARITY_SPOKE_SYNDROME",
            "claim_boundary": "kernel-checked UNSAT of the actual supported ASCII DIMACS input; novelty and speed unproved",
        }
    except (ValueError, TypeError, KeyError, IndexError, AttributeError,
            OSError, subprocess.TimeoutExpired) as exc:
        return {**failure, "reason": type(exc).__name__,
                "detail": str(exc)[-1200:]}
