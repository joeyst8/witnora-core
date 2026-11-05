//! R-086: exact bounded primal minimum vertex cut by split-vertex max flow.
//! Source validation and conditional independence certificate remain independent.
use num_bigint::BigUint;
use num_traits::{One,Zero};
use std::collections::{BTreeMap,BTreeSet,VecDeque};
use std::str::FromStr;

fn scope_vertices(z:&str,o:&str)->Result<Vec<usize>,String>{
    let z=BigUint::from_str(z).map_err(|_|"invalid normalized zero mask")?;
    let o=BigUint::from_str(o).map_err(|_|"invalid normalized one mask")?;
    let mask=z|o;
    let mut vertices=Vec::new();
    for (w,word) in mask.iter_u32_digits().enumerate(){
        for bit in 0..32{if (word>>bit)&1==1{vertices.push(w*32+bit+1);}}
    }
    Ok(vertices)
}

fn arc(residual:&mut [Vec<(usize,usize)>],u:usize,v:usize,capacity:usize){
    if let Some((_,old))=residual[u].iter_mut().find(|(target,_)|*target==v){
        *old+=capacity;
    }else{residual[u].push((v,capacity));}
    if !residual[v].iter().any(|(target,_)|*target==u){residual[v].push((u,0));}
}
fn adjust(residual:&mut [Vec<(usize,usize)>],u:usize,v:usize,amount:usize,add:bool){
    let (_,capacity)=residual[u].iter_mut().find(|(target,_)|*target==v).unwrap();
    if add{*capacity+=amount;}else{*capacity-=amount;}
}

pub fn discover(normalized:&[(String,String)],boundary:&[usize],left:&[usize],right:&[usize],
    max_separator:usize,max_edges:usize)
    ->Result<Option<(Vec<usize>,usize,usize,usize)>,String>{
    let n=boundary.len();
    let pos:BTreeMap<usize,usize>=boundary.iter().enumerate().map(|(i,&v)|(v,i)).collect();
    if pos.len()!=n{return Err("duplicate boundary variable".into());}
    let left:BTreeSet<usize>=left.iter().copied().collect();
    let right:BTreeSet<usize>=right.iter().copied().collect();
    if left.is_empty()||right.is_empty() || !left.is_disjoint(&right)
        || left.iter().chain(right.iter()).any(|v|!pos.contains_key(v)){
        return Err("invalid group membership".into());
    }
    let mut edges=BTreeSet::new();
    let mut graph:BTreeMap<usize,BTreeSet<usize>>=boundary.iter()
        .map(|&v|(v,BTreeSet::new())).collect();
    for (z,o) in normalized{
        let vertices=scope_vertices(z,o)?;
        for (i,&u) in vertices.iter().enumerate(){
            for &v in &vertices[i+1..]{
                if u==v{continue;}
                let edge=(u.min(v),u.max(v));
                if edges.insert(edge){
                    if edges.len()>max_edges{return Ok(None);}
                    graph.get_mut(&u).ok_or("source variable outside boundary")?.insert(v);
                    graph.get_mut(&v).ok_or("source variable outside boundary")?.insert(u);
                }
            }
        }
    }
    let src=2*n;
    let dst=2*n+1;
    let infinite=n.max(max_separator)+1;
    let mut residual=vec![Vec::<(usize,usize)>::new();2*n+2];
    for &v in boundary{
        let i=pos[&v];
        arc(&mut residual,2*i,2*i+1,if left.contains(&v)||right.contains(&v){infinite}else{1});
    }
    for &(u,v) in &edges{
        let (a,b)=(pos[&u],pos[&v]);
        arc(&mut residual,2*a+1,2*b,infinite);
        arc(&mut residual,2*b+1,2*a,infinite);
    }
    for &v in &left{arc(&mut residual,src,2*pos[&v],infinite);}
    for &v in &right{arc(&mut residual,2*pos[&v]+1,dst,infinite);}
    let mut flow=0usize;
    let mut augmentations=0usize;
    let reachable=loop{
        let mut parent=vec![None::<usize>;2*n+2];
        parent[src]=Some(src);
        let mut queue=VecDeque::from([src]);
        while let Some(at)=queue.pop_front(){
            if parent[dst].is_some(){break;}
            for &(other,capacity) in &residual[at]{
                if capacity>0 && parent[other].is_none(){
                    parent[other]=Some(at);
                    queue.push_back(other);
                }
            }
        }
        if parent[dst].is_none(){break parent;}
        let mut increment=infinite;
        let mut at=dst;
        while at!=src{
            let prev=parent[at].unwrap();
            let cap=residual[prev].iter().find(|(target,_)|*target==at).unwrap().1;
            increment=increment.min(cap);
            at=prev;
        }
        at=dst;
        while at!=src{
            let prev=parent[at].unwrap();
            adjust(&mut residual,prev,at,increment,false);
            adjust(&mut residual,at,prev,increment,true);
            at=prev;
        }
        flow+=increment;
        augmentations+=1;
        if flow>max_separator{return Ok(None);}
    };
    let separator:Vec<usize>=boundary.iter().copied().filter(|v|{
        let i=pos[v];
        reachable[2*i].is_some() && reachable[2*i+1].is_none()
    }).collect();
    let mut separator=separator;
    separator.sort_unstable();
    if separator.len()!=flow || separator.iter().any(|v|left.contains(v)||right.contains(v)){
        return Err("minimum vertex cut extraction invariant".into());
    }
    Ok(Some((separator,flow,edges.len(),augmentations)))
}

#[cfg(test)]
mod tests{
 use super::*;
 #[test]fn center_cut(){
  let clauses=vec![("5".into(),"0".into()),("6".into(),"0".into())];
  let cut=discover(&clauses,&[1,2,3],&[1],&[2],1,5).unwrap().unwrap();
  assert_eq!(cut.0,vec![3]);
 }
}
