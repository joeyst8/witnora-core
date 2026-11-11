# HV-006 predeclared development cohort (before solving)

Date: 2026-11-10. Status: **FROZEN selection and test protocol; results
not yet measured at time of this record**. This selection is a purposely
size-diverse development cohort, **not** a random or representative sample.

Source: `lsils/sim-LSV_exp` pinned revision
`071c4a9998eb5660c8f955c29e905315bdad2da2`, with positional
matched primary inputs and outputs, zero latches. Reference file
`benchmarks_ifraig-s/NAME.aig`; optimized file
`benchmarks_dc2syn2/NAME.aig`. Archived AIGER files include ABC metadata;
ABC's own reader accepts them. No source normalization or logic editing is
planned for this benchmark. Source SHA-256s follow.

| Design | Reference SHA-256 | Optimized SHA-256 |
| --- | --- | --- |
| `iwls05_i2c` | `c95b50c7cabfc6240690a2f3896d8d68cd69937169f40a3bd6567f148082b161` | `4de18d2e443b1f5e0c588dcd6b891c42780ec337ffe0e1969816cad384ce3e22` |
| `ss_pcm` | `c81c449772d9f5264a15d4a69ab086224e752bdecf881d2930fb0c3ac97e9687` | `4fe088d523f8ba705f740763501c716ab5ea5cfa9619602f5445aa1e3340b68f` |
| `systemcdes` | `17583f72a28d2f802004bbb293a0206145a3f65ea4dc5460bacec1a7103e4e4e` | `6fcc64eb68fd945fcf6f03cbb444db06d9af32c7dad01f76fc2b0db238413526` |
| `ac97_ctrl` | `608c45f2ef793d18a99a5dcfef6e4a4b5d9ad95f73d93b3cf6c5af70c60b2386` | `3d3caa873f086cd388232a3950b1142a2f01023a7073fb149357ed059c2c18fb` |
| `DMA` | `af8618f434123dabcaeb181d525bbdb9cdc72d88615066f24d5ebca504ba85de` | `db03bb56d2c955b3b6952837672f2e83627122d0873ac9f75ac0ef5dcf1f33ab` |
| `DSP` | `9f3a8317b26f990424bf14cc0221f23f0a6a2fd304c6fc4f65e4818f579639c5` | `fa30a2233dd0b9420c34ed9a5c222dde8b5356301d5ae53de1161fc4b6ce39dc` |
| `des_perf` | `149bbac4c99566a7104efbb4df453b0754a7db7ef31b0198493626a7772e22d1` | `2a94a8f354c34f5893657ba6c49c56cce9dd07de78c82c527ffd92c00375b894` |
| `wb_conmax` | `a22d48ee6ab9a35c23942a3edca7e6fad2b750ced797edb7153443a88cab0ec0` | `a49959c1817c95735be707eeb4b6379a15b0b23aa066bf05396c902677f0d45e` |
| `ethernet` | `6695eeb807ab06903b3daf993d49f1539d87b63b7cec349d6a6848778b7a30ff` | `d3a9f90950a18c93071f31e23a46b35887e80cb350b599a58b6bace15896a2f1` |
| `vga_lcd` | `43d59b319e1dcb5b48f56c0a1be0ef31b22626c3681f400bf11e443d8e59b58f` | `695e5820dd33f33a2d9ab9f382ac967d7dd11d8734b8b48d73cfe4b361aa11d1` |

Independent reserved holdouts from HV-003—**`tv80`, `spi`, `systemcaes`**—
must not be run, tuned or included here. The five HV-003/005 exploratory
designs are excluded, too.

## Fixed initial screen

Use official `berkeley-abc/abc` revision
`25d4ee221b2a9ab5124f3a222bcdf6f922d3d8a3`, built with
`make ABC_USE_NO_READLINE=1 -j4`. On every pair execute both modes once,
in the list order, sequentially on the same host:

1. Unpartitioned: `abc -c 'cec -n -C 10000 -T 9 REF OPT'`.
2. Partitioned: `abc -c 'cec -n -p -C 10000 -T 9 REF OPT'`.

Each call has an independent external `timeout -k 1s 14s` guard; this
is **not** a claim that the ABC internal `-T 9` is strict. Record process
elapsed wall time, external exit status and the exact native ABC conclusion:
`Networks are equivalent`, `Networks are not equivalent`, `undecided`, or
`external cutoff`. Do not treat *undecided* as incorrect equivalence.
Extract partition count from ABC's own `Verifying part ... (out of N)`
message when present. Observe both a solved-count metric and time of
correctly solved cases; record slowdowns as well as improvements.

## Hypothesis and reject criteria

Question: Is there a consistent performance regression for established ABC
automatic multi-output partitioning on **optimized circuit pairs**, and is
it better explained by visible structural factors than by output count alone?
This tests for a future research *gap*, not a new algorithm. Automatic
partitioning and FRAIG/SAT sweeping have substantial prior art (ICCAD 2006);
2026 miter-aware LUT mapping also investigates representation and structural
alignment. At least one reproducible material failure of existing methods
and a mechanism not already known must be established before implementing
new Witnora inference.

**No new mathematics, certified speedup, or source-level correctness claim
from this predeclaration.** Independently checked DRAT was not planned for
this ABC screen; equivalence conclusions are from ABC's native AIG checker.
