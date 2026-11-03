import Std

/-!
# Exact independent-component counting

If two finite assignment blocks have independent predicates `p` and
`q`, the number of satisfying pairs is the product of their
respective satisfying-assignment counts. This validates the algebraic
rule behind the Python ANF solver's disjoint-scope split.

This theorem is universal over all Boolean predicates on lists, but it
does not yet refine the Python union-find scope detection or compiled
bit-mask evaluator into Lean.
-/

namespace Witnora.ANFComponentFactor

def satCount {α : Type} (p : α → Bool) : List α → Nat
  | [] => 0
  | x :: xs => (if p x then 1 else 0) + satCount p xs

/-- Count satisfying pairs by iterating the first assignment block,
    and counting compatible second-block assignments for each element. -/
def splitCount {α β : Type} (p : α → Bool) (q : β → Bool)
    (ys : List β) : List α → Nat
  | [] => 0
  | x :: xs =>
      (if p x then satCount q ys else 0) +
        splitCount p q ys xs

theorem splitCount_mul {α β : Type}
    (p : α → Bool) (q : β → Bool)
    (xs : List α) (ys : List β) :
    splitCount p q ys xs = satCount p xs * satCount q ys := by
  induction xs with
  | nil => rfl
  | cons x xs ih =>
      simp only [splitCount, satCount]
      rw [ih]
      cases h : p x <;> simp [h, Nat.add_mul]

example :
    splitCount (fun x : Bool => x)
      (fun y : Bool => !y)
      [false, true] [false, true] = 1 := by decide

#print axioms Witnora.ANFComponentFactor.splitCount_mul

end Witnora.ANFComponentFactor
