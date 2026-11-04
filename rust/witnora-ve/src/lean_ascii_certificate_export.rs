//! R-094 canonical ASCII certificate and exact Lean source emission.
//! Lean remains the only proof checker; this module formats bytes and text.
pub type Case=(String,usize,Vec<(usize,usize)>,Vec<usize>,Vec<usize>,usize);

pub fn serialize(n:usize,edges:&[(usize,usize)],colors:&[usize],clique:&[usize],k:usize)->Vec<u8>{
 let edges=edges.iter().map(|(u,v)|format!("{u},{v}")).collect::<Vec<_>>().join(";");
 let colors=colors.iter().map(|v|v.to_string()).collect::<Vec<_>>().join(",");
 let clique=clique.iter().map(|v|v.to_string()).collect::<Vec<_>>().join(",");
 format!("{}|{}|{}|{}|{}",n-1,k-1,edges,colors,clique).into_bytes()
}
pub fn lean_bytes(bytes:&[u8])->String{
 format!("[{}]",bytes.iter().map(|b|b.to_string()).collect::<Vec<_>>().join(", "))
}
pub fn emit(cases:&[Case])->String{
 let mut lines=vec![
  "import Witnora.KernelAsciiNumericCertificate".to_string(),
  "".into(),
  "/- Python DSATUR source bytes as Lean Nat lists; checked by Lean. -/".into(),
  "namespace Witnora.GeneratedAsciiCertificates".into(),
  "open Witnora.KernelAsciiNumericCertificate".into(),
  "open Witnora.NumericColorCertificate".into(),
  "open Witnora.ConcreteColorCertificate".into(),
  "open Witnora.ChromaticMinimum".into(),
  "set_option maxRecDepth 8192".into(),
  "set_option maxHeartbeats 4000000".into(),
 ];
 for (name,n,edges,colors,clique,k) in cases{
  let data=serialize(*n,edges,colors,clique,*k);
  let mut damaged=data.clone();damaged[0]=120;
  let raw_edges=edges.iter().map(|(u,v)|format!("({u}, {v})")).collect::<Vec<_>>().join(", ");
  let raw_colors=colors.iter().map(|v|v.to_string()).collect::<Vec<_>>().join(", ");
  let raw_clique=clique.iter().map(|v|v.to_string()).collect::<Vec<_>>().join(", ");
  lines.push("".into());
  lines.push(format!("def {name}AsciiBytes : List Nat := {}",lean_bytes(&data)));
  lines.push(format!("def {name}DamagedBytes : List Nat := {}",lean_bytes(&damaged)));
  lines.push(format!("theorem {name}AsciiParses :\n    parseAsciiCertificate {name}AsciiBytes =\n      some ({}, {}, [{raw_edges}], [{raw_colors}], [{raw_clique}]) := by\n  decide",n-1,k-1));
  lines.push(format!("theorem {name}AsciiPasses :\n    checkAsciiCertificate {name}AsciiBytes = true := by\n  decide"));
  lines.push(format!("theorem {name}AsciiDamagedRejects :\n    checkAsciiCertificate {name}DamagedBytes = false := by\n  decide"));
  lines.push(format!("theorem {name}AsciiOptimal :\n    ∃ hNoLoops : ∀ u : Fin {n},\n        ¬ edgeAdj (decodedEdges {} [{raw_edges}]) u u,\n      chromaticNumber (edgeAdj (decodedEdges {} [{raw_edges}]))\n        hNoLoops = {k} := by\n  exact checked_ascii_certificate_sound {name}AsciiBytes\n    {} {} [{raw_edges}] [{raw_colors}] [{raw_clique}]\n    {name}AsciiParses {name}AsciiPasses",n-1,n-1,n-1,k-1));
  lines.push(format!("#print axioms {name}AsciiOptimal"));
 }
 lines.push("".into());
 lines.push("end Witnora.GeneratedAsciiCertificates".into());
 lines.push("".into());
 lines.join("\n")
}

#[cfg(test)]mod tests{use super::*;#[test]fn sample_wire(){
 assert_eq!(serialize(2,&[(0,1)],&[0,1],&[0,1],2),b"1|1|0,1|0,1|0,1");
 assert_eq!(lean_bytes(&[0,1,120]),"[0, 1, 120]");
}}
