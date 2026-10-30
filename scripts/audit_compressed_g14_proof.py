"""Adversarial real-Lean audit of the compressed G14 proof boundary.

This tests that a sound native certificate cannot make a corrupted final
Lean proof pass. It does not claim independence from Lean's own kernel.
"""
from __future__ import annotations

from dataclasses import replace
import re
import subprocess
from unittest.mock import patch

from witnora_core.cnf import CNFFormula
from witnora_core.lean_compressed_g14_gate import verify_compressed_g14_with_lean
from witnora_core.parity_compression import (
    compress_binary_xor_components, substitute_residual_formula,
)
from witnora_core.separator_affine_family_theorem import (
    build_separator_affine_certificate, make_separator_affine_instance,
)
from witnora_core.xor import canonical_xor_cnf_clauses


def main():
    base = make_separator_affine_instance("saf_unsat_cover_2")
    original = CNFFormula.from_raw_clauses(
        base.formula.to_clause_lists() +
        list(canonical_xor_cnf_clauses((100, 101), 0))
    )
    residual = substitute_residual_formula(
        original, compress_binary_xor_components(original)
    )
    certificate = build_separator_affine_certificate(
        replace(base, formula=residual, instance_id="audit_compressed_g14")
    )
    raw = original.to_clause_lists()
    tokens = [lit for clause in raw for lit in (*clause, 0)]
    evidence = dict(
        raw_clauses=raw, source_tokens=tokens,
        source_spellings=list(map(str, tokens)),
        source_text=original.canonical_dimacs(),
        timeout_seconds=180,
    )
    clean = verify_compressed_g14_with_lean(original, certificate, **evidence)
    if not clean.get("original_unsat_kernel_verified"):
        raise AssertionError(f"clean proof must pass: {clean}")
    print("clean proof: Lean accepted")

    real_run = subprocess.run
    attacks = (
        (
            "source_path_erasure",
            r"(?m)^def sourcePath .*$",
            "def sourcePath (v : Nat) : List (Nat × Bool) := []",
        ),
        (
            "selected_component_erasure",
            r"(?m)^def certSelected .*$",
            "def certSelected (branch : List (Nat × Bool)) : Witnora.Concrete.CNF := []",
        ),
    )
    for name, pattern, replacement in attacks:
        observed = {"intercepted": False}
        def tamper(argv, **kwargs):
            target = argv[-1]
            if str(target).endswith("CompressedG14Proof.lean"):
                from pathlib import Path
                proof = Path(target)
                before = proof.read_text(encoding="utf-8")
                after, count = re.subn(pattern, replacement, before, count=1)
                if count != 1 or after == before:
                    raise AssertionError("intended Lean evidence was not changed")
                proof.write_text(after, encoding="utf-8")
                observed["intercepted"] = True
            return real_run(argv, **kwargs)
        with patch("witnora_core.lean_compressed_g14_gate.subprocess.run",
                   side_effect=tamper):
            result = verify_compressed_g14_with_lean(
                original, certificate, **evidence
            )
        if (not observed["intercepted"] or result.get("verified") is not False
                or result.get("original_unsat_kernel_verified") is True):
            raise AssertionError(f"{name} bypassed gate: {result}")
        print(f"{name}: rejected by real Lean gate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
