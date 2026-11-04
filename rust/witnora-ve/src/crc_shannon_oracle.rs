//! R-083: exact state-budgeted Shannon recursion for selected Walsh modes.
//! Worst-case exponential; a budget hit returns None, never an inferred coefficient.
use num_bigint::{BigInt,BigUint};
use num_traits::{One,Zero};
use std::collections::{BTreeMap,HashMap};
use std::str::FromStr;

fn read_mask(raw:&str)->Result<BigUint,String>{
    BigUint::from_str(raw).map_err(|_|"invalid nonnegative bitmask".into())
}
fn weight(mask:&BigUint)->usize{
    mask.iter_u32_digits().map(|word|word.count_ones() as usize).sum()
}
fn canonical(mut clauses:Vec<Vec<i32>>)->Vec<Vec<i32>>{
    if clauses.iter().any(Vec::is_empty){return vec![vec![]];}
    clauses.sort_by(|a,b|a.len().cmp(&b.len()).then_with(||a.cmp(b)));
    clauses.dedup();
    clauses
}
fn cofactor(clauses:&[Vec<i32>],var:i32,value:bool)->Vec<Vec<i32>>{
    let mut reduced=Vec::new();
    for clause in clauses{
        if clause.iter().any(|&lit|lit.abs()==var&&(lit>0)==value){continue;}
        let rest:Vec<i32>=clause.iter().copied().filter(|lit|lit.abs()!=var).collect();
        if rest.is_empty(){return vec![vec![]];}
        reduced.push(rest);
    }
    canonical(reduced)
}

struct Solver<'a>{
    modes:&'a [BigUint],
    memo:HashMap<(Vec<Vec<i32>>,BigUint),Vec<BigInt>>,
    states:usize,
    hits:usize,
    limit:usize,
}
impl Solver<'_>{
    fn solve(&mut self,clauses:Vec<Vec<i32>>,remaining:BigUint)
        ->Result<Vec<BigInt>,()> {
        let key=(clauses.clone(),remaining.clone());
        if let Some(cached)=self.memo.get(&key){
            self.hits+=1;
            return Ok(cached.clone());
        }
        if self.states>=self.limit{return Err(());}
        self.states+=1;
        let result=if clauses.iter().any(Vec::is_empty){
            vec![BigInt::zero();self.modes.len()]
        }else if clauses.is_empty(){
            let val=BigInt::one()<<weight(&remaining);
            self.modes.iter().map(|mode|
                if (mode & &remaining).is_zero(){val.clone()}else{BigInt::zero()}).collect()
        }else{
            let mut unit:Option<i32>=None;
            let mut appearances:BTreeMap<i32,usize>=BTreeMap::new();
            for clause in &clauses{
                if clause.len()==1{
                    let var=clause[0].abs();
                    unit=Some(unit.map_or(var,|old|old.min(var)));
                }
                for lit in clause{*appearances.entry(lit.abs()).or_insert(0)+=1;}
            }
            let chosen=if let Some(v)=unit{v}else{
                appearances.into_iter().max_by_key(|&(v,count)|(count,std::cmp::Reverse(v)))
                    .map(|(v,_)|v).ok_or(())?
            };
            let bit=BigUint::one()<<(chosen as usize-1);
            if (&remaining & &bit).is_zero(){return Err(());}
            let next=&remaining ^ &bit;
            let zeros=self.solve(cofactor(&clauses,chosen,false),next.clone())?;
            let ones=self.solve(cofactor(&clauses,chosen,true),next)?;
            self.modes.iter().zip(zeros.iter().zip(ones.iter()))
                .map(|(mode,(a,b))|if !(mode & &bit).is_zero(){a-b}else{a+b}).collect()
        };
        self.memo.insert(key,result.clone());
        Ok(result)
    }
}

pub fn query(normalized:Option<Vec<(String,String)>>,boundary:&[usize],
    modes:&[String],max_states:usize)
    ->Result<Option<(Vec<(String,String,String)>,usize,usize)>,String>{
    if max_states==0{return Err("max_states must be positive".into());}
    let mut mask=BigUint::zero();
    for &var in boundary{
        if !(1..=256).contains(&var){return Err("prototype variable IDs outside 1..256".into());}
        let bit=BigUint::one()<<(var-1);
        if !(&mask & &bit).is_zero(){return Err("duplicate boundary variable".into());}
        mask|=bit;
    }
    let mut parsed=Vec::new();
    for raw in modes{
        let mode=read_mask(raw)?;
        if (&mode & &mask)!=mode{return Err("Walsh mode mentions nonboundary variables".into());}
        parsed.push(mode);
    }
    let normalized=if let Some(rows)=normalized{rows}else{
        return Ok(Some((modes.iter().map(|m|(m.clone(),"0".into(),"1".into())).collect(),0,0)));
    };
    let mut clauses=Vec::new();
    for (z,o) in normalized{
        let z=read_mask(&z)?;
        let o=read_mask(&o)?;
        let mut lits=Vec::new();
        for var in 1..=256{
            let bit=BigUint::one()<<(var-1);
            if !(&z & &bit).is_zero(){lits.push(var as i32);}
            if !(&o & &bit).is_zero(){lits.push(-(var as i32));}
        }
        lits.sort_by_key(|&lit|(lit.abs(),lit));
        clauses.push(lits);
    }
    let mut solver=Solver{modes:&parsed,memo:HashMap::new(),states:0,hits:0,limit:max_states};
    let result=match solver.solve(canonical(clauses),mask){Ok(result)=>result,Err(())=>return Ok(None)};
    let divisor=(BigInt::one()<<boundary.len()).to_string();
    let rows=modes.iter().zip(result.iter())
        .map(|(mode,coeff)|(mode.clone(),coeff.to_string(),divisor.clone())).collect();
    Ok(Some((rows,solver.states,solver.hits)))
}

#[cfg(test)]
mod tests{
 use super::*;
 #[test]fn source_unit(){
  let q=query(Some(vec![("1".into(),"0".into())]),&[1],
      &["0".into(),"1".into()],10).unwrap().unwrap();
  assert_eq!(q.0[0].1,"1");
  assert_eq!(q.0[1].1,"-1");
 }
}
