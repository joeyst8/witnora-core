"""Fail-closed, source-bound Lean verification of parity residual compression.

Python's component graph, paths, root offsets and residual rows are untrusted.
The Lean kernel checks every emitted source path, literal substitution and
SAT-equivalence theorem. The canonical residual is separately checked by the
existing Lean CNF normalization gate. This is per-instance, not CPython
language refinement or an operator-performance claim.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

from .cnf import CNFFormula
from .lean_cnf_gate import (
    _lean_rows, _strict_rows, verify_cnf_normalization_with_lean,
)
from .parity_compression import (
    compress_binary_xor_components, substitute_residual_formula,
)


def _if_lookup(entries: list[tuple[int, str]], default: str) -> str:
    expr = default
    for vertex, value in reversed(entries):
        expr = f"(if v = {vertex} then {value} else {expr})"
    return expr


def _paths_proof(vertices: list[int]) -> str:
    def rec(i: int, indent: str, negative: list[str]) -> str:
        if i == len(vertices):
            conds = ", ".join(negative)
            return indent + "simp [rootOf, parityOffset, sourcePath, " + conds + "]\n"
        v = vertices[i]
        h = f"h{i}"
        return (
            indent + f"by_cases {h} : v = {v}\n"
            + indent + "· subst v\n"
            + indent + "  decide\n"
            + indent + "· " + rec(i + 1, indent + "  ", negative + [h]).lstrip()
        )
    return rec(0, "    ", [])


def verify_parity_compression_with_lean(
    formula: CNFFormula,
    *,
    raw_clauses: object,
    source_tokens: object,
    source_spellings: object,
    source_text: object,
    timeout_seconds: int = 120,
    project_root: Path | None = None,
) -> dict:
    failure = {"verified": False, "lean_formal_status": "NOT_LEAN_VERIFIED"}
    try:
        if type(source_text) is not str or not source_text.isascii() or len(source_text) > 65536:
            raise ValueError("unsupported ASCII document")
        if type(source_tokens) not in (list, tuple) or any(type(x) is not int for x in source_tokens):
            raise ValueError("invalid token stream")
        raw = _strict_rows(raw_clauses)
        root = Path(project_root) if project_root is not None else Path(__file__).resolve().parents[1]
        norm = verify_cnf_normalization_with_lean(
            raw, formula.to_clause_lists(), source_tokens=source_tokens,
            source_spellings=source_spellings, source_text=source_text,
            timeout_seconds=timeout_seconds, project_root=root,
        )
        if not all(norm.get(key) is True for key in
                   ("verified", "source_document_verified", "token_stream_verified",
                    "decimal_lexemes_verified")):
            raise ValueError("original source-to-canonical check rejected")
        candidate = compress_binary_xor_components(formula)
        if candidate["status"] != "UNVERIFIED_STRUCTURAL_CANDIDATE":
            raise ValueError("inconsistent source binary XOR graph")
        residual = substitute_residual_formula(formula, candidate)
        roots = dict(candidate["roots"])
        offsets = dict(candidate["offsets"])
        paths = dict(candidate["source_paths"])
        vertices = sorted(roots)
        if (set(offsets) != set(roots) or set(paths) != set(roots)
                or any(type(v) is not int or v <= 0 for v in vertices)):
            raise ValueError("invalid component mapping")
        root_expr = _if_lookup([(v, str(roots[v])) for v in vertices], "v")
        offset_expr = _if_lookup(
            [(v, "true" if offsets[v] else "false") for v in vertices], "false")
        path_expr = _if_lookup(
            [(v, "[" + ", ".join(f"({n}, {'true' if bit else 'false'})"
                               for n, bit in paths[v]) + "]") for v in vertices], "[]")
        rewritten = [
            [((roots.get(abs(lit), abs(lit))) *
              (1 if (lit > 0) != bool(offsets.get(abs(lit), 0)) else -1))
             for lit in clause]
            for clause in raw
        ]
        # The exact *pre-normalization* rewritten clause list is checked
        # against Lean's literal-by-literal substitution. A second kernel
        # check establishes the Python canonical output independently.
        normalized_residual = verify_cnf_normalization_with_lean(
            rewritten, residual.to_clause_lists(),
            timeout_seconds=timeout_seconds, project_root=root,
        )
        if normalized_residual.get("verified") is not True:
            raise ValueError("canonical residual mismatch")
        source_bytes = [ord(ch) for ch in source_text]
        cnf = f"(Witnora.SignedSerialization.decodeCNF {_lean_rows(raw)})"
        proof = (
            "import Witnora.ParityResidual\n"
            "import Witnora.DIMACSDocument\n"
            "import Witnora.SignedSerialization\n"
            "set_option maxRecDepth 16384\n"
            "set_option maxHeartbeats 0\n"
            "namespace WitnoraCompressionCheck\n"
            f"def rootOf (v : Nat) : Nat := {root_expr}\n"
            f"def parityOffset (v : Nat) : Bool := {offset_expr}\n"
            f"def sourcePath (v : Nat) : List (Nat × Bool) := {path_expr}\n"
            "example : Witnora.DIMACSDocument.parseDocument "
            f"{source_bytes} = some (Witnora.DIMACSTokens.serialize {_lean_rows(raw)}) "
            "∧ ((∃ a, Witnora.G5Extraction.CNFHolds "
            f"{cnf} a) ↔ (∃ roots, Witnora.G5Extraction.CNFHolds "
            f"(Witnora.ParityResidual.substituteCNF rootOf parityOffset {cnf}) roots)) "
            "∧ (Witnora.ParityResidual.substituteCNF rootOf parityOffset "
            f"{cnf} = Witnora.SignedSerialization.decodeCNF {_lean_rows(rewritten)}) := by\n"
            "  have hpaths : Witnora.ParityCompression.ValidSourcePaths "
            f"{cnf} rootOf parityOffset sourcePath := by\n"
            "    intro v\n"
            + _paths_proof(vertices)
            + "  constructor\n"
            "  · decide\n"
            "  · constructor\n"
            "    · exact Witnora.ParityResidual.source_iff_rewritten_residual "
            f"{cnf} rootOf parityOffset sourcePath hpaths\n"
            "    · decide\n"
            "end WitnoraCompressionCheck\n"
        )
        formal = root / "formal"
        if not (formal / "lakefile.toml").is_file():
            raise ValueError("Lean project unavailable")
        with TemporaryDirectory(prefix="witnora_compression_") as temp:
            file = Path(temp) / "CompressionProof.lean"
            file.write_text(proof, encoding="utf-8")
            result = subprocess.run(
                ["lake", "env", "lean", str(file)], cwd=formal,
                capture_output=True, text=True, timeout=timeout_seconds,
                check=False,
            )
        if result.returncode:
            raise ValueError("Lean rejected residual certificate: " +
                             (result.stdout + result.stderr)[-1200:])
        return {
            "verified": True,
            "lean_formal_status": "LEAN_SOURCE_PARITY_RESIDUAL_EQUIVALENT",
            "proof_source_sha256": sha256(proof.encode("utf-8")).hexdigest(),
            "normalization_proof_source_sha256": norm.get("proof_source_sha256"),
            "residual_normalization_proof_sha256": normalized_residual.get("proof_source_sha256"),
            "input_vertices": candidate["input_vertices"],
            "component_count": candidate["component_count"],
            "root_variables_saved": candidate["root_variables_saved"],
            "residual_clauses": residual.num_clauses,
            "claim_boundary": "source-backed per-instance CNF SAT equivalence; speed and novelty unproved",
        }
    except (ValueError, TypeError, KeyError, IndexError, AttributeError,
            OSError, subprocess.TimeoutExpired) as exc:
        return {**failure, "reason": type(exc).__name__, "detail": str(exc)[-1200:]}
