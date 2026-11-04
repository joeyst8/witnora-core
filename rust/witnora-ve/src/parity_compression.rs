//! R-074: exact source-binary-XOR root-offset compression and residual rewrite.
//! Structural candidates remain NOT_LEAN_VERIFIED until an independent proof.
use crate::cnf::CanonicalCnf;
use crate::spoke_discovery::extract_binary_xor_equations;
use std::collections::{BTreeMap,BTreeSet,VecDeque};

pub type Compression=(Option<(i32,i32,u32)>,Vec<(i32,i32)>,Vec<(i32,u32)>,
    Vec<(i32,Vec<(i32,u32)>)>,usize,Vec<(i32,i32,u32)>);

pub fn compress(source:&[Vec<i32>])->Result<Compression,String> {
    let equations=extract_binary_xor_equations(source)?;
    let mut adj=BTreeMap::<i32,Vec<(i32,u32)>>::new();
    for &(u,v,rhs) in &equations {
        adj.entry(u).or_default().push((v,rhs));
        adj.entry(v).or_default().push((u,rhs));
    }
    for neighbors in adj.values_mut() {neighbors.sort_unstable();}
    let mut roots=BTreeMap::<i32,i32>::new();
    let mut offsets=BTreeMap::<i32,u32>::new();
    let mut paths=BTreeMap::<i32,Vec<(i32,u32)>>::new();
    for &start in adj.keys() {
        if roots.contains_key(&start) {continue;}
        roots.insert(start,start);
        offsets.insert(start,0);
        paths.insert(start,vec![]);
        let mut queue=VecDeque::from([start]);
        while let Some(u)=queue.pop_front() {
            for &(v,rhs) in &adj[&u] {
                let proposal=offsets[&u]^rhs;
                if let Some(&vroot)=roots.get(&v) {
                    if vroot!=start || offsets[&v]!=proposal {
                        return Ok((Some((u,v,rhs)),vec![],vec![],vec![],0,equations));
                    }
                } else {
                    roots.insert(v,start);
                    offsets.insert(v,proposal);
                    let mut path=paths[&u].clone();
                    path.push((v,rhs));
                    paths.insert(v,path);
                    queue.push_back(v);
                }
            }
        }
    }
    let component_count=roots.values().copied().collect::<BTreeSet<_>>().len();
    Ok((None,roots.into_iter().collect(),offsets.into_iter().collect(),
        paths.into_iter().collect(),component_count,equations))
}

pub fn reconstruct(roots:&[(i32,i32)],offsets:&[(i32,u32)],
    root_values:&[(i32,u32)])->Result<Vec<(i32,u32)>,String> {
    let values=root_values.iter().copied().collect::<BTreeMap<_,_>>();
    let offset_map=offsets.iter().copied().collect::<BTreeMap<_,_>>();
    let mut out=Vec::new();
    for &(v,root) in roots {
        let value=*values.get(&root).ok_or("missing root assignment")?;
        if value>1 {return Err("invalid root Boolean value".into());}
        out.push((v,value^offset_map.get(&v).copied().unwrap_or(0)));
    }
    Ok(out)
}

pub fn rewrite(source:&[Vec<i32>],roots:&[(i32,i32)],offsets:&[(i32,u32)])
    ->Result<Vec<Vec<i32>>,String> {
    let mapping=roots.iter().copied().collect::<BTreeMap<_,_>>();
    let shifts=offsets.iter().copied().collect::<BTreeMap<_,_>>();
    let formula=CanonicalCnf::from_signed(source)?;
    let mut rows=Vec::new();
    for clause in &formula.clauses {
        let mut row=Vec::new();
        for &lit in clause {
            let var=lit.unsigned_abs() as i32;
            let root=*mapping.get(&var).unwrap_or(&var);
            let flip=*shifts.get(&var).unwrap_or(&0)!=0;
            row.push(if (lit>0)!=flip {root} else {-root});
        }
        rows.push(row);
    }
    Ok(CanonicalCnf::from_signed(&rows)?.clauses)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn conflict_reconstruct_and_rewrite() {
        let source=vec![vec![-1,2],vec![1,-2],vec![-2,-3],vec![2,3]];
        let (bad,roots,offsets,_,count,eqs)=compress(&source).unwrap();
        assert!(bad.is_none());
        assert_eq!(count,1);
        assert_eq!(eqs.len(),2);
        assert_eq!(reconstruct(&roots,&offsets,&[(1,0)]).unwrap(),
            vec![(1,0),(2,0),(3,1)]);
        assert!(rewrite(&source,&roots,&offsets).unwrap().is_empty());
    }
}
