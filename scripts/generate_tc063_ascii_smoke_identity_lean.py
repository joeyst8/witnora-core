"""Ensure the checked Lean smoke theorem uses the exact committed DIMACS bytes.

The generated Lean obligation fails if anyone edits the source fixture
without updating and re-verifying the proof's literal input bytes.
"""

from pathlib import Path

FIXTURE = Path("fixtures/tc063_ascii_two_cut_unsat_smoke.cnf")


def emit() -> str:
    data = FIXTURE.read_bytes()
    values = ", ".join(str(b) for b in data)
    return (
        "import Witnora.TC063AsciiTwoCutSmoke\n"
        "namespace Witnora.GeneratedTC063SmokeFileIdentity\n"
        "set_option maxRecDepth 8192\n"
        "set_option maxHeartbeats 8000000\n"
        f"example : Witnora.TC063AsciiTwoCutSmoke.smokeSource = [{values}] := by decide\n"
        "end Witnora.GeneratedTC063SmokeFileIdentity\n"
    )


if __name__ == "__main__":
    print(emit(), end="")
