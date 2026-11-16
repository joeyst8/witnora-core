# HV-003 — Published optimized-circuit equivalence gate

Status: **real public hardware benchmark admitted and independently checked;
no new Witnora solver or scientific breakthrough**. Date: 2026-11-10.

## Source and exact scope

Public dataset: `lsils/sim-LSV_exp`, pinned commit
`071c4a9998eb5660c8f955c29e905315bdad2da2`, with pairs of combinational
AIGER circuits at paths `benchmarks_ifraig-s/NAME.aig` (reference) and
`benchmarks_dc2syn2/NAME.aig` (further optimized), as documented in the
repository's README: https://github.com/lsils/sim-LSV_exp. The pairs
originate from the IWLS'05 logic benchmarks and are used in published
simulation-guided synthesis/verification research (Lee et al., IWLS 2020,
https://arxiv.org/abs/2007.02579). This is a **real benchmark source** with
named hardware blocks, **not** proof of deployment in manufactured chips.

The original and optimized AIG files have identical primary input/output
counts and zero latches. We check **combinational** behavior, not unbounded
sequential correctness. The exact source commits and SHA-256 input digests
are in `research/results/hv003_published_circuit_miters.json`.

### Necessary lossless format normalization

The archived AIGER files carry trailing ABC metadata that this version of
`aigmiter` rejects as an unexpected constraint-symbol prefix (`c `).
`research/hv003_strip_aiger_suffix.rs` strictly parses a **basic binary AIGER
`aig M I 0 O A`** header, the exact `O` output-literal lines, and two delta
varints per each of the `A` AND gates. It writes this complete prefix
*byte for byte* and omits only the trailer. Nonzero latches, noncanonical
variable counts, or extended AIGER properties are rejected (fail closed).
`cmp -n` confirmed that **all ten normalized files** are byte-identical
prefixes of their respective archived sources. This is a compatibility
fix, not logic optimization or claimed research novelty.

Miter and CNF tools: `arminbiere/aiger` commit
`039ec1a2cc37d3093ac35c4b6df65336b346f409` (`aigmiter` followed
by the XOR/ITE-aware `aigtocnf`). The miter asserts at least one mismatched
output for the same primary inputs. UNSAT means the encoded circuits are
equivalent; a SAT model is a possible counterexample subject to input/output
semantics and independent validation. Source-to-CNF equivalence has **not**
been formally certified at the tool-implementation level; independently
checked SAT proofs certify the generated *CNF*, while independent ABC CEC
checks establish a second source-circuit-level baseline.

## Exploratory baseline: exact matched hardware tasks

Kissat 4.0.4 commit `8af8e56f174b778aef3aa45af9f739b2a5f492c2`;
`--time=10 -n` on the CNFs; ABC commit
`25d4ee221b2a9ab5124f3a222bcdf6f922d3d8a3`;
`cec -n -T 10 REF.aig OPT.aig` using the normalized AIG pair, default
FRAIG+SAT mode. All source pairs use positional I/O matching. Every row
below is a **single exploratory run**; machines were not isolated from
compilation/other tasks, so no significance should be inferred from timing.

| Hardware block | Reference / optimized ANDs | CNF vars / clauses | Kissat 10s | Kissat conflicts | ABC CEC (reported s) | Independent UNSAT proof |
| --- | ---: | ---: | --- | ---: | --- | --- |
| `des_area` | 4,827 / 4,824 | 8,588 / 25,962 | UNSAT | 265,696 | equivalent, 0.43 | **DRAT VERIFIED** |
| `usb_funct` | 15,245 / 13,414 | 24,717 / 68,567 | UNSAT | 59,451 | equivalent, 2.62 | **DRAT VERIFIED** |
| `aes_core` | 21,441 / 23,362 | 38,138 / 116,371 | UNKNOWN at cutoff | 129,984 | equivalent, 4.41 | not produced |
| `pci_bridge32` | 22,521 / 16,392 | 31,333 / 83,163 | UNKNOWN at cutoff | 494,178 | equivalent, 3.48 | not produced |
| `RISC` | 73,789 / 61,900 | 121,977 / 338,754 | UNKNOWN at cutoff | 25,664 | equivalent, 30.51 | not produced |

Kissat's `UNKNOWN` here means an enforced 10-second cutoff, **not
non-equivalence**. ABC's `-T 10` is an *approximate internal runtime limit*;
it ran RISC for 30.51 reported seconds, so it must not be treated as having
the same hard 10-second cutoff. Kissat's reported process time is not the
entire verified pipeline, while ABC `cec` runs were not accompanied by
independently checked external proofs.

For `usb_funct` and `des_area`, Kissat generated UNSAT DRAT logs and
`marijnheule/drat-trim` pinned at
`2e3b2dc0ecf938addbd779d42877b6ed69d9a985` independently reported
**`s VERIFIED`** against the original generated CNFs. Proof-checking times
were 4.644 and 8.722 seconds, respectively. Their CNF/proof SHA-256 digests
are recorded in JSON; these large raw files are not vendored into GitHub.

### Known XOR/ITE encoding ablation

The exact same miter AIG was translated with (a) standard XOR/ITE-aware
encoding, (b) `aigtocnf --no-xor` preserving ITEs, and (c)
`aigtocnf --no-xor --no-ite`. All three are **preexisting** AIGER options.

| Circuit | Standard CNF vars / clauses; Kissat conflicts | No-XOR vars / clauses; conflicts | AND-only vars / clauses; conflicts |
| --- | --- | --- | --- |
| DES | 8,588 / 25,962; **265,696** UNSAT | 9,080 / 27,031; **183,144** UNSAT | 10,297 / 29,373; **223,605** UNSAT |
| USB | 24,717 / 68,567; **59,451** UNSAT | 30,179 / 78,590; **63,421** UNSAT | 37,191 / 96,093; **57,703** UNSAT |
| AES | 38,138 / 116,371; **129,984** UNKNOWN | 43,418 / 128,331; **105,206** UNKNOWN | 47,587 / 137,601; **105,190** UNKNOWN |

The standard encoding uses fewer variables/clauses in these cases, but
**does not consistently reduce conflicts or solve more cases** under this
small cutoff. This is a *negative/ambiguous result about a known encoding
choice*, not evidence for a novel parity method. Do not interpret fewer
conflicts as proof-inclusive runtime improvement or solver dominance.

## Reproduction (tools already used in this record)

```sh
rustc --edition=2021 -O research/hv003_strip_aiger_suffix.rs -o /tmp/hv003-strip
/tmp/hv003-strip benchmarks_ifraig-s/usb_funct.aig /tmp/hv003-usb-ref.aig
/tmp/hv003-strip benchmarks_dc2syn2/usb_funct.aig /tmp/hv003-usb-opt.aig
aigmiter -o /tmp/hv003-usb-miter.aig /tmp/hv003-usb-ref.aig /tmp/hv003-usb-opt.aig
aigtocnf /tmp/hv003-usb-miter.aig /tmp/hv003-usb.cnf
kissat --time=30 -n /tmp/hv003-usb.cnf /tmp/hv003-usb.drat
drat-trim /tmp/hv003-usb.cnf /tmp/hv003-usb.drat
abc -c 'cec -n -T 10 /tmp/hv003-usb-ref.aig /tmp/hv003-usb-opt.aig'
```

Paths in the example are relative to the checked-out source corpus (for
the first two commands) or the Witnora repository (for the Rust source);
the binaries should be on the caller's `PATH` and pinned as above.
`kissat`'s exit code 20 means UNSAT, not failure.

## Predeclared next gate and scientific boundary

Holdout hardware pairs **`tv80`, `spi`, `systemcaes`** were selected and
their raw source SHA-256 hashes fixed **after the above pilot, before any
new solver algorithm or parameter tuning**. They were **not normalized,
miterized, solved, or benchmarked** here. Hashes in JSON.

Any future Witnora parity/inference mechanism must first document exact
differences from clausal congruence closure (Biere et al., SAT 2024,
https://doi.org/10.4230/LIPIcs.SAT.2024.6), SAT sweeping, circuit-native
SAT, and XOR-aware miter mapping. Test it against **ABC CEC**, Kissat,
CaDiCaL, and strong settings for the same task. Compare verified solves,
full proof-inclusive time, memory and ablations on disjoint holdouts.
Reject claims based solely on CNF size, extracted XOR count or conflicts.

**Current conclusion:** Witnora now has a verified real-circuit benchmark
gate that exposes nontrivial SAT search. ABC's established circuit-level
method already handles all five pairs, often faster. **No Witnora speedup,
new SAT theorem, or general-complexity implication has been established.**
