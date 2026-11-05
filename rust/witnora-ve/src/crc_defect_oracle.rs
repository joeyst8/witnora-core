//! R-082: fixed-parameter defect-hypergraph Walsh coefficients, never a general SAT solver.
use num_bigint::{BigInt,BigUint};
use num_traits::{One,Zero};
use std::collections::BTreeSet;
use std::str::FromStr;

fn parse(raw:&str)->Result<BigUint,String>{
    BigUint::from_str(raw).map_err(|_|"invalid nonnegative normalized bitmask".into())
}
fn weight(bits:&BigUint)->usize{
    bits.iter_u32_digits().map(|v|v.count_ones() as usize).sum()
}
fn choose(n:usize,k:usize)->usize{
    if k>n{return 0;}
    let k=k.min(n-k);
    let mut result=1usize;
    for i in 0..k{result=result*(n-i)/(i+1);}
    result
}
fn support_masks(variables:&[usize],rank:usize)->Vec<BigUint>{
    let mut masks=Vec::new();
    for a in 0..variables.len(){
        for b in a+1..variables.len(){
            let ab=(BigUint::one()<<(variables[a]-1)) | (BigUint::one()<<(variables[b]-1));
            if rank==2{masks.push(ab);continue;}
            for c in b+1..variables.len(){
                masks.push(&ab | (BigUint::one()<<(variables[c]-1)));
            }
        }
    }
    masks
}

pub fn query(normalized:Option<Vec<(String,String)>>,boundary:&[usize],modes:&[String],
    max_missing:usize,max_defect_variables:usize,max_subset_checks:usize)
 ->Result<Option<(Vec<(String,String,String)>,usize,usize,usize,usize)>,String>{
    if max_subset_checks==0{return Err("invalid defect enumeration limits".into());}
    let mut boundary_mask=BigUint::zero();
    for &v in boundary{
        if !(1..=256).contains(&v){return Err("boundary IDs must be in 1..256".into());}
        let bit=BigUint::one()<<(v-1);
        if !(&boundary_mask & &bit).is_zero(){return Err("duplicate boundary variable".into());}
        boundary_mask|=bit;
    }
    let mut parsed_modes=Vec::new();
    for mode in modes{
        let mask=parse(mode)?;
        if !mask_subset(&mask,&boundary_mask){
            return Err("Walsh mode outside boundary".into());
        }
        parsed_modes.push(mask);
    }
    let normalized=match normalized{Some(rows) if !rows.is_empty()=>rows,_=>return Ok(None)};
    let mut entries=Vec::new();
    for (z,o) in normalized{entries.push((parse(&z)?,parse(&o)?));}
    let rank=weight(&(&entries[0].0 | &entries[0].1));
    if rank!=2 && rank!=3{return Ok(None);}
    let mut supports=BTreeSet::new();
    let mut reference_ones=BigUint::zero();
    let mut reference_zeros=BigUint::zero();
    let mut active=BigUint::zero();
    for (zeros,ones) in &entries{
        let scope=zeros|ones;
        if !(zeros&ones).is_zero() || !mask_subset(&scope,&boundary_mask){
            return Err("invalid normalized clause".into());
        }
        if weight(&scope)!=rank{return Ok(None);}
        if !(zeros & &reference_zeros).is_zero() || !(ones & &reference_ones).is_zero(){
            return Ok(None);
        }
        reference_ones|=zeros;
        reference_zeros|=ones;
        supports.insert(scope.clone());
        active|=scope;
    }
    let mut variables:Vec<usize>=boundary.iter().copied().filter(|&v|
        !(&active & (BigUint::one()<<(v-1))).is_zero()).collect();
    variables.sort_unstable();
    let n=variables.len();
    if n<rank || choose(n,rank).saturating_sub(supports.len())>max_missing{return Ok(None);}
    let mut missing=BTreeSet::new();
    for mask in support_masks(&variables,rank){
        if !supports.contains(&mask){
            missing.insert(mask);
            if missing.len()>max_missing{return Ok(None);}
        }
    }
    let defect_union=missing.iter().fold(BigUint::zero(),|acc,item|acc|item);
    let defect_vars:Vec<usize>=variables.iter().copied().filter(|&v|
        !(&defect_union & (BigUint::one()<<(v-1))).is_zero()).collect();
    let q=defect_vars.len();
    if q>max_defect_variables || q>=usize::BITS as usize || (1usize<<q)>max_subset_checks{
        return Ok(None);
    }
    let mut high=Vec::new();
    for selection in 0..(1usize<<q){
        let size=selection.count_ones() as usize;
        if size<rank || choose(size,rank)>missing.len(){continue;}
        let chosen:Vec<usize>=defect_vars.iter().enumerate().filter_map(|(i,&v)|
            if (selection>>i)&1==1{Some(v)}else{None}).collect();
        if support_masks(&chosen,rank).iter().all(|mask|missing.contains(mask)){
            high.push(chosen.iter().fold(BigUint::zero(),|acc,&v|acc|(BigUint::one()<<(v-1))));
        }
    }
    let free=&boundary_mask ^ &active;
    let denominator=BigUint::one()<<boundary.len();
    let mut coefficients=Vec::new();
    for (original,mode) in modes.iter().zip(parsed_modes.iter()){
        let mut weighted=BigInt::zero();
        if (mode & &free).is_zero(){
            let t=weight(&(mode & &active));
            for j in 0..rank{
                for a in 0..=j{
                    if a<=t && j-a<=n-t{
                        let value=BigInt::from(choose(t,a)*choose(n-t,j-a));
                        if a%2==1{weighted-=value;}else{weighted+=value;}
                    }
                }
            }
            for mask in &high{
                if weight(&(mode&mask))%2==1{weighted-=1;}else{weighted+=1;}
            }
            if weight(&(mode & &reference_ones))%2==1{weighted=-weighted;}
            weighted <<= weight(&free);
        }
        coefficients.push((original.clone(),weighted.to_string(),denominator.to_string()));
    }
    Ok(Some((coefficients,rank,missing.len(),q,high.len())))
}

fn mask_subset(mask:&BigUint,universe:&BigUint)->bool{(mask & universe)==*mask}

#[cfg(test)]
mod tests{
 use super::*;
 #[test]fn coherent_triangle(){
  let normalized=Some(vec![("0".into(),"3".into()),
      ("0".into(),"5".into()),("0".into(),"6".into())]);
  assert!(query(normalized,&[1,2,3], &["0".into()],6,18,1<<18).unwrap().is_some());
 }
}
