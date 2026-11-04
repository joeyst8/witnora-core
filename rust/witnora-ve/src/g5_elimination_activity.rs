//! R-054: G5 indexed row-XOR activity diagnostics, without proof promotion.
use std::collections::{BTreeMap,BTreeSet};

pub type Operation=(String,Vec<i64>,Vec<i64>);

fn validate_universe(variables:&[i64])->Result<Vec<i64>,String> {
    if variables.iter().any(|&v|v<=0) {
        return Err("variables must be positive integer IDs".into());
    }
    Ok(variables.iter().copied().collect::<BTreeSet<_>>()
        .into_iter().collect())
}

fn valid_support(support:&[i64])->Result<BTreeSet<i64>,String> {
    let mut result=BTreeSet::new();
    for &v in support {
        if v<=0 {
            return Err("G5 row coefficients must be positive integer IDs".into());
        }
        if !result.insert(v) {
            return Err("G5 row coefficients must be unique".into());
        }
    }
    Ok(result)
}

fn extract(
    op:&Operation, universe:&BTreeSet<i64>
)->Result<Option<(BTreeSet<i64>,BTreeSet<i64>)>,String> {
    if op.0=="SWAP_ROWS" { return Ok(None); }
    if op.0!="ADD_ROW_XOR" { return Err("unsupported G5 operation kind".into()); }
    let before=valid_support(&op.1)?;
    let source=valid_support(&op.2)?;
    if !before.union(&source).all(|v|universe.contains(v)) {
        return Err("operation has variable outside declared universe".into());
    }
    Ok(Some((before,source)))
}

#[derive(Clone,Debug,PartialEq,Eq)]
pub struct Activity {
    pub ranked_variables:Vec<i64>,
    pub touches:Vec<(i64,usize)>,
    pub cancellations:Vec<(i64,usize)>,
    pub xor_operations:usize,
    pub top_pair:Vec<i64>,
}

pub fn activity_from_g5_operations(
    operations:&[Operation], variables:&[i64],
)->Result<Activity,String> {
    let universe=validate_universe(variables)?;
    let permitted:BTreeSet<i64>=universe.iter().copied().collect();
    let mut touches=BTreeMap::<i64,usize>::new();
    let mut cancellations=BTreeMap::<i64,usize>::new();
    let mut xor_operations=0;
    for op in operations {
        let Some((before,source))=extract(op,&permitted)? else {continue;};
        xor_operations+=1;
        for &v in before.union(&source) {
            *touches.entry(v).or_default()+=1;
        }
        for &v in before.intersection(&source) {
            *cancellations.entry(v).or_default()+=1;
        }
    }
    let mut ranked=universe.clone();
    ranked.sort_by_key(|v|(
        std::cmp::Reverse(*touches.get(v).unwrap_or(&0)),
        std::cmp::Reverse(*cancellations.get(v).unwrap_or(&0)),
        *v,
    ));
    let top_pair=if ranked.len()>=2 {ranked[..2].to_vec()} else {vec![]};
    Ok(Activity {
        ranked_variables:ranked,
        touches:universe.iter().map(|&v|(v,*touches.get(&v).unwrap_or(&0))).collect(),
        cancellations:universe.iter().map(|&v|(v,*cancellations.get(&v).unwrap_or(&0))).collect(),
        xor_operations,top_pair,
    })
}

pub fn ranked_pair_candidates(
    ranked:&[i64],limit:Option<i64>,
)->Result<Vec<(i64,i64)>,String> {
    if limit.is_some_and(|n|n<0) { return Err("limit must be a nonnegative integer".into()); }
    let n=limit.map(|v|usize::try_from(v).unwrap_or(usize::MAX))
        .unwrap_or(ranked.len()).min(ranked.len());
    let mut pairs=Vec::new();
    for i in 0..n {
        for j in (i+1)..n { pairs.push((ranked[i],ranked[j])); }
    }
    Ok(pairs)
}

#[derive(Clone,Debug,PartialEq,Eq)]
pub struct CrossMerge {
    pub ranked_pairs:Vec<(i64,i64)>,
    pub scores:Vec<((i64,i64),usize)>,
    pub cross_merge_events:usize,
}

pub fn pairwise_cross_merge_activity(
    operations:&[Operation],variables:&[i64],
)->Result<CrossMerge,String> {
    let universe=validate_universe(variables)?;
    let permitted:BTreeSet<_>=universe.iter().copied().collect();
    let mut scores=BTreeMap::<(i64,i64),usize>::new();
    let mut events=0;
    for op in operations {
        let Some((before,source))=extract(op,&permitted)? else {continue;};
        for &left in before.difference(&source) {
            for &right in source.difference(&before) {
                let pair=(left.min(right),left.max(right));
                *scores.entry(pair).or_default()+=1;
                events+=1;
            }
        }
    }
    let mut pairs=Vec::new();
    for i in 0..universe.len() {
        for j in (i+1)..universe.len() {
            pairs.push((universe[i],universe[j]));
        }
    }
    let expanded_scores:Vec<_>=pairs.iter()
        .map(|&pair|(pair,*scores.get(&pair).unwrap_or(&0))).collect();
    pairs.sort_by_key(|pair|(
        std::cmp::Reverse(*scores.get(pair).unwrap_or(&0)),*pair,
    ));
    Ok(CrossMerge{
        ranked_pairs:pairs,scores:expanded_scores,cross_merge_events:events,
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn overlap_touches_and_cross_merge() {
        let operations=vec![
            ("SWAP_ROWS".to_string(),vec![],vec![]),
            ("ADD_ROW_XOR".to_string(),vec![1,2],vec![2,3]),
        ];
        let activity=activity_from_g5_operations(&operations,&[1,2,3,4]).unwrap();
        assert_eq!(activity.ranked_variables,vec![2,1,3,4]);
        assert_eq!(activity.top_pair,vec![2,1]);
        assert_eq!(activity.xor_operations,1);
        let cross=pairwise_cross_merge_activity(&operations,&[1,2,3,4]).unwrap();
        assert_eq!(cross.cross_merge_events,1);
        assert_eq!(cross.ranked_pairs[0],(1,3));
        assert_eq!(ranked_pair_candidates(&activity.ranked_variables,Some(2)).unwrap(),
            vec![(2,1)]);
    }
}
