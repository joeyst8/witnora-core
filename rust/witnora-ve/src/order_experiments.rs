//! R-038: exact experimental graph fill orders and independent width replay.
//! This is heuristic GRAPH elimination, not tensor contraction or a SAT proof.

use std::collections::BTreeSet;

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct OrderStats {
    pub induced_width: usize,
    pub added_fill_edges: usize,
    pub order: Vec<i32>,
}

fn build_graph(scopes: &[Vec<i32>], nvars: i32, invalid: &str)
    -> Result<Vec<BTreeSet<i32>>,String> {
    if nvars < 0 || nvars > 10000 {
        return Err("native factor-order variable universe out of bounds".into());
    }
    let mut graph = vec![BTreeSet::<i32>::new(); nvars as usize + 1];
    for raw in scopes {
        let scope = raw.iter().copied().collect::<BTreeSet<_>>();
        if scope.iter().any(|&v| v < 1 || v > nvars) {
            return Err(invalid.into());
        }
        for &v in &scope {
            for &u in &scope {
                if v != u { graph[v as usize].insert(u); }
            }
        }
    }
    Ok(graph)
}

fn fill_missing(graph: &[BTreeSet<i32>], neighbors: &[i32]) -> usize {
    let mut count=0usize;
    for i in 0..neighbors.len() {
        for j in i+1..neighbors.len() {
            if !graph[neighbors[i] as usize].contains(&neighbors[j]) {
                count+=1;
            }
        }
    }
    count
}

pub fn elimination_order(
    scopes: &[Vec<i32>], nvars: i32, nsource: i32,
    mode: &str, beam: i32,
) -> Result<OrderStats,String> {
    if nvars < 0 || nsource < 0 || nsource > nvars {
        return Err("invalid source/total variable counts".into());
    }
    if !matches!(mode, "min_degree" | "source_first" | "aux_first" | "beam_fill") {
        return Err("unknown order mode".into());
    }
    if beam < 1 { return Err("beam must be positive".into()); }
    let mut graph = build_graph(
        scopes,nvars,"factor variable outside declared domain")?;
    let mut active = (1..=nvars).collect::<BTreeSet<_>>();
    let mut order=Vec::new();
    let mut width=0usize;
    let mut added=0usize;
    while !active.is_empty() {
        let mut ranked = active.iter().map(|&v| {
            let neighbors = graph[v as usize].intersection(&active)
                .copied().collect::<Vec<_>>();
            (v,neighbors)
        }).collect::<Vec<_>>();
        ranked.sort_by_key(|(v,ns)| (ns.len(),*v));
        let chosen = match mode {
            "source_first" => ranked.iter().min_by_key(|(v,ns)|
                (*v > nsource,ns.len(),*v)).unwrap().0,
            "aux_first" => ranked.iter().min_by_key(|(v,ns)|
                (*v <= nsource,ns.len(),*v)).unwrap().0,
            "beam_fill" => ranked.iter().take(beam as usize).min_by_key(
                |(v,ns)| (fill_missing(&graph,ns),ns.len(),*v))
                .unwrap().0,
            _ => ranked[0].0,
        };
        let neighbors = ranked.iter().find(|(v,_)| *v==chosen)
            .unwrap().1.clone();
        width=width.max(neighbors.len());
        added+=fill_missing(&graph,&neighbors);
        for &u in &neighbors {
            for &v in &neighbors {
                if u!=v { graph[u as usize].insert(v); }
            }
            graph[u as usize].remove(&chosen);
        }
        active.remove(&chosen);
        order.push(chosen);
    }
    Ok(OrderStats{induced_width:width,added_fill_edges:added,order})
}

pub fn replay_elimination_width(
    scopes: &[Vec<i32>], nvars: i32, order: &[i32],
) -> Result<usize,String> {
    if nvars < 0 || order.len()!=nvars as usize
        || order.iter().copied().collect::<BTreeSet<_>>()
           !=(1..=nvars).collect::<BTreeSet<_>>() {
        return Err("order must be a permutation of all variable IDs".into());
    }
    let mut graph=build_graph(scopes,nvars,"invalid factor scope")?;
    let mut width=0usize;
    for &v in order {
        let neighbors=graph[v as usize].iter().copied()
            .collect::<Vec<_>>();
        width=width.max(neighbors.len());
        for &u in &neighbors {
            for &z in &neighbors {
                if u!=z { graph[u as usize].insert(z); }
            }
            graph[u as usize].remove(&v);
        }
        graph[v as usize].clear();
    }
    Ok(width)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn source_aux_minfill_and_empty_scope() {
        let scopes=vec![vec![1,2],vec![2,3],vec![3,4],vec![1,4]];
        for mode in ["min_degree","source_first","aux_first","beam_fill"] {
            let r=elimination_order(&scopes,4,2,mode,3).unwrap();
            assert_eq!(r.order.len(),4);
            assert_eq!(replay_elimination_width(&scopes,4,&r.order).unwrap(),
                r.induced_width);
        }
        assert_eq!(elimination_order(&[],0,0,"min_degree",1).unwrap().order,
                   Vec::<i32>::new());
    }
    #[test]
    fn domain_and_order_attack_rejection() {
        assert_eq!(elimination_order(&[vec![7]],3,2,"beam_fill",2).unwrap_err(),
                   "factor variable outside declared domain");
        assert_eq!(replay_elimination_width(&[],3,&[1,1,3]).unwrap_err(),
                   "order must be a permutation of all variable IDs");
    }
}
