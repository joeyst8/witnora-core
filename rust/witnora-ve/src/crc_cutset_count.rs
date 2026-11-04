//! R-087: bounded exact cutset-conditioned component enumeration.
//! The alternate Python VE backends remain separate pending native parity.
use num_bigint::BigUint;
use num_traits::{One,Zero};
use std::collections::BTreeMap;
use std::str::FromStr;

fn parse(mask:&str)->Result<BigUint,String>{
    BigUint::from_str(mask).map_err(|_|"invalid normalized clause mask".into())
}
fn mask_bit(v:usize)->BigUint{BigUint::one()<<(v-1)}
fn first_variable(mask:&BigUint)->Option<usize>{
    for (i,word) in mask.iter_u32_digits().enumerate(){
        if word!=0{return Some(i*32+word.trailing_zeros() as usize+1);}
    }
    None
}
fn variables(mask:&BigUint)->Vec<usize>{
    let mut ids=Vec::new();
    for (i,word) in mask.iter_u32_digits().enumerate(){
        for bit in 0..32{if (word>>bit)&1!=0{ids.push(i*32+bit+1);}}
    }
    ids
}
fn root(v:usize,parent:&mut BTreeMap<usize,usize>)->usize{
    let current=parent[&v];
    if current==v{return v;}
    let final_root=root(current,parent);
    parent.insert(v,final_root);
    final_root
}

pub fn count(normalized:&[(String,String)],boundary:&[usize],separator:&[usize],
    max_component_variables:usize,max_assignment_states:usize,max_separator_branches:usize)
    ->Result<Option<(String,usize,usize,usize)>,String>{
    if max_component_variables==0||max_assignment_states==0||max_separator_branches==0{
        return Err("invalid component/state cap".into());
    }
    let mut clauses=Vec::new();
    for (z,o) in normalized{clauses.push((parse(z)?,parse(o)?));}
    let separator_mask=separator.iter().fold(BigUint::zero(),|acc,&v|acc|mask_bit(v));
    let remaining:Vec<usize>=boundary.iter().copied().filter(|v|!separator.contains(v)).collect();
    let branches=if separator.len()<usize::BITS as usize{
        1usize<<separator.len()
    }else{return Ok(None)};
    if branches>max_separator_branches{return Ok(None);}
    let mut total=BigUint::zero();
    let mut states=0usize;
    let mut biggest=0usize;
    let mut largest_component_count=0usize;
    for branch in 0..branches{
        let condition=separator.iter().enumerate()
            .filter(|(i,_)|(branch>>i)&1!=0)
            .fold(BigUint::zero(),|acc,(_,&v)|acc|mask_bit(v));
        let missing_separator_bits=&separator_mask ^ &condition;
        let mut residual=Vec::new();
        let mut incompatible=false;
        for (zeros,ones) in &clauses{
            if !(zeros & &condition).is_zero()
                || !(ones & &missing_separator_bits).is_zero(){continue;}
            let z=zeros ^ (zeros & &separator_mask);
            let o=ones ^ (ones & &separator_mask);
            if (&z | &o).is_zero(){incompatible=true;break;}
            residual.push((z,o));
        }
        if incompatible{continue;}
        let mut parent:BTreeMap<usize,usize>=remaining.iter().map(|&v|(v,v)).collect();
        for (z,o) in &residual{
            let scope=z|o;
            let vars=variables(&scope);
            if let Some(&first)=vars.first(){
                for &v in &vars[1..]{
                    let (a,b)=(root(first,&mut parent),root(v,&mut parent));
                    if a!=b{parent.insert(b,a);}
                }
            }
        }
        let mut by_component:BTreeMap<usize,Vec<usize>>=BTreeMap::new();
        let mut component_order=Vec::new();
        for &v in &remaining{
            let r=root(v,&mut parent);
            if !by_component.contains_key(&r){component_order.push(r);}
            by_component.entry(r).or_default().push(v);
        }
        let mut clauses_by_component:BTreeMap<usize,Vec<(BigUint,BigUint)>>=BTreeMap::new();
        for (z,o) in residual{
            let scope=&z|&o;
            let first=first_variable(&scope).ok_or("unexpected empty residual clause")?;
            let r=root(first,&mut parent);
            clauses_by_component.entry(r).or_default().push((z,o));
        }
        largest_component_count=largest_component_count.max(by_component.len());
        let mut branch_models=BigUint::one();
        for component in component_order{
            let vars=&by_component[&component];
            let local=if let Some(c)=clauses_by_component.get(&component){c}else{
                branch_models<<=vars.len();
                continue;
            };
            let width=vars.len();
            biggest=biggest.max(width);
            if width>max_component_variables || width>=usize::BITS as usize{return Ok(None);}
            let attempts=1usize<<width;
            if attempts>max_assignment_states-states{return Ok(None);}
            states+=attempts;
            let mut models=0usize;
            for packed in 0..attempts{
                let bits=vars.iter().enumerate().filter(|(i,_)|(packed>>i)&1!=0)
                    .fold(BigUint::zero(),|acc,(_,&v)|acc|mask_bit(v));
                if local.iter().all(|(z,o)|
                    !((&bits & z).is_zero() && (&bits & o)==*o)){
                    models+=1;
                }
            }
            branch_models*=BigUint::from(models);
            if branch_models.is_zero(){break;}
        }
        total+=branch_models;
    }
    Ok(Some((total.to_string(),biggest,states,largest_component_count)))
}

#[cfg(test)]
mod tests{
 use super::*;
 #[test]fn star_count(){
  let source=vec![("5".into(),"0".into()),("6".into(),"0".into())];
  let count=count(&source,&[1,2,3],&[3],14,1000,64).unwrap().unwrap();
  assert_eq!(count.0,"5");
 }
}
