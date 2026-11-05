//! Opt-in exact GF(2) XOR equation primitives for the Python reference model.
use std::collections::{BTreeMap,BTreeSet};

/// R-121: canonicalize XOR support by toggling each variable occurrence.
pub fn normalize_variables(variables:&[usize])->Result<Vec<usize>,String>{
 let mut active=BTreeSet::new();
 for &v in variables{
  if v==0{return Err("XOR variable IDs must be positive".into());}
  if !active.insert(v){active.remove(&v);}
 }
 Ok(active.into_iter().collect())
}

/// R-122: exact partial-assignment evaluation, retaining UNKNOWN on missing bits.
pub fn evaluate(variables:&[usize],rhs:u8,assignment:&[(usize,bool)])->Option<bool>{
 let bindings=assignment.iter().copied().collect::<BTreeMap<_,_>>();
 let mut parity=rhs&1;
 for &v in variables{
  parity^=u8::from(*bindings.get(&v)?);
 }
 Some(parity==0)
}

/// R-123: exact GF(2) substitution, returning residual support and RHS.
pub fn substitute(variables:&[usize],rhs:u8,assignment:&[(usize,bool)])
 ->(Vec<usize>,u8){
 let bindings=assignment.iter().copied().collect::<BTreeMap<_,_>>();
 let mut residual=Vec::new();let mut parity=rhs&1;
 for &v in variables{
  if let Some(&bit)=bindings.get(&v){parity^=u8::from(bit);}
  else{residual.push(v);}
 }
 (residual,parity)
}

/// R-124: batch exact substitution for whole XOR systems.
pub fn substitute_system(equations:&[(Vec<usize>,u8)],assignment:&[(usize,bool)])
 ->Vec<(Vec<usize>,u8)>{
 equations.iter().map(|(variables,rhs)|
  substitute(variables,*rhs,assignment)).collect()
}

/// R-125: exact deterministic Gaussian elimination over GF(2).
/// Trace tuple: (event-kind,row-index/pivot,using-pivot,before/variables,after,rhs).
pub type GaussianTrace=(u8,usize,usize,Vec<usize>,Vec<usize>,u8);
pub type GaussianAnswer=(bool,Vec<(usize,bool)>,Vec<usize>,Vec<usize>,
 Vec<(usize,bool)>,Vec<GaussianTrace>,Vec<(usize,Vec<usize>,u8)>);

fn xor_rows(a:&(BTreeSet<usize>,u8),b:&(BTreeSet<usize>,u8))
 ->(BTreeSet<usize>,u8){
 (a.0.symmetric_difference(&b.0).copied().collect(),a.1^b.1)
}

pub fn gaussian(equations:&[(Vec<usize>,u8)])->GaussianAnswer{
 let mut pivot_rows=BTreeMap::<usize,(BTreeSet<usize>,u8)>::new();
 let mut trace=Vec::<GaussianTrace>::new();
 let mut universe=BTreeSet::<usize>::new();
 for (index,(variables,rhs)) in equations.iter().enumerate(){
  let mut row=(variables.iter().copied().collect::<BTreeSet<_>>(),*rhs&1);
  universe.extend(row.0.iter().copied());
  trace.push((0,index,0,row.0.iter().copied().collect(),vec![],row.1));
  while let Some(&pivot)=row.0.iter().next(){
   if let Some(basis)=pivot_rows.get(&pivot){
    let before=row.0.iter().copied().collect();
    row=xor_rows(&row,basis);
    trace.push((2,pivot,0,before,row.0.iter().copied().collect(),row.1));
   }else{
    trace.push((1,pivot,0,row.0.iter().copied().collect(),vec![],row.1));
    pivot_rows.insert(pivot,row.clone());
    break;
   }
  }
  if row.0.is_empty() && row.1==1{
   trace.push((3,index,0,vec![],vec![],0));
   return (true,vec![],pivot_rows.keys().copied().collect(),vec![],
           vec![],trace,vec![]);
  }
 }
 let pivots=pivot_rows.keys().copied().collect::<Vec<_>>();
 for &pivot in pivots.iter().rev(){
  let mut row=pivot_rows[&pivot].clone();
  for &higher in pivots.iter().rev().filter(|&&p|p>pivot){
   if row.0.contains(&higher){
    row=xor_rows(&row,&pivot_rows[&higher]);
    trace.push((4,pivot,higher,row.0.iter().copied().collect(),vec![],row.1));
   }
  }
  pivot_rows.insert(pivot,row);
 }
 let pivot_set=pivots.iter().copied().collect::<BTreeSet<_>>();
 let free=universe.difference(&pivot_set)
     .copied().collect::<Vec<_>>();
 let mut assignment=free.iter().copied().map(|v|(v,false))
     .collect::<BTreeMap<_,_>>();
 for &pivot in pivots.iter().rev(){
  let (variables,rhs)=&pivot_rows[&pivot];
  let mut value=*rhs;
  for &v in variables{
   if v!=pivot{value^=u8::from(*assignment.get(&v).unwrap_or(&false));}
  }
  assignment.insert(pivot,value!=0);
 }
 let forced=pivots.iter().filter_map(|&pivot|{
  let (vars,rhs)=&pivot_rows[&pivot];
  if vars.len()==1 && vars.contains(&pivot){Some((pivot,*rhs!=0))}
  else{None}
 }).collect::<Vec<_>>();
 let rref=pivots.iter().map(|&pivot|{
  let (vars,rhs)=&pivot_rows[&pivot];
  (pivot,vars.iter().copied().collect(),*rhs)
 }).collect();
 (false,assignment.into_iter().collect(),pivots,free,forced,trace,rref)
}

/// R-126: independently verify that a partial assignment satisfies every row.
pub fn verify_assignment(equations:&[(Vec<usize>,u8)],
 assignment:&[(usize,bool)])->bool{
 equations.iter().all(|(vars,rhs)|evaluate(vars,*rhs,assignment)==Some(true))
}

/// R-127: bounded exact complete CNF encoding of an XOR parity equation.
pub fn canonical_xor_cnf(variables:&[usize],rhs:u8,max_width:usize)
 ->Result<Vec<Vec<i64>>,String>{
 let canonical=normalize_variables(variables)?;
 if canonical.len()>max_width || canonical.len()>=usize::BITS as usize{
  return Err(format!("native XOR CNF width limit {} exceeded",max_width));
 }
 let mut clauses=Vec::new();
 for mask in 0..(1usize<<canonical.len()){
  if ((mask.count_ones() as u8)&1)==(rhs&1){continue;}
  let mut clause=Vec::with_capacity(canonical.len());
  for (i,&variable) in canonical.iter().enumerate(){
   let v=i64::try_from(variable).map_err(|_|"variable exceeds signed literal range")?;
   clause.push(if (mask & (1usize<<i))!=0{-v}else{v});
  }
  clause.sort_unstable();clauses.push(clause);
 }
 clauses.sort();Ok(clauses)
}

/// R-128: extra CNF clauses that intersect an XOR support, excluding its witness.
pub fn extra_touching_clauses(clauses:&[Vec<i64>],variables:&[usize],
 source_clauses:&[Vec<i64>])->Vec<Vec<i64>>{
 let active=variables.iter().map(|&v|v as u64).collect::<BTreeSet<_>>();
 let source=source_clauses.iter().cloned().collect::<BTreeSet<_>>();
 clauses.iter().filter(|clause|{
  !source.contains(*clause) && clause.iter().any(|lit|
      active.contains(&lit.unsigned_abs()))
 }).cloned().collect::<BTreeSet<_>>().into_iter().collect()
}

/// R-130: discover only complete CNF XOR gadgets in one native pass.
/// Diagnostic: kind 0=skipped max-k, 1=not an exact full encoding.
pub type DetectedPattern=(Vec<usize>,u8,Vec<Vec<i64>>,Vec<Vec<i64>>);
pub type DetectionDiagnostic=(u8,Vec<usize>,usize,usize,usize);
pub fn detect_cnf_patterns(clauses:&[Vec<i64>],include_3var:bool,max_k:usize)
 ->Result<(Vec<DetectedPattern>,Vec<DetectionDiagnostic>),String>{
 if max_k<2{return Ok((vec![],vec![]));}
 let effective_max_k=if include_3var{max_k}else{max_k.min(2)};
 let mut groups=BTreeMap::<Vec<usize>,BTreeSet<Vec<i64>>>::new();
 for clause in clauses{
  let mut support=BTreeSet::new();
  for &lit in clause{
   let v=usize::try_from(lit.unsigned_abs())
       .map_err(|_|"literal variable outside usize")?;
   support.insert(v);
  }
  if support.len()!=clause.len(){continue;}
  groups.entry(support.into_iter().collect()).or_default().insert(clause.clone());
 }
 let mut detected=Vec::new();let mut diagnostics=Vec::new();
 for (vars,group) in groups{
  let k=vars.len();
  if k<2{continue;}
  if k>effective_max_k{
   diagnostics.push((0,vars,k,effective_max_k,group.len()));continue;
  }
  if k>=usize::BITS as usize{
   return Err("native XOR pattern width exceeds platform capacity".into());
  }
  let expected=1usize<<(k-1);
  if group.len()!=expected{
   diagnostics.push((1,vars,k,expected,group.len()));continue;
  }
  let mut found=false;
  for rhs in 0..=1u8{
   let required=canonical_xor_cnf(&vars,rhs,16)?;
   if required.into_iter().collect::<BTreeSet<_>>()==group{
    let source=group.iter().cloned().collect::<Vec<_>>();
    let extra=extra_touching_clauses(clauses,&vars,&source);
    detected.push((vars.clone(),rhs,source,extra));
    found=true;break;
   }
  }
  if !found{diagnostics.push((1,vars,k,expected,group.len()));}
 }
 Ok((detected,diagnostics))
}

/// R-131: parse explicit XOR sidecar lines with finite signed literals.
pub fn parse_xor_lines(text:&str)->Result<Vec<(Vec<i64>,u8)>,String>{
 let mut equations=Vec::new();
 for (line_id,raw) in text.lines().enumerate(){
  let line=raw.trim();
  if line.is_empty() || line.starts_with('#') || line.starts_with("c "){
   continue;
  }
  let spaced=line.replace('='," = ");
  let parts=spaced.split_whitespace().collect::<Vec<_>>();
  let bad=||format!("invalid XOR line {}: {:?}",line_id+1,raw);
  if parts.len()<4 || parts[0]!="xor" || !parts.contains(&"="){
   return Err(bad());
  }
  let eq_index=parts.iter().position(|&v|v=="=").ok_or_else(||bad())?;
  if eq_index==1 || eq_index!=parts.len()-2{return Err(bad());}
  let mut vars=Vec::new();
  for token in &parts[1..eq_index]{
   let v=token.parse::<i64>()
       .map_err(|_|format!("invalid XOR variable on line {}",line_id+1))?;
   if v<=0{return Err("XOR variable IDs must be positive".into());}
   vars.push(v);
  }
  let rhs=parts[parts.len()-1].parse::<i64>()
      .map_err(|_|format!("invalid XOR rhs on line {}",line_id+1))?;
  if rhs!=0 && rhs!=1{
   return Err(format!("invalid XOR rhs on line {}: {}",line_id+1,rhs));
  }
  equations.push((vars,rhs as u8));
 }
 Ok(equations)
}

#[cfg(test)]mod tests{use super::*;#[test]fn normalization(){
 assert_eq!(normalize_variables(&[3,1,3,2,1,7]).unwrap(),vec![2,7]);
 assert_eq!(normalize_variables(&[]).unwrap(),Vec::<usize>::new());
 assert!(normalize_variables(&[1,0]).is_err());
 assert_eq!(evaluate(&[1,2],1,&[(1,true),(2,false)]),Some(true));
 assert_eq!(evaluate(&[1,2],0,&[(1,true)]),None);
 assert_eq!(substitute(&[1,2,3],1,&[(2,true)]),(vec![1,3],0));
 assert_eq!(substitute_system(&[(vec![1,2],1),(vec![2],0)],&[(2,true)]),
  vec![(vec![1],0),(vec![],1)]);
 let sat=gaussian(&[(vec![1,2],1),(vec![2],0)]);
 assert!(!sat.0);assert_eq!(sat.1,vec![(1,true),(2,false)]);
 let unsat=gaussian(&[(vec![1],0),(vec![1],1)]);
 assert!(unsat.0);
 assert!(verify_assignment(&[(vec![1,2],1)],&[(1,true),(2,false)]));
 assert!(!verify_assignment(&[(vec![1,2],1)],&[(1,true)]));
 assert_eq!(canonical_xor_cnf(&[],1,16).unwrap(),vec![Vec::<i32>::new()]);
 assert_eq!(canonical_xor_cnf(&[1,2],1,16).unwrap(),
  vec![vec![-2,-1],vec![1,2]]);
 assert_eq!(extra_touching_clauses(&[vec![1],vec![2],vec![3]],&[1,2],
   &[vec![1]]),vec![vec![2]]);
 let input=vec![vec![1,2],vec![-2,-1],vec![3]];
 let found=detect_cnf_patterns(&input,true,6).unwrap();
 assert_eq!(found.0.len(),1);assert_eq!(found.0[0].1,1);
 assert_eq!(parse_xor_lines("# comment\nxor 1 2 = 1\nc note\nxor 3=0").unwrap(),
  vec![(vec![1,2],1),(vec![3],0)]);
}}
