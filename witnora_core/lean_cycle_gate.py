"""Source-bound Lean verifier for discovered odd-parity XOR cycles.

A Python-discovered cycle is untrusted evidence. The Lean kernel independently
checks each source CNF pattern, endpoint closure, and odd parity before
granting its narrow UNSAT attestation.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import subprocess
from typing import Any

from .cnf import CNFFormula
from .cycle_discovery import discover_odd_xor_cycle
from .lean_cnf_gate import _lean_rows, _strict_rows


def verify_odd_cycle_with_lean(
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
            raise ValueError("unsupported ASCII document")
        if (type(source_tokens) not in (list, tuple) or
                any(type(x) is not int for x in source_tokens)):
            raise ValueError("invalid source token stream")
        raw = _lean_rows(_strict_rows(raw_clauses))
        candidate = discover_odd_xor_cycle(formula)
        if candidate is None:
            return {**failure, "reason": "NO_ODD_CYCLE_FOUND"}
        start = candidate["start"]
        if type(start) is not int or start <= 0:
            raise ValueError("invalid start")
        steps = candidate["steps"]
        if not isinstance(steps, list) or not steps:
            raise ValueError("empty cycle")
        current, odd = start, 0
        rendered = []
        for item in steps:
            nxt, rhs = item["next"], item["rhs"]
            if type(nxt) is not int or nxt <= 0 or type(rhs) is not int or rhs not in (0, 1):
                raise ValueError("invalid cycle step")
            rendered.append(f"({nxt}, {'true' if rhs else 'false'})")
            current = nxt
            odd ^= rhs
        if current != start or odd != 1:
            raise ValueError("cycle is not closed and odd")
        encoded_steps = "[" + ", ".join(rendered) + "]"
        source_bytes = [ord(ch) for ch in source_text]
        proof = (
            "import Witnora.CycleParity\n"
            "import Witnora.DIMACSDocument\n"
            "import Witnora.SignedSerialization\n"
            "set_option maxRecDepth 16384\n"
            "set_option maxHeartbeats 0\n"
            "example : Witnora.DIMACSTokens.serialize "
            f"{raw} = {list(source_tokens)} := by decide\n"
            "example : Witnora.DIMACSDocument.parseDocument "
            f"{source_bytes} = some (Witnora.DIMACSTokens.serialize {raw}) "
            "∧ ¬ ∃ a, Witnora.SignedSerialization.signedCNFHolds "
            f"{raw} a := by\n"
            "  constructor\n"
            "  · decide\n"
            "  · intro h\n"
            "    apply Witnora.CycleParity.closedWalk_unsat "
            f"(Witnora.SignedSerialization.decodeCNF {raw}) "
            f"{start} {encoded_steps} (by decide) (by decide) (by decide)\n"
            "    rcases h with ⟨a, ha⟩\n"
            "    exact ⟨a, (Witnora.SignedSerialization.signedCNFHolds_iff "
            f"{raw} a).mp ha⟩\n"
        )
        root = Path(project_root) if project_root is not None else Path(__file__).resolve().parents[1]
        formal_dir = root / "formal"
        if not (formal_dir / "lakefile.toml").is_file():
            raise ValueError("Lean project unavailable")
        with TemporaryDirectory(prefix="witnora_cycle_source_") as temp:
            path = Path(temp) / "CycleProof.lean"
            path.write_text(proof, encoding="utf-8")
            result = subprocess.run(
                ["lake", "env", "lean", str(path)], cwd=formal_dir,
                capture_output=True, text=True, check=False,
                timeout=timeout_seconds,
            )
        if result.returncode != 0:
            raise ValueError("Lean rejected closed walk: " + (result.stdout + result.stderr)[-1100:])
        return {
            "verified": True,
            "lean_formal_status": "LEAN_SOURCE_CYCLE_UNSAT_VERIFIED",
            "operator": "ODD_XOR_CYCLE",
            "cycle_length": len(steps),
            "proof_source_sha256": sha256(proof.encode("utf-8")).hexdigest(),
            "claim_boundary": "source-backed UNSAT for this checked cycle; novelty and performance unproved",
        }
    except (ValueError, TypeError, IndexError, KeyError, OSError, subprocess.TimeoutExpired) as exc:
        return {**failure, "reason": type(exc).__name__, "detail": str(exc)[-1100:]}
