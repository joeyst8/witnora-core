"""Read-only extraction of public random 2-XNF formulas and paired outcomes.

Upstream formula archives: j-danner/2xnf_sat_solving, pinned in WU-012 doc.
Upstream timing database: msoos/xnf-tests, pinned in WU-011 doc.
The *Rust* consumer parses formula grammar and computes all structural features;
this bridge only matches original named instances and preserves XNF lines.
"""

import argparse
import sqlite3
import sys
import zipfile


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("sqlite_db")
    ap.add_argument("rand_zip")
    ap.add_argument("rand_sat_zip")
    args = ap.parse_args()

    with sqlite3.connect(f"file:{args.sqlite_db}?mode=ro", uri=True) as db:
        rows = db.execute(
            """SELECT a.family, a.instance, a.solved, b.solved,
                      a.result, b.result
               FROM data a JOIN data b
                 ON a.family=b.family AND a.instance=b.instance
               WHERE a.solver='cms-improved' AND b.solver='xorcle'
                 AND a.family IN ('2xnf-rand','2xnf-rand_sat')
               ORDER BY a.family, a.instance"""
        ).fetchall()

    if len(rows) != 800 or len({(x[0], x[1]) for x in rows}) != 800:
        raise ValueError("expected 800 distinct random-family paired instances")

    archives = {}
    for family, filename, prefix in (
        ("2xnf-rand", args.rand_zip, "rand/"),
        ("2xnf-rand_sat", args.rand_sat_zip, "rand_sat/"),
    ):
        with zipfile.ZipFile(filename) as z:
            names = [name for name in z.namelist() if name.endswith(".xnf")]
            if len(names) != 400 or len(set(names)) != 400:
                raise ValueError(f"{family}: expected 400 distinct XNF files")
            entries = {}
            for name in names:
                if not name.startswith(prefix) or name.count("/") != 1:
                    raise ValueError(f"{family}: unexpected path {name}")
                instance = name[len(prefix):-4]
                body = z.read(name).decode("ascii")
                lines = [line.strip() for line in body.splitlines()
                         if line.strip() and not line.startswith("c ")]
                if not lines or any("\t" in line or "|" in line for line in lines):
                    raise ValueError(f"{family}: malformed XNF {name}")
                entries[instance] = "|".join(lines)
            archives[family] = entries

    print("family\tinstance\tcms_solved\txor_solved\tformula")
    seen = {family: set() for family in archives}
    for family, instance, cms, xor, cms_answer, xor_answer in rows:
        if cms not in (0, 1) or xor not in (0, 1):
            raise ValueError("invalid solved flag")
        if cms and xor and cms_answer != xor_answer:
            raise ValueError(f"{family}/{instance}: solver answers disagree")
        try:
            formula = archives[family][instance]
        except KeyError as exc:
            raise ValueError(f"missing formula: {family}/{instance}") from exc
        seen[family].add(instance)
        print(f"{family}\t{instance}\t{cms}\t{xor}\t{formula}")
    if any(set(archives[family]) != keys for family, keys in seen.items()):
        raise ValueError("original archive contains unmatched benchmark formulas")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, sqlite3.Error, zipfile.BadZipFile, UnicodeError) as exc:
        print(f"WU-012 export rejected source: {exc}", file=sys.stderr)
        sys.exit(2)
