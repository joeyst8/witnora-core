"""Fail-closed Lean check of an actual Python CNF normalization result.

This checks concrete invocations against Lean's executable canonicalizer. It
proves acceptance soundness for this artifact, not universal CPython execution.
Only signed integer data is interpolated into fixed Lean syntax.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

from .cnf import CNFFormula

MAX_CLAUSES = 4096
MAX_LITERALS = 16384


def _strict_rows(rows: object) -> list[list[int]]:
    if type(rows) not in (list, tuple):
        raise ValueError("CNF must be a list or tuple of clauses")
    if len(rows) > MAX_CLAUSES:
        raise ValueError("CNF clause limit exceeded")
    result = []
    total = 0
    for clause in rows:
        if type(clause) not in (list, tuple):
            raise ValueError("each clause must be a list or tuple")
        total += len(clause)
        if total > MAX_LITERALS:
            raise ValueError("CNF literal limit exceeded")
        clean = []
        for literal in clause:
            if type(literal) is not int or literal == 0:
                raise ValueError("literals must be nonzero signed integers")
            clean.append(literal)
        result.append(clean)
    return result


def _lean_rows(rows: list[list[int]]) -> str:
    return "[" + ", ".join(
        "[" + ", ".join(str(literal) for literal in clause) + "]"
        for clause in rows
    ) + "]"


def verify_cnf_normalization_with_lean(
    raw_clauses: object,
    proposed_clauses: object | None = None,
    *,
    timeout_seconds: int = 120,
    project_root: Path | None = None,
    source_tokens: object | None = None,
) -> dict[str, object]:
    """Check exact ordered normalization through Lean, fail closed on error.

    If proposed_clauses is omitted, run Python's actual CNF constructor.
    The returned attestation is bound to both raw and normalized clause data.
    """
    failure: dict[str, object] = {
        "verified": False, "lean_formal_status": "NOT_LEAN_VERIFIED",
    }
    try:
        raw = _strict_rows(raw_clauses)
        if proposed_clauses is None:
            actual = CNFFormula.from_raw_clauses(raw).to_clause_lists()
        else:
            actual = _strict_rows(proposed_clauses)
        tokens = None
        if source_tokens is not None:
            if type(source_tokens) not in (list, tuple) or len(source_tokens) > MAX_LITERALS + MAX_CLAUSES:
                raise ValueError("invalid DIMACS integer token stream")
            if any(type(token) is not int for token in source_tokens):
                raise ValueError("tokens must be signed integers")
            tokens = list(source_tokens)
        digest = sha256(json.dumps(
            {"raw": raw, "normalized": actual, "source_tokens": tokens},
            sort_keys=True, separators=(",", ":"),
        ).encode("utf-8")).hexdigest()
        lean_source = (
            "import Witnora.CNFSorted\n"
            "import Witnora.SignedSerialization\n"
            "set_option maxRecDepth 16384\n"
            "set_option maxHeartbeats 0\n"
            "example : Witnora.CNFSorted.canonicalize "
            "(Witnora.SignedSerialization.decodeCNF "
            f"{_lean_rows(raw)}) = "
            "(Witnora.SignedSerialization.decodeCNF "
            f"{_lean_rows(actual)}) := by decide\n"
        )
        if tokens is not None:
            lean_source = "import Witnora.DIMACSTokens\n" + lean_source
            lean_source += (
                "example : Witnora.DIMACSTokens.checkStream "
                f"{str(tokens)} {_lean_rows(raw)} = true := by decide\n"
            )
        root = Path(project_root) if project_root is not None else Path(__file__).resolve().parents[1]
        formal_dir = root / "formal"
        if not (formal_dir / "lakefile.toml").is_file():
            raise ValueError("Lean project unavailable")
        with TemporaryDirectory(prefix="witnora_cnf_lean_") as temp:
            proof_file = Path(temp) / "CNFNormalizationCheck.lean"
            proof_file.write_text(lean_source, encoding="utf-8")
            result = subprocess.run(
                ["lake", "env", "lean", str(proof_file)],
                cwd=formal_dir, capture_output=True, text=True,
                timeout=timeout_seconds, check=False,
            )
        if result.returncode != 0:
            raise ValueError("Lean rejected normalized CNF")
        return {
            "verified": True,
            "lean_formal_status": "LEAN_CNF_NORMALIZATION_VERIFIED",
            "input_sha256": digest,
            "proof_source_sha256": sha256(lean_source.encode("utf-8")).hexdigest(),
            "token_stream_verified": tokens is not None,
        }
    except (ValueError, TypeError, OSError, subprocess.TimeoutExpired) as exc:
        return {**failure, "reason": type(exc).__name__}
