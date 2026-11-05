//! R-072: deterministic out-of-distribution SAT source construction.
//! Source labels are experimental fixtures, not solver or hardness claims.
use crate::cnf::CanonicalCnf;
use std::collections::BTreeSet;

fn canonical(rows:Vec<Vec<i32>>)->Result<Vec<Vec<i32>>,String> {
    Ok(CanonicalCnf::from_signed(&rows)?.clauses)
}

fn require_capacity(n:i32,k:i32)->Result<(),String> {
    if n<1 || k<1 || (n as i64)*(k as i64)>i32::MAX as i64 {
        return Err("positive bounded source dimensions required".into());
    }
    Ok(())
}

pub fn pigeonhole(pigeons:i32,holes:i32)->Result<Vec<Vec<i32>>,String> {
    require_capacity(pigeons,holes)?;
    let v=|p:i32,h:i32|1+p*holes+h;
    let mut rows=Vec::new();
    for p in 0..pigeons { rows.push((0..holes).map(|h|v(p,h)).collect()); }
    for h in 0..holes {
        for p in 0..pigeons { for q in p+1..pigeons {
            rows.push(vec![-v(p,h),-v(q,h)]);
        }}
    }
    canonical(rows)
}

pub fn graph_coloring(vertices:i32,edges:&[(i32,i32)],colors:i32)
    ->Result<Vec<Vec<i32>>,String> {
    require_capacity(vertices,colors)?;
    let v=|node:i32,color:i32|(node-1)*colors+color;
    let mut rows=Vec::new();
    for node in 1..=vertices {
        rows.push((1..=colors).map(|c|v(node,c)).collect());
        for c in 1..=colors { for d in c+1..=colors {
            rows.push(vec![-v(node,c),-v(node,d)]);
        }}
    }
    for &(u,w) in edges {
        if u<1 || u>vertices || w<1 || w>vertices || u==w {
            return Err("invalid graph edge".into());
        }
        for c in 1..=colors { rows.push(vec![-v(u,c),-v(w,c)]); }
    }
    canonical(rows)
}

fn xor_clauses(vars:&[i32],rhs:u32,rows:&mut Vec<Vec<i32>>) {
    for mask in 0u32..(1u32<<vars.len()) {
        if mask.count_ones()%2==rhs {continue;}
        rows.push(vars.iter().enumerate().map(|(i,&v)|
            if (mask>>(vars.len()-1-i))&1==1 {-v} else {v}).collect());
    }
}

pub fn tseitin_complete_graph(vertices:i32,contradictory:bool)
    ->Result<Vec<Vec<i32>>,String> {
    if !(3..=7).contains(&vertices) {
        return Err("bounded complete-graph XOR family requires 3..7 vertices".into());
    }
    let mut edges=Vec::new();
    for u in 1..=vertices {for v in u+1..=vertices {edges.push((u,v));}}
    let mut rows=Vec::new();
    for vertex in 1..=vertices {
        let incident=edges.iter().enumerate().filter_map(|(i,&(u,v))|
            if u==vertex || v==vertex {Some((i+1) as i32)} else {None})
            .collect::<Vec<_>>();
        xor_clauses(&incident,if contradictory && vertex==1 {1} else {0},&mut rows);
    }
    canonical(rows)
}

pub fn n_queens(n:i32)->Result<Vec<Vec<i32>>,String> {
    require_capacity(n,n)?;
    let v=|r:i32,c:i32|1+r*n+c;
    let mut rows=Vec::new();
    for r in 0..n {
        rows.push((0..n).map(|c|v(r,c)).collect());
        for c in 0..n {for d in c+1..n {rows.push(vec![-v(r,c),-v(r,d)]);}}
    }
    for c in 0..n {for r in 0..n {for s in r+1..n {
        rows.push(vec![-v(r,c),-v(s,c)]);
    }}}
    for r in 0..n {for c in 0..n {for s in r..n {
        for d in 0..n {
            if (s>r || d>c) && (r-s).abs()==(c-d).abs() {
                rows.push(vec![-v(r,c),-v(s,d)]);
            }
        }
    }}}
    canonical(rows)
}

/// The exact Python MT19937 sample stream is frozen at the adapter boundary.
pub fn planted_from_samples(n:i32,witness:&[bool],sampled:&[Vec<i32>])
    ->Result<Vec<Vec<i32>>,String> {
    if n<3 || witness.len()!=n as usize {return Err("invalid planted CNF dimensions".into());}
    for row in sampled {
        if row.len()!=3 || row.iter().any(|&lit|lit==0 || lit==i32::MIN || lit.unsigned_abs()>n as u32) ||
            row.iter().map(|v|v.unsigned_abs()).collect::<BTreeSet<_>>().len()!=3 ||
            !row.iter().any(|&lit|witness[lit.unsigned_abs() as usize-1]==(lit>0)) {
            return Err("invalid planted signed sample".into());
        }
    }
    canonical(sampled.to_vec())
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn known_sizes_and_invalid_inputs() {
        assert_eq!(pigeonhole(3,2).unwrap().len(),9);
        assert_eq!(graph_coloring(2,&[(1,2)],2).unwrap().len(),6);
        assert_eq!(tseitin_complete_graph(4,false).unwrap().len(),16);
        assert_eq!(n_queens(3).unwrap().len(),31);
        assert!(pigeonhole(0,2).is_err());
        assert!(graph_coloring(2,&[(1,1)],2).is_err());
        assert!(tseitin_complete_graph(8,false).is_err());
        assert!(planted_from_samples(3,&[true,true,true],&[vec![-1,-2,-3]]).is_err());
    }
}
