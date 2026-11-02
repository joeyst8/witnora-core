import Lean

set_option maxHeartbeats 2000000
set_option linter.unusedSimpArgs false

/-!
  Kernel-only proof candidate for the 160-clause Dubois20 CNF as re-ordered
  by the archived 40-row source-exact XOR certificate. Variables are represented
  by BitVec 60 bit indexes; original DIMACS variable i maps to bit i-1.

  Decompressed source SHA-256:
  82059aba0e5773644b386eb6bcbe53680655390cb041873a3cb3e93f7bd896a7

  Each sourceGroup is four original clauses. Each sourceGroup_exact proof
  enumerates its three local Boolean variables using Lean cases/simp only.
  The global contradiction is a kernel-reduced XOR cancellation, not a
  native SAT-solver oracle. Source-text parser/refinement still remains open.
-/

namespace Witnora.Dubois20

def sourceGroup0 (bits : BitVec 60) : Bool :=
  ((!(bits.getLsbD 40)) || (!(bits.getLsbD 1)) || (bits.getLsbD 0)) &&
  ((!(bits.getLsbD 40)) || (!(bits.getLsbD 0)) || (bits.getLsbD 1)) &&
  ((!(bits.getLsbD 1)) || (!(bits.getLsbD 0)) || (bits.getLsbD 40)) &&
  ((bits.getLsbD 0) || (bits.getLsbD 1) || (bits.getLsbD 40))

def sourceGroup1 (bits : BitVec 60) : Bool :=
  ((!(bits.getLsbD 39)) || (!(bits.getLsbD 38)) || (bits.getLsbD 0)) &&
  ((!(bits.getLsbD 39)) || (!(bits.getLsbD 0)) || (bits.getLsbD 38)) &&
  ((!(bits.getLsbD 38)) || (!(bits.getLsbD 0)) || (bits.getLsbD 39)) &&
  ((bits.getLsbD 0) || (bits.getLsbD 38) || (bits.getLsbD 39))

def sourceGroup2 (bits : BitVec 60) : Bool :=
  ((!(bits.getLsbD 41)) || (!(bits.getLsbD 2)) || (bits.getLsbD 1)) &&
  ((!(bits.getLsbD 41)) || (!(bits.getLsbD 1)) || (bits.getLsbD 2)) &&
  ((!(bits.getLsbD 2)) || (!(bits.getLsbD 1)) || (bits.getLsbD 41)) &&
  ((bits.getLsbD 1) || (bits.getLsbD 2) || (bits.getLsbD 41))

def sourceGroup3 (bits : BitVec 60) : Bool :=
  ((!(bits.getLsbD 42)) || (!(bits.getLsbD 3)) || (bits.getLsbD 2)) &&
  ((!(bits.getLsbD 42)) || (!(bits.getLsbD 2)) || (bits.getLsbD 3)) &&
  ((!(bits.getLsbD 3)) || (!(bits.getLsbD 2)) || (bits.getLsbD 42)) &&
  ((bits.getLsbD 2) || (bits.getLsbD 3) || (bits.getLsbD 42))

def sourceGroup4 (bits : BitVec 60) : Bool :=
  ((!(bits.getLsbD 43)) || (!(bits.getLsbD 4)) || (bits.getLsbD 3)) &&
  ((!(bits.getLsbD 43)) || (!(bits.getLsbD 3)) || (bits.getLsbD 4)) &&
  ((!(bits.getLsbD 4)) || (!(bits.getLsbD 3)) || (bits.getLsbD 43)) &&
  ((bits.getLsbD 3) || (bits.getLsbD 4) || (bits.getLsbD 43))

def sourceGroup5 (bits : BitVec 60) : Bool :=
  ((!(bits.getLsbD 44)) || (!(bits.getLsbD 5)) || (bits.getLsbD 4)) &&
  ((!(bits.getLsbD 44)) || (!(bits.getLsbD 4)) || (bits.getLsbD 5)) &&
  ((!(bits.getLsbD 5)) || (!(bits.getLsbD 4)) || (bits.getLsbD 44)) &&
  ((bits.getLsbD 4) || (bits.getLsbD 5) || (bits.getLsbD 44))

def sourceGroup6 (bits : BitVec 60) : Bool :=
  ((!(bits.getLsbD 45)) || (!(bits.getLsbD 6)) || (bits.getLsbD 5)) &&
  ((!(bits.getLsbD 45)) || (!(bits.getLsbD 5)) || (bits.getLsbD 6)) &&
  ((!(bits.getLsbD 6)) || (!(bits.getLsbD 5)) || (bits.getLsbD 45)) &&
  ((bits.getLsbD 5) || (bits.getLsbD 6) || (bits.getLsbD 45))

def sourceGroup7 (bits : BitVec 60) : Bool :=
  ((!(bits.getLsbD 46)) || (!(bits.getLsbD 7)) || (bits.getLsbD 6)) &&
  ((!(bits.getLsbD 46)) || (!(bits.getLsbD 6)) || (bits.getLsbD 7)) &&
  ((!(bits.getLsbD 7)) || (!(bits.getLsbD 6)) || (bits.getLsbD 46)) &&
  ((bits.getLsbD 6) || (bits.getLsbD 7) || (bits.getLsbD 46))

def sourceGroup8 (bits : BitVec 60) : Bool :=
  ((!(bits.getLsbD 47)) || (!(bits.getLsbD 8)) || (bits.getLsbD 7)) &&
  ((!(bits.getLsbD 47)) || (!(bits.getLsbD 7)) || (bits.getLsbD 8)) &&
  ((!(bits.getLsbD 8)) || (!(bits.getLsbD 7)) || (bits.getLsbD 47)) &&
  ((bits.getLsbD 7) || (bits.getLsbD 8) || (bits.getLsbD 47))

def sourceGroup9 (bits : BitVec 60) : Bool :=
  ((!(bits.getLsbD 48)) || (!(bits.getLsbD 9)) || (bits.getLsbD 8)) &&
  ((!(bits.getLsbD 48)) || (!(bits.getLsbD 8)) || (bits.getLsbD 9)) &&
  ((!(bits.getLsbD 9)) || (!(bits.getLsbD 8)) || (bits.getLsbD 48)) &&
  ((bits.getLsbD 8) || (bits.getLsbD 9) || (bits.getLsbD 48))

def sourceGroup10 (bits : BitVec 60) : Bool :=
  ((!(bits.getLsbD 49)) || (!(bits.getLsbD 10)) || (bits.getLsbD 9)) &&
  ((!(bits.getLsbD 49)) || (!(bits.getLsbD 9)) || (bits.getLsbD 10)) &&
  ((!(bits.getLsbD 10)) || (!(bits.getLsbD 9)) || (bits.getLsbD 49)) &&
  ((bits.getLsbD 9) || (bits.getLsbD 10) || (bits.getLsbD 49))

def sourceGroup11 (bits : BitVec 60) : Bool :=
  ((!(bits.getLsbD 50)) || (!(bits.getLsbD 11)) || (bits.getLsbD 10)) &&
  ((!(bits.getLsbD 50)) || (!(bits.getLsbD 10)) || (bits.getLsbD 11)) &&
  ((!(bits.getLsbD 11)) || (!(bits.getLsbD 10)) || (bits.getLsbD 50)) &&
  ((bits.getLsbD 10) || (bits.getLsbD 11) || (bits.getLsbD 50))

def sourceGroup12 (bits : BitVec 60) : Bool :=
  ((!(bits.getLsbD 51)) || (!(bits.getLsbD 12)) || (bits.getLsbD 11)) &&
  ((!(bits.getLsbD 51)) || (!(bits.getLsbD 11)) || (bits.getLsbD 12)) &&
  ((!(bits.getLsbD 12)) || (!(bits.getLsbD 11)) || (bits.getLsbD 51)) &&
  ((bits.getLsbD 11) || (bits.getLsbD 12) || (bits.getLsbD 51))

def sourceGroup13 (bits : BitVec 60) : Bool :=
  ((!(bits.getLsbD 52)) || (!(bits.getLsbD 13)) || (bits.getLsbD 12)) &&
  ((!(bits.getLsbD 52)) || (!(bits.getLsbD 12)) || (bits.getLsbD 13)) &&
  ((!(bits.getLsbD 13)) || (!(bits.getLsbD 12)) || (bits.getLsbD 52)) &&
  ((bits.getLsbD 12) || (bits.getLsbD 13) || (bits.getLsbD 52))

def sourceGroup14 (bits : BitVec 60) : Bool :=
  ((!(bits.getLsbD 53)) || (!(bits.getLsbD 14)) || (bits.getLsbD 13)) &&
  ((!(bits.getLsbD 53)) || (!(bits.getLsbD 13)) || (bits.getLsbD 14)) &&
  ((!(bits.getLsbD 14)) || (!(bits.getLsbD 13)) || (bits.getLsbD 53)) &&
  ((bits.getLsbD 13) || (bits.getLsbD 14) || (bits.getLsbD 53))

def sourceGroup15 (bits : BitVec 60) : Bool :=
  ((!(bits.getLsbD 54)) || (!(bits.getLsbD 15)) || (bits.getLsbD 14)) &&
  ((!(bits.getLsbD 54)) || (!(bits.getLsbD 14)) || (bits.getLsbD 15)) &&
  ((!(bits.getLsbD 15)) || (!(bits.getLsbD 14)) || (bits.getLsbD 54)) &&
  ((bits.getLsbD 14) || (bits.getLsbD 15) || (bits.getLsbD 54))

def sourceGroup16 (bits : BitVec 60) : Bool :=
  ((!(bits.getLsbD 55)) || (!(bits.getLsbD 16)) || (bits.getLsbD 15)) &&
  ((!(bits.getLsbD 55)) || (!(bits.getLsbD 15)) || (bits.getLsbD 16)) &&
  ((!(bits.getLsbD 16)) || (!(bits.getLsbD 15)) || (bits.getLsbD 55)) &&
  ((bits.getLsbD 15) || (bits.getLsbD 16) || (bits.getLsbD 55))

def sourceGroup17 (bits : BitVec 60) : Bool :=
  ((!(bits.getLsbD 56)) || (!(bits.getLsbD 17)) || (bits.getLsbD 16)) &&
  ((!(bits.getLsbD 56)) || (!(bits.getLsbD 16)) || (bits.getLsbD 17)) &&
  ((!(bits.getLsbD 17)) || (!(bits.getLsbD 16)) || (bits.getLsbD 56)) &&
  ((bits.getLsbD 16) || (bits.getLsbD 17) || (bits.getLsbD 56))

def sourceGroup18 (bits : BitVec 60) : Bool :=
  ((!(bits.getLsbD 57)) || (!(bits.getLsbD 18)) || (bits.getLsbD 17)) &&
  ((!(bits.getLsbD 57)) || (!(bits.getLsbD 17)) || (bits.getLsbD 18)) &&
  ((!(bits.getLsbD 18)) || (!(bits.getLsbD 17)) || (bits.getLsbD 57)) &&
  ((bits.getLsbD 17) || (bits.getLsbD 18) || (bits.getLsbD 57))

def sourceGroup19 (bits : BitVec 60) : Bool :=
  ((!(bits.getLsbD 59)) || (!(bits.getLsbD 58)) || (bits.getLsbD 18)) &&
  ((!(bits.getLsbD 59)) || (!(bits.getLsbD 18)) || (bits.getLsbD 58)) &&
  ((!(bits.getLsbD 58)) || (!(bits.getLsbD 18)) || (bits.getLsbD 59)) &&
  ((bits.getLsbD 18) || (bits.getLsbD 58) || (bits.getLsbD 59))

def sourceGroup20 (bits : BitVec 60) : Bool :=
  ((!(bits.getLsbD 57)) || (!(bits.getLsbD 20)) || (bits.getLsbD 19)) &&
  ((!(bits.getLsbD 57)) || (!(bits.getLsbD 19)) || (bits.getLsbD 20)) &&
  ((!(bits.getLsbD 20)) || (!(bits.getLsbD 19)) || (bits.getLsbD 57)) &&
  ((bits.getLsbD 19) || (bits.getLsbD 20) || (bits.getLsbD 57))

def sourceGroup21 (bits : BitVec 60) : Bool :=
  ((!(bits.getLsbD 59)) || (!(bits.getLsbD 58)) || (bits.getLsbD 19)) &&
  ((!(bits.getLsbD 59)) || (!(bits.getLsbD 19)) || (bits.getLsbD 58)) &&
  ((!(bits.getLsbD 58)) || (!(bits.getLsbD 19)) || (bits.getLsbD 59)) &&
  ((bits.getLsbD 19) || (bits.getLsbD 58) || (bits.getLsbD 59))

def sourceGroup22 (bits : BitVec 60) : Bool :=
  ((!(bits.getLsbD 56)) || (!(bits.getLsbD 21)) || (bits.getLsbD 20)) &&
  ((!(bits.getLsbD 56)) || (!(bits.getLsbD 20)) || (bits.getLsbD 21)) &&
  ((!(bits.getLsbD 21)) || (!(bits.getLsbD 20)) || (bits.getLsbD 56)) &&
  ((bits.getLsbD 20) || (bits.getLsbD 21) || (bits.getLsbD 56))

def sourceGroup23 (bits : BitVec 60) : Bool :=
  ((!(bits.getLsbD 55)) || (!(bits.getLsbD 22)) || (bits.getLsbD 21)) &&
  ((!(bits.getLsbD 55)) || (!(bits.getLsbD 21)) || (bits.getLsbD 22)) &&
  ((!(bits.getLsbD 22)) || (!(bits.getLsbD 21)) || (bits.getLsbD 55)) &&
  ((bits.getLsbD 21) || (bits.getLsbD 22) || (bits.getLsbD 55))

def sourceGroup24 (bits : BitVec 60) : Bool :=
  ((!(bits.getLsbD 54)) || (!(bits.getLsbD 23)) || (bits.getLsbD 22)) &&
  ((!(bits.getLsbD 54)) || (!(bits.getLsbD 22)) || (bits.getLsbD 23)) &&
  ((!(bits.getLsbD 23)) || (!(bits.getLsbD 22)) || (bits.getLsbD 54)) &&
  ((bits.getLsbD 22) || (bits.getLsbD 23) || (bits.getLsbD 54))

def sourceGroup25 (bits : BitVec 60) : Bool :=
  ((!(bits.getLsbD 53)) || (!(bits.getLsbD 24)) || (bits.getLsbD 23)) &&
  ((!(bits.getLsbD 53)) || (!(bits.getLsbD 23)) || (bits.getLsbD 24)) &&
  ((!(bits.getLsbD 24)) || (!(bits.getLsbD 23)) || (bits.getLsbD 53)) &&
  ((bits.getLsbD 23) || (bits.getLsbD 24) || (bits.getLsbD 53))

def sourceGroup26 (bits : BitVec 60) : Bool :=
  ((!(bits.getLsbD 52)) || (!(bits.getLsbD 25)) || (bits.getLsbD 24)) &&
  ((!(bits.getLsbD 52)) || (!(bits.getLsbD 24)) || (bits.getLsbD 25)) &&
  ((!(bits.getLsbD 25)) || (!(bits.getLsbD 24)) || (bits.getLsbD 52)) &&
  ((bits.getLsbD 24) || (bits.getLsbD 25) || (bits.getLsbD 52))

def sourceGroup27 (bits : BitVec 60) : Bool :=
  ((!(bits.getLsbD 51)) || (!(bits.getLsbD 26)) || (bits.getLsbD 25)) &&
  ((!(bits.getLsbD 51)) || (!(bits.getLsbD 25)) || (bits.getLsbD 26)) &&
  ((!(bits.getLsbD 26)) || (!(bits.getLsbD 25)) || (bits.getLsbD 51)) &&
  ((bits.getLsbD 25) || (bits.getLsbD 26) || (bits.getLsbD 51))

def sourceGroup28 (bits : BitVec 60) : Bool :=
  ((!(bits.getLsbD 50)) || (!(bits.getLsbD 27)) || (bits.getLsbD 26)) &&
  ((!(bits.getLsbD 50)) || (!(bits.getLsbD 26)) || (bits.getLsbD 27)) &&
  ((!(bits.getLsbD 27)) || (!(bits.getLsbD 26)) || (bits.getLsbD 50)) &&
  ((bits.getLsbD 26) || (bits.getLsbD 27) || (bits.getLsbD 50))

def sourceGroup29 (bits : BitVec 60) : Bool :=
  ((!(bits.getLsbD 49)) || (!(bits.getLsbD 28)) || (bits.getLsbD 27)) &&
  ((!(bits.getLsbD 49)) || (!(bits.getLsbD 27)) || (bits.getLsbD 28)) &&
  ((!(bits.getLsbD 28)) || (!(bits.getLsbD 27)) || (bits.getLsbD 49)) &&
  ((bits.getLsbD 27) || (bits.getLsbD 28) || (bits.getLsbD 49))

def sourceGroup30 (bits : BitVec 60) : Bool :=
  ((!(bits.getLsbD 48)) || (!(bits.getLsbD 29)) || (bits.getLsbD 28)) &&
  ((!(bits.getLsbD 48)) || (!(bits.getLsbD 28)) || (bits.getLsbD 29)) &&
  ((!(bits.getLsbD 29)) || (!(bits.getLsbD 28)) || (bits.getLsbD 48)) &&
  ((bits.getLsbD 28) || (bits.getLsbD 29) || (bits.getLsbD 48))

def sourceGroup31 (bits : BitVec 60) : Bool :=
  ((!(bits.getLsbD 47)) || (!(bits.getLsbD 30)) || (bits.getLsbD 29)) &&
  ((!(bits.getLsbD 47)) || (!(bits.getLsbD 29)) || (bits.getLsbD 30)) &&
  ((!(bits.getLsbD 30)) || (!(bits.getLsbD 29)) || (bits.getLsbD 47)) &&
  ((bits.getLsbD 29) || (bits.getLsbD 30) || (bits.getLsbD 47))

def sourceGroup32 (bits : BitVec 60) : Bool :=
  ((!(bits.getLsbD 46)) || (!(bits.getLsbD 31)) || (bits.getLsbD 30)) &&
  ((!(bits.getLsbD 46)) || (!(bits.getLsbD 30)) || (bits.getLsbD 31)) &&
  ((!(bits.getLsbD 31)) || (!(bits.getLsbD 30)) || (bits.getLsbD 46)) &&
  ((bits.getLsbD 30) || (bits.getLsbD 31) || (bits.getLsbD 46))

def sourceGroup33 (bits : BitVec 60) : Bool :=
  ((!(bits.getLsbD 45)) || (!(bits.getLsbD 32)) || (bits.getLsbD 31)) &&
  ((!(bits.getLsbD 45)) || (!(bits.getLsbD 31)) || (bits.getLsbD 32)) &&
  ((!(bits.getLsbD 32)) || (!(bits.getLsbD 31)) || (bits.getLsbD 45)) &&
  ((bits.getLsbD 31) || (bits.getLsbD 32) || (bits.getLsbD 45))

def sourceGroup34 (bits : BitVec 60) : Bool :=
  ((!(bits.getLsbD 44)) || (!(bits.getLsbD 33)) || (bits.getLsbD 32)) &&
  ((!(bits.getLsbD 44)) || (!(bits.getLsbD 32)) || (bits.getLsbD 33)) &&
  ((!(bits.getLsbD 33)) || (!(bits.getLsbD 32)) || (bits.getLsbD 44)) &&
  ((bits.getLsbD 32) || (bits.getLsbD 33) || (bits.getLsbD 44))

def sourceGroup35 (bits : BitVec 60) : Bool :=
  ((!(bits.getLsbD 43)) || (!(bits.getLsbD 34)) || (bits.getLsbD 33)) &&
  ((!(bits.getLsbD 43)) || (!(bits.getLsbD 33)) || (bits.getLsbD 34)) &&
  ((!(bits.getLsbD 34)) || (!(bits.getLsbD 33)) || (bits.getLsbD 43)) &&
  ((bits.getLsbD 33) || (bits.getLsbD 34) || (bits.getLsbD 43))

def sourceGroup36 (bits : BitVec 60) : Bool :=
  ((!(bits.getLsbD 42)) || (!(bits.getLsbD 35)) || (bits.getLsbD 34)) &&
  ((!(bits.getLsbD 42)) || (!(bits.getLsbD 34)) || (bits.getLsbD 35)) &&
  ((!(bits.getLsbD 35)) || (!(bits.getLsbD 34)) || (bits.getLsbD 42)) &&
  ((bits.getLsbD 34) || (bits.getLsbD 35) || (bits.getLsbD 42))

def sourceGroup37 (bits : BitVec 60) : Bool :=
  ((!(bits.getLsbD 41)) || (!(bits.getLsbD 36)) || (bits.getLsbD 35)) &&
  ((!(bits.getLsbD 41)) || (!(bits.getLsbD 35)) || (bits.getLsbD 36)) &&
  ((!(bits.getLsbD 36)) || (!(bits.getLsbD 35)) || (bits.getLsbD 41)) &&
  ((bits.getLsbD 35) || (bits.getLsbD 36) || (bits.getLsbD 41))

def sourceGroup38 (bits : BitVec 60) : Bool :=
  ((!(bits.getLsbD 40)) || (!(bits.getLsbD 37)) || (bits.getLsbD 36)) &&
  ((!(bits.getLsbD 40)) || (!(bits.getLsbD 36)) || (bits.getLsbD 37)) &&
  ((!(bits.getLsbD 37)) || (!(bits.getLsbD 36)) || (bits.getLsbD 40)) &&
  ((bits.getLsbD 36) || (bits.getLsbD 37) || (bits.getLsbD 40))

def sourceGroup39 (bits : BitVec 60) : Bool :=
  ((!(bits.getLsbD 39)) || (!(bits.getLsbD 38)) || (!(bits.getLsbD 37))) &&
  ((!(bits.getLsbD 39)) || (bits.getLsbD 37) || (bits.getLsbD 38)) &&
  ((!(bits.getLsbD 38)) || (bits.getLsbD 37) || (bits.getLsbD 39)) &&
  ((!(bits.getLsbD 37)) || (bits.getLsbD 38) || (bits.getLsbD 39))

def parity0 (bits : BitVec 60) : Bool :=
  ((bits.getLsbD 0) ^^ (bits.getLsbD 1) ^^ (bits.getLsbD 40))

def parity1 (bits : BitVec 60) : Bool :=
  ((bits.getLsbD 0) ^^ (bits.getLsbD 38) ^^ (bits.getLsbD 39))

def parity2 (bits : BitVec 60) : Bool :=
  ((bits.getLsbD 1) ^^ (bits.getLsbD 2) ^^ (bits.getLsbD 41))

def parity3 (bits : BitVec 60) : Bool :=
  ((bits.getLsbD 2) ^^ (bits.getLsbD 3) ^^ (bits.getLsbD 42))

def parity4 (bits : BitVec 60) : Bool :=
  ((bits.getLsbD 3) ^^ (bits.getLsbD 4) ^^ (bits.getLsbD 43))

def parity5 (bits : BitVec 60) : Bool :=
  ((bits.getLsbD 4) ^^ (bits.getLsbD 5) ^^ (bits.getLsbD 44))

def parity6 (bits : BitVec 60) : Bool :=
  ((bits.getLsbD 5) ^^ (bits.getLsbD 6) ^^ (bits.getLsbD 45))

def parity7 (bits : BitVec 60) : Bool :=
  ((bits.getLsbD 6) ^^ (bits.getLsbD 7) ^^ (bits.getLsbD 46))

def parity8 (bits : BitVec 60) : Bool :=
  ((bits.getLsbD 7) ^^ (bits.getLsbD 8) ^^ (bits.getLsbD 47))

def parity9 (bits : BitVec 60) : Bool :=
  ((bits.getLsbD 8) ^^ (bits.getLsbD 9) ^^ (bits.getLsbD 48))

def parity10 (bits : BitVec 60) : Bool :=
  ((bits.getLsbD 9) ^^ (bits.getLsbD 10) ^^ (bits.getLsbD 49))

def parity11 (bits : BitVec 60) : Bool :=
  ((bits.getLsbD 10) ^^ (bits.getLsbD 11) ^^ (bits.getLsbD 50))

def parity12 (bits : BitVec 60) : Bool :=
  ((bits.getLsbD 11) ^^ (bits.getLsbD 12) ^^ (bits.getLsbD 51))

def parity13 (bits : BitVec 60) : Bool :=
  ((bits.getLsbD 12) ^^ (bits.getLsbD 13) ^^ (bits.getLsbD 52))

def parity14 (bits : BitVec 60) : Bool :=
  ((bits.getLsbD 13) ^^ (bits.getLsbD 14) ^^ (bits.getLsbD 53))

def parity15 (bits : BitVec 60) : Bool :=
  ((bits.getLsbD 14) ^^ (bits.getLsbD 15) ^^ (bits.getLsbD 54))

def parity16 (bits : BitVec 60) : Bool :=
  ((bits.getLsbD 15) ^^ (bits.getLsbD 16) ^^ (bits.getLsbD 55))

def parity17 (bits : BitVec 60) : Bool :=
  ((bits.getLsbD 16) ^^ (bits.getLsbD 17) ^^ (bits.getLsbD 56))

def parity18 (bits : BitVec 60) : Bool :=
  ((bits.getLsbD 17) ^^ (bits.getLsbD 18) ^^ (bits.getLsbD 57))

def parity19 (bits : BitVec 60) : Bool :=
  ((bits.getLsbD 18) ^^ (bits.getLsbD 58) ^^ (bits.getLsbD 59))

def parity20 (bits : BitVec 60) : Bool :=
  ((bits.getLsbD 19) ^^ (bits.getLsbD 20) ^^ (bits.getLsbD 57))

def parity21 (bits : BitVec 60) : Bool :=
  ((bits.getLsbD 19) ^^ (bits.getLsbD 58) ^^ (bits.getLsbD 59))

def parity22 (bits : BitVec 60) : Bool :=
  ((bits.getLsbD 20) ^^ (bits.getLsbD 21) ^^ (bits.getLsbD 56))

def parity23 (bits : BitVec 60) : Bool :=
  ((bits.getLsbD 21) ^^ (bits.getLsbD 22) ^^ (bits.getLsbD 55))

def parity24 (bits : BitVec 60) : Bool :=
  ((bits.getLsbD 22) ^^ (bits.getLsbD 23) ^^ (bits.getLsbD 54))

def parity25 (bits : BitVec 60) : Bool :=
  ((bits.getLsbD 23) ^^ (bits.getLsbD 24) ^^ (bits.getLsbD 53))

def parity26 (bits : BitVec 60) : Bool :=
  ((bits.getLsbD 24) ^^ (bits.getLsbD 25) ^^ (bits.getLsbD 52))

def parity27 (bits : BitVec 60) : Bool :=
  ((bits.getLsbD 25) ^^ (bits.getLsbD 26) ^^ (bits.getLsbD 51))

def parity28 (bits : BitVec 60) : Bool :=
  ((bits.getLsbD 26) ^^ (bits.getLsbD 27) ^^ (bits.getLsbD 50))

def parity29 (bits : BitVec 60) : Bool :=
  ((bits.getLsbD 27) ^^ (bits.getLsbD 28) ^^ (bits.getLsbD 49))

def parity30 (bits : BitVec 60) : Bool :=
  ((bits.getLsbD 28) ^^ (bits.getLsbD 29) ^^ (bits.getLsbD 48))

def parity31 (bits : BitVec 60) : Bool :=
  ((bits.getLsbD 29) ^^ (bits.getLsbD 30) ^^ (bits.getLsbD 47))

def parity32 (bits : BitVec 60) : Bool :=
  ((bits.getLsbD 30) ^^ (bits.getLsbD 31) ^^ (bits.getLsbD 46))

def parity33 (bits : BitVec 60) : Bool :=
  ((bits.getLsbD 31) ^^ (bits.getLsbD 32) ^^ (bits.getLsbD 45))

def parity34 (bits : BitVec 60) : Bool :=
  ((bits.getLsbD 32) ^^ (bits.getLsbD 33) ^^ (bits.getLsbD 44))

def parity35 (bits : BitVec 60) : Bool :=
  ((bits.getLsbD 33) ^^ (bits.getLsbD 34) ^^ (bits.getLsbD 43))

def parity36 (bits : BitVec 60) : Bool :=
  ((bits.getLsbD 34) ^^ (bits.getLsbD 35) ^^ (bits.getLsbD 42))

def parity37 (bits : BitVec 60) : Bool :=
  ((bits.getLsbD 35) ^^ (bits.getLsbD 36) ^^ (bits.getLsbD 41))

def parity38 (bits : BitVec 60) : Bool :=
  ((bits.getLsbD 36) ^^ (bits.getLsbD 37) ^^ (bits.getLsbD 40))

def parity39 (bits : BitVec 60) : Bool :=
  ((bits.getLsbD 37) ^^ (bits.getLsbD 38) ^^ (bits.getLsbD 39))

theorem sourceGroup0_exact (bits : BitVec 60) :
    (sourceGroup0 bits = true) ↔ (parity0 bits = true) := by
  unfold sourceGroup0 parity0
  cases h0 : bits.getLsbD 0 <;>
    cases h1 : bits.getLsbD 1 <;>
    cases h2 : bits.getLsbD 40 <;>
    simp [h0, h1, h2]

theorem sourceGroup1_exact (bits : BitVec 60) :
    (sourceGroup1 bits = true) ↔ (parity1 bits = true) := by
  unfold sourceGroup1 parity1
  cases h0 : bits.getLsbD 0 <;>
    cases h1 : bits.getLsbD 38 <;>
    cases h2 : bits.getLsbD 39 <;>
    simp [h0, h1, h2]

theorem sourceGroup2_exact (bits : BitVec 60) :
    (sourceGroup2 bits = true) ↔ (parity2 bits = true) := by
  unfold sourceGroup2 parity2
  cases h0 : bits.getLsbD 1 <;>
    cases h1 : bits.getLsbD 2 <;>
    cases h2 : bits.getLsbD 41 <;>
    simp [h0, h1, h2]

theorem sourceGroup3_exact (bits : BitVec 60) :
    (sourceGroup3 bits = true) ↔ (parity3 bits = true) := by
  unfold sourceGroup3 parity3
  cases h0 : bits.getLsbD 2 <;>
    cases h1 : bits.getLsbD 3 <;>
    cases h2 : bits.getLsbD 42 <;>
    simp [h0, h1, h2]

theorem sourceGroup4_exact (bits : BitVec 60) :
    (sourceGroup4 bits = true) ↔ (parity4 bits = true) := by
  unfold sourceGroup4 parity4
  cases h0 : bits.getLsbD 3 <;>
    cases h1 : bits.getLsbD 4 <;>
    cases h2 : bits.getLsbD 43 <;>
    simp [h0, h1, h2]

theorem sourceGroup5_exact (bits : BitVec 60) :
    (sourceGroup5 bits = true) ↔ (parity5 bits = true) := by
  unfold sourceGroup5 parity5
  cases h0 : bits.getLsbD 4 <;>
    cases h1 : bits.getLsbD 5 <;>
    cases h2 : bits.getLsbD 44 <;>
    simp [h0, h1, h2]

theorem sourceGroup6_exact (bits : BitVec 60) :
    (sourceGroup6 bits = true) ↔ (parity6 bits = true) := by
  unfold sourceGroup6 parity6
  cases h0 : bits.getLsbD 5 <;>
    cases h1 : bits.getLsbD 6 <;>
    cases h2 : bits.getLsbD 45 <;>
    simp [h0, h1, h2]

theorem sourceGroup7_exact (bits : BitVec 60) :
    (sourceGroup7 bits = true) ↔ (parity7 bits = true) := by
  unfold sourceGroup7 parity7
  cases h0 : bits.getLsbD 6 <;>
    cases h1 : bits.getLsbD 7 <;>
    cases h2 : bits.getLsbD 46 <;>
    simp [h0, h1, h2]

theorem sourceGroup8_exact (bits : BitVec 60) :
    (sourceGroup8 bits = true) ↔ (parity8 bits = true) := by
  unfold sourceGroup8 parity8
  cases h0 : bits.getLsbD 7 <;>
    cases h1 : bits.getLsbD 8 <;>
    cases h2 : bits.getLsbD 47 <;>
    simp [h0, h1, h2]

theorem sourceGroup9_exact (bits : BitVec 60) :
    (sourceGroup9 bits = true) ↔ (parity9 bits = true) := by
  unfold sourceGroup9 parity9
  cases h0 : bits.getLsbD 8 <;>
    cases h1 : bits.getLsbD 9 <;>
    cases h2 : bits.getLsbD 48 <;>
    simp [h0, h1, h2]

theorem sourceGroup10_exact (bits : BitVec 60) :
    (sourceGroup10 bits = true) ↔ (parity10 bits = true) := by
  unfold sourceGroup10 parity10
  cases h0 : bits.getLsbD 9 <;>
    cases h1 : bits.getLsbD 10 <;>
    cases h2 : bits.getLsbD 49 <;>
    simp [h0, h1, h2]

theorem sourceGroup11_exact (bits : BitVec 60) :
    (sourceGroup11 bits = true) ↔ (parity11 bits = true) := by
  unfold sourceGroup11 parity11
  cases h0 : bits.getLsbD 10 <;>
    cases h1 : bits.getLsbD 11 <;>
    cases h2 : bits.getLsbD 50 <;>
    simp [h0, h1, h2]

theorem sourceGroup12_exact (bits : BitVec 60) :
    (sourceGroup12 bits = true) ↔ (parity12 bits = true) := by
  unfold sourceGroup12 parity12
  cases h0 : bits.getLsbD 11 <;>
    cases h1 : bits.getLsbD 12 <;>
    cases h2 : bits.getLsbD 51 <;>
    simp [h0, h1, h2]

theorem sourceGroup13_exact (bits : BitVec 60) :
    (sourceGroup13 bits = true) ↔ (parity13 bits = true) := by
  unfold sourceGroup13 parity13
  cases h0 : bits.getLsbD 12 <;>
    cases h1 : bits.getLsbD 13 <;>
    cases h2 : bits.getLsbD 52 <;>
    simp [h0, h1, h2]

theorem sourceGroup14_exact (bits : BitVec 60) :
    (sourceGroup14 bits = true) ↔ (parity14 bits = true) := by
  unfold sourceGroup14 parity14
  cases h0 : bits.getLsbD 13 <;>
    cases h1 : bits.getLsbD 14 <;>
    cases h2 : bits.getLsbD 53 <;>
    simp [h0, h1, h2]

theorem sourceGroup15_exact (bits : BitVec 60) :
    (sourceGroup15 bits = true) ↔ (parity15 bits = true) := by
  unfold sourceGroup15 parity15
  cases h0 : bits.getLsbD 14 <;>
    cases h1 : bits.getLsbD 15 <;>
    cases h2 : bits.getLsbD 54 <;>
    simp [h0, h1, h2]

theorem sourceGroup16_exact (bits : BitVec 60) :
    (sourceGroup16 bits = true) ↔ (parity16 bits = true) := by
  unfold sourceGroup16 parity16
  cases h0 : bits.getLsbD 15 <;>
    cases h1 : bits.getLsbD 16 <;>
    cases h2 : bits.getLsbD 55 <;>
    simp [h0, h1, h2]

theorem sourceGroup17_exact (bits : BitVec 60) :
    (sourceGroup17 bits = true) ↔ (parity17 bits = true) := by
  unfold sourceGroup17 parity17
  cases h0 : bits.getLsbD 16 <;>
    cases h1 : bits.getLsbD 17 <;>
    cases h2 : bits.getLsbD 56 <;>
    simp [h0, h1, h2]

theorem sourceGroup18_exact (bits : BitVec 60) :
    (sourceGroup18 bits = true) ↔ (parity18 bits = true) := by
  unfold sourceGroup18 parity18
  cases h0 : bits.getLsbD 17 <;>
    cases h1 : bits.getLsbD 18 <;>
    cases h2 : bits.getLsbD 57 <;>
    simp [h0, h1, h2]

theorem sourceGroup19_exact (bits : BitVec 60) :
    (sourceGroup19 bits = true) ↔ (parity19 bits = true) := by
  unfold sourceGroup19 parity19
  cases h0 : bits.getLsbD 18 <;>
    cases h1 : bits.getLsbD 58 <;>
    cases h2 : bits.getLsbD 59 <;>
    simp [h0, h1, h2]

theorem sourceGroup20_exact (bits : BitVec 60) :
    (sourceGroup20 bits = true) ↔ (parity20 bits = true) := by
  unfold sourceGroup20 parity20
  cases h0 : bits.getLsbD 19 <;>
    cases h1 : bits.getLsbD 20 <;>
    cases h2 : bits.getLsbD 57 <;>
    simp [h0, h1, h2]

theorem sourceGroup21_exact (bits : BitVec 60) :
    (sourceGroup21 bits = true) ↔ (parity21 bits = true) := by
  unfold sourceGroup21 parity21
  cases h0 : bits.getLsbD 19 <;>
    cases h1 : bits.getLsbD 58 <;>
    cases h2 : bits.getLsbD 59 <;>
    simp [h0, h1, h2]

theorem sourceGroup22_exact (bits : BitVec 60) :
    (sourceGroup22 bits = true) ↔ (parity22 bits = true) := by
  unfold sourceGroup22 parity22
  cases h0 : bits.getLsbD 20 <;>
    cases h1 : bits.getLsbD 21 <;>
    cases h2 : bits.getLsbD 56 <;>
    simp [h0, h1, h2]

theorem sourceGroup23_exact (bits : BitVec 60) :
    (sourceGroup23 bits = true) ↔ (parity23 bits = true) := by
  unfold sourceGroup23 parity23
  cases h0 : bits.getLsbD 21 <;>
    cases h1 : bits.getLsbD 22 <;>
    cases h2 : bits.getLsbD 55 <;>
    simp [h0, h1, h2]

theorem sourceGroup24_exact (bits : BitVec 60) :
    (sourceGroup24 bits = true) ↔ (parity24 bits = true) := by
  unfold sourceGroup24 parity24
  cases h0 : bits.getLsbD 22 <;>
    cases h1 : bits.getLsbD 23 <;>
    cases h2 : bits.getLsbD 54 <;>
    simp [h0, h1, h2]

theorem sourceGroup25_exact (bits : BitVec 60) :
    (sourceGroup25 bits = true) ↔ (parity25 bits = true) := by
  unfold sourceGroup25 parity25
  cases h0 : bits.getLsbD 23 <;>
    cases h1 : bits.getLsbD 24 <;>
    cases h2 : bits.getLsbD 53 <;>
    simp [h0, h1, h2]

theorem sourceGroup26_exact (bits : BitVec 60) :
    (sourceGroup26 bits = true) ↔ (parity26 bits = true) := by
  unfold sourceGroup26 parity26
  cases h0 : bits.getLsbD 24 <;>
    cases h1 : bits.getLsbD 25 <;>
    cases h2 : bits.getLsbD 52 <;>
    simp [h0, h1, h2]

theorem sourceGroup27_exact (bits : BitVec 60) :
    (sourceGroup27 bits = true) ↔ (parity27 bits = true) := by
  unfold sourceGroup27 parity27
  cases h0 : bits.getLsbD 25 <;>
    cases h1 : bits.getLsbD 26 <;>
    cases h2 : bits.getLsbD 51 <;>
    simp [h0, h1, h2]

theorem sourceGroup28_exact (bits : BitVec 60) :
    (sourceGroup28 bits = true) ↔ (parity28 bits = true) := by
  unfold sourceGroup28 parity28
  cases h0 : bits.getLsbD 26 <;>
    cases h1 : bits.getLsbD 27 <;>
    cases h2 : bits.getLsbD 50 <;>
    simp [h0, h1, h2]

theorem sourceGroup29_exact (bits : BitVec 60) :
    (sourceGroup29 bits = true) ↔ (parity29 bits = true) := by
  unfold sourceGroup29 parity29
  cases h0 : bits.getLsbD 27 <;>
    cases h1 : bits.getLsbD 28 <;>
    cases h2 : bits.getLsbD 49 <;>
    simp [h0, h1, h2]

theorem sourceGroup30_exact (bits : BitVec 60) :
    (sourceGroup30 bits = true) ↔ (parity30 bits = true) := by
  unfold sourceGroup30 parity30
  cases h0 : bits.getLsbD 28 <;>
    cases h1 : bits.getLsbD 29 <;>
    cases h2 : bits.getLsbD 48 <;>
    simp [h0, h1, h2]

theorem sourceGroup31_exact (bits : BitVec 60) :
    (sourceGroup31 bits = true) ↔ (parity31 bits = true) := by
  unfold sourceGroup31 parity31
  cases h0 : bits.getLsbD 29 <;>
    cases h1 : bits.getLsbD 30 <;>
    cases h2 : bits.getLsbD 47 <;>
    simp [h0, h1, h2]

theorem sourceGroup32_exact (bits : BitVec 60) :
    (sourceGroup32 bits = true) ↔ (parity32 bits = true) := by
  unfold sourceGroup32 parity32
  cases h0 : bits.getLsbD 30 <;>
    cases h1 : bits.getLsbD 31 <;>
    cases h2 : bits.getLsbD 46 <;>
    simp [h0, h1, h2]

theorem sourceGroup33_exact (bits : BitVec 60) :
    (sourceGroup33 bits = true) ↔ (parity33 bits = true) := by
  unfold sourceGroup33 parity33
  cases h0 : bits.getLsbD 31 <;>
    cases h1 : bits.getLsbD 32 <;>
    cases h2 : bits.getLsbD 45 <;>
    simp [h0, h1, h2]

theorem sourceGroup34_exact (bits : BitVec 60) :
    (sourceGroup34 bits = true) ↔ (parity34 bits = true) := by
  unfold sourceGroup34 parity34
  cases h0 : bits.getLsbD 32 <;>
    cases h1 : bits.getLsbD 33 <;>
    cases h2 : bits.getLsbD 44 <;>
    simp [h0, h1, h2]

theorem sourceGroup35_exact (bits : BitVec 60) :
    (sourceGroup35 bits = true) ↔ (parity35 bits = true) := by
  unfold sourceGroup35 parity35
  cases h0 : bits.getLsbD 33 <;>
    cases h1 : bits.getLsbD 34 <;>
    cases h2 : bits.getLsbD 43 <;>
    simp [h0, h1, h2]

theorem sourceGroup36_exact (bits : BitVec 60) :
    (sourceGroup36 bits = true) ↔ (parity36 bits = true) := by
  unfold sourceGroup36 parity36
  cases h0 : bits.getLsbD 34 <;>
    cases h1 : bits.getLsbD 35 <;>
    cases h2 : bits.getLsbD 42 <;>
    simp [h0, h1, h2]

theorem sourceGroup37_exact (bits : BitVec 60) :
    (sourceGroup37 bits = true) ↔ (parity37 bits = true) := by
  unfold sourceGroup37 parity37
  cases h0 : bits.getLsbD 35 <;>
    cases h1 : bits.getLsbD 36 <;>
    cases h2 : bits.getLsbD 41 <;>
    simp [h0, h1, h2]

theorem sourceGroup38_exact (bits : BitVec 60) :
    (sourceGroup38 bits = true) ↔ (parity38 bits = true) := by
  unfold sourceGroup38 parity38
  cases h0 : bits.getLsbD 36 <;>
    cases h1 : bits.getLsbD 37 <;>
    cases h2 : bits.getLsbD 40 <;>
    simp [h0, h1, h2]

theorem sourceGroup39_exact (bits : BitVec 60) :
    (sourceGroup39 bits = true) ↔ (parity39 bits = false) := by
  unfold sourceGroup39 parity39
  cases h0 : bits.getLsbD 37 <;>
    cases h1 : bits.getLsbD 38 <;>
    cases h2 : bits.getLsbD 39 <;>
    simp [h0, h1, h2]

def sourceCNF (bits : BitVec 60) : Prop :=
    sourceGroup0 bits = true ∧
    sourceGroup1 bits = true ∧
    sourceGroup2 bits = true ∧
    sourceGroup3 bits = true ∧
    sourceGroup4 bits = true ∧
    sourceGroup5 bits = true ∧
    sourceGroup6 bits = true ∧
    sourceGroup7 bits = true ∧
    sourceGroup8 bits = true ∧
    sourceGroup9 bits = true ∧
    sourceGroup10 bits = true ∧
    sourceGroup11 bits = true ∧
    sourceGroup12 bits = true ∧
    sourceGroup13 bits = true ∧
    sourceGroup14 bits = true ∧
    sourceGroup15 bits = true ∧
    sourceGroup16 bits = true ∧
    sourceGroup17 bits = true ∧
    sourceGroup18 bits = true ∧
    sourceGroup19 bits = true ∧
    sourceGroup20 bits = true ∧
    sourceGroup21 bits = true ∧
    sourceGroup22 bits = true ∧
    sourceGroup23 bits = true ∧
    sourceGroup24 bits = true ∧
    sourceGroup25 bits = true ∧
    sourceGroup26 bits = true ∧
    sourceGroup27 bits = true ∧
    sourceGroup28 bits = true ∧
    sourceGroup29 bits = true ∧
    sourceGroup30 bits = true ∧
    sourceGroup31 bits = true ∧
    sourceGroup32 bits = true ∧
    sourceGroup33 bits = true ∧
    sourceGroup34 bits = true ∧
    sourceGroup35 bits = true ∧
    sourceGroup36 bits = true ∧
    sourceGroup37 bits = true ∧
    sourceGroup38 bits = true ∧
    sourceGroup39 bits = true

def certificateRows (bits : BitVec 60) : Prop :=
    parity0 bits = true ∧
    parity1 bits = true ∧
    parity2 bits = true ∧
    parity3 bits = true ∧
    parity4 bits = true ∧
    parity5 bits = true ∧
    parity6 bits = true ∧
    parity7 bits = true ∧
    parity8 bits = true ∧
    parity9 bits = true ∧
    parity10 bits = true ∧
    parity11 bits = true ∧
    parity12 bits = true ∧
    parity13 bits = true ∧
    parity14 bits = true ∧
    parity15 bits = true ∧
    parity16 bits = true ∧
    parity17 bits = true ∧
    parity18 bits = true ∧
    parity19 bits = true ∧
    parity20 bits = true ∧
    parity21 bits = true ∧
    parity22 bits = true ∧
    parity23 bits = true ∧
    parity24 bits = true ∧
    parity25 bits = true ∧
    parity26 bits = true ∧
    parity27 bits = true ∧
    parity28 bits = true ∧
    parity29 bits = true ∧
    parity30 bits = true ∧
    parity31 bits = true ∧
    parity32 bits = true ∧
    parity33 bits = true ∧
    parity34 bits = true ∧
    parity35 bits = true ∧
    parity36 bits = true ∧
    parity37 bits = true ∧
    parity38 bits = true ∧
    parity39 bits = false

theorem source_iff_certificate (bits : BitVec 60) :
    sourceCNF bits ↔ certificateRows bits := by
  simp only [sourceCNF, certificateRows, sourceGroup0_exact, sourceGroup1_exact, sourceGroup2_exact, sourceGroup3_exact, sourceGroup4_exact, sourceGroup5_exact, sourceGroup6_exact, sourceGroup7_exact, sourceGroup8_exact, sourceGroup9_exact, sourceGroup10_exact, sourceGroup11_exact, sourceGroup12_exact, sourceGroup13_exact, sourceGroup14_exact, sourceGroup15_exact, sourceGroup16_exact, sourceGroup17_exact, sourceGroup18_exact, sourceGroup19_exact, sourceGroup20_exact, sourceGroup21_exact, sourceGroup22_exact, sourceGroup23_exact, sourceGroup24_exact, sourceGroup25_exact, sourceGroup26_exact, sourceGroup27_exact, sourceGroup28_exact, sourceGroup29_exact, sourceGroup30_exact, sourceGroup31_exact, sourceGroup32_exact, sourceGroup33_exact, sourceGroup34_exact, sourceGroup35_exact, sourceGroup36_exact, sourceGroup37_exact, sourceGroup38_exact, sourceGroup39_exact]

def paritySum (bits : BitVec 60) : Bool :=
    parity0 bits ^^ parity1 bits ^^ parity2 bits ^^ parity3 bits ^^ parity4 bits ^^ parity5 bits ^^ parity6 bits ^^ parity7 bits ^^ parity8 bits ^^ parity9 bits ^^ parity10 bits ^^ parity11 bits ^^ parity12 bits ^^ parity13 bits ^^ parity14 bits ^^ parity15 bits ^^ parity16 bits ^^ parity17 bits ^^ parity18 bits ^^ parity19 bits ^^ parity20 bits ^^ parity21 bits ^^ parity22 bits ^^ parity23 bits ^^ parity24 bits ^^ parity25 bits ^^ parity26 bits ^^ parity27 bits ^^ parity28 bits ^^ parity29 bits ^^ parity30 bits ^^ parity31 bits ^^ parity32 bits ^^ parity33 bits ^^ parity34 bits ^^ parity35 bits ^^ parity36 bits ^^ parity37 bits ^^ parity38 bits ^^ parity39 bits

theorem certificate_inconsistent (bits : BitVec 60) :
    ¬ certificateRows bits := by
  intro hs
  rcases hs with ⟨h0, h1, h2, h3, h4, h5, h6, h7, h8, h9, h10, h11, h12, h13, h14, h15, h16, h17, h18, h19, h20, h21, h22, h23, h24, h25, h26, h27, h28, h29, h30, h31, h32, h33, h34, h35, h36, h37, h38, h39⟩
  have hsum : paritySum bits = true := by
    simp [paritySum, h0, h1, h2, h3, h4, h5, h6, h7, h8, h9, h10, h11, h12, h13, h14, h15, h16, h17, h18, h19, h20, h21, h22, h23, h24, h25, h26, h27, h28, h29, h30, h31, h32, h33, h34, h35, h36, h37, h38, h39]
  letI : Std.Associative (fun (x y : Bool) => x ^^ y) := ⟨Bool.xor_assoc⟩
  letI : Std.Commutative (fun (x y : Bool) => x ^^ y) := ⟨Bool.xor_comm⟩
  have hcancel : paritySum bits = false := by
    calc
      paritySum bits =
        ((bits.getLsbD 0) ^^ (bits.getLsbD 0)) ^^
        ((bits.getLsbD 1) ^^ (bits.getLsbD 1)) ^^
        ((bits.getLsbD 2) ^^ (bits.getLsbD 2)) ^^
        ((bits.getLsbD 3) ^^ (bits.getLsbD 3)) ^^
        ((bits.getLsbD 4) ^^ (bits.getLsbD 4)) ^^
        ((bits.getLsbD 5) ^^ (bits.getLsbD 5)) ^^
        ((bits.getLsbD 6) ^^ (bits.getLsbD 6)) ^^
        ((bits.getLsbD 7) ^^ (bits.getLsbD 7)) ^^
        ((bits.getLsbD 8) ^^ (bits.getLsbD 8)) ^^
        ((bits.getLsbD 9) ^^ (bits.getLsbD 9)) ^^
        ((bits.getLsbD 10) ^^ (bits.getLsbD 10)) ^^
        ((bits.getLsbD 11) ^^ (bits.getLsbD 11)) ^^
        ((bits.getLsbD 12) ^^ (bits.getLsbD 12)) ^^
        ((bits.getLsbD 13) ^^ (bits.getLsbD 13)) ^^
        ((bits.getLsbD 14) ^^ (bits.getLsbD 14)) ^^
        ((bits.getLsbD 15) ^^ (bits.getLsbD 15)) ^^
        ((bits.getLsbD 16) ^^ (bits.getLsbD 16)) ^^
        ((bits.getLsbD 17) ^^ (bits.getLsbD 17)) ^^
        ((bits.getLsbD 18) ^^ (bits.getLsbD 18)) ^^
        ((bits.getLsbD 19) ^^ (bits.getLsbD 19)) ^^
        ((bits.getLsbD 20) ^^ (bits.getLsbD 20)) ^^
        ((bits.getLsbD 21) ^^ (bits.getLsbD 21)) ^^
        ((bits.getLsbD 22) ^^ (bits.getLsbD 22)) ^^
        ((bits.getLsbD 23) ^^ (bits.getLsbD 23)) ^^
        ((bits.getLsbD 24) ^^ (bits.getLsbD 24)) ^^
        ((bits.getLsbD 25) ^^ (bits.getLsbD 25)) ^^
        ((bits.getLsbD 26) ^^ (bits.getLsbD 26)) ^^
        ((bits.getLsbD 27) ^^ (bits.getLsbD 27)) ^^
        ((bits.getLsbD 28) ^^ (bits.getLsbD 28)) ^^
        ((bits.getLsbD 29) ^^ (bits.getLsbD 29)) ^^
        ((bits.getLsbD 30) ^^ (bits.getLsbD 30)) ^^
        ((bits.getLsbD 31) ^^ (bits.getLsbD 31)) ^^
        ((bits.getLsbD 32) ^^ (bits.getLsbD 32)) ^^
        ((bits.getLsbD 33) ^^ (bits.getLsbD 33)) ^^
        ((bits.getLsbD 34) ^^ (bits.getLsbD 34)) ^^
        ((bits.getLsbD 35) ^^ (bits.getLsbD 35)) ^^
        ((bits.getLsbD 36) ^^ (bits.getLsbD 36)) ^^
        ((bits.getLsbD 37) ^^ (bits.getLsbD 37)) ^^
        ((bits.getLsbD 38) ^^ (bits.getLsbD 38)) ^^
        ((bits.getLsbD 39) ^^ (bits.getLsbD 39)) ^^
        ((bits.getLsbD 40) ^^ (bits.getLsbD 40)) ^^
        ((bits.getLsbD 41) ^^ (bits.getLsbD 41)) ^^
        ((bits.getLsbD 42) ^^ (bits.getLsbD 42)) ^^
        ((bits.getLsbD 43) ^^ (bits.getLsbD 43)) ^^
        ((bits.getLsbD 44) ^^ (bits.getLsbD 44)) ^^
        ((bits.getLsbD 45) ^^ (bits.getLsbD 45)) ^^
        ((bits.getLsbD 46) ^^ (bits.getLsbD 46)) ^^
        ((bits.getLsbD 47) ^^ (bits.getLsbD 47)) ^^
        ((bits.getLsbD 48) ^^ (bits.getLsbD 48)) ^^
        ((bits.getLsbD 49) ^^ (bits.getLsbD 49)) ^^
        ((bits.getLsbD 50) ^^ (bits.getLsbD 50)) ^^
        ((bits.getLsbD 51) ^^ (bits.getLsbD 51)) ^^
        ((bits.getLsbD 52) ^^ (bits.getLsbD 52)) ^^
        ((bits.getLsbD 53) ^^ (bits.getLsbD 53)) ^^
        ((bits.getLsbD 54) ^^ (bits.getLsbD 54)) ^^
        ((bits.getLsbD 55) ^^ (bits.getLsbD 55)) ^^
        ((bits.getLsbD 56) ^^ (bits.getLsbD 56)) ^^
        ((bits.getLsbD 57) ^^ (bits.getLsbD 57)) ^^
        ((bits.getLsbD 58) ^^ (bits.getLsbD 58)) ^^
        ((bits.getLsbD 59) ^^ (bits.getLsbD 59)) := by
          unfold paritySum parity0 parity1 parity2 parity3 parity4 parity5 parity6 parity7 parity8 parity9 parity10 parity11 parity12 parity13 parity14 parity15 parity16 parity17 parity18 parity19 parity20 parity21 parity22 parity23 parity24 parity25 parity26 parity27 parity28 parity29 parity30 parity31 parity32 parity33 parity34 parity35 parity36 parity37 parity38 parity39
          ac_rfl
      _ = false := by
        simp [Bool.xor_self, Bool.xor_false, Bool.false_xor]
  have impossible : false = true := hcancel.symm.trans hsum
  cases impossible

theorem source_unsat (bits : BitVec 60) : ¬ sourceCNF bits := by
  intro hs
  exact certificate_inconsistent bits ((source_iff_certificate bits).mp hs)

end Witnora.Dubois20

#print axioms Witnora.Dubois20.source_unsat

