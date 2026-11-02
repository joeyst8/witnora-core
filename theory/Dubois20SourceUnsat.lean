import Lean

/-!
  Dubois20 original-clause SAT bridge, generated from the independently
  audited 40-row certificate in PR #119.

  SOURCE (decompressed DIMACS SHA-256):
  82059aba0e5773644b386eb6bcbe53680655390cb041873a3cb3e93f7bd896a7

  The source representation below contains all 160 distinct archived signed
  clauses, re-ordered by certificate row, and the 40 corresponding exact
  width-three XOR rows. `source_iff_certificate` must check their pointwise
  equivalence for every assignment; `certificate_inconsistent` must prove
  no assignment satisfies the XOR rows. A separate source-byte/parser
  refinement remains open; matching the SHA is NOT kernel-verified.

  Do not mark this file Lean-kernel-checked before a real toolchain accepts it.
  No `sorry`, `admit`, `native_decide`, or trust-compiler option is used.
-/

set_option sat.timeout 120

namespace Witnora.Dubois20

def sourceCNF (bits : BitVec 60) : Bool :=
  ((!(bits.getLsbD 40)) || (!(bits.getLsbD 1)) || (bits.getLsbD 0)) &&
  ((!(bits.getLsbD 40)) || (!(bits.getLsbD 0)) || (bits.getLsbD 1)) &&
  ((!(bits.getLsbD 1)) || (!(bits.getLsbD 0)) || (bits.getLsbD 40)) &&
  ((bits.getLsbD 0) || (bits.getLsbD 1) || (bits.getLsbD 40)) &&
  ((!(bits.getLsbD 39)) || (!(bits.getLsbD 38)) || (bits.getLsbD 0)) &&
  ((!(bits.getLsbD 39)) || (!(bits.getLsbD 0)) || (bits.getLsbD 38)) &&
  ((!(bits.getLsbD 38)) || (!(bits.getLsbD 0)) || (bits.getLsbD 39)) &&
  ((bits.getLsbD 0) || (bits.getLsbD 38) || (bits.getLsbD 39)) &&
  ((!(bits.getLsbD 41)) || (!(bits.getLsbD 2)) || (bits.getLsbD 1)) &&
  ((!(bits.getLsbD 41)) || (!(bits.getLsbD 1)) || (bits.getLsbD 2)) &&
  ((!(bits.getLsbD 2)) || (!(bits.getLsbD 1)) || (bits.getLsbD 41)) &&
  ((bits.getLsbD 1) || (bits.getLsbD 2) || (bits.getLsbD 41)) &&
  ((!(bits.getLsbD 42)) || (!(bits.getLsbD 3)) || (bits.getLsbD 2)) &&
  ((!(bits.getLsbD 42)) || (!(bits.getLsbD 2)) || (bits.getLsbD 3)) &&
  ((!(bits.getLsbD 3)) || (!(bits.getLsbD 2)) || (bits.getLsbD 42)) &&
  ((bits.getLsbD 2) || (bits.getLsbD 3) || (bits.getLsbD 42)) &&
  ((!(bits.getLsbD 43)) || (!(bits.getLsbD 4)) || (bits.getLsbD 3)) &&
  ((!(bits.getLsbD 43)) || (!(bits.getLsbD 3)) || (bits.getLsbD 4)) &&
  ((!(bits.getLsbD 4)) || (!(bits.getLsbD 3)) || (bits.getLsbD 43)) &&
  ((bits.getLsbD 3) || (bits.getLsbD 4) || (bits.getLsbD 43)) &&
  ((!(bits.getLsbD 44)) || (!(bits.getLsbD 5)) || (bits.getLsbD 4)) &&
  ((!(bits.getLsbD 44)) || (!(bits.getLsbD 4)) || (bits.getLsbD 5)) &&
  ((!(bits.getLsbD 5)) || (!(bits.getLsbD 4)) || (bits.getLsbD 44)) &&
  ((bits.getLsbD 4) || (bits.getLsbD 5) || (bits.getLsbD 44)) &&
  ((!(bits.getLsbD 45)) || (!(bits.getLsbD 6)) || (bits.getLsbD 5)) &&
  ((!(bits.getLsbD 45)) || (!(bits.getLsbD 5)) || (bits.getLsbD 6)) &&
  ((!(bits.getLsbD 6)) || (!(bits.getLsbD 5)) || (bits.getLsbD 45)) &&
  ((bits.getLsbD 5) || (bits.getLsbD 6) || (bits.getLsbD 45)) &&
  ((!(bits.getLsbD 46)) || (!(bits.getLsbD 7)) || (bits.getLsbD 6)) &&
  ((!(bits.getLsbD 46)) || (!(bits.getLsbD 6)) || (bits.getLsbD 7)) &&
  ((!(bits.getLsbD 7)) || (!(bits.getLsbD 6)) || (bits.getLsbD 46)) &&
  ((bits.getLsbD 6) || (bits.getLsbD 7) || (bits.getLsbD 46)) &&
  ((!(bits.getLsbD 47)) || (!(bits.getLsbD 8)) || (bits.getLsbD 7)) &&
  ((!(bits.getLsbD 47)) || (!(bits.getLsbD 7)) || (bits.getLsbD 8)) &&
  ((!(bits.getLsbD 8)) || (!(bits.getLsbD 7)) || (bits.getLsbD 47)) &&
  ((bits.getLsbD 7) || (bits.getLsbD 8) || (bits.getLsbD 47)) &&
  ((!(bits.getLsbD 48)) || (!(bits.getLsbD 9)) || (bits.getLsbD 8)) &&
  ((!(bits.getLsbD 48)) || (!(bits.getLsbD 8)) || (bits.getLsbD 9)) &&
  ((!(bits.getLsbD 9)) || (!(bits.getLsbD 8)) || (bits.getLsbD 48)) &&
  ((bits.getLsbD 8) || (bits.getLsbD 9) || (bits.getLsbD 48)) &&
  ((!(bits.getLsbD 49)) || (!(bits.getLsbD 10)) || (bits.getLsbD 9)) &&
  ((!(bits.getLsbD 49)) || (!(bits.getLsbD 9)) || (bits.getLsbD 10)) &&
  ((!(bits.getLsbD 10)) || (!(bits.getLsbD 9)) || (bits.getLsbD 49)) &&
  ((bits.getLsbD 9) || (bits.getLsbD 10) || (bits.getLsbD 49)) &&
  ((!(bits.getLsbD 50)) || (!(bits.getLsbD 11)) || (bits.getLsbD 10)) &&
  ((!(bits.getLsbD 50)) || (!(bits.getLsbD 10)) || (bits.getLsbD 11)) &&
  ((!(bits.getLsbD 11)) || (!(bits.getLsbD 10)) || (bits.getLsbD 50)) &&
  ((bits.getLsbD 10) || (bits.getLsbD 11) || (bits.getLsbD 50)) &&
  ((!(bits.getLsbD 51)) || (!(bits.getLsbD 12)) || (bits.getLsbD 11)) &&
  ((!(bits.getLsbD 51)) || (!(bits.getLsbD 11)) || (bits.getLsbD 12)) &&
  ((!(bits.getLsbD 12)) || (!(bits.getLsbD 11)) || (bits.getLsbD 51)) &&
  ((bits.getLsbD 11) || (bits.getLsbD 12) || (bits.getLsbD 51)) &&
  ((!(bits.getLsbD 52)) || (!(bits.getLsbD 13)) || (bits.getLsbD 12)) &&
  ((!(bits.getLsbD 52)) || (!(bits.getLsbD 12)) || (bits.getLsbD 13)) &&
  ((!(bits.getLsbD 13)) || (!(bits.getLsbD 12)) || (bits.getLsbD 52)) &&
  ((bits.getLsbD 12) || (bits.getLsbD 13) || (bits.getLsbD 52)) &&
  ((!(bits.getLsbD 53)) || (!(bits.getLsbD 14)) || (bits.getLsbD 13)) &&
  ((!(bits.getLsbD 53)) || (!(bits.getLsbD 13)) || (bits.getLsbD 14)) &&
  ((!(bits.getLsbD 14)) || (!(bits.getLsbD 13)) || (bits.getLsbD 53)) &&
  ((bits.getLsbD 13) || (bits.getLsbD 14) || (bits.getLsbD 53)) &&
  ((!(bits.getLsbD 54)) || (!(bits.getLsbD 15)) || (bits.getLsbD 14)) &&
  ((!(bits.getLsbD 54)) || (!(bits.getLsbD 14)) || (bits.getLsbD 15)) &&
  ((!(bits.getLsbD 15)) || (!(bits.getLsbD 14)) || (bits.getLsbD 54)) &&
  ((bits.getLsbD 14) || (bits.getLsbD 15) || (bits.getLsbD 54)) &&
  ((!(bits.getLsbD 55)) || (!(bits.getLsbD 16)) || (bits.getLsbD 15)) &&
  ((!(bits.getLsbD 55)) || (!(bits.getLsbD 15)) || (bits.getLsbD 16)) &&
  ((!(bits.getLsbD 16)) || (!(bits.getLsbD 15)) || (bits.getLsbD 55)) &&
  ((bits.getLsbD 15) || (bits.getLsbD 16) || (bits.getLsbD 55)) &&
  ((!(bits.getLsbD 56)) || (!(bits.getLsbD 17)) || (bits.getLsbD 16)) &&
  ((!(bits.getLsbD 56)) || (!(bits.getLsbD 16)) || (bits.getLsbD 17)) &&
  ((!(bits.getLsbD 17)) || (!(bits.getLsbD 16)) || (bits.getLsbD 56)) &&
  ((bits.getLsbD 16) || (bits.getLsbD 17) || (bits.getLsbD 56)) &&
  ((!(bits.getLsbD 57)) || (!(bits.getLsbD 18)) || (bits.getLsbD 17)) &&
  ((!(bits.getLsbD 57)) || (!(bits.getLsbD 17)) || (bits.getLsbD 18)) &&
  ((!(bits.getLsbD 18)) || (!(bits.getLsbD 17)) || (bits.getLsbD 57)) &&
  ((bits.getLsbD 17) || (bits.getLsbD 18) || (bits.getLsbD 57)) &&
  ((!(bits.getLsbD 59)) || (!(bits.getLsbD 58)) || (bits.getLsbD 18)) &&
  ((!(bits.getLsbD 59)) || (!(bits.getLsbD 18)) || (bits.getLsbD 58)) &&
  ((!(bits.getLsbD 58)) || (!(bits.getLsbD 18)) || (bits.getLsbD 59)) &&
  ((bits.getLsbD 18) || (bits.getLsbD 58) || (bits.getLsbD 59)) &&
  ((!(bits.getLsbD 57)) || (!(bits.getLsbD 20)) || (bits.getLsbD 19)) &&
  ((!(bits.getLsbD 57)) || (!(bits.getLsbD 19)) || (bits.getLsbD 20)) &&
  ((!(bits.getLsbD 20)) || (!(bits.getLsbD 19)) || (bits.getLsbD 57)) &&
  ((bits.getLsbD 19) || (bits.getLsbD 20) || (bits.getLsbD 57)) &&
  ((!(bits.getLsbD 59)) || (!(bits.getLsbD 58)) || (bits.getLsbD 19)) &&
  ((!(bits.getLsbD 59)) || (!(bits.getLsbD 19)) || (bits.getLsbD 58)) &&
  ((!(bits.getLsbD 58)) || (!(bits.getLsbD 19)) || (bits.getLsbD 59)) &&
  ((bits.getLsbD 19) || (bits.getLsbD 58) || (bits.getLsbD 59)) &&
  ((!(bits.getLsbD 56)) || (!(bits.getLsbD 21)) || (bits.getLsbD 20)) &&
  ((!(bits.getLsbD 56)) || (!(bits.getLsbD 20)) || (bits.getLsbD 21)) &&
  ((!(bits.getLsbD 21)) || (!(bits.getLsbD 20)) || (bits.getLsbD 56)) &&
  ((bits.getLsbD 20) || (bits.getLsbD 21) || (bits.getLsbD 56)) &&
  ((!(bits.getLsbD 55)) || (!(bits.getLsbD 22)) || (bits.getLsbD 21)) &&
  ((!(bits.getLsbD 55)) || (!(bits.getLsbD 21)) || (bits.getLsbD 22)) &&
  ((!(bits.getLsbD 22)) || (!(bits.getLsbD 21)) || (bits.getLsbD 55)) &&
  ((bits.getLsbD 21) || (bits.getLsbD 22) || (bits.getLsbD 55)) &&
  ((!(bits.getLsbD 54)) || (!(bits.getLsbD 23)) || (bits.getLsbD 22)) &&
  ((!(bits.getLsbD 54)) || (!(bits.getLsbD 22)) || (bits.getLsbD 23)) &&
  ((!(bits.getLsbD 23)) || (!(bits.getLsbD 22)) || (bits.getLsbD 54)) &&
  ((bits.getLsbD 22) || (bits.getLsbD 23) || (bits.getLsbD 54)) &&
  ((!(bits.getLsbD 53)) || (!(bits.getLsbD 24)) || (bits.getLsbD 23)) &&
  ((!(bits.getLsbD 53)) || (!(bits.getLsbD 23)) || (bits.getLsbD 24)) &&
  ((!(bits.getLsbD 24)) || (!(bits.getLsbD 23)) || (bits.getLsbD 53)) &&
  ((bits.getLsbD 23) || (bits.getLsbD 24) || (bits.getLsbD 53)) &&
  ((!(bits.getLsbD 52)) || (!(bits.getLsbD 25)) || (bits.getLsbD 24)) &&
  ((!(bits.getLsbD 52)) || (!(bits.getLsbD 24)) || (bits.getLsbD 25)) &&
  ((!(bits.getLsbD 25)) || (!(bits.getLsbD 24)) || (bits.getLsbD 52)) &&
  ((bits.getLsbD 24) || (bits.getLsbD 25) || (bits.getLsbD 52)) &&
  ((!(bits.getLsbD 51)) || (!(bits.getLsbD 26)) || (bits.getLsbD 25)) &&
  ((!(bits.getLsbD 51)) || (!(bits.getLsbD 25)) || (bits.getLsbD 26)) &&
  ((!(bits.getLsbD 26)) || (!(bits.getLsbD 25)) || (bits.getLsbD 51)) &&
  ((bits.getLsbD 25) || (bits.getLsbD 26) || (bits.getLsbD 51)) &&
  ((!(bits.getLsbD 50)) || (!(bits.getLsbD 27)) || (bits.getLsbD 26)) &&
  ((!(bits.getLsbD 50)) || (!(bits.getLsbD 26)) || (bits.getLsbD 27)) &&
  ((!(bits.getLsbD 27)) || (!(bits.getLsbD 26)) || (bits.getLsbD 50)) &&
  ((bits.getLsbD 26) || (bits.getLsbD 27) || (bits.getLsbD 50)) &&
  ((!(bits.getLsbD 49)) || (!(bits.getLsbD 28)) || (bits.getLsbD 27)) &&
  ((!(bits.getLsbD 49)) || (!(bits.getLsbD 27)) || (bits.getLsbD 28)) &&
  ((!(bits.getLsbD 28)) || (!(bits.getLsbD 27)) || (bits.getLsbD 49)) &&
  ((bits.getLsbD 27) || (bits.getLsbD 28) || (bits.getLsbD 49)) &&
  ((!(bits.getLsbD 48)) || (!(bits.getLsbD 29)) || (bits.getLsbD 28)) &&
  ((!(bits.getLsbD 48)) || (!(bits.getLsbD 28)) || (bits.getLsbD 29)) &&
  ((!(bits.getLsbD 29)) || (!(bits.getLsbD 28)) || (bits.getLsbD 48)) &&
  ((bits.getLsbD 28) || (bits.getLsbD 29) || (bits.getLsbD 48)) &&
  ((!(bits.getLsbD 47)) || (!(bits.getLsbD 30)) || (bits.getLsbD 29)) &&
  ((!(bits.getLsbD 47)) || (!(bits.getLsbD 29)) || (bits.getLsbD 30)) &&
  ((!(bits.getLsbD 30)) || (!(bits.getLsbD 29)) || (bits.getLsbD 47)) &&
  ((bits.getLsbD 29) || (bits.getLsbD 30) || (bits.getLsbD 47)) &&
  ((!(bits.getLsbD 46)) || (!(bits.getLsbD 31)) || (bits.getLsbD 30)) &&
  ((!(bits.getLsbD 46)) || (!(bits.getLsbD 30)) || (bits.getLsbD 31)) &&
  ((!(bits.getLsbD 31)) || (!(bits.getLsbD 30)) || (bits.getLsbD 46)) &&
  ((bits.getLsbD 30) || (bits.getLsbD 31) || (bits.getLsbD 46)) &&
  ((!(bits.getLsbD 45)) || (!(bits.getLsbD 32)) || (bits.getLsbD 31)) &&
  ((!(bits.getLsbD 45)) || (!(bits.getLsbD 31)) || (bits.getLsbD 32)) &&
  ((!(bits.getLsbD 32)) || (!(bits.getLsbD 31)) || (bits.getLsbD 45)) &&
  ((bits.getLsbD 31) || (bits.getLsbD 32) || (bits.getLsbD 45)) &&
  ((!(bits.getLsbD 44)) || (!(bits.getLsbD 33)) || (bits.getLsbD 32)) &&
  ((!(bits.getLsbD 44)) || (!(bits.getLsbD 32)) || (bits.getLsbD 33)) &&
  ((!(bits.getLsbD 33)) || (!(bits.getLsbD 32)) || (bits.getLsbD 44)) &&
  ((bits.getLsbD 32) || (bits.getLsbD 33) || (bits.getLsbD 44)) &&
  ((!(bits.getLsbD 43)) || (!(bits.getLsbD 34)) || (bits.getLsbD 33)) &&
  ((!(bits.getLsbD 43)) || (!(bits.getLsbD 33)) || (bits.getLsbD 34)) &&
  ((!(bits.getLsbD 34)) || (!(bits.getLsbD 33)) || (bits.getLsbD 43)) &&
  ((bits.getLsbD 33) || (bits.getLsbD 34) || (bits.getLsbD 43)) &&
  ((!(bits.getLsbD 42)) || (!(bits.getLsbD 35)) || (bits.getLsbD 34)) &&
  ((!(bits.getLsbD 42)) || (!(bits.getLsbD 34)) || (bits.getLsbD 35)) &&
  ((!(bits.getLsbD 35)) || (!(bits.getLsbD 34)) || (bits.getLsbD 42)) &&
  ((bits.getLsbD 34) || (bits.getLsbD 35) || (bits.getLsbD 42)) &&
  ((!(bits.getLsbD 41)) || (!(bits.getLsbD 36)) || (bits.getLsbD 35)) &&
  ((!(bits.getLsbD 41)) || (!(bits.getLsbD 35)) || (bits.getLsbD 36)) &&
  ((!(bits.getLsbD 36)) || (!(bits.getLsbD 35)) || (bits.getLsbD 41)) &&
  ((bits.getLsbD 35) || (bits.getLsbD 36) || (bits.getLsbD 41)) &&
  ((!(bits.getLsbD 40)) || (!(bits.getLsbD 37)) || (bits.getLsbD 36)) &&
  ((!(bits.getLsbD 40)) || (!(bits.getLsbD 36)) || (bits.getLsbD 37)) &&
  ((!(bits.getLsbD 37)) || (!(bits.getLsbD 36)) || (bits.getLsbD 40)) &&
  ((bits.getLsbD 36) || (bits.getLsbD 37) || (bits.getLsbD 40)) &&
  ((!(bits.getLsbD 39)) || (!(bits.getLsbD 38)) || (!(bits.getLsbD 37))) &&
  ((!(bits.getLsbD 39)) || (bits.getLsbD 37) || (bits.getLsbD 38)) &&
  ((!(bits.getLsbD 38)) || (bits.getLsbD 37) || (bits.getLsbD 39)) &&
  ((!(bits.getLsbD 37)) || (bits.getLsbD 38) || (bits.getLsbD 39))

def certificateRows (bits : BitVec 60) : Bool :=
  ((xor (xor (bits.getLsbD 0) (bits.getLsbD 1)) (bits.getLsbD 40)) == true) &&
  ((xor (xor (bits.getLsbD 0) (bits.getLsbD 38)) (bits.getLsbD 39)) == true) &&
  ((xor (xor (bits.getLsbD 1) (bits.getLsbD 2)) (bits.getLsbD 41)) == true) &&
  ((xor (xor (bits.getLsbD 2) (bits.getLsbD 3)) (bits.getLsbD 42)) == true) &&
  ((xor (xor (bits.getLsbD 3) (bits.getLsbD 4)) (bits.getLsbD 43)) == true) &&
  ((xor (xor (bits.getLsbD 4) (bits.getLsbD 5)) (bits.getLsbD 44)) == true) &&
  ((xor (xor (bits.getLsbD 5) (bits.getLsbD 6)) (bits.getLsbD 45)) == true) &&
  ((xor (xor (bits.getLsbD 6) (bits.getLsbD 7)) (bits.getLsbD 46)) == true) &&
  ((xor (xor (bits.getLsbD 7) (bits.getLsbD 8)) (bits.getLsbD 47)) == true) &&
  ((xor (xor (bits.getLsbD 8) (bits.getLsbD 9)) (bits.getLsbD 48)) == true) &&
  ((xor (xor (bits.getLsbD 9) (bits.getLsbD 10)) (bits.getLsbD 49)) == true) &&
  ((xor (xor (bits.getLsbD 10) (bits.getLsbD 11)) (bits.getLsbD 50)) == true) &&
  ((xor (xor (bits.getLsbD 11) (bits.getLsbD 12)) (bits.getLsbD 51)) == true) &&
  ((xor (xor (bits.getLsbD 12) (bits.getLsbD 13)) (bits.getLsbD 52)) == true) &&
  ((xor (xor (bits.getLsbD 13) (bits.getLsbD 14)) (bits.getLsbD 53)) == true) &&
  ((xor (xor (bits.getLsbD 14) (bits.getLsbD 15)) (bits.getLsbD 54)) == true) &&
  ((xor (xor (bits.getLsbD 15) (bits.getLsbD 16)) (bits.getLsbD 55)) == true) &&
  ((xor (xor (bits.getLsbD 16) (bits.getLsbD 17)) (bits.getLsbD 56)) == true) &&
  ((xor (xor (bits.getLsbD 17) (bits.getLsbD 18)) (bits.getLsbD 57)) == true) &&
  ((xor (xor (bits.getLsbD 18) (bits.getLsbD 58)) (bits.getLsbD 59)) == true) &&
  ((xor (xor (bits.getLsbD 19) (bits.getLsbD 20)) (bits.getLsbD 57)) == true) &&
  ((xor (xor (bits.getLsbD 19) (bits.getLsbD 58)) (bits.getLsbD 59)) == true) &&
  ((xor (xor (bits.getLsbD 20) (bits.getLsbD 21)) (bits.getLsbD 56)) == true) &&
  ((xor (xor (bits.getLsbD 21) (bits.getLsbD 22)) (bits.getLsbD 55)) == true) &&
  ((xor (xor (bits.getLsbD 22) (bits.getLsbD 23)) (bits.getLsbD 54)) == true) &&
  ((xor (xor (bits.getLsbD 23) (bits.getLsbD 24)) (bits.getLsbD 53)) == true) &&
  ((xor (xor (bits.getLsbD 24) (bits.getLsbD 25)) (bits.getLsbD 52)) == true) &&
  ((xor (xor (bits.getLsbD 25) (bits.getLsbD 26)) (bits.getLsbD 51)) == true) &&
  ((xor (xor (bits.getLsbD 26) (bits.getLsbD 27)) (bits.getLsbD 50)) == true) &&
  ((xor (xor (bits.getLsbD 27) (bits.getLsbD 28)) (bits.getLsbD 49)) == true) &&
  ((xor (xor (bits.getLsbD 28) (bits.getLsbD 29)) (bits.getLsbD 48)) == true) &&
  ((xor (xor (bits.getLsbD 29) (bits.getLsbD 30)) (bits.getLsbD 47)) == true) &&
  ((xor (xor (bits.getLsbD 30) (bits.getLsbD 31)) (bits.getLsbD 46)) == true) &&
  ((xor (xor (bits.getLsbD 31) (bits.getLsbD 32)) (bits.getLsbD 45)) == true) &&
  ((xor (xor (bits.getLsbD 32) (bits.getLsbD 33)) (bits.getLsbD 44)) == true) &&
  ((xor (xor (bits.getLsbD 33) (bits.getLsbD 34)) (bits.getLsbD 43)) == true) &&
  ((xor (xor (bits.getLsbD 34) (bits.getLsbD 35)) (bits.getLsbD 42)) == true) &&
  ((xor (xor (bits.getLsbD 35) (bits.getLsbD 36)) (bits.getLsbD 41)) == true) &&
  ((xor (xor (bits.getLsbD 36) (bits.getLsbD 37)) (bits.getLsbD 40)) == true) &&
  ((xor (xor (bits.getLsbD 37) (bits.getLsbD 38)) (bits.getLsbD 39)) == false)

theorem source_iff_certificate (bits : BitVec 60) :
    sourceCNF bits = certificateRows bits := by
  unfold sourceCNF certificateRows
  bv_decide

theorem certificate_inconsistent (bits : BitVec 60) :
    certificateRows bits = false := by
  unfold certificateRows
  bv_decide

theorem source_unsat (bits : BitVec 60) : sourceCNF bits = false := by
  calc
    sourceCNF bits = certificateRows bits := source_iff_certificate bits
    _ = false := certificate_inconsistent bits

end Witnora.Dubois20

#print axioms Witnora.Dubois20.source_unsat

