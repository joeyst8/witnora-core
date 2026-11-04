//! R-095: exact concrete-coloring Lean source emission, not proof checking.
pub type Case=(String,usize,Vec<(usize,usize)>,Vec<usize>,Vec<usize>,usize);

pub fn fin_values(name:&str,var:&str,n:usize,codomain:usize,values:&[usize])->String{
 let mut lines=vec![format!("def {name} ({var} : Fin {n}) : Fin {codomain} :=")];
 if n==1{lines.push(format!("  {}",values[0]));}
 else{
  for (index,&value) in values[..n-1].iter().enumerate(){
   let prefix=if index==0{"if"}else{"else if"};
   lines.push(format!("  {prefix} {var}.val = {index} then {value}"));
  }
  lines.push(format!("  else {}",values[n-1]));
 }
 lines.join("\n")
}

pub fn find_clique(n:usize,edges:&[(usize,usize)],size:usize)->Option<Vec<usize>>{
 if size>n{return None;}
 let edge_set:std::collections::BTreeSet<_>=edges.iter().copied().collect();
 // Python itertools.combinations lexicographic order.
 fn search(n:usize,size:usize,start:usize,current:&mut Vec<usize>,
   edges:&std::collections::BTreeSet<(usize,usize)>)->Option<Vec<usize>>{
  if current.len()==size{return Some(current.clone());}
  for v in start..n{
   if current.iter().all(|&u|edges.contains(&(u,v))){
    current.push(v);
    if let Some(result)=search(n,size,v+1,current,edges){return Some(result);}
    current.pop();
   }
  }
  None
 }
 search(n,size,0,&mut Vec::new(),&edge_set)
}

fn emit_case((name,n,edges,colors,clique,k):&Case)->String{
 let edge_items=edges.iter().map(|(u,v)|format!("({u}, {v})")).collect::<Vec<_>>().join(", ");
 let edges_decl=format!("def {name}Edges : List (Fin {n} × Fin {n}) :=\n  [{edge_items}]");
 let paint_decl=fin_values(&format!("{name}Paint"),"v",*n,*k,colors);
 let mut clique_lines=vec![format!("def {name}Clique : Option (Fin {}) → Fin {n}",k-1),
  format!("  | none => {}",clique[0])];
 let clique_values=&clique[1..];
 if clique_values.is_empty(){clique_lines.push(format!("  | some _ => {}",clique[0]));}
 else if clique_values.len()==1{
  clique_lines.push("  | some _ =>".into());
  clique_lines.push(format!("      {}",clique_values[0]));
 }else{
  clique_lines.push("  | some i =>".into());
  for (index,&value) in clique_values[..clique_values.len()-1].iter().enumerate(){
   let prefix=if index==0{"if"}else{"else if"};
   clique_lines.push(format!("      {prefix} i.val = {index} then {value}"));
  }
  clique_lines.push(format!("      else {}",clique_values[clique_values.len()-1]));
 }
 [edges_decl,paint_decl,clique_lines.join("\n"),
  format!("theorem {name}Passes :\n    checkCertificate {name}Edges {name}Paint {name}Clique = true := by\n  decide"),
  format!("theorem {name}Optimal :\n    ∃ hNoLoops : ∀ u : Fin {n}, ¬ edgeAdj {name}Edges u u,\n      chromaticNumber (edgeAdj {name}Edges) hNoLoops = {k} := by\n  exact checked_certificate_sound\n    {name}Edges {name}Paint {name}Clique {name}Passes"),
  format!("#print axioms {name}Optimal")].join("\n\n")
}

pub fn emit(cases:&[Case])->String{
 let mut blocks=vec![
  "import Witnora.ConcreteColorCertificate".to_string(),"".into(),
  "/- Generated deterministically by Python; Lean checks all data. -/".into(),
  "namespace Witnora.GeneratedColorCertificates".into(),"".into(),
  "open Witnora.ConcreteColorCertificate".into(),
  "open Witnora.ChromaticMinimum".into(),
 ];
 for case in cases{blocks.push("".into());blocks.push(emit_case(case));}
 blocks.push("".into());blocks.push("end Witnora.GeneratedColorCertificates".into());
 blocks.push("".into());blocks.join("\n")
}

#[cfg(test)]mod tests{use super::*;#[test]fn clique_and_single_vertex(){
 assert_eq!(find_clique(3,&[(0,1),(0,2),(1,2)],2),Some(vec![0,1]));
 assert_eq!(fin_values("c","v",1,1,&[0]),"def c (v : Fin 1) : Fin 1 :=\n  0");
}}
