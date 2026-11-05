"""Fail-closed, source-bound Lean verification of parity residual compression.

Python's component graph, paths, root offsets and residual rows are untrusted.
The Lean kernel checks every emitted source path, literal substitution and
SAT-equivalence theorem. The canonical residual is separately checked by the
existing Lean CNF normalization gate. This is per-instance, not CPython
language refinement or an operator-performance claim.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

from .cnf import CNFFormula
from .lean_g5_gate import (_compile_dag, _serialize_rows, _serialize_cnf,
                           verify_g5_certificate_with_lean)
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
            return indent + "simp [rootOf, parityOffset, sourcePath, " + conds + ", " + "Witnora.CycleParity.checkSteps, Witnora.CycleParity.lastVertex, " + "Witnora.CycleParity.rhsParity]\n"
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
    residual_g5_certificate: object | None = None,
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
        g5_proof_digest = None
        if residual_g5_certificate is not None:
            g5check = verify_g5_certificate_with_lean(
                residual, residual_g5_certificate,
                raw_clauses=rewritten,
                timeout_seconds=timeout_seconds,
                project_root=root,
            )
            if (g5check.get("verified") is not True
                    or g5check.get("lean_formal_status") != "LEAN_VERIFIED"
                    or g5check.get("source_normalization_verified") is not True):
                raise ValueError("G5 residual certificate rejected")
            data = (residual_g5_certificate.to_dict()
                    if hasattr(residual_g5_certificate, "to_dict")
                    else residual_g5_certificate)
            trace = data.get("gaussian_elimination_trace")
            if not isinstance(trace, list) or not trace or not isinstance(trace[0], dict):
                raise ValueError("G5 initial trace unavailable")
            initial = trace[0].get("rows")
            if not isinstance(initial, list):
                raise ValueError("G5 initial rows unavailable")
            bound = residual.max_var + 1
            rows_expr = _serialize_rows(initial)
            dag_expr = _compile_dag(initial, data.get("row_operations"))
            raw_rewrite = _lean_rows(rewritten)
            canonical_expr = _serialize_cnf(residual)
            composed = (
                "example : ¬ ∃ a, Witnora.G5Extraction.CNFHolds "
                f"{cnf} a := by\n"
                "  have hpaths : Witnora.ParityCompression.ValidSourcePaths "
                f"{cnf} rootOf parityOffset sourcePath := by\n"
                "    intro v\n"
                + _paths_proof(vertices)
                + "  have hrewrite : Witnora.ParityResidual.substituteCNF "
                f"rootOf parityOffset {cnf} = "
                f"Witnora.SignedSerialization.decodeCNF {raw_rewrite} := by decide\n"
                + "  have hg5 : Witnora.SourceG5.checkRawG5 "
                f"{bound} {raw_rewrite} {rows_expr} {dag_expr} = true := by\n"
                "    unfold Witnora.SourceG5.checkRawG5\n"
                "    have hcanonical : Witnora.CNFSorted.canonicalize "
                f"(Witnora.SignedSerialization.decodeCNF {raw_rewrite}) = "
                f"{canonical_expr} := by decide\n"
                "    rw [hcanonical]\n"
                "    decide\n"
                "  exact Witnora.CompressedG5.residual_g5_implies_original_unsat "
                f"{cnf} rootOf parityOffset sourcePath hpaths {raw_rewrite} "
                f"hrewrite {bound} {rows_expr} {dag_expr} hg5\n"
            )
            proof = "import Witnora.CompressedG5\n" + proof.replace(
                "end WitnoraCompressionCheck\n", composed + "end WitnoraCompressionCheck\n")
            g5_proof_digest = g5check.get("proof_source_sha256")
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
            "residual_formula_sha256": residual.formula_hash,
            "component_certificate_sha256": sha256(json.dumps(candidate, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest(),
            "residual_g5_proof_source_sha256": g5_proof_digest,
            "original_unsat_kernel_verified": g5_proof_digest is not None,
            "claim_boundary": "source-backed SAT equivalence plus original UNSAT only if G5 residual composition was accepted",
        }
    except (ValueError, TypeError, KeyError, IndexError, AttributeError,
            OSError, subprocess.TimeoutExpired) as exc:
        return {**failure, "reason": type(exc).__name__, "detail": str(exc)[-1200:]}
