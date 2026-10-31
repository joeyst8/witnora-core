"""Generate four baseline and four structured Python-to-Lean certificates."""
from __future__ import annotations

from pathlib import Path

from witnora_core.ascii_certificate_adversarial import generate_structured_cases
from witnora_core.lean_ascii_certificate_export import emit_ascii_lean
from witnora_core.lean_color_certificate_export import generate_default_cases


def main():
    source = emit_ascii_lean(generate_default_cases() + generate_structured_cases())
    path = Path("formal/Witnora/GeneratedAdversarialAsciiCertificates.lean")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")
    print({"cases": 8, "source_bytes": len(source.encode("utf-8")), "output": str(path)})


if __name__ == "__main__":
    main()
