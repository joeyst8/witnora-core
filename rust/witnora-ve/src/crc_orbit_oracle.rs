//! R-085: near-complete orbit oracle as a bounded subset of the R-082 defect kernel.
//! With at most rank r missing rank-r supports, no admissible flip set can
//! have size greater than r; such a set would require r+1 missing supports.
use num_bigint::BigUint;
use num_traits::Zero;
use std::str::FromStr;

pub fn query(normalized:Option<Vec<(String,String)>>,boundary:&[usize],
    modes:&[String],max_missing:usize)
    ->Result<Option<(Vec<(String,String,String)>,usize,usize,usize)>,String>{
    let entries=match normalized.as_ref(){Some(entries) if !entries.is_empty()=>entries,
        _=>return Ok(None)};
    let parse=|raw:&str|BigUint::from_str(raw)
        .map_err(|_|"invalid nonnegative normalized bitmask".to_string());
    let (z,o)=(&entries[0].0,&entries[0].1);
    let rank=(&parse(z)? | &parse(o)?).iter_u32_digits()
        .map(|w|w.count_ones() as usize).sum::<usize>();
    if rank!=2 && rank!=3{return Ok(None);}
    let mut active=BigUint::zero();
    for (z,o) in entries{active|=parse(z)? | parse(o)?;}
    let n=active.iter_u32_digits().map(|w|w.count_ones() as usize).sum();
    let result=crate::crc_defect_oracle::query(
        normalized,boundary,modes,max_missing.min(rank),rank*rank,1usize<<(rank*rank))?;
    Ok(result.map(|(coeffs,actual_rank,missing,_,high)|{
        debug_assert_eq!(actual_rank,rank);
        debug_assert_eq!(high,missing);
        (coeffs,rank,missing,n)
    }))
}

#[cfg(test)]
mod tests{
 use super::*;
 #[test]fn no_missing_triangle(){
  let rows=vec![("0".into(),"3".into()),("0".into(),"5".into()),
    ("0".into(),"6".into())];
  let got=query(Some(rows),&[1,2,3], &["0".into()],3).unwrap().unwrap();
  assert_eq!((got.1,got.2,got.3),(2,0,3));
 }
}
