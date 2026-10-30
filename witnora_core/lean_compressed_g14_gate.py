"""End-to-end original ASCII DIMACS -> compression -> G14 -> original UNSAT.

All Python-derived branch data are rechecked inside one Lean proposition. This
gate is opt-in and fail-closed; it does not assert universal CPython refinement.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

from .lean_cnf_gate import _lean_rows, _strict_rows
from .lean_g5_gate import _serialize_cnf, _serialize_rows, _compile_dag
from .lean_g14_gate import verify_g14_unsat_cover_with_lean
from .lean_parity_compression_gate import (
    _if_lookup, _paths_proof, verify_parity_compression_with_lean,
)
from .parity_compression import compress_binary_xor_components, substitute_residual_formula
from .separator_affine_family_theorem import (
    _all_assignments, _assignment_from_payload, _component_dicts,
    _condition_by_separator,
)


def verify_compressed_g14_with_lean(
    formula, g14_certificate, *, raw_clauses, source_tokens,
    source_spellings, source_text, timeout_seconds=180, project_root=None,
):
    failure = {"verified": False, "lean_formal_status": "NOT_LEAN_VERIFIED"}
    try:
        if type(source_text) is not str or not source_text.isascii() or len(source_text) > 65536:
            raise ValueError("unsupported source document")
        if type(source_tokens) not in (tuple, list) or any(type(n) is not int for n in source_tokens):
            raise ValueError("invalid source tokens")
        root = Path(project_root) if project_root is not None else Path(__file__).resolve().parents[1]
        raw = _strict_rows(raw_clauses)
        compression = verify_parity_compression_with_lean(
            formula, raw_clauses=raw, source_tokens=source_tokens,
            source_spellings=source_spellings, source_text=source_text,
            timeout_seconds=timeout_seconds, project_root=root,
        )
        if compression.get("verified") is not True:
            raise ValueError("source-bound compression rejected")
        candidate = compress_binary_xor_components(formula)
        residual = substitute_residual_formula(formula, candidate)
        if residual.formula_hash != compression.get("residual_formula_sha256"):
            raise ValueError("post-verification residual changed")
        roots, offsets, paths = (dict(candidate[k]) for k in ("roots", "offsets", "source_paths"))
        vertices = sorted(roots)
        rewritten = [
            [roots.get(abs(lit), abs(lit)) *
             (1 if (lit > 0) != bool(offsets.get(abs(lit), 0)) else -1)
             for lit in clause] for clause in raw
        ]
        g14 = verify_g14_unsat_cover_with_lean(
            residual, g14_certificate, raw_clauses=rewritten,
            timeout_seconds=timeout_seconds, project_root=root,
        )
        if (g14.get("verified") is not True or
                g14.get("lean_formal_status") != "LEAN_G5_COVER_AND_PARTITIONS_VERIFIED"):
            raise ValueError("residual G14 branch certificates rejected")
        data = (g14_certificate.to_dict() if hasattr(g14_certificate, "to_dict")
                else g14_certificate)
        sep = data["separator_variables"]
        components = _component_dicts(residual, sep)
        records = {r["assignment_id"]: r for r in data["separator_assignments"]}
        cover = data["unsat_cover"]["covering_unsat_component_per_assignment"]
        patterns, component_values, chosen_values = [], [], []
        bounds, rows, dags = [], [], []
        for i, assignment in enumerate(_all_assignments(sep), start=1):
            key = f"S{i}"
            rec = records[key]
            if _assignment_from_payload(rec["separator_assignment"]) != assignment:
                raise ValueError("G14 branch assignment changed")
            _, part_map, errors = _condition_by_separator(residual, assignment, components)
            if errors:
                raise ValueError("G14 decomposition changed")
            selected_id = cover[key]
            matching = [v for v in rec["component_records"] if v["component_id"] == selected_id]
            if len(matching) != 1 or selected_id not in part_map:
                raise ValueError("missing selected G5 component")
            parts = [part_map[c["component_id"]] for c in components]
            selected = part_map[selected_id]
            cert = matching[0]["affine_certificate"]
            trace = cert["gaussian_elimination_trace"]
            initial = trace[0]["rows"]
            pattern = "[" + ", ".join(
                f"({v}, {'true' if assignment[v] else 'false'})" for v in sorted(sep)
            ) + "]"
            patterns.append(pattern)
            component_values.append("[" + ", ".join(_serialize_cnf(p) for p in parts) + "]")
            chosen_values.append(_serialize_cnf(selected))
            bounds.append(str(selected.max_var + 1))
            rows.append(_serialize_rows(initial))
            dags.append(_compile_dag(initial, cert["row_operations"]))
        if not patterns or len(set(patterns)) != len(patterns):
            raise ValueError("invalid G14 branch coverage")

        def definition(name, typ, values, default):
            expr = default
            for pattern, value in reversed(list(zip(patterns, values))):
                expr = f"(if branch == {pattern} then {value} else {expr})"
            return f"def {name} (branch : List (Nat × Bool)) : {typ} := {expr}"

        root_expr = _if_lookup([(v, str(roots[v])) for v in vertices], "v")
        offset_expr = _if_lookup([(v, "true" if offsets[v] else "false")
                                  for v in vertices], "false")
        path_expr = _if_lookup([
            (v, "[" + ", ".join(f"({n}, {'true' if bit else 'false'})"
                                for n, bit in paths[v]) + "]") for v in vertices
        ], "[]")
        raw_expr = _lean_rows(raw)
        rewrite_expr = _lean_rows(rewritten)
        canonical_expr = _lean_rows(residual.to_clause_lists())
        original_cnf = f"(Witnora.SignedSerialization.decodeCNF {raw_expr})"
        enumerated = "[" + ", ".join(patterns) + "]"
        lines = [
            "import Witnora.CompressedG14",
            "import Witnora.DIMACSDocument",
            "import Witnora.DIMACSTokens",
            "set_option maxRecDepth 16384",
            "set_option maxHeartbeats 0",
            "namespace WitnoraCompressedG14Check",
            f"def rootOf (v : Nat) : Nat := {root_expr}",
            f"def parityOffset (v : Nat) : Bool := {offset_expr}",
            f"def sourcePath (v : Nat) : List (Nat × Bool) := {path_expr}",
            definition("certComponents", "List Witnora.Concrete.CNF", component_values, "[]"),
            definition("certSelected", "Witnora.Concrete.CNF", chosen_values, "[]"),
            definition("certBound", "Nat", bounds, "0"),
            definition("certRows", "List Witnora.G5Trace.Row", rows, "[]"),
            definition("certSteps", "List Witnora.G5Dag.XorRef", dags, "[]"),
            "example : Witnora.DIMACSDocument.parseDocument "
            f"{[ord(c) for c in source_text]} = some "
            f"(Witnora.DIMACSTokens.serialize {raw_expr}) ∧ "
            f"¬ ∃ a, Witnora.G5Extraction.CNFHolds {original_cnf} a := by",
            "  constructor",
            "  · decide",
            "  · have hpaths : Witnora.ParityCompression.ValidSourcePaths "
            f"{original_cnf} rootOf parityOffset sourcePath := by",
            "      intro v",
        ]
        lines[-1] += "\n" + _paths_proof(vertices).rstrip("\n")
        lines.extend([
            "    have hrewrite : Witnora.ParityResidual.substituteCNF "
            f"rootOf parityOffset {original_cnf} = "
            f"Witnora.SignedSerialization.decodeCNF {rewrite_expr} := by decide",
            "    have hcanonical : Witnora.CNFSorted.canonicalize "
            f"(Witnora.SignedSerialization.decodeCNF {rewrite_expr}) = "
            f"Witnora.SignedSerialization.decodeCNF {canonical_expr} := by decide",
        ])
        def cases_for(label, proposition):
            lines.append(f"    have {label} : {proposition} := by")
            lines.append("      intro branch hb")
            lines.append(f"      have he : Witnora.SeparatorAssignments.enumerate {sorted(sep)} = {enumerated} := by decide")
            lines.append("      rw [he] at hb")
            lines.append("      simp at hb")
            lines.append("      rcases hb with " + " | ".join(f"h{j}" for j in range(len(patterns))))
            for _ in patterns:
                lines.extend(["      · subst branch", "        decide"])
        prefix = f"∀ branch ∈ Witnora.SeparatorAssignments.enumerate {sorted(sep)}, "
        cases_for("hpart", prefix + "Witnora.ComponentPartition.checkPartition "
                  "(Witnora.Conditioning.conditionCNF "
                  "(Witnora.SeparatorAssignments.fixedOf branch) "
                  f"(Witnora.SignedSerialization.decodeCNF {canonical_expr})) "
                  "(certComponents branch) = true")
        cases_for("hselected", prefix + "certSelected branch ∈ certComponents branch")
        cases_for("hcert", prefix + "Witnora.SparseBridge.checkG5Closed "
                  "(certBound branch) (certSelected branch) "
                  "(certRows branch) (certSteps branch) = true")
        lines.append(
            "    exact Witnora.CompressedG14.residual_g14_implies_original_unsat "
            f"{original_cnf} rootOf parityOffset sourcePath hpaths "
            f"{rewrite_expr} hrewrite {canonical_expr} hcanonical {sorted(sep)} "
            "certComponents hpart certSelected hselected certBound certRows certSteps hcert"
        )
        lines.append("end WitnoraCompressedG14Check")
        proof = "\n".join(lines) + "\n"
        formal = root / "formal"
        if not (formal / "lakefile.toml").is_file():
            raise ValueError("Lean project unavailable")
        with TemporaryDirectory(prefix="witnora_compressed_g14_") as temp:
            path = Path(temp) / "CompressedG14Proof.lean"
            path.write_text(proof, encoding="utf-8")
            result = subprocess.run(
                ["lake", "env", "lean", str(path)], cwd=formal,
                capture_output=True, text=True, timeout=timeout_seconds, check=False,
            )
        if result.returncode:
            raise ValueError("combined Lean G14 proof rejected: " +
                             (result.stdout + result.stderr)[-1600:])
        return {
            "verified": True,
            "lean_formal_status": "LEAN_ORIGINAL_SOURCE_COMPRESSED_G14_UNSAT_VERIFIED",
            "original_unsat_kernel_verified": True,
            "proof_source_sha256": sha256(proof.encode("utf-8")).hexdigest(),
            "compression_proof_sha256": compression["proof_source_sha256"],
            "residual_g14_cover_proof_sha256": g14["partition_proof_source_sha256"],
            "source_document_verified": True,
            "branch_count": len(patterns),
        }
    except (ValueError, TypeError, KeyError, IndexError, AttributeError,
            OSError, subprocess.TimeoutExpired) as exc:
        return {**failure, "reason": type(exc).__name__, "detail": str(exc)[-1600:]}
