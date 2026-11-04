//! R-053: sparse GF(2) parity-row subset basis and reconstruction witnesses.
//! Preserves original bounded-width rows, never claiming source-CNF equivalence.

use num_bigint::BigUint;
use num_traits::{One,Zero};
use std::collections::{BTreeMap,BTreeSet};
use std::ops::BitXorAssign;

#[derive(Clone,Debug,PartialEq,Eq)]
pub struct SparseBasisCertificate {
    pub clause_count: usize,
    pub original_row_count: usize,
    pub selected_indices: Vec<usize>,
    pub rows: Vec<Vec<usize>>,
    pub expansions: Vec<BigUint>,
    pub ordering: String,
}

fn checked_rows(
    clause_count: i64, max_row_width: i64, input: &[Vec<i64>],
) -> Result<(usize,usize,Vec<Vec<usize>>),String> {
    if clause_count < 0 || max_row_width < 1 {
        return Err("invalid sketch dimension".into());
    }
    let m=usize::try_from(clause_count).map_err(|_|"clause count overflows usize")?;
    let max_width=usize::try_from(max_row_width).map_err(|_|"row width overflows usize")?;
    let mut rows=Vec::new();
    for input_row in input {
        if input_row.len() > max_width {
            return Err("invalid parity row".into());
        }
        let mut row=Vec::new();
        let mut previous=None;
        for &column in input_row {
            if column < 0 || column >= clause_count || previous.is_some_and(|v| column<=v) {
                return Err("invalid parity row".into());
            }
            row.push(column as usize);
            previous=Some(column);
        }
        rows.push(row);
    }
    Ok((m,max_width,rows))
}

fn row_bits(row: &[usize]) -> BigUint {
    let mut mask=BigUint::zero();
    for &j in row {
        mask ^= BigUint::one() << j;
    }
    mask
}

fn least_bit(mask: &BigUint) -> Option<usize> {
    mask.iter_u32_digits().enumerate()
        .find(|&(_,word)|word != 0)
        .map(|(index,word)| 32*index+word.trailing_zeros() as usize)
}

fn xor_selected(coefficients: &BigUint, rows: &[BigUint]) -> BigUint {
    let mut result=BigUint::zero();
    for (index,row) in rows.iter().enumerate() {
        if ((coefficients >> index) & BigUint::one()) == BigUint::one() {
            result ^= row;
        }
    }
    result
}

fn verify(
    source_rows: &[Vec<usize>],
    max_row_width: usize,
    cert: &SparseBasisCertificate,
) -> Result<(),String> {
    if cert.original_row_count != source_rows.len()
        || cert.expansions.len() != source_rows.len()
        || (cert.ordering!="shortest_first" && cert.ordering!="source_order")
        || cert.selected_indices.len()!=cert.rows.len()
        || cert.selected_indices.iter().any(|&j|j>=source_rows.len())
        || cert.selected_indices.iter().collect::<BTreeSet<_>>().len()!=cert.selected_indices.len()
    {
        return Err("basis dimensions or indexing invalid".into());
    }
    for (&source_index,row) in cert.selected_indices.iter().zip(cert.rows.iter()) {
        if &source_rows[source_index]!=row {
            return Err("a retained row differs from the source sketch".into());
        }
        if row.len()>max_row_width {
            return Err("basis row scope too large".into());
        }
    }
    let rowbits:Vec<_>=cert.rows.iter().map(|row|row_bits(row)).collect();
    let originalbits:Vec<_>=source_rows.iter().map(|row|row_bits(row)).collect();
    let limit=BigUint::one()<<rowbits.len();
    for (original,expression) in originalbits.iter().zip(cert.expansions.iter()) {
        if expression >= &limit {
            return Err("out-of-range row reconstruction coefficients".into());
        }
        if xor_selected(expression,&rowbits)!=*original {
            return Err("invalid GF(2) reconstruction witness".into());
        }
    }
    for (basis_index,&source_index) in cert.selected_indices.iter().enumerate() {
        if cert.expansions[source_index] != BigUint::one()<<basis_index {
            return Err("retained row has invalid identity witness".into());
        }
    }
    let mut pivots=BTreeMap::<usize,BigUint>::new();
    for source in &rowbits {
        let mut remaining=source.clone();
        while let Some(pivot)=least_bit(&remaining) {
            if let Some(reduced)=pivots.get(&pivot) {
                remaining.bitxor_assign(reduced);
            } else {
                pivots.insert(pivot,remaining);
                break;
            }
        }
        if remaining.is_zero() {
            return Err("claimed basis has linearly dependent rows".into());
        }
    }
    Ok(())
}

pub fn build_sparse_parity_basis(
    clause_count: i64,
    max_row_width: i64,
    input: &[Vec<i64>],
    ordering: &str,
) -> Result<SparseBasisCertificate,String> {
    if ordering!="shortest_first" && ordering!="source_order" {
        return Err("unsupported row ordering".into());
    }
    let (m,width,rows)=checked_rows(clause_count,max_row_width,input)?;
    let mut order:Vec<usize>=(0..rows.len()).collect();
    if ordering=="shortest_first" {
        order.sort_by_key(|&j|(rows[j].len(),rows[j].clone(),j));
    }
    let mut pivots=BTreeMap::<usize,(BigUint,BigUint)>::new();
    let mut chosen=Vec::<usize>::new();
    let mut coefficients=vec![BigUint::zero();rows.len()];
    for source_index in order {
        let mut remaining=row_bits(&rows[source_index]);
        let mut expression=BigUint::zero();
        while let Some(pivot)=least_bit(&remaining) {
            if let Some((reduced,retained_expression))=pivots.get(&pivot) {
                remaining.bitxor_assign(reduced);
                expression.bitxor_assign(retained_expression);
            } else {
                let basis_index=chosen.len();
                chosen.push(source_index);
                pivots.insert(pivot,(
                    remaining.clone(),&expression ^ (BigUint::one()<<basis_index)
                ));
                expression=BigUint::one()<<basis_index;
                break;
            }
        }
        coefficients[source_index]=expression;
    }
    let cert=SparseBasisCertificate{
        clause_count:m,
        original_row_count:rows.len(),
        selected_indices:chosen.clone(),
        rows:chosen.iter().map(|&j|rows[j].clone()).collect(),
        expansions:coefficients,
        ordering:ordering.to_string(),
    };
    verify(&rows,width,&cert)?;
    Ok(cert)
}

pub fn verify_sparse_parity_basis(
    clause_count:i64,
    max_row_width:i64,
    input:&[Vec<i64>],
    selected_indices:&[usize],
    cert_rows:&[Vec<i64>],
    expansions:&[String],
    ordering:&str,
) -> Result<(),String> {
    let (m,width,rows)=checked_rows(clause_count,max_row_width,input)?;
    let (_,_,retained)=checked_rows(clause_count,max_row_width,cert_rows)?;
    let mut coefficients=Vec::new();
    for value in expansions {
        if value.starts_with('-') {
            return Err("out-of-range row reconstruction coefficients".into());
        }
        coefficients.push(BigUint::parse_bytes(value.as_bytes(),10)
            .ok_or("invalid GF(2) coefficient integer")?);
    }
    let cert=SparseBasisCertificate{
        clause_count:m,original_row_count:rows.len(),
        selected_indices:selected_indices.to_vec(),
        rows:retained,expansions:coefficients,ordering:ordering.to_string(),
    };
    verify(&rows,width,&cert)
}

pub fn accepts_masks(mask:&BigUint, rows:&[Vec<usize>]) -> bool {
    rows.iter().all(|row| {
        let bits=row_bits(row);
        let intersection=mask & &bits;
        intersection.iter_u32_digits().map(|digit|digit.count_ones()).sum::<u32>()%2 == 0
    })
}

pub fn accepts_masks_decimal(
    mask:&str, input:&[Vec<i64>],
) -> Result<bool,String> {
    if mask.starts_with('-') { return Err("negative violation bit mask".into()); }
    let parsed=BigUint::parse_bytes(mask.as_bytes(),10)
        .ok_or("invalid decimal violation bit mask")?;
    let mut rows=Vec::new();
    for input_row in input {
        let mut row=Vec::new();
        for &col in input_row {
            if col < 0 { return Err("negative row column".into()); }
            row.push(col as usize);
        }
        rows.push(row);
    }
    Ok(accepts_masks(&parsed,&rows))
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn dependent_rows_reconstruct() {
        let input=vec![vec![0,1],vec![1,2],vec![0,2],vec![],vec![0,1]];
        let cert=build_sparse_parity_basis(3,2,&input,"source_order").unwrap();
        assert_eq!(cert.selected_indices,vec![0,1]);
        assert_eq!(cert.expansions.iter().map(ToString::to_string).collect::<Vec<_>>(),
            vec!["1","2","3","0","1"]);
        assert!(accepts_masks(&BigUint::from(7u32),&cert.rows));
        assert!(!accepts_masks(&BigUint::from(1u32),&cert.rows));
    }
    #[test]
    fn malformed_certificate_is_rejected() {
        let input=vec![vec![0],vec![0]];
        let cert=build_sparse_parity_basis(1,1,&input,"source_order").unwrap();
        let mut expansions=cert.expansions.iter().map(ToString::to_string).collect::<Vec<_>>();
        expansions[1]="0".into();
        assert!(verify_sparse_parity_basis(
            1,1,&input,&cert.selected_indices,
            &input[0..1],&expansions,"source_order"
        ).is_err());
    }
}
