"""Optional drat-trim adapter for checking exported DRAT-style proofs."""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
from typing import Any


def find_drat_trim(provided_path: str | Path | None = None) -> str | None:
    """Return an executable drat-trim path from an explicit path or PATH."""

    if provided_path is not None:
        candidate = Path(provided_path)
        if candidate.is_file():
            return str(candidate)
        return None
    for name in ("drat-trim", "drat-trim.exe"):
        found = shutil.which(name)
        if found:
            return found
    return None


def run_drat_trim(
    original_dimacs_path: str | Path,
    proof_drat_path: str | Path,
    drat_trim_path: str | Path | None,
    timeout_seconds: float | None = None,
) -> dict[str, Any]:
    """Run drat-trim on an existing original DIMACS file and proof file.

    This adapter never solves a SAT instance. It only records whether the
    provided checker process accepted the already-exported proof.
    """

    if drat_trim_path is None:
        return {
            "external_checker": "NOT_RUN",
            "external_checker_path": None,
            "external_checker_ran": False,
            "external_checker_verified": False,
            "exit_code": None,
            "stdout": "",
            "stderr": "",
            "timeout": False,
            "error": None,
        }

    checker_path = str(drat_trim_path)
    try:
        proc = subprocess.run(
            [checker_path, str(original_dimacs_path), str(proof_drat_path)],
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout_seconds,
        )
        return {
            "external_checker": "DRAT_TRIM",
            "external_checker_path": checker_path,
            "external_checker_ran": True,
            "external_checker_verified": proc.returncode == 0,
            "exit_code": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "timeout": False,
            "error": None if proc.returncode == 0 else f"drat-trim exited with code {proc.returncode}",
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "external_checker": "DRAT_TRIM",
            "external_checker_path": checker_path,
            "external_checker_ran": True,
            "external_checker_verified": False,
            "exit_code": None,
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
            "timeout": True,
            "error": "drat-trim timed out",
        }
    except Exception as exc:
        return {
            "external_checker": "DRAT_TRIM",
            "external_checker_path": checker_path,
            "external_checker_ran": False,
            "external_checker_verified": False,
            "exit_code": None,
            "stdout": "",
            "stderr": "",
            "timeout": False,
            "error": str(exc),
        }
