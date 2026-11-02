import Lean

set_option maxHeartbeats 2000000
set_option maxRecDepth 4096
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

def traceRow40 (bits : BitVec 60) : Bool := ((bits.getLsbD 17) ^^ (bits.getLsbD 18) ^^ (bits.getLsbD 19) ^^ (bits.getLsbD 20))

def traceRow41 (bits : BitVec 60) : Bool := ((bits.getLsbD 18) ^^ (bits.getLsbD 19))

def traceRow42 (bits : BitVec 60) : Bool := ((bits.getLsbD 16) ^^ (bits.getLsbD 17) ^^ (bits.getLsbD 20) ^^ (bits.getLsbD 21))

def traceRow43 (bits : BitVec 60) : Bool := ((bits.getLsbD 15) ^^ (bits.getLsbD 16) ^^ (bits.getLsbD 21) ^^ (bits.getLsbD 22))

def traceRow44 (bits : BitVec 60) : Bool := ((bits.getLsbD 14) ^^ (bits.getLsbD 15) ^^ (bits.getLsbD 22) ^^ (bits.getLsbD 23))

def traceRow45 (bits : BitVec 60) : Bool := ((bits.getLsbD 13) ^^ (bits.getLsbD 14) ^^ (bits.getLsbD 23) ^^ (bits.getLsbD 24))

def traceRow46 (bits : BitVec 60) : Bool := ((bits.getLsbD 12) ^^ (bits.getLsbD 13) ^^ (bits.getLsbD 24) ^^ (bits.getLsbD 25))

def traceRow47 (bits : BitVec 60) : Bool := ((bits.getLsbD 11) ^^ (bits.getLsbD 12) ^^ (bits.getLsbD 25) ^^ (bits.getLsbD 26))

def traceRow48 (bits : BitVec 60) : Bool := ((bits.getLsbD 10) ^^ (bits.getLsbD 11) ^^ (bits.getLsbD 26) ^^ (bits.getLsbD 27))

def traceRow49 (bits : BitVec 60) : Bool := ((bits.getLsbD 9) ^^ (bits.getLsbD 10) ^^ (bits.getLsbD 27) ^^ (bits.getLsbD 28))

def traceRow50 (bits : BitVec 60) : Bool := ((bits.getLsbD 8) ^^ (bits.getLsbD 9) ^^ (bits.getLsbD 28) ^^ (bits.getLsbD 29))

def traceRow51 (bits : BitVec 60) : Bool := ((bits.getLsbD 7) ^^ (bits.getLsbD 8) ^^ (bits.getLsbD 29) ^^ (bits.getLsbD 30))

def traceRow52 (bits : BitVec 60) : Bool := ((bits.getLsbD 6) ^^ (bits.getLsbD 7) ^^ (bits.getLsbD 30) ^^ (bits.getLsbD 31))

def traceRow53 (bits : BitVec 60) : Bool := ((bits.getLsbD 5) ^^ (bits.getLsbD 6) ^^ (bits.getLsbD 31) ^^ (bits.getLsbD 32))

def traceRow54 (bits : BitVec 60) : Bool := ((bits.getLsbD 4) ^^ (bits.getLsbD 5) ^^ (bits.getLsbD 32) ^^ (bits.getLsbD 33))

def traceRow55 (bits : BitVec 60) : Bool := ((bits.getLsbD 3) ^^ (bits.getLsbD 4) ^^ (bits.getLsbD 33) ^^ (bits.getLsbD 34))

def traceRow56 (bits : BitVec 60) : Bool := ((bits.getLsbD 2) ^^ (bits.getLsbD 3) ^^ (bits.getLsbD 34) ^^ (bits.getLsbD 35))

def traceRow57 (bits : BitVec 60) : Bool := ((bits.getLsbD 1) ^^ (bits.getLsbD 2) ^^ (bits.getLsbD 35) ^^ (bits.getLsbD 36))

def traceRow58 (bits : BitVec 60) : Bool := ((bits.getLsbD 0) ^^ (bits.getLsbD 1) ^^ (bits.getLsbD 36) ^^ (bits.getLsbD 37))

def traceRow59 (bits : BitVec 60) : Bool := ((bits.getLsbD 0) ^^ (bits.getLsbD 37))

def traceRow60 (bits : BitVec 60) : Bool := ((bits.getLsbD 1) ^^ (bits.getLsbD 36))

def traceRow61 (bits : BitVec 60) : Bool := ((bits.getLsbD 2) ^^ (bits.getLsbD 35))

def traceRow62 (bits : BitVec 60) : Bool := ((bits.getLsbD 3) ^^ (bits.getLsbD 34))

def traceRow63 (bits : BitVec 60) : Bool := ((bits.getLsbD 4) ^^ (bits.getLsbD 33))

def traceRow64 (bits : BitVec 60) : Bool := ((bits.getLsbD 5) ^^ (bits.getLsbD 32))

def traceRow65 (bits : BitVec 60) : Bool := ((bits.getLsbD 6) ^^ (bits.getLsbD 31))

def traceRow66 (bits : BitVec 60) : Bool := ((bits.getLsbD 7) ^^ (bits.getLsbD 30))

def traceRow67 (bits : BitVec 60) : Bool := ((bits.getLsbD 8) ^^ (bits.getLsbD 29))

def traceRow68 (bits : BitVec 60) : Bool := ((bits.getLsbD 9) ^^ (bits.getLsbD 28))

def traceRow69 (bits : BitVec 60) : Bool := ((bits.getLsbD 10) ^^ (bits.getLsbD 27))

def traceRow70 (bits : BitVec 60) : Bool := ((bits.getLsbD 11) ^^ (bits.getLsbD 26))

def traceRow71 (bits : BitVec 60) : Bool := ((bits.getLsbD 12) ^^ (bits.getLsbD 25))

def traceRow72 (bits : BitVec 60) : Bool := ((bits.getLsbD 13) ^^ (bits.getLsbD 24))

def traceRow73 (bits : BitVec 60) : Bool := ((bits.getLsbD 14) ^^ (bits.getLsbD 23))

def traceRow74 (bits : BitVec 60) : Bool := ((bits.getLsbD 15) ^^ (bits.getLsbD 22))

def traceRow75 (bits : BitVec 60) : Bool := ((bits.getLsbD 16) ^^ (bits.getLsbD 21))

def traceRow76 (bits : BitVec 60) : Bool := ((bits.getLsbD 17) ^^ (bits.getLsbD 20))

def traceRow77 (bits : BitVec 60) : Bool := ((bits.getLsbD 18) ^^ (bits.getLsbD 19))

def traceRow78 (bits : BitVec 60) : Bool := false

theorem traceStep40 (bits : BitVec 60)
    (ha : parity20 bits = true)
    (hb : parity18 bits = true) :
    traceRow40 bits = false := by
  have hxor : traceRow40 bits = (parity20 bits ^^ parity18 bits) := by
    cases h0 : bits.getLsbD 17 <;>
    cases h1 : bits.getLsbD 18 <;>
    cases h2 : bits.getLsbD 19 <;>
    cases h3 : bits.getLsbD 20 <;>
    cases h4 : bits.getLsbD 57 <;>
    simp [traceRow40, parity20, parity18]
  simp [hxor, ha, hb]

theorem traceStep41 (bits : BitVec 60)
    (ha : parity21 bits = true)
    (hb : parity19 bits = true) :
    traceRow41 bits = false := by
  have hxor : traceRow41 bits = (parity21 bits ^^ parity19 bits) := by
    cases h0 : bits.getLsbD 18 <;>
    cases h1 : bits.getLsbD 19 <;>
    cases h2 : bits.getLsbD 58 <;>
    cases h3 : bits.getLsbD 59 <;>
    simp [traceRow41, parity21, parity19]
  simp [hxor, ha, hb]

theorem traceStep42 (bits : BitVec 60)
    (ha : parity22 bits = true)
    (hb : parity17 bits = true) :
    traceRow42 bits = false := by
  have hxor : traceRow42 bits = (parity22 bits ^^ parity17 bits) := by
    cases h0 : bits.getLsbD 16 <;>
    cases h1 : bits.getLsbD 17 <;>
    cases h2 : bits.getLsbD 20 <;>
    cases h3 : bits.getLsbD 21 <;>
    cases h4 : bits.getLsbD 56 <;>
    simp [traceRow42, parity22, parity17]
  simp [hxor, ha, hb]

theorem traceStep43 (bits : BitVec 60)
    (ha : parity23 bits = true)
    (hb : parity16 bits = true) :
    traceRow43 bits = false := by
  have hxor : traceRow43 bits = (parity23 bits ^^ parity16 bits) := by
    cases h0 : bits.getLsbD 15 <;>
    cases h1 : bits.getLsbD 16 <;>
    cases h2 : bits.getLsbD 21 <;>
    cases h3 : bits.getLsbD 22 <;>
    cases h4 : bits.getLsbD 55 <;>
    simp [traceRow43, parity23, parity16]
  simp [hxor, ha, hb]

theorem traceStep44 (bits : BitVec 60)
    (ha : parity24 bits = true)
    (hb : parity15 bits = true) :
    traceRow44 bits = false := by
  have hxor : traceRow44 bits = (parity24 bits ^^ parity15 bits) := by
    cases h0 : bits.getLsbD 14 <;>
    cases h1 : bits.getLsbD 15 <;>
    cases h2 : bits.getLsbD 22 <;>
    cases h3 : bits.getLsbD 23 <;>
    cases h4 : bits.getLsbD 54 <;>
    simp [traceRow44, parity24, parity15]
  simp [hxor, ha, hb]

theorem traceStep45 (bits : BitVec 60)
    (ha : parity25 bits = true)
    (hb : parity14 bits = true) :
    traceRow45 bits = false := by
  have hxor : traceRow45 bits = (parity25 bits ^^ parity14 bits) := by
    cases h0 : bits.getLsbD 13 <;>
    cases h1 : bits.getLsbD 14 <;>
    cases h2 : bits.getLsbD 23 <;>
    cases h3 : bits.getLsbD 24 <;>
    cases h4 : bits.getLsbD 53 <;>
    simp [traceRow45, parity25, parity14]
  simp [hxor, ha, hb]

theorem traceStep46 (bits : BitVec 60)
    (ha : parity26 bits = true)
    (hb : parity13 bits = true) :
    traceRow46 bits = false := by
  have hxor : traceRow46 bits = (parity26 bits ^^ parity13 bits) := by
    cases h0 : bits.getLsbD 12 <;>
    cases h1 : bits.getLsbD 13 <;>
    cases h2 : bits.getLsbD 24 <;>
    cases h3 : bits.getLsbD 25 <;>
    cases h4 : bits.getLsbD 52 <;>
    simp [traceRow46, parity26, parity13]
  simp [hxor, ha, hb]

theorem traceStep47 (bits : BitVec 60)
    (ha : parity27 bits = true)
    (hb : parity12 bits = true) :
    traceRow47 bits = false := by
  have hxor : traceRow47 bits = (parity27 bits ^^ parity12 bits) := by
    cases h0 : bits.getLsbD 11 <;>
    cases h1 : bits.getLsbD 12 <;>
    cases h2 : bits.getLsbD 25 <;>
    cases h3 : bits.getLsbD 26 <;>
    cases h4 : bits.getLsbD 51 <;>
    simp [traceRow47, parity27, parity12]
  simp [hxor, ha, hb]

theorem traceStep48 (bits : BitVec 60)
    (ha : parity28 bits = true)
    (hb : parity11 bits = true) :
    traceRow48 bits = false := by
  have hxor : traceRow48 bits = (parity28 bits ^^ parity11 bits) := by
    cases h0 : bits.getLsbD 10 <;>
    cases h1 : bits.getLsbD 11 <;>
    cases h2 : bits.getLsbD 26 <;>
    cases h3 : bits.getLsbD 27 <;>
    cases h4 : bits.getLsbD 50 <;>
    simp [traceRow48, parity28, parity11]
  simp [hxor, ha, hb]

theorem traceStep49 (bits : BitVec 60)
    (ha : parity29 bits = true)
    (hb : parity10 bits = true) :
    traceRow49 bits = false := by
  have hxor : traceRow49 bits = (parity29 bits ^^ parity10 bits) := by
    cases h0 : bits.getLsbD 9 <;>
    cases h1 : bits.getLsbD 10 <;>
    cases h2 : bits.getLsbD 27 <;>
    cases h3 : bits.getLsbD 28 <;>
    cases h4 : bits.getLsbD 49 <;>
    simp [traceRow49, parity29, parity10]
  simp [hxor, ha, hb]

theorem traceStep50 (bits : BitVec 60)
    (ha : parity30 bits = true)
    (hb : parity9 bits = true) :
    traceRow50 bits = false := by
  have hxor : traceRow50 bits = (parity30 bits ^^ parity9 bits) := by
    cases h0 : bits.getLsbD 8 <;>
    cases h1 : bits.getLsbD 9 <;>
    cases h2 : bits.getLsbD 28 <;>
    cases h3 : bits.getLsbD 29 <;>
    cases h4 : bits.getLsbD 48 <;>
    simp [traceRow50, parity30, parity9]
  simp [hxor, ha, hb]

theorem traceStep51 (bits : BitVec 60)
    (ha : parity31 bits = true)
    (hb : parity8 bits = true) :
    traceRow51 bits = false := by
  have hxor : traceRow51 bits = (parity31 bits ^^ parity8 bits) := by
    cases h0 : bits.getLsbD 7 <;>
    cases h1 : bits.getLsbD 8 <;>
    cases h2 : bits.getLsbD 29 <;>
    cases h3 : bits.getLsbD 30 <;>
    cases h4 : bits.getLsbD 47 <;>
    simp [traceRow51, parity31, parity8]
  simp [hxor, ha, hb]

theorem traceStep52 (bits : BitVec 60)
    (ha : parity32 bits = true)
    (hb : parity7 bits = true) :
    traceRow52 bits = false := by
  have hxor : traceRow52 bits = (parity32 bits ^^ parity7 bits) := by
    cases h0 : bits.getLsbD 6 <;>
    cases h1 : bits.getLsbD 7 <;>
    cases h2 : bits.getLsbD 30 <;>
    cases h3 : bits.getLsbD 31 <;>
    cases h4 : bits.getLsbD 46 <;>
    simp [traceRow52, parity32, parity7]
  simp [hxor, ha, hb]

theorem traceStep53 (bits : BitVec 60)
    (ha : parity33 bits = true)
    (hb : parity6 bits = true) :
    traceRow53 bits = false := by
  have hxor : traceRow53 bits = (parity33 bits ^^ parity6 bits) := by
    cases h0 : bits.getLsbD 5 <;>
    cases h1 : bits.getLsbD 6 <;>
    cases h2 : bits.getLsbD 31 <;>
    cases h3 : bits.getLsbD 32 <;>
    cases h4 : bits.getLsbD 45 <;>
    simp [traceRow53, parity33, parity6]
  simp [hxor, ha, hb]

theorem traceStep54 (bits : BitVec 60)
    (ha : parity34 bits = true)
    (hb : parity5 bits = true) :
    traceRow54 bits = false := by
  have hxor : traceRow54 bits = (parity34 bits ^^ parity5 bits) := by
    cases h0 : bits.getLsbD 4 <;>
    cases h1 : bits.getLsbD 5 <;>
    cases h2 : bits.getLsbD 32 <;>
    cases h3 : bits.getLsbD 33 <;>
    cases h4 : bits.getLsbD 44 <;>
    simp [traceRow54, parity34, parity5]
  simp [hxor, ha, hb]

theorem traceStep55 (bits : BitVec 60)
    (ha : parity35 bits = true)
    (hb : parity4 bits = true) :
    traceRow55 bits = false := by
  have hxor : traceRow55 bits = (parity35 bits ^^ parity4 bits) := by
    cases h0 : bits.getLsbD 3 <;>
    cases h1 : bits.getLsbD 4 <;>
    cases h2 : bits.getLsbD 33 <;>
    cases h3 : bits.getLsbD 34 <;>
    cases h4 : bits.getLsbD 43 <;>
    simp [traceRow55, parity35, parity4]
  simp [hxor, ha, hb]

theorem traceStep56 (bits : BitVec 60)
    (ha : parity36 bits = true)
    (hb : parity3 bits = true) :
    traceRow56 bits = false := by
  have hxor : traceRow56 bits = (parity36 bits ^^ parity3 bits) := by
    cases h0 : bits.getLsbD 2 <;>
    cases h1 : bits.getLsbD 3 <;>
    cases h2 : bits.getLsbD 34 <;>
    cases h3 : bits.getLsbD 35 <;>
    cases h4 : bits.getLsbD 42 <;>
    simp [traceRow56, parity36, parity3]
  simp [hxor, ha, hb]

theorem traceStep57 (bits : BitVec 60)
    (ha : parity37 bits = true)
    (hb : parity2 bits = true) :
    traceRow57 bits = false := by
  have hxor : traceRow57 bits = (parity37 bits ^^ parity2 bits) := by
    cases h0 : bits.getLsbD 1 <;>
    cases h1 : bits.getLsbD 2 <;>
    cases h2 : bits.getLsbD 35 <;>
    cases h3 : bits.getLsbD 36 <;>
    cases h4 : bits.getLsbD 41 <;>
    simp [traceRow57, parity37, parity2]
  simp [hxor, ha, hb]

theorem traceStep58 (bits : BitVec 60)
    (ha : parity38 bits = true)
    (hb : parity0 bits = true) :
    traceRow58 bits = false := by
  have hxor : traceRow58 bits = (parity38 bits ^^ parity0 bits) := by
    cases h0 : bits.getLsbD 0 <;>
    cases h1 : bits.getLsbD 1 <;>
    cases h2 : bits.getLsbD 36 <;>
    cases h3 : bits.getLsbD 37 <;>
    cases h4 : bits.getLsbD 40 <;>
    simp [traceRow58, parity38, parity0]
  simp [hxor, ha, hb]

theorem traceStep59 (bits : BitVec 60)
    (ha : parity39 bits = false)
    (hb : parity1 bits = true) :
    traceRow59 bits = true := by
  have hxor : traceRow59 bits = (parity39 bits ^^ parity1 bits) := by
    cases h0 : bits.getLsbD 0 <;>
    cases h1 : bits.getLsbD 37 <;>
    cases h2 : bits.getLsbD 38 <;>
    cases h3 : bits.getLsbD 39 <;>
    simp [traceRow59, parity39, parity1]
  simp [hxor, ha, hb]

theorem traceStep60 (bits : BitVec 60)
    (ha : traceRow59 bits = true)
    (hb : traceRow58 bits = false) :
    traceRow60 bits = true := by
  have hxor : traceRow60 bits = (traceRow59 bits ^^ traceRow58 bits) := by
    cases h0 : bits.getLsbD 0 <;>
    cases h1 : bits.getLsbD 1 <;>
    cases h2 : bits.getLsbD 36 <;>
    cases h3 : bits.getLsbD 37 <;>
    simp [traceRow60, traceRow59, traceRow58]
  simp [hxor, ha, hb]

theorem traceStep61 (bits : BitVec 60)
    (ha : traceRow60 bits = true)
    (hb : traceRow57 bits = false) :
    traceRow61 bits = true := by
  have hxor : traceRow61 bits = (traceRow60 bits ^^ traceRow57 bits) := by
    cases h0 : bits.getLsbD 1 <;>
    cases h1 : bits.getLsbD 2 <;>
    cases h2 : bits.getLsbD 35 <;>
    cases h3 : bits.getLsbD 36 <;>
    simp [traceRow61, traceRow60, traceRow57]
  simp [hxor, ha, hb]

theorem traceStep62 (bits : BitVec 60)
    (ha : traceRow61 bits = true)
    (hb : traceRow56 bits = false) :
    traceRow62 bits = true := by
  have hxor : traceRow62 bits = (traceRow61 bits ^^ traceRow56 bits) := by
    cases h0 : bits.getLsbD 2 <;>
    cases h1 : bits.getLsbD 3 <;>
    cases h2 : bits.getLsbD 34 <;>
    cases h3 : bits.getLsbD 35 <;>
    simp [traceRow62, traceRow61, traceRow56]
  simp [hxor, ha, hb]

theorem traceStep63 (bits : BitVec 60)
    (ha : traceRow62 bits = true)
    (hb : traceRow55 bits = false) :
    traceRow63 bits = true := by
  have hxor : traceRow63 bits = (traceRow62 bits ^^ traceRow55 bits) := by
    cases h0 : bits.getLsbD 3 <;>
    cases h1 : bits.getLsbD 4 <;>
    cases h2 : bits.getLsbD 33 <;>
    cases h3 : bits.getLsbD 34 <;>
    simp [traceRow63, traceRow62, traceRow55]
  simp [hxor, ha, hb]

theorem traceStep64 (bits : BitVec 60)
    (ha : traceRow63 bits = true)
    (hb : traceRow54 bits = false) :
    traceRow64 bits = true := by
  have hxor : traceRow64 bits = (traceRow63 bits ^^ traceRow54 bits) := by
    cases h0 : bits.getLsbD 4 <;>
    cases h1 : bits.getLsbD 5 <;>
    cases h2 : bits.getLsbD 32 <;>
    cases h3 : bits.getLsbD 33 <;>
    simp [traceRow64, traceRow63, traceRow54]
  simp [hxor, ha, hb]

theorem traceStep65 (bits : BitVec 60)
    (ha : traceRow64 bits = true)
    (hb : traceRow53 bits = false) :
    traceRow65 bits = true := by
  have hxor : traceRow65 bits = (traceRow64 bits ^^ traceRow53 bits) := by
    cases h0 : bits.getLsbD 5 <;>
    cases h1 : bits.getLsbD 6 <;>
    cases h2 : bits.getLsbD 31 <;>
    cases h3 : bits.getLsbD 32 <;>
    simp [traceRow65, traceRow64, traceRow53]
  simp [hxor, ha, hb]

theorem traceStep66 (bits : BitVec 60)
    (ha : traceRow65 bits = true)
    (hb : traceRow52 bits = false) :
    traceRow66 bits = true := by
  have hxor : traceRow66 bits = (traceRow65 bits ^^ traceRow52 bits) := by
    cases h0 : bits.getLsbD 6 <;>
    cases h1 : bits.getLsbD 7 <;>
    cases h2 : bits.getLsbD 30 <;>
    cases h3 : bits.getLsbD 31 <;>
    simp [traceRow66, traceRow65, traceRow52]
  simp [hxor, ha, hb]

theorem traceStep67 (bits : BitVec 60)
    (ha : traceRow66 bits = true)
    (hb : traceRow51 bits = false) :
    traceRow67 bits = true := by
  have hxor : traceRow67 bits = (traceRow66 bits ^^ traceRow51 bits) := by
    cases h0 : bits.getLsbD 7 <;>
    cases h1 : bits.getLsbD 8 <;>
    cases h2 : bits.getLsbD 29 <;>
    cases h3 : bits.getLsbD 30 <;>
    simp [traceRow67, traceRow66, traceRow51]
  simp [hxor, ha, hb]

theorem traceStep68 (bits : BitVec 60)
    (ha : traceRow67 bits = true)
    (hb : traceRow50 bits = false) :
    traceRow68 bits = true := by
  have hxor : traceRow68 bits = (traceRow67 bits ^^ traceRow50 bits) := by
    cases h0 : bits.getLsbD 8 <;>
    cases h1 : bits.getLsbD 9 <;>
    cases h2 : bits.getLsbD 28 <;>
    cases h3 : bits.getLsbD 29 <;>
    simp [traceRow68, traceRow67, traceRow50]
  simp [hxor, ha, hb]

theorem traceStep69 (bits : BitVec 60)
    (ha : traceRow68 bits = true)
    (hb : traceRow49 bits = false) :
    traceRow69 bits = true := by
  have hxor : traceRow69 bits = (traceRow68 bits ^^ traceRow49 bits) := by
    cases h0 : bits.getLsbD 9 <;>
    cases h1 : bits.getLsbD 10 <;>
    cases h2 : bits.getLsbD 27 <;>
    cases h3 : bits.getLsbD 28 <;>
    simp [traceRow69, traceRow68, traceRow49]
  simp [hxor, ha, hb]

theorem traceStep70 (bits : BitVec 60)
    (ha : traceRow69 bits = true)
    (hb : traceRow48 bits = false) :
    traceRow70 bits = true := by
  have hxor : traceRow70 bits = (traceRow69 bits ^^ traceRow48 bits) := by
    cases h0 : bits.getLsbD 10 <;>
    cases h1 : bits.getLsbD 11 <;>
    cases h2 : bits.getLsbD 26 <;>
    cases h3 : bits.getLsbD 27 <;>
    simp [traceRow70, traceRow69, traceRow48]
  simp [hxor, ha, hb]

theorem traceStep71 (bits : BitVec 60)
    (ha : traceRow70 bits = true)
    (hb : traceRow47 bits = false) :
    traceRow71 bits = true := by
  have hxor : traceRow71 bits = (traceRow70 bits ^^ traceRow47 bits) := by
    cases h0 : bits.getLsbD 11 <;>
    cases h1 : bits.getLsbD 12 <;>
    cases h2 : bits.getLsbD 25 <;>
    cases h3 : bits.getLsbD 26 <;>
    simp [traceRow71, traceRow70, traceRow47]
  simp [hxor, ha, hb]

theorem traceStep72 (bits : BitVec 60)
    (ha : traceRow71 bits = true)
    (hb : traceRow46 bits = false) :
    traceRow72 bits = true := by
  have hxor : traceRow72 bits = (traceRow71 bits ^^ traceRow46 bits) := by
    cases h0 : bits.getLsbD 12 <;>
    cases h1 : bits.getLsbD 13 <;>
    cases h2 : bits.getLsbD 24 <;>
    cases h3 : bits.getLsbD 25 <;>
    simp [traceRow72, traceRow71, traceRow46]
  simp [hxor, ha, hb]

theorem traceStep73 (bits : BitVec 60)
    (ha : traceRow72 bits = true)
    (hb : traceRow45 bits = false) :
    traceRow73 bits = true := by
  have hxor : traceRow73 bits = (traceRow72 bits ^^ traceRow45 bits) := by
    cases h0 : bits.getLsbD 13 <;>
    cases h1 : bits.getLsbD 14 <;>
    cases h2 : bits.getLsbD 23 <;>
    cases h3 : bits.getLsbD 24 <;>
    simp [traceRow73, traceRow72, traceRow45]
  simp [hxor, ha, hb]

theorem traceStep74 (bits : BitVec 60)
    (ha : traceRow73 bits = true)
    (hb : traceRow44 bits = false) :
    traceRow74 bits = true := by
  have hxor : traceRow74 bits = (traceRow73 bits ^^ traceRow44 bits) := by
    cases h0 : bits.getLsbD 14 <;>
    cases h1 : bits.getLsbD 15 <;>
    cases h2 : bits.getLsbD 22 <;>
    cases h3 : bits.getLsbD 23 <;>
    simp [traceRow74, traceRow73, traceRow44]
  simp [hxor, ha, hb]

theorem traceStep75 (bits : BitVec 60)
    (ha : traceRow74 bits = true)
    (hb : traceRow43 bits = false) :
    traceRow75 bits = true := by
  have hxor : traceRow75 bits = (traceRow74 bits ^^ traceRow43 bits) := by
    cases h0 : bits.getLsbD 15 <;>
    cases h1 : bits.getLsbD 16 <;>
    cases h2 : bits.getLsbD 21 <;>
    cases h3 : bits.getLsbD 22 <;>
    simp [traceRow75, traceRow74, traceRow43]
  simp [hxor, ha, hb]

theorem traceStep76 (bits : BitVec 60)
    (ha : traceRow75 bits = true)
    (hb : traceRow42 bits = false) :
    traceRow76 bits = true := by
  have hxor : traceRow76 bits = (traceRow75 bits ^^ traceRow42 bits) := by
    cases h0 : bits.getLsbD 16 <;>
    cases h1 : bits.getLsbD 17 <;>
    cases h2 : bits.getLsbD 20 <;>
    cases h3 : bits.getLsbD 21 <;>
    simp [traceRow76, traceRow75, traceRow42]
  simp [hxor, ha, hb]

theorem traceStep77 (bits : BitVec 60)
    (ha : traceRow76 bits = true)
    (hb : traceRow40 bits = false) :
    traceRow77 bits = true := by
  have hxor : traceRow77 bits = (traceRow76 bits ^^ traceRow40 bits) := by
    cases h0 : bits.getLsbD 17 <;>
    cases h1 : bits.getLsbD 18 <;>
    cases h2 : bits.getLsbD 19 <;>
    cases h3 : bits.getLsbD 20 <;>
    simp [traceRow77, traceRow76, traceRow40]
  simp [hxor, ha, hb]

theorem traceStep78 (bits : BitVec 60)
    (ha : traceRow77 bits = true)
    (hb : traceRow41 bits = false) :
    traceRow78 bits = true := by
  have hxor : traceRow78 bits = (traceRow77 bits ^^ traceRow41 bits) := by
    cases h0 : bits.getLsbD 18 <;>
    cases h1 : bits.getLsbD 19 <;>
    simp [traceRow78, traceRow77, traceRow41]
  simp [hxor, ha, hb]

theorem certificate_inconsistent (bits : BitVec 60) :
    ¬ certificateRows bits := by
  intro hs
  rcases hs with ⟨h0, h1, h2, h3, h4, h5, h6, h7, h8, h9, h10, h11, h12, h13, h14, h15, h16, h17, h18, h19, h20, h21, h22, h23, h24, h25, h26, h27, h28, h29, h30, h31, h32, h33, h34, h35, h36, h37, h38, h39⟩
  have h40 : traceRow40 bits = false :=
    traceStep40 bits h20 h18
  have h41 : traceRow41 bits = false :=
    traceStep41 bits h21 h19
  have h42 : traceRow42 bits = false :=
    traceStep42 bits h22 h17
  have h43 : traceRow43 bits = false :=
    traceStep43 bits h23 h16
  have h44 : traceRow44 bits = false :=
    traceStep44 bits h24 h15
  have h45 : traceRow45 bits = false :=
    traceStep45 bits h25 h14
  have h46 : traceRow46 bits = false :=
    traceStep46 bits h26 h13
  have h47 : traceRow47 bits = false :=
    traceStep47 bits h27 h12
  have h48 : traceRow48 bits = false :=
    traceStep48 bits h28 h11
  have h49 : traceRow49 bits = false :=
    traceStep49 bits h29 h10
  have h50 : traceRow50 bits = false :=
    traceStep50 bits h30 h9
  have h51 : traceRow51 bits = false :=
    traceStep51 bits h31 h8
  have h52 : traceRow52 bits = false :=
    traceStep52 bits h32 h7
  have h53 : traceRow53 bits = false :=
    traceStep53 bits h33 h6
  have h54 : traceRow54 bits = false :=
    traceStep54 bits h34 h5
  have h55 : traceRow55 bits = false :=
    traceStep55 bits h35 h4
  have h56 : traceRow56 bits = false :=
    traceStep56 bits h36 h3
  have h57 : traceRow57 bits = false :=
    traceStep57 bits h37 h2
  have h58 : traceRow58 bits = false :=
    traceStep58 bits h38 h0
  have h59 : traceRow59 bits = true :=
    traceStep59 bits h39 h1
  have h60 : traceRow60 bits = true :=
    traceStep60 bits h59 h58
  have h61 : traceRow61 bits = true :=
    traceStep61 bits h60 h57
  have h62 : traceRow62 bits = true :=
    traceStep62 bits h61 h56
  have h63 : traceRow63 bits = true :=
    traceStep63 bits h62 h55
  have h64 : traceRow64 bits = true :=
    traceStep64 bits h63 h54
  have h65 : traceRow65 bits = true :=
    traceStep65 bits h64 h53
  have h66 : traceRow66 bits = true :=
    traceStep66 bits h65 h52
  have h67 : traceRow67 bits = true :=
    traceStep67 bits h66 h51
  have h68 : traceRow68 bits = true :=
    traceStep68 bits h67 h50
  have h69 : traceRow69 bits = true :=
    traceStep69 bits h68 h49
  have h70 : traceRow70 bits = true :=
    traceStep70 bits h69 h48
  have h71 : traceRow71 bits = true :=
    traceStep71 bits h70 h47
  have h72 : traceRow72 bits = true :=
    traceStep72 bits h71 h46
  have h73 : traceRow73 bits = true :=
    traceStep73 bits h72 h45
  have h74 : traceRow74 bits = true :=
    traceStep74 bits h73 h44
  have h75 : traceRow75 bits = true :=
    traceStep75 bits h74 h43
  have h76 : traceRow76 bits = true :=
    traceStep76 bits h75 h42
  have h77 : traceRow77 bits = true :=
    traceStep77 bits h76 h40
  have h78 : traceRow78 bits = true :=
    traceStep78 bits h77 h41
  have impossible : false = true := by
    simpa [traceRow78] using h78
  cases impossible

theorem source_unsat (bits : BitVec 60) : ¬ sourceCNF bits := by
  intro hs
  exact certificate_inconsistent bits ((source_iff_certificate bits).mp hs)

end Witnora.Dubois20

#print axioms Witnora.Dubois20.source_unsat

