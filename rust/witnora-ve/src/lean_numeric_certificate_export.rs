//! R-093: exact numeric Lean certificate source formatting.
//! This is code generation, never proof checking or theorem promotion.
pub type Case=(String,usize,Vec<(usize,usize)>,Vec<usize>,Vec<usize>,usize);

pub fn emit(cases:&[Case])->String{
 let mut lines=vec![
  "import Witnora.NumericEdgeListBridge".to_string(),
  "".into(),
  "/- Python-generated raw Nat lists; Lean checks their meaning. -/".into(),
  "namespace Witnora.GeneratedNumericCertificates".into(),
  "".into(),
  "open Witnora.NumericColorCertificate".into(),
  "open Witnora.ConcreteColorCertificate".into(),
  "open Witnora.ChromaticMinimum".into(),
 ];
 for (name,n,edges,colors,clique,k) in cases{
  let edge_list=edges.iter().map(|(u,v)|format!("({u}, {v})")).collect::<Vec<_>>().join(", ");
  let color_list=colors.iter().map(|v|v.to_string()).collect::<Vec<_>>().join(", ");
  let clique_list=clique.iter().map(|v|v.to_string()).collect::<Vec<_>>().join(", ");
  lines.push("".into());
  lines.push(format!("def {name}RawEdges : List (Nat × Nat) := [{edge_list}]"));
  lines.push(format!("def {name}RawColors : List Nat := [{color_list}]"));
  lines.push(format!("def {name}RawClique : List Nat := [{clique_list}]"));
  lines.push("".into());
  lines.push(format!("theorem {name}NumericPasses :\n    checkNumeric {} {}\n      {name}RawEdges {name}RawColors {name}RawClique = true := by\n  decide",n-1,k-1));
  lines.push("".into());
  lines.push(format!("theorem {name}NumericOptimal :\n    ∃ hNoLoops : ∀ u : Fin {n},\n        ¬ edgeAdj (decodedEdges {} {name}RawEdges) u u,\n      chromaticNumber (edgeAdj (decodedEdges {} {name}RawEdges))\n        hNoLoops = {k} := by\n  exact checked_numeric_sound\n    {} {}\n    {name}RawEdges {name}RawColors {name}RawClique\n    {name}NumericPasses",n-1,n-1,n-1,k-1));
  lines.push(format!("#print axioms {name}NumericOptimal"));
 }
 lines.push("".into());
 lines.push("end Witnora.GeneratedNumericCertificates".into());
 lines.push("".into());
 lines.join("\n")
}

#[cfg(test)]mod tests{use super::*;#[test]fn empty_header(){
 let out=emit(&[]);assert!(out.ends_with("end Witnora.GeneratedNumericCertificates\n"));
}}
