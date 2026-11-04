//! R-084: bounded exceptional-polarity transform and exact Walsh convolution.
use num_bigint::{BigInt,BigUint};
use num_traits::{One,Zero};
use std::collections::{BTreeMap,BTreeSet};
use std::str::FromStr;

fn parse(raw:&str)->Result<BigUint,String>{
    BigUint::from_str(raw).map_err(|_|"invalid unsigned source bitmask".into())
}
fn weight(mask:&BigUint)->usize{
    mask.iter_u32_digits().map(|v|v.count_ones() as usize).sum()
}

pub struct Prepared{
    pub base:Vec<(String,String)>,
    pub local_masks:Vec<String>,
    pub values:Vec<i64>,
    pub needed:Vec<String>,
    pub exceptions:usize,
    pub variables:usize,
}

pub fn prepare(normalized:&[(String,String)],boundary:&[usize],modes:&[String],
    max_clauses:usize,max_variables:usize,max_base_modes:usize)
    ->Result<Option<Prepared>,String>{
    if normalized.is_empty(){return Ok(None);}
    let mut boundary_mask=BigUint::zero();
    for &v in boundary{
        if !(1..=256).contains(&v){return Err("boundary IDs must be in 1..256".into());}
        let bit=BigUint::one()<<(v-1);
        if !(&boundary_mask & &bit).is_zero(){return Err("duplicate boundary variable".into());}
        boundary_mask|=bit;
    }
    let parsed_modes=modes.iter().map(|s|parse(s)).collect::<Result<Vec<_>,_>>()?;
    if parsed_modes.iter().any(|m|(m & &boundary_mask)!=*m){
        return Err("Walsh mode outside boundary".into());
    }
    let entries=normalized.iter().map(|(z,o)|Ok((parse(z)?,parse(o)?)))
        .collect::<Result<Vec<_>,String>>()?;
    let rank=weight(&(&entries[0].0 | &entries[0].1));
    if rank!=2 && rank!=3{return Ok(None);}
    let mut counts:BTreeMap<usize,(usize,usize)>=BTreeMap::new();
    for (zeros,ones) in &entries{
        let scope=zeros|ones;
        if !(zeros & ones).is_zero() || (&scope & &boundary_mask)!=scope{
            return Err("invalid normalized clause".into());
        }
        if weight(&scope)!=rank{return Ok(None);}
        for &v in boundary{
            let bit=BigUint::one()<<(v-1);
            let count=counts.entry(v).or_insert((0,0));
            if !(zeros & &bit).is_zero(){count.0+=1;}
            if !(ones & &bit).is_zero(){count.1+=1;}
        }
    }
    let mut reference_positive=BigUint::zero();
    let mut reference_negative=BigUint::zero();
    for (v,(pos,neg)) in counts{
        if pos==neg && pos>0{return Ok(None);}
        if pos>neg{reference_positive|=BigUint::one()<<(v-1);}
        else if neg>pos{reference_negative|=BigUint::one()<<(v-1);}
    }
    let mut base=Vec::new();
    let mut exceptions=Vec::new();
    let mut exception_mask=BigUint::zero();
    for (zeros,ones) in entries{
        if !(&zeros & &reference_negative).is_zero()
            || !(&ones & &reference_positive).is_zero(){
            exception_mask|=&zeros|&ones;
            exceptions.push((zeros,ones));
        }else{base.push((zeros.to_string(),ones.to_string()));}
    }
    if exceptions.is_empty() || exceptions.len()>max_clauses{return Ok(None);}
    let bits:Vec<BigUint>=boundary.iter().map(|&v|BigUint::one()<<(v-1))
        .filter(|bit|!(&exception_mask & bit).is_zero()).collect();
    let q=bits.len();
    if q>max_variables || q>=usize::BITS as usize || (1usize<<q)>max_base_modes{
        return Ok(None);
    }
    let mut local_masks=Vec::new();
    let mut values=Vec::new();
    for subset in 0..(1usize<<q){
        let assignment=bits.iter().enumerate().filter(|(i,_)|subset&(1usize<<i)!=0)
            .fold(BigUint::zero(),|acc,(_,bit)|acc|bit);
        let satisfied=exceptions.iter().all(|(z,o)|
            !((&assignment & z).is_zero() && (&assignment & o)==*o));
        local_masks.push(assignment);
        values.push(i64::from(satisfied));
    }
    for i in 0..q{
        let stride=1usize<<i;
        for start in (0..(1usize<<q)).step_by(stride*2){
            for offset in 0..stride{
                let l=start+offset;let r=l+stride;
                let (a,b)=(values[l],values[r]);
                values[l]=a+b;values[r]=a-b;
            }
        }
    }
    let mut needed=BTreeSet::new();
    for mode in parsed_modes{
        for (i,&v) in values.iter().enumerate(){
            if v==0{continue;}
            needed.insert(&mode ^ &local_masks[i]);
            if needed.len()>max_base_modes{return Ok(None);}
        }
    }
    Ok(Some(Prepared{
        base,local_masks:local_masks.iter().map(ToString::to_string).collect(),
        values,needed:needed.iter().map(ToString::to_string).collect(),
        exceptions:exceptions.len(),variables:q,
    }))
}

pub fn convolve(modes:&[String],local_masks:&[String],values:&[i64],
    coefficients:&[(String,String,String)],q:usize)
    ->Result<Vec<(String,String,String)>,String>{
    let local=local_masks.iter().map(|s|parse(s)).collect::<Result<Vec<_>,_>>()?;
    if local.len()!=values.len(){return Err("Walsh transform shape mismatch".into());}
    let mut table=BTreeMap::new();
    for (m,n,d) in coefficients{
        let num=BigInt::from_str(n).map_err(|_|"invalid numerator")?;
        let den=BigInt::from_str(d).map_err(|_|"invalid denominator")?;
        if den<=BigInt::zero(){return Err("invalid denominator".into());}
        table.insert(parse(m)?,(num,den));
    }
    let mut result=Vec::new();
    for raw in modes{
        let mode=parse(raw)?;
        let mut num=BigInt::zero();
        let mut den=BigInt::one();
        for (i,&value) in values.iter().enumerate(){
            if value==0{continue;}
            let (n,d)=table.get(&(&mode ^ &local[i])).ok_or("missing base coefficient")?;
            num=num*d+BigInt::from(value)*n*&den;
            den*=d;
        }
        den <<= q;
        result.push((raw.clone(),num.to_string(),den.to_string()));
    }
    Ok(result)
}

#[cfg(test)]
mod tests{
 use super::*;
 #[test]fn exact_transform(){
  let rows=convolve(&["0".into()], &["0".into()], &[2],
      &[("0".into(),"1".into(),"2".into())],1).unwrap();
  assert_eq!(rows[0].1,"2");assert_eq!(rows[0].2,"4");
 }
}
