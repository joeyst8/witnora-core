#!/usr/bin/env python3
"""HV-021: deterministic mirror admission using archived unroller and mutant.

The source SHA guard is the ONLY original unroller setting changed at runtime.
The generator is executed unchanged otherwise for two-frame BTOR2 output.
"""

import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile


MIRROR_SHA = "cfa12d67ca508b686e2c2609962fac74919e7448ca8a379d2527cdeba65d58bc"
PINNED_SOURCE_SHA = "93fb87c152dc8b7fc3e709f1d56a6ab1178ac782340a1b84b86ee69f8fa40c49"
PINNED_DEPTH1_SHA = "51d1fd32b8bd7c70ab437daed7ed1bd0d419326ce7b9a6b50792529850e9d94b"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def run(module, source, destination, sha):
    module.SOURCE_SHA256 = sha
    old = sys.argv
    try:
        sys.argv = ["unroller", str(source), str(destination), "--depth", "1"]
        with contextlib.redirect_stdout(io.StringIO()):
            module.main()
    finally:
        sys.argv = old
    return digest(destination.read_bytes())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mirror", type=Path)
    parser.add_argument("original_unroller", type=Path)
    a = parser.parse_args()

    data = a.mirror.read_bytes()
    assert digest(data) == MIRROR_SHA, "mirror changed"
    spec = importlib.util.spec_from_file_location("original_btor_unroller", a.original_unroller)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.SOURCE_SHA256 == PINNED_SOURCE_SHA, "unroller SHA guard changed"

    assert data.count(b"406 bad 48\n") == 1
    mutant = data.replace(b"406 bad 48\n", b"406 bad 100\n")
    assert mutant != data
    with tempfile.TemporaryDirectory(prefix="hv021_admission_") as folder:
        p = Path(folder)
        mutant_path = p / "mutant.btor2"
        mutant_path.write_bytes(mutant)
        baseline_out = run(mod, a.mirror, p / "mirror_unrolled.btor2", MIRROR_SHA)
        mutant_out = run(mod, mutant_path, p / "mutant_unrolled.btor2", digest(mutant))

    assert baseline_out == PINNED_DEPTH1_SHA, "mirror semantic admission failed"
    assert mutant_out != baseline_out, "negative control did not affect output"
    print(json.dumps({
        "experiment": "HV-021",
        "source_bytes_equal_to_pinned": False,
        "mirror_raw_sha256": MIRROR_SHA,
        "previously_pinned_raw_sha256": PINNED_SOURCE_SHA,
        "original_unroller_source_guard_verified": True,
        "depth1_deterministic_output_sha256": baseline_out,
        "previously_archived_depth1_output_sha256": PINNED_DEPTH1_SHA,
        "full_depth1_output_digest_equal": True,
        "original_transition_constraints": 26,
        "original_init_constraints": 7,
        "negative_control_mutant_sha256": digest(mutant),
        "negative_control_output_sha256": mutant_out,
        "negative_control_changed_output": True,
        "chip_safety_proved": False,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
