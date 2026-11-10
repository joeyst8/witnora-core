# WU-014 — new-seed XNF solver runs with independent SAT / UNSAT checks

**Status:** new real solver executions completed; baseline and certificate
costs measured; **no new Witnora solver speedup or complexity theorem**.

## Why this matters

WU-011–013 analyzed published solver results and falsified a proposed
input-only parity geometry feature. They did **not** run independent new
solvers. WU-014 is the first prospectively seeded XNF execution/certificate
pilot of this series. It measures source conversion, real wall time and
answer verification, not simulated nodes or retrospective timing replay.

## Established sources, build provenance, important limitations

- Xorcle from [Beame and Sun, SAT 2026](https://doi.org/10.4230/LIPIcs.SAT.2026.5):
  <https://github.com/glenn-sun/xorcle>, source commit
  `af93ea646a4237958e9925bc684dcd545e68de30`, version `0.2.0-dev`.
  Built release with GCC 14.2.0, CMake 3.31.10, gf2 dependency
  `0b09e44fd2c6615a6a1958c480650e207703b84c`.
- CryptoMiniSat: <https://github.com/msoos/cryptominisat>, source commit
  `97c6efeae45d93c45d2ebc3e4e83c2014c79513d`, version 5.18.0.
  Release build, statically linked, native parity/XOR input; downloaded
  pinned upstream CaDiCaL/CaDiBaCk CMake dependencies.
- CryptoMiniSat CNF-XOR preprocessing is the independent Xorcle upstream
  `tools/xnf_convert.py cnf-xor`. Both solvers receive semantically
  equivalent input; **its measured conversion time is charged to CMS**.
  Xorcle reads the native 2-XNF without conversion.
- UNSAT verifier: separately compiled `cake_xlrup` from
  <https://github.com/meelgroup/frat-xor>, commit
  `18cd6bc17af10a9891c10a846ce966166f9fe0dc`. Its independently
  checkable output `s VERIFIED UNSAT` is **required** for our certified
  CryptoMiniSat UNSAT subset. Xorcle native LRUP(⊕) is separately checked
  by its published `tools/check_lrup_parity.py`.
- **Upstream test caveat:** Xorcle's release build and proof roundtrip pass,
  but its upstream 268-case C++ unit suite has **267 passing / 1 failing**:
  `test_random.cpp`'s hard-coded `random_int(rng,2)` bit sequence disagrees
  with the standard-library `std::uniform_int_distribution` output here
  (51 assertions in that case). This may be compiler/library portability,
  not a solver-correctness failure; we have **not** repaired or ignored it.
  Our selected runs use default `--phase=falsify`, and final SAT models and
  selected UNSAT proofs are checked independently. The CMS source build
  was configured with upstream tests disabled; we do not claim they passed.

## Original, fresh, independently generated inputs

The included **Rust** generator `wu014_generate_xnf.rs` samples independent,
uniformly random *nonempty* dense GF(2) variable supports and independent
signs. Each formula has `n` variables, `3n` clauses and exactly two affine
linerals per clause. For planted variants, the generator first chooses a
random witness and flips one parity constant if neither side is satisfied;
every planted witness is rechecked by the benchmark harness before any
solver starts. No Boolean assignment enumeration is performed.

This follows the **distributional description** in
`j-danner/2xnf_sat_solving/benchmark/rand/README.md`, but it is **not**
the original unpublished generator or a bit-for-bit replacement. Thus this
is a *new synthetic family with comparable features*, not a literal
replication of the exact source benchmark distribution. Results do not
generalize to arbitrary industrial SAT or original Ascon XNF.

- Main independent sample: `n=28..35`, two seeds per `n` and family,
  32 input formulae, base seed `910001`.
  SHA-256 of reproducible `manifest.tsv`:
  `3d2974876e85d3057bf3ada88974f7786422a82cf245a45f6a82725696c2fe73`.
- Easy calibration sample: `n=21..23`, two seeds per `n` and family,
  12 input formulae, base seed `910002`.
  SHA-256 of `manifest.tsv`:
  `2d0363f7cda11551cef722361c220843912e08ec1ff3aa013eea6f771ce8dfc3`.
- Each input's seed is deterministically
  `BASE + (n << 32) + 2*index + planted_bit` in the code.
  Individual seeds/witness bitsets and all per-run CSV records are preserved
  under `research_data/wu014/`. The 44 large input formulae can be regenerated;
  they are not embedded in the Git history.

## Actual wall-clock pilot outcomes

Both solvers executed **serially**, with individually enforced wall-clock
deadlines and no concurrent competing benchmark process. CMS's end-to-end
score includes the independently measured XNF→CNF-XOR conversion cost.
Timeouts are **right-censored**, not claimed to have solved in T seconds.

| Corpus / deadline | Xorcle SAT | Xorcle UNSAT | Xorcle timeout | CMS SAT | CMS UNSAT | CMS timeout |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Main 32, 2s (first run) | 0 | 0 | 32 | 6 | 2 | 24 |
| Main 32, 2s (repeat) | 0 | 0 | 32 | 6 | 1 | 25 |
| First eight main (n28–29), 10s | 0 | 0 | 8 | 4 | 4 | 0 |
| Easy controls (n21–23), 2s | 6 | 4 | 2 | 6 | 6 | 0 |

The first/repeated 2s runs disagree on **one borderline CMS case**:
`unplanted n28 seed 120259994289`, observed at approximately **1.974s**
in the first run (UNSAT) and **2.004s** in the second (TIMEOUT).
This is direct evidence that single-run hard cutoff counts are noisy;
we retain both original per-instance result files and make no robust
ranking claim from these small samples. The easy controls show the
Xorcle build **does** produce SAT and UNSAT results on actual fresh XNF;
the n28..35 timeouts are not evidence of a universally broken solver.

**SAT validity:** all SAT statuses above were accompanied by solver-provided
assignment vectors evaluated independently against **every original XNF
clause**, including the original variables only (auxiliary CMS parity
variables do not substitute for checking the XNF). Planted witnesses are
separately validated. No mismatched SAT model was accepted.

## Independently certified UNSAT and measured certificate cost

For all four no-proof CMS UNSAT cases at n28/29 in the 10s sample, we
reran the same binary with text **XLRUP proof generation**, then checked
the proof using separately compiled Cake XLRUP. All **four passed**.
This step is *not included* in the previous no-proof runtime totals.

The Xorcle converter's XCNF header counts ordinary clauses only;
Cake's header convention counts both CNF and XOR constraints. Included
`wu014_checker_xcnf.py` creates a separate format-normalized checker
input with **unchanged constraint sequence and literal signs**, making
the two source conventions compatible without modifying solver inputs.

| Original XNF | Text XLRUP size | Proof-generation time | Cake check time | Result |
| --- | ---: | ---: | ---: | --- |
| Unplanted n28 seed 120259994289 | 216,513,595 bytes | 3.214s | 7.856s | VERIFIED UNSAT |
| Unplanted n28 seed 120259994291 | 208,887,962 bytes | 3.112s | 7.271s | VERIFIED UNSAT |
| Unplanted n29 seed 124554961585 | 344,695,735 bytes | 5.075s | 10.360s | VERIFIED UNSAT |
| Unplanted n29 seed 124554961587 | 336,857,542 bytes | 4.839s | 10.515s | VERIFIED UNSAT |

**Equal-budget caveat:** the 10-second comparison above counts the
*no-proof answer* only. With proof rerun and external checker, the four
text-certificate pipelines each exceed ten seconds even before minor
wrapper/format-normalization overhead: including the original measured
XNF→CNF-XOR conversion, their respective totals are approximately
**11.102s, 10.418s, 15.467s, and 15.389s**. Thus the table's 8/8 CMS
answers at 10s must **not** be read as 8/8 *verified* answers under
the same 10-second total budget. The four SAT models were independently
checked and the four UNSAT answers eventually certified, under a
larger full-pipeline budget. No like-for-like 10-second certificate
success ranking is asserted.

As a known-format negative-control/engineering comparison, the first
n28 proof was also generated as **binary XLRUP** and checked with Cake:
97,820,541 bytes, 2.928s proof generation, 4.503s proof checking,
again `VERIFIED UNSAT`. Relative to its text counterpart, binary
serialization reduces size by ~54.8% and checking time by ~42.7% on
this one sample. On that same instance the binary proof+check+conversion
total was approximately **7.462s**, versus **11.102s** in text (and
2.026s for the initial unverified solve). This is an independent
*rerun*, not a same-run change of serialization with all other
conditions fixed. **Binary proof compression is already an established
technique**, not a Witnora discovery. Even compressed, verified output
remains expensive enough to matter in end-to-end solver design.

For independent native-XNF confirmation, the newly generated unplanted
`n=21, seed=90195223218` was rerun through Xorcle with
`--compact=false --proof=...`. It returned UNSAT and its LRUP(⊕) proof
passed the separate Python checker (`1962` learned proof lines checked).

## Reproduction and gates

Build both pinned upstream solvers and the Cake checker as documented in
their respective repositories. From Witnora root, generate input datasets:

```sh
cargo run --release --manifest-path rust/witnora-ve/Cargo.toml \
  --bin wu014_generate_xnf -- /tmp/wu014-fresh 28 35 2 910001
cargo run --release --manifest-path rust/witnora-ve/Cargo.toml \
  --bin wu014_generate_xnf -- /tmp/wu014-easy 21 23 2 910002
```

The timed pilot uses explicitly supplied paths to the two upstream
executables and Xorcle's conversion script (no subprocess downloads):

```sh
python3 scripts/wu014_real_solver_pilot.py \
  --instances /tmp/wu014-fresh \
  --xorcle /path/to/xorcle/build/xorcle \
  --cms /path/to/cryptominisat/build/cryptominisat5 \
  --converter /path/to/xorcle/tools/xnf_convert.py \
  --timeout 2 --results /tmp/wu014-first.csv

python3 -m unittest -v scripts/test_wu014_real_solver_pilot.py
cargo test --release --manifest-path rust/witnora-ve/Cargo.toml --all-targets
```

For UNSAT verification, use `scripts/wu014_certify_cms_unsat.py` with
the no-proof pilot CSV, CMS, Cake, the normalizer, and a separate proof
time limit. `--proof-mode 1` is textual and `2` is binary. The harness
records proof bytes, hashes, generation and check timings, and fails
when any selected UNSAT proof cannot be independently verified.

## Outcome and next research gate

- **Measured:** Xorcle's native constraint handling and CryptoMiniSat's
  CNF-XOR path differ strongly on this new dense random synthetic family
  under short budgets. The result is *not* a proof of broad superiority.
- **Measured:** published proof formats create nontrivial CPU, storage,
  and checker costs. Counting only solve-time can make a verified pipeline
  appear much faster than it really is.
- **Negative result:** no new Witnora technique has yet reduced actual
  runtime on this family. The WU-012 local parity-cancellation predictor
  did not pass an independent evidence gate.
- **WU-015 gate:** profile where native XNF CDCL spends time (matrix basis,
  watch/propagation, proof construction) using source instrumentation,
  propose **one precisely specified, certified transformation**, and
  compare it to these untouched solver versions on additional *held-out*
  generator seeds. Measure solution/proof production, independent proof
  checking, RAM, and conversion together. Reject it if cost-adjusted
  verified time or success coverage fails to improve.

Nothing here implies P=NP, general-purpose polynomial SAT, a new proof
complexity theorem, or an independently established SAT breakthrough.
