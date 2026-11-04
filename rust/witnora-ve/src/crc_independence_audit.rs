//! R-081: exact cross-group Fourier-moment independence arithmetic.
use num_bigint::{BigUint, BigInt};
use num_traits::Zero;
use std::collections::BTreeMap;
use std::str::FromStr;

fn decimal_mask(raw:&str)->Result<BigUint,String>{
    BigUint::from_str(raw).map_err(|_|"invalid Fourier mask".to_string())
}

fn submasks(bits:&[BigUint])->Vec<BigUint>{
    let mut masks=vec![BigUint::zero()];
    for bit in bits{
        let added=masks.iter().map(|mask|mask|bit).collect::<Vec<_>>();
        masks.extend(added);
    }
    masks
}

pub fn mode_masks(left:&[String],right:&[String])
 ->Result<Vec<String>,String>{
    let left=left.iter().map(|x|decimal_mask(x)).collect::<Result<Vec<_>,_>>()?;
    let right=right.iter().map(|x|decimal_mask(x)).collect::<Result<Vec<_>,_>>()?;
    let mut modes=Vec::new();
    for l in submasks(&left){for r in submasks(&right){modes.push(&l|r);}}
    modes.sort();
    modes.dedup();
    Ok(modes.iter().map(ToString::to_string).collect())
}

pub fn audit(left:&[String],right:&[String],coefficients:&[(String,String,String)])
 ->Result<Option<(String,String,String,String)>,String>{
    let left=left.iter().map(|x|decimal_mask(x)).collect::<Result<Vec<_>,_>>()?;
    let right=right.iter().map(|x|decimal_mask(x)).collect::<Result<Vec<_>,_>>()?;
    let mut coeff:BTreeMap<BigUint,(BigInt,BigInt)>=BTreeMap::new();
    for (mask,numerator,denominator) in coefficients{
        let key=decimal_mask(mask)?;
        let n=BigInt::from_str(numerator).map_err(|_|"invalid coefficient numerator")?;
        let d=BigInt::from_str(denominator).map_err(|_|"invalid coefficient denominator")?;
        if d<=BigInt::zero(){return Err("invalid Fourier coefficient denominator".into());}
        coeff.insert(key,(n,d));
    }
    let (n0,d0)=coeff.get(&BigUint::zero()).ok_or("missing Fourier base coefficient")?;
    for l in submasks(&left){
        for r in submasks(&right){
            let (nl,dl)=coeff.get(&l).ok_or("missing left Fourier coefficient")?;
            let (nr,dr)=coeff.get(&r).ok_or("missing right Fourier coefficient")?;
            let (nj,dj)=coeff.get(&(&l|&r)).ok_or("missing joint Fourier coefficient")?;
            let numerator=nj*n0*dl*dr-nl*nr*dj*d0;
            if !numerator.is_zero(){
                let denominator=dj*d0*dl*dr;
                return Ok(Some((l.to_string(),r.to_string(),numerator.to_string(),denominator.to_string())));
            }
        }
    }
    Ok(None)
}

#[cfg(test)]
mod tests{
    use super::*;
    #[test]fn detects_cross_moment(){
        let left=vec!["1".into()];let right=vec!["2".into()];
        assert_eq!(mode_masks(&left,&right).unwrap(),vec!["0","1","2","3"]);
        let coefficients=vec![("0".into(),"4".into(),"1".into()),
            ("1".into(),"2".into(),"1".into()),
            ("2".into(),"2".into(),"1".into()),
            ("3".into(),"3".into(),"1".into())];
        assert!(audit(&left,&right,&coefficients).unwrap().is_some());
    }
}
