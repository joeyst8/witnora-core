//! R-056: sparse odd-column check matrices, bounded diagnostics, finite audit.
//! Python supplies the legacy MT19937 jitter stream to retain exact seeded
//! experiment reproduction. This is not a source-CNF equivalence theorem.

use num_bigint::BigUint;
use num_traits::{One,Zero};
use std::collections::{BTreeMap,BTreeSet};

pub fn validate_rows(
    clause_count:usize,max_width:usize,rows:&[Vec<usize>],
)->Result<(),String>{
    if max_width==0 {return Err("invalid row-width bound".into());}
    for row in rows{
        if row.len()>max_width {return Err("row exceeds declared width".into());}
        let mut previous=None;
        for &j in row{
            if j>=clause_count || previous.is_some_and(|v|j<=v){
                return Err("invalid sparse row".into());
            }
            previous=Some(j);
        }
    }
    let signatures=column_signatures(rows,clause_count)?;
    if signatures.iter().any(|s|s.iter_u32_digits()
        .map(|d|d.count_ones()).sum::<u32>()!=3){
        return Err("column degree is not three".into());
    }
    if signatures.iter().collect::<BTreeSet<_>>().len()!=signatures.len(){
        return Err("columns have duplicate signatures".into());
    }
    Ok(())
}

pub fn column_signatures(
    rows:&[Vec<usize>],clause_count:usize,
)->Result<Vec<BigUint>,String>{
    let mut signatures=vec![BigUint::zero();clause_count];
    for (rid,row) in rows.iter().enumerate(){
        for &j in row{
            if j>=clause_count {return Err("row references absent clause".into());}
            signatures[j]|=BigUint::one()<<rid;
        }
    }
    Ok(signatures)
}

fn count_zero_combinations(
    signatures:&[BigUint], start:usize, left:usize, current:&BigUint,
)->usize{
    if left==0 {return usize::from(current.is_zero());}
    if start>signatures.len() || left>signatures.len()-start {return 0;}
    let mut count=0;
    for j in start..=(signatures.len()-left){
        count+=count_zero_combinations(signatures,j+1,left-1,
            &(current ^ &signatures[j]));
    }
    count
}

pub fn low_weight_collisions(
    rows:&[Vec<usize>],clause_count:usize,max_weight:i64,
)->Result<usize,String>{
    let signatures=column_signatures(rows,clause_count)?;
    let mut collisions=0;
    for weight in 1..=(max_weight.max(0) as usize).min(clause_count){
        collisions+=count_zero_combinations(&signatures,0,weight,&BigUint::zero());
    }
    Ok(collisions)
}

fn choose_three(n:usize)->u128{
    if n<3 {return 0;}
    (n as u128)*(n as u128-1)*(n as u128-2)/6
}

pub fn build_sparse_odd_rows<F>(
    clause_count:usize,max_width:usize,max_attempts:usize,
    mut jitter:F,
)->Result<Vec<Vec<usize>>,String>
where F: FnMut()->Result<f64,String>{
    if max_width==0 || max_attempts==0 {
        return Err("row width and attempt count must be positive".into());
    }
    if clause_count==0 {return Ok(vec![]);}
    let degree=3usize;
    let total=degree.checked_mul(clause_count).ok_or("matrix size overflow")?;
    let mut row_count=degree.max(
        (total+max_width-1)/max_width+degree
    );
    while choose_three(row_count)<clause_count as u128 {row_count+=1;}
    for _ in 0..max_attempts{
        let mut loads=vec![0usize;row_count];
        let mut cols=Vec::<[usize;3]>::new();
        let mut used=BTreeSet::<[usize;3]>::new();
        let mut success=true;
        for _ in 0..clause_count{
            let choices:Vec<usize>=(0..row_count)
                .filter(|&j|loads[j]<max_width).collect();
            if choices.len()<degree {success=false;break;}
            let mut winner=None;
            for _ in 0..50{
                let mut scored=Vec::<(usize,f64,usize)>::new();
                for &j in &choices {
                    let next=jitter()?;
                    if !next.is_finite() {
                        return Err("random jitter must be finite".into());
                    }
                    scored.push((loads[j],next,j));
                }
                scored.sort_by(|a,b|{
                    a.0.cmp(&b.0).then_with(||a.1.total_cmp(&b.1))
                });
                let mut proposal=[scored[0].2,scored[1].2,scored[2].2];
                proposal.sort_unstable();
                if !used.contains(&proposal){winner=Some(proposal);break;}
            }
            let Some(chosen)=winner else {success=false;break;};
            used.insert(chosen);
            cols.push(chosen);
            for j in chosen {loads[j]+=1;}
        }
        if success{
            let mut row_sets=vec![BTreeSet::<usize>::new();row_count];
            for (col,chosen) in cols.iter().enumerate(){
                for &rid in chosen {row_sets[rid].insert(col);}
            }
            let rows:Vec<Vec<usize>>=row_sets.into_iter()
                .map(|r|r.into_iter().collect()).collect();
            validate_rows(clause_count,max_width,&rows)?;
            return Ok(rows);
        }
    }
    Err("could not construct bounded-degree odd-column matrix".into())
}

pub fn source_row_scope(source:&[Vec<i32>],row:&[usize])
    ->Result<usize,String>{
    let mut variables=BTreeSet::new();
    for &j in row {
        let clause=source.get(j).ok_or("row references absent clause")?;
        for &lit in clause {variables.insert(lit.unsigned_abs());}
    }
    Ok(variables.len())
}

pub fn audit_sparse_small(
    source:&[Vec<i32>],nvars:usize,rows:&[Vec<usize>],
    max_variables:i64,
)->Result<(usize,usize,usize,usize,f64),String>{
    if nvars>max_variables.max(0) as usize || nvars>20 {
        return Err("small-only assignment audit".into());
    }
    let mut models=0usize;
    let mut false_positives=0usize;
    for assignment in 0..(1usize<<nvars) {
        let violated:Vec<bool>=source.iter().map(|clause|{
            !clause.iter().any(|&lit|{
                if lit==0 || lit.unsigned_abs() as usize >nvars {return false;}
                let bit=((assignment >> ((lit.unsigned_abs() as usize)-1))&1)!=0;
                bit==(lit>0)
            })
        }).collect();
        if violated.iter().all(|v| !v) {models+=1;}
        else if rows.iter().all(|row|row.iter()
                .filter(|&&j|violated.get(j).copied().unwrap_or(false))
                .count()%2==0) {
            false_positives+=1;
        }
    }
    let mut sizes=Vec::new();
    for row in rows { sizes.push(source_row_scope(source,row)?); }
    let total=1usize<<nvars;
    let max_scope=sizes.iter().copied().max().unwrap_or(0);
    let mean=if sizes.is_empty(){0.0}
        else{sizes.iter().sum::<usize>() as f64/sizes.len() as f64};
    Ok((models,total-models,false_positives,max_scope,mean))
}

pub fn min_degree_elimination_width(
    scopes:&[Vec<i64>],nvars:i64,
)->Result<usize,String>{
    if nvars<0 {return Err("nvars must be nonnegative".into());}
    let mut graph=BTreeMap::<i64,BTreeSet<i64>>::new();
    for v in 1..=nvars {graph.insert(v,BTreeSet::new());}
    for scope in scopes{
        let vertices:BTreeSet<i64>=scope.iter().copied().collect();
        if vertices.iter().any(|&v|v<1 || v>nvars) {
            return Err("factor variable out of range".into());
        }
        for &v in &vertices {
            graph.get_mut(&v).unwrap().extend(vertices.iter()
                .filter(|&&u|u!=v).copied());
        }
    }
    let mut active:BTreeSet<i64>=graph.keys().copied().collect();
    let mut max_width=0;
    while !active.is_empty(){
        let v=*active.iter().min_by_key(|&&v|{
            (graph[&v].intersection(&active).count(),v)
        }).unwrap();
        let neighbors:BTreeSet<i64>=graph[&v].intersection(&active).copied().collect();
        max_width=max_width.max(neighbors.len());
        for &u in &neighbors{
            let row=graph.get_mut(&u).unwrap();
            row.extend(neighbors.iter().copied().filter(|&j|j!=u));
            row.remove(&v);
        }
        active.remove(&v);
    }
    Ok(max_width)
}

#[cfg(test)]
mod tests{
    use super::*;
    #[test]
    fn three_sparse_odd_columns(){
        let rows=vec![vec![0,1],vec![0,2],vec![0],vec![1,2],
            vec![1],vec![2]];
        assert!(validate_rows(3,2,&rows).is_ok());
        assert_eq!(low_weight_collisions(&rows,3,3).unwrap(),0);
        assert_eq!(min_degree_elimination_width(&[vec![1,2],vec![2,3]],3)
            .unwrap(),1);
    }
}
