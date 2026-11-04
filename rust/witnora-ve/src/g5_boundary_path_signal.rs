//! R-055: indexed G5 provenance boundary-path discovery.
//! Structural diagnostic only, never a G14 separator, SAT, or Lean certificate.
use std::collections::{BTreeMap,BTreeSet};

pub type Snapshot=Option<Vec<Vec<i64>>>;
pub type Operation=(String,usize,usize,Vec<i64>,Vec<i64>,Vec<i64>,Snapshot);
#[derive(Clone,Debug,PartialEq,Eq)]
pub struct Candidate {
    pub separator:(i64,i64),
    pub path_interior:usize,
    pub path_edges:usize,
    pub balance_proxy:usize,
    pub operation_index:usize,
}
#[derive(Clone,Debug,PartialEq,Eq)]
pub struct PathSignal {
    pub initial_edge_rows:usize,
    pub xor_operations:usize,
    pub candidates:Vec<Candidate>,
}

fn support(row:&[i64])->Result<BTreeSet<i64>,String> {
    let mut found=BTreeSet::new();
    for &v in row {
        if v<=0 { return Err("G5 row coefficients must be positive integer IDs".into()); }
        if !found.insert(v) {
            return Err("G5 row coefficients must be unique".into());
        }
    }
    Ok(found)
}

fn path_interior(
    provenance:&BTreeSet<usize>,
    original:&[(i64,i64)],
    boundary:&BTreeSet<i64>,
)->Option<usize> {
    if provenance.len()<2 || boundary.len()!=2 { return None; }
    let mut adjacency=BTreeMap::<i64,BTreeSet<i64>>::new();
    let mut seen_edges=BTreeSet::<(i64,i64)>::new();
    for &idx in provenance {
        let edge=*original.get(idx)?;
        if !seen_edges.insert(edge) { return None; }
        adjacency.entry(edge.0).or_default().insert(edge.1);
        adjacency.entry(edge.1).or_default().insert(edge.0);
    }
    if !boundary.iter().all(|v|adjacency.contains_key(v))
        || provenance.len()+1!=adjacency.len()
        || adjacency.iter().any(|(v,nbrs)| nbrs.len() !=
            if boundary.contains(v) {1} else {2})
    {
        return None;
    }
    let root=*adjacency.keys().next()?;
    let mut seen=BTreeSet::from([root]);
    let mut pending=vec![root];
    while let Some(v)=pending.pop() {
        for &neighbor in &adjacency[&v] {
            if seen.insert(neighbor) { pending.push(neighbor); }
        }
    }
    (seen.len()==adjacency.len()).then_some(adjacency.len()-2)
}

pub fn boundary_path_candidates_from_g5(
    initial:&[Vec<i64>],operations:&[Operation],
)->Result<PathSignal,String> {
    let mut original=Vec::<(i64,i64)>::new();
    let mut live_support=Vec::<BTreeSet<i64>>::new();
    let mut universe=BTreeSet::<i64>::new();
    for row in initial {
        let vars=support(row)?;
        if vars.len()!=2 {
            return Err("path signal requires binary initial XOR rows".into());
        }
        let values:Vec<_>=vars.iter().copied().collect();
        original.push((values[0],values[1]));
        universe.extend(vars.iter().copied());
        live_support.push(vars);
    }
    let mut provenance:Vec<BTreeSet<usize>>=(0..initial.len())
        .map(|j|BTreeSet::from([j])).collect();
    let mut xor_count=0;
    let mut candidates=BTreeMap::<(i64,i64),Candidate>::new();
    for (op_index,op) in operations.iter().enumerate() {
        let (kind,a,b,before,source,after,snapshot)=op;
        if kind=="SWAP_ROWS" {
            if *a>=initial.len() || *b>=initial.len() {
                return Err("out-of-range or noninteger live G5 row index".into());
            }
            live_support.swap(*a,*b);
            provenance.swap(*a,*b);
            if let Some(rows)=snapshot {
                if rows.len()!=initial.len() {
                    return Err("G5 swap snapshot disagrees with live slots".into());
                }
                for (row,actual) in rows.iter().zip(live_support.iter()) {
                    if support(row)? != *actual {
                        return Err("G5 swap snapshot disagrees with live slots".into());
                    }
                }
            }
        } else if kind=="ADD_ROW_XOR" {
            if *a>=initial.len() || *b>=initial.len() {
                return Err("out-of-range or noninteger live G5 row index".into());
            }
            if *a==*b {
                return Err("self-XOR is not an indexed G5 operation".into());
            }
            let before=support(before)?;
            let source=support(source)?;
            let after=support(after)?;
            let expected:BTreeSet<i64>=before.symmetric_difference(&source)
                .copied().collect();
            if before!=live_support[*a] || source!=live_support[*b] || after!=expected {
                return Err("G5 XOR snapshot disagrees with replay".into());
            }
            live_support[*a]=after.clone();
            let new_provenance:BTreeSet<usize>=provenance[*a]
                .symmetric_difference(&provenance[*b]).copied().collect();
            provenance[*a]=new_provenance;
            xor_count+=1;
            if after.len()!=2 { continue; }
            let Some(interior)=path_interior(&provenance[*a],&original,&after) else {
                continue;
            };
            let outside=universe.len()-2-interior;
            let proxy=interior.min(outside);
            if proxy==0 { continue; }
            let ends:Vec<i64>=after.iter().copied().collect();
            let pair=(ends[0],ends[1]);
            let candidate=Candidate {
                separator:pair,
                path_interior:interior,
                path_edges:provenance[*a].len(),
                balance_proxy:proxy,
                operation_index:op_index,
            };
            if !candidates.get(&pair).is_some_and(|prior|
                (prior.balance_proxy,prior.path_edges) >=
                (candidate.balance_proxy,candidate.path_edges))
            {
                candidates.insert(pair,candidate);
            }
        } else {
            return Err("unsupported G5 operation kind".into());
        }
    }
    let mut ranked:Vec<_>=candidates.into_values().collect();
    ranked.sort_by_key(|row|(
        std::cmp::Reverse(row.balance_proxy),
        std::cmp::Reverse(row.path_edges),
        row.separator,
    ));
    Ok(PathSignal{
        initial_edge_rows:initial.len(),
        xor_operations:xor_count,
        candidates:ranked,
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn real_three_edge_path_is_only_a_diagnostic() {
        // 1-2, 2-3, 3-4 and an isolated graph edge 5-6.
        let initial=vec![vec![1,2],vec![2,3],vec![3,4],vec![5,6]];
        let ops=vec![
            ("ADD_ROW_XOR".into(),0,1,vec![1,2],vec![2,3],vec![1,3],None),
            ("ADD_ROW_XOR".into(),0,2,vec![1,3],vec![3,4],vec![1,4],None),
        ];
        let report=boundary_path_candidates_from_g5(&initial,&ops).unwrap();
        assert_eq!(report.xor_operations,2);
        assert_eq!(report.candidates.len(),2);
        assert_eq!(report.candidates[0].separator,(1,4));
        assert_eq!(report.candidates[0].path_edges,3);
        assert_eq!(report.candidates[0].path_interior,2);
        assert_eq!(report.candidates[0].balance_proxy,2);
    }
    #[test]
    fn altered_snapshot_fails() {
        let initial=vec![vec![1,2],vec![2,3]];
        let ops=vec![("ADD_ROW_XOR".into(),0,1,vec![1,2],vec![2,3],vec![1,2],None)];
        assert!(boundary_path_candidates_from_g5(&initial,&ops).is_err());
    }
}
