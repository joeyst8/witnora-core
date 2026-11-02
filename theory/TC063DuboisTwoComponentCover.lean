import Dubois20SourceUnsat

set_option maxHeartbeats 2000000
set_option maxRecDepth 4096

/-!
  A genuine two-vertex G14 separator cover for archived Dubois20 (60/160).

  Original DIMACS variables 10 and 29 (bit positions 9 and 28) separate
  the remaining variables into two 29-vertex primal-graph components.
  Rows 0..9,30..39 belong to A; rows 10..29 belong to B.

  Exact 160-clause partition and literal substitutions are audited by
  tests/test_tc063_dubois_two_component.py. The Lean kernel independently
  proves source-level decomposition, the two local G5 component consequences,
  exact branch substitution, and complete two-variable UNSAT cover.

  This remains one benchmark: no general separator-recognition theorem,
  verified DIMACS parser, or general solver-complexity theorem is claimed.
-/

namespace Witnora.TC063

open Witnora.Dubois20

def componentACNF (bits : BitVec 60) : Prop :=
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

def componentBCNF (bits : BitVec 60) : Prop :=
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
    sourceGroup29 bits = true

-- These clauses partition the original 160-clause conjunction exactly.
theorem source_component_iff (bits : BitVec 60) :
    sourceCNF bits ↔ componentACNF bits ∧ componentBCNF bits := by
  constructor
  · intro hs
    rcases hs with ⟨h0, h1, h2, h3, h4, h5, h6, h7, h8, h9, h10, h11, h12, h13, h14, h15, h16, h17, h18, h19, h20, h21, h22, h23, h24, h25, h26, h27, h28, h29, h30, h31, h32, h33, h34, h35, h36, h37, h38, h39⟩
    exact ⟨⟨h0, h1, h2, h3, h4, h5, h6, h7, h8, h9, h30, h31, h32, h33, h34, h35, h36, h37, h38, h39⟩, ⟨h10, h11, h12, h13, h14, h15, h16, h17, h18, h19, h20, h21, h22, h23, h24, h25, h26, h27, h28, h29⟩⟩
  · rintro ⟨ha, hb⟩
    rcases ha with ⟨h0, h1, h2, h3, h4, h5, h6, h7, h8, h9, h30, h31, h32, h33, h34, h35, h36, h37, h38, h39⟩
    rcases hb with ⟨h10, h11, h12, h13, h14, h15, h16, h17, h18, h19, h20, h21, h22, h23, h24, h25, h26, h27, h28, h29⟩
    exact ⟨h0, h1, h2, h3, h4, h5, h6, h7, h8, h9, h10, h11, h12, h13, h14, h15, h16, h17, h18, h19, h20, h21, h22, h23, h24, h25, h26, h27, h28, h29, h30, h31, h32, h33, h34, h35, h36, h37, h38, h39⟩

-- Reusable local 4-variable XOR propagation; proved by Boolean cases.
private theorem pair_extension (a b c d : Bool)
    (hp : (b ^^ c) = false)
    (hq : (a ^^ b ^^ c ^^ d) = false) :
    (a ^^ d) = false := by
  cases a <;> cases b <;> cases c <;> cases d <;> simp_all

-- G5 component A: its twenty *own* clause groups require x10 XOR x29 = 1.
theorem componentA_separator_parity (bits : BitVec 60)
    (ha : componentACNF bits) :
    (bits.getLsbD 9 ^^ bits.getLsbD 28) = true := by
  rcases ha with ⟨h0, h1, h2, h3, h4, h5, h6, h7, h8, h9, h30, h31, h32, h33, h34, h35, h36, h37, h38, h39⟩
  have p0 : parity0 bits = true :=
    (sourceGroup0_exact bits).mp h0
  have p1 : parity1 bits = true :=
    (sourceGroup1_exact bits).mp h1
  have p2 : parity2 bits = true :=
    (sourceGroup2_exact bits).mp h2
  have p3 : parity3 bits = true :=
    (sourceGroup3_exact bits).mp h3
  have p4 : parity4 bits = true :=
    (sourceGroup4_exact bits).mp h4
  have p5 : parity5 bits = true :=
    (sourceGroup5_exact bits).mp h5
  have p6 : parity6 bits = true :=
    (sourceGroup6_exact bits).mp h6
  have p7 : parity7 bits = true :=
    (sourceGroup7_exact bits).mp h7
  have p8 : parity8 bits = true :=
    (sourceGroup8_exact bits).mp h8
  have p9 : parity9 bits = true :=
    (sourceGroup9_exact bits).mp h9
  have p30 : parity30 bits = true :=
    (sourceGroup30_exact bits).mp h30
  have p31 : parity31 bits = true :=
    (sourceGroup31_exact bits).mp h31
  have p32 : parity32 bits = true :=
    (sourceGroup32_exact bits).mp h32
  have p33 : parity33 bits = true :=
    (sourceGroup33_exact bits).mp h33
  have p34 : parity34 bits = true :=
    (sourceGroup34_exact bits).mp h34
  have p35 : parity35 bits = true :=
    (sourceGroup35_exact bits).mp h35
  have p36 : parity36 bits = true :=
    (sourceGroup36_exact bits).mp h36
  have p37 : parity37 bits = true :=
    (sourceGroup37_exact bits).mp h37
  have p38 : parity38 bits = true :=
    (sourceGroup38_exact bits).mp h38
  have p39 : parity39 bits = false :=
    (sourceGroup39_exact bits).mp h39
  have h50 : traceRow50 bits = false :=
    traceStep50 bits p30 p9
  have h51 : traceRow51 bits = false :=
    traceStep51 bits p31 p8
  have h52 : traceRow52 bits = false :=
    traceStep52 bits p32 p7
  have h53 : traceRow53 bits = false :=
    traceStep53 bits p33 p6
  have h54 : traceRow54 bits = false :=
    traceStep54 bits p34 p5
  have h55 : traceRow55 bits = false :=
    traceStep55 bits p35 p4
  have h56 : traceRow56 bits = false :=
    traceStep56 bits p36 p3
  have h57 : traceRow57 bits = false :=
    traceStep57 bits p37 p2
  have h58 : traceRow58 bits = false :=
    traceStep58 bits p38 p0
  have h59 : traceRow59 bits = true :=
    traceStep59 bits p39 p1
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
  simpa only [traceRow68] using h68

-- G5 component B: its twenty *own* clause groups require x10 XOR x29 = 0.
theorem componentB_separator_parity (bits : BitVec 60)
    (hb : componentBCNF bits) :
    (bits.getLsbD 9 ^^ bits.getLsbD 28) = false := by
  rcases hb with ⟨h10, h11, h12, h13, h14, h15, h16, h17, h18, h19, h20, h21, h22, h23, h24, h25, h26, h27, h28, h29⟩
  have p10 : parity10 bits = true :=
    (sourceGroup10_exact bits).mp h10
  have p11 : parity11 bits = true :=
    (sourceGroup11_exact bits).mp h11
  have p12 : parity12 bits = true :=
    (sourceGroup12_exact bits).mp h12
  have p13 : parity13 bits = true :=
    (sourceGroup13_exact bits).mp h13
  have p14 : parity14 bits = true :=
    (sourceGroup14_exact bits).mp h14
  have p15 : parity15 bits = true :=
    (sourceGroup15_exact bits).mp h15
  have p16 : parity16 bits = true :=
    (sourceGroup16_exact bits).mp h16
  have p17 : parity17 bits = true :=
    (sourceGroup17_exact bits).mp h17
  have p18 : parity18 bits = true :=
    (sourceGroup18_exact bits).mp h18
  have p19 : parity19 bits = true :=
    (sourceGroup19_exact bits).mp h19
  have p20 : parity20 bits = true :=
    (sourceGroup20_exact bits).mp h20
  have p21 : parity21 bits = true :=
    (sourceGroup21_exact bits).mp h21
  have p22 : parity22 bits = true :=
    (sourceGroup22_exact bits).mp h22
  have p23 : parity23 bits = true :=
    (sourceGroup23_exact bits).mp h23
  have p24 : parity24 bits = true :=
    (sourceGroup24_exact bits).mp h24
  have p25 : parity25 bits = true :=
    (sourceGroup25_exact bits).mp h25
  have p26 : parity26 bits = true :=
    (sourceGroup26_exact bits).mp h26
  have p27 : parity27 bits = true :=
    (sourceGroup27_exact bits).mp h27
  have p28 : parity28 bits = true :=
    (sourceGroup28_exact bits).mp h28
  have p29 : parity29 bits = true :=
    (sourceGroup29_exact bits).mp h29
  have h40 : traceRow40 bits = false :=
    traceStep40 bits p20 p18
  have h41 : traceRow41 bits = false :=
    traceStep41 bits p21 p19
  have h42 : traceRow42 bits = false :=
    traceStep42 bits p22 p17
  have h43 : traceRow43 bits = false :=
    traceStep43 bits p23 p16
  have h44 : traceRow44 bits = false :=
    traceStep44 bits p24 p15
  have h45 : traceRow45 bits = false :=
    traceStep45 bits p25 p14
  have h46 : traceRow46 bits = false :=
    traceStep46 bits p26 p13
  have h47 : traceRow47 bits = false :=
    traceStep47 bits p27 p12
  have h48 : traceRow48 bits = false :=
    traceStep48 bits p28 p11
  have h49 : traceRow49 bits = false :=
    traceStep49 bits p29 p10
  have g18 : (bits.getLsbD 18 ^^ bits.getLsbD 19) = false := by
    simpa only [traceRow41] using h41
  have g17 : (bits.getLsbD 17 ^^ bits.getLsbD 20) = false :=
    pair_extension _ _ _ _ g18
      (by simpa only [traceRow40] using h40)
  have g16 : (bits.getLsbD 16 ^^ bits.getLsbD 21) = false :=
    pair_extension _ _ _ _ g17
      (by simpa only [traceRow42] using h42)
  have g15 : (bits.getLsbD 15 ^^ bits.getLsbD 22) = false :=
    pair_extension _ _ _ _ g16
      (by simpa only [traceRow43] using h43)
  have g14 : (bits.getLsbD 14 ^^ bits.getLsbD 23) = false :=
    pair_extension _ _ _ _ g15
      (by simpa only [traceRow44] using h44)
  have g13 : (bits.getLsbD 13 ^^ bits.getLsbD 24) = false :=
    pair_extension _ _ _ _ g14
      (by simpa only [traceRow45] using h45)
  have g12 : (bits.getLsbD 12 ^^ bits.getLsbD 25) = false :=
    pair_extension _ _ _ _ g13
      (by simpa only [traceRow46] using h46)
  have g11 : (bits.getLsbD 11 ^^ bits.getLsbD 26) = false :=
    pair_extension _ _ _ _ g12
      (by simpa only [traceRow47] using h47)
  have g10 : (bits.getLsbD 10 ^^ bits.getLsbD 27) = false :=
    pair_extension _ _ _ _ g11
      (by simpa only [traceRow48] using h48)
  have g9 : (bits.getLsbD 9 ^^ bits.getLsbD 28) = false :=
    pair_extension _ _ _ _ g10
      (by simpa only [traceRow49] using h49)
  exact g9

-- The four source groups containing the two separator variables are changed
-- by literal substitution only. Every other source group is identical.
def residualGroup9 (s10 : Bool) (bits : BitVec 60) : Bool :=
  ((!(bits.getLsbD 48)) || (!s10) || (bits.getLsbD 8)) &&
  ((!(bits.getLsbD 48)) || (!(bits.getLsbD 8)) || s10) &&
  ((!s10) || (!(bits.getLsbD 8)) || (bits.getLsbD 48)) &&
  ((bits.getLsbD 8) || s10 || (bits.getLsbD 48))

def residualGroup10 (s10 : Bool) (bits : BitVec 60) : Bool :=
  ((!(bits.getLsbD 49)) || (!(bits.getLsbD 10)) || s10) &&
  ((!(bits.getLsbD 49)) || (!s10) || (bits.getLsbD 10)) &&
  ((!(bits.getLsbD 10)) || (!s10) || (bits.getLsbD 49)) &&
  (s10 || (bits.getLsbD 10) || (bits.getLsbD 49))

def residualGroup29 (s29 : Bool) (bits : BitVec 60) : Bool :=
  ((!(bits.getLsbD 49)) || (!s29) || (bits.getLsbD 27)) &&
  ((!(bits.getLsbD 49)) || (!(bits.getLsbD 27)) || s29) &&
  ((!s29) || (!(bits.getLsbD 27)) || (bits.getLsbD 49)) &&
  ((bits.getLsbD 27) || s29 || (bits.getLsbD 49))

def residualGroup30 (s29 : Bool) (bits : BitVec 60) : Bool :=
  ((!(bits.getLsbD 48)) || (!(bits.getLsbD 29)) || s29) &&
  ((!(bits.getLsbD 48)) || (!s29) || (bits.getLsbD 29)) &&
  ((!(bits.getLsbD 29)) || (!s29) || (bits.getLsbD 48)) &&
  (s29 || (bits.getLsbD 29) || (bits.getLsbD 48))

def componentAResidual (s10 s29 : Bool) (bits : BitVec 60) : Prop :=
    sourceGroup0 bits = true ∧
    sourceGroup1 bits = true ∧
    sourceGroup2 bits = true ∧
    sourceGroup3 bits = true ∧
    sourceGroup4 bits = true ∧
    sourceGroup5 bits = true ∧
    sourceGroup6 bits = true ∧
    sourceGroup7 bits = true ∧
    sourceGroup8 bits = true ∧
    residualGroup9 s10 bits = true ∧
    residualGroup30 s29 bits = true ∧
    sourceGroup31 bits = true ∧
    sourceGroup32 bits = true ∧
    sourceGroup33 bits = true ∧
    sourceGroup34 bits = true ∧
    sourceGroup35 bits = true ∧
    sourceGroup36 bits = true ∧
    sourceGroup37 bits = true ∧
    sourceGroup38 bits = true ∧
    sourceGroup39 bits = true

def componentBResidual (s10 s29 : Bool) (bits : BitVec 60) : Prop :=
    residualGroup10 s10 bits = true ∧
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
    residualGroup29 s29 bits = true

-- These are definitional equalities, not SAT-solver assumptions.
theorem componentA_exact (bits : BitVec 60) :
    componentACNF bits ↔
      componentAResidual (bits.getLsbD 9) (bits.getLsbD 28) bits := by
  rfl

theorem componentB_exact (bits : BitVec 60) :
    componentBCNF bits ↔
      componentBResidual (bits.getLsbD 9) (bits.getLsbD 28) bits := by
  rfl

theorem componentA_assigned_exact (bits : BitVec 60) (s10 s29 : Bool)
    (h10 : bits.getLsbD 9 = s10) (h29 : bits.getLsbD 28 = s29) :
    componentACNF bits ↔ componentAResidual s10 s29 bits := by
  rw [← h10, ← h29]
  exact componentA_exact bits

theorem componentB_assigned_exact (bits : BitVec 60) (s10 s29 : Bool)
    (h10 : bits.getLsbD 9 = s10) (h29 : bits.getLsbD 28 = s29) :
    componentBCNF bits ↔ componentBResidual s10 s29 bits := by
  rw [← h10, ← h29]
  exact componentB_exact bits

theorem source_two_component_exact (bits : BitVec 60) :
    sourceCNF bits ↔
      componentAResidual (bits.getLsbD 9) (bits.getLsbD 28) bits ∧
      componentBResidual (bits.getLsbD 9) (bits.getLsbD 28) bits := by
  constructor
  · intro hs
    obtain ⟨ha, hb⟩ := (source_component_iff bits).mp hs
    exact ⟨(componentA_exact bits).mp ha, (componentB_exact bits).mp hb⟩
  · rintro ⟨ha, hb⟩
    exact (source_component_iff bits).mpr
      ⟨(componentA_exact bits).mpr ha, (componentB_exact bits).mpr hb⟩

-- All four (s10,s29) assignments are covered: equal bits refute A;
-- unequal bits refute B. Neither branch assumes global source UNSAT.
theorem two_bit_assignment_cover (bits : BitVec 60) (s10 s29 : Bool)
    (h10 : bits.getLsbD 9 = s10) (h29 : bits.getLsbD 28 = s29) :
    ¬ componentAResidual s10 s29 bits ∨
    ¬ componentBResidual s10 s29 bits := by
  have hA : componentACNF bits ↔ componentAResidual s10 s29 bits :=
    componentA_assigned_exact bits s10 s29 h10 h29
  have hB : componentBCNF bits ↔ componentBResidual s10 s29 bits :=
    componentB_assigned_exact bits s10 s29 h10 h29
  cases s10 <;> cases s29
  · left
    intro hr
    have h := componentA_separator_parity bits (hA.mpr hr)
    rw [h10, h29] at h
    cases h
  · right
    intro hr
    have h := componentB_separator_parity bits (hB.mpr hr)
    rw [h10, h29] at h
    cases h
  · right
    intro hr
    have h := componentB_separator_parity bits (hB.mpr hr)
    rw [h10, h29] at h
    cases h
  · left
    intro hr
    have h := componentA_separator_parity bits (hA.mpr hr)
    rw [h10, h29] at h
    cases h

theorem dubois20_two_component_unsat_cover (bits : BitVec 60) :
    ¬ sourceCNF bits := by
  intro hs
  have hr := (source_two_component_exact bits).mp hs
  have hc := two_bit_assignment_cover bits
    (bits.getLsbD 9) (bits.getLsbD 28) rfl rfl
  rcases hc with ha | hb
  · exact ha hr.1
  · exact hb hr.2

end Witnora.TC063

#print axioms Witnora.TC063.dubois20_two_component_unsat_cover
