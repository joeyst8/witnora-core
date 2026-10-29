import Witnora.Conditioning

/-!
# Complete ordered separator assignment enumeration

The first variable in the input list changes slowest, matching Python's
`itertools.product([False, True], repeat=n)` for a sorted separator list.
Every Boolean assignment on these variables is represented, irrespective
of the number of variables. This is a theorem about the Lean generator,
not a formal semantics for CPython.
-/

namespace Witnora.SeparatorAssignments

def enumerate : List Nat → List (List (Nat × Bool))
  | [] => [[]]
  | v :: rest =>
      [false, true].flatMap (fun b =>
        (enumerate rest).map (fun tail => (v, b) :: tail))

def encode (variables : List Nat) (a : Nat → Bool) : List (Nat × Bool) :=
  variables.map (fun v => (v, a v))

theorem enumerate_complete (variables : List Nat) (a : Nat → Bool) :
    encode variables a ∈ enumerate variables := by
  induction variables with
  | nil => simp [encode, enumerate]
  | cons v rest ih =>
      simp only [encode, List.map_cons, enumerate, List.mem_flatMap]
      refine ⟨a v, ?_, ?_⟩
      · cases a v <;> simp
      · simp [List.mem_map, ih]

example : enumerate [1, 2] =
  [[(1, false), (2, false)], [(1, false), (2, true)],
   [(1, true), (2, false)], [(1, true), (2, true)]] := by decide

example : enumerate [] = [[]] := by decide

#print axioms Witnora.SeparatorAssignments.enumerate_complete

end Witnora.SeparatorAssignments
