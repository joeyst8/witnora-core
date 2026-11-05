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
 assert_eq!(canonical_xor_cnf(&[],1,16).unwrap(),vec![vec![]]);
 assert_eq!(canonical_xor_cnf(&[1,2],1,16).unwrap(),
  vec![vec![-2,-1],vec![1,2]]);
}}
