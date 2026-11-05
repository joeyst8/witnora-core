//! R-079: deterministic width-bounded incidence rows for distinct 3-CNF.
use std::collections::BTreeSet;

fn pairs(scope:&BTreeSet<usize>)->BTreeSet<(usize,usize)>{
    let values:Vec<usize>=scope.iter().copied().collect();
    let mut result=BTreeSet::new();
    for (i,&a) in values.iter().enumerate(){for &b in &values[i+1..]{result.insert((a,b));}}
    result
}

fn fill_count(scope:&BTreeSet<usize>,original:&BTreeSet<(usize,usize)>)->usize{
    pairs(scope).difference(original).count()
}

pub fn primal_pairs(source:&[Vec<i32>])->Vec<(usize,usize)>{
    let mut result=BTreeSet::new();
    for row in source{
        for (i,&a) in row.iter().enumerate(){for &b in &row[i+1..]{
            let (a,b)=(a.unsigned_abs() as usize,b.unsigned_abs() as usize);
            result.insert((a.min(b),a.max(b)));
        }}
    }
    result.into_iter().collect()
}

pub fn build(source:&[Vec<i32>],nvars:usize,width:usize)->Result<Vec<Vec<usize>>,String>{
    if nvars==0{return Err("nvars must be positive".into());}
    if width==0{return Err("max_row_width must be positive".into());}
    let mut scopes=Vec::new();
    for clause in source{
        let scope:BTreeSet<usize>=clause.iter().map(|v|v.unsigned_abs() as usize).collect();
        if clause.len()!=3 || scope.len()!=3 || scope.contains(&0)
            || scope.iter().any(|v|*v>nvars){
            return Err("geometry-aware prototype supports distinct 3-CNF only".into());
        }
        scopes.push(scope);
    }
    let originals:BTreeSet<(usize,usize)>=primal_pairs(source).into_iter().collect();
    let m=source.len();
    let mut incident=vec![Vec::<usize>::new();nvars+1];
    for (j,scope) in scopes.iter().enumerate(){for &v in scope{incident[v].push(j);}}
    let mut rows:Vec<BTreeSet<usize>>=Vec::new();
    let mut selected=vec![BTreeSet::<usize>::new();m];
    for v in 1..=nvars{
        let mut buckets:Vec<BTreeSet<usize>>=Vec::new();
        let mut bucket_scopes:Vec<BTreeSet<usize>>=Vec::new();
        let mut ordered=incident[v].clone();
        ordered.sort_by_key(|&j|scopes[j].iter().filter(|&&x|x!=v).copied().collect::<Vec<_>>());
        for j in ordered{
            let chosen=(0..buckets.len()).filter(|&i|buckets[i].len()<width)
                .min_by_key(|&i|{
                    let union:BTreeSet<usize>=bucket_scopes[i].union(&scopes[j]).copied().collect();
                    (fill_count(&union,&originals)-fill_count(&bucket_scopes[i],&originals),
                     union.difference(&bucket_scopes[i]).count(),
                     std::cmp::Reverse(buckets[i].len()),i)
                });
            let id=if let Some(i)=chosen{i}else{
                buckets.push(BTreeSet::new());
                bucket_scopes.push(BTreeSet::from([v]));
                buckets.len()-1
            };
            buckets[id].insert(j);
            bucket_scopes[id].extend(scopes[j].iter().copied());
        }
        for bucket in buckets{
            let row_id=rows.len();
            for &j in &bucket{selected[j].insert(row_id);}
            rows.push(bucket);
        }
    }
    let mut used:BTreeSet<Vec<usize>>=BTreeSet::new();
    for j in 0..m{
        let signature=selected[j].iter().copied().collect::<Vec<_>>();
        if used.contains(&signature){
            let old=*selected[j].iter().max_by_key(|&&i|(rows[i].len(),std::cmp::Reverse(i)))
                .ok_or("empty signature")?;
            rows[old].remove(&j);
            selected[j].remove(&old);
            let new_id=rows.len();
            rows.push(BTreeSet::from([j]));
            selected[j].insert(new_id);
        }
        used.insert(selected[j].iter().copied().collect());
    }
    Ok(rows.into_iter().filter(|row|!row.is_empty())
        .map(|row|row.into_iter().collect()).collect())
}

#[cfg(test)]
mod tests{
 use super::*;
 #[test]fn width_three(){
  let source=vec![vec![1,2,3],vec![-1,2,3],vec![1,2,-3]];
  let rows=build(&source,3,2).unwrap();
  assert!(rows.iter().all(|r|r.len()<=2));
  assert!(!rows.is_empty());
 }
}
