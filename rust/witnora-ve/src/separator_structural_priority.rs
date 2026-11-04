//! R-050: native iterative graph articulation discovery for TC-063 hints.
//! This generates structural candidates, not proof acceptance. Exhaustive
//! G14/SAT fallback and Lean gates must remain unchanged.

use std::collections::{BTreeMap,BTreeSet};

fn normalize_graph(
    graph:&[(i32,Vec<i32>)],
)->Result<BTreeMap<i32,Vec<i32>>,String> {
    let mut result=BTreeMap::<i32,Vec<i32>>::new();
    for (v,neighbors) in graph {
        if result.contains_key(v) {
            return Err("duplicate graph vertex".into());
        }
        let adjacency=neighbors.iter().copied()
            .collect::<BTreeSet<_>>().into_iter().collect();
        result.insert(*v,adjacency);
    }
    for (&v,neighbors) in &result {
        for u in neighbors {
            if *u==v || !result.get(u).is_some_and(|rows|
                rows.binary_search(&v).is_ok()
            ) {
                return Err("graph must be symmetric with known distinct vertices".into());
            }
        }
    }
    Ok(result)
}

pub fn articulation_vertices(
    input:&[(i32,Vec<i32>)],
)->Result<Vec<i32>,String> {
    let adjacency=normalize_graph(input)?;
    let mut discovery=BTreeMap::<i32,usize>::new();
    let mut low=BTreeMap::<i32,usize>::new();
    let mut parent=BTreeMap::<i32,Option<i32>>::new();
    let mut children=BTreeMap::<i32,usize>::new();
    let mut cuts=BTreeSet::<i32>::new();
    let mut clock=0usize;
    for &root in adjacency.keys() {
        if discovery.contains_key(&root){continue;}
        parent.insert(root,None);
        children.insert(root,0);
        discovery.insert(root,clock);
        low.insert(root,clock);
        clock+=1;
        let mut stack=vec![(root,0usize)];
        while let Some((vertex,next))=stack.last_mut() {
            let v=*vertex;
            if *next==adjacency[&v].len() {
                stack.pop();
                match parent[&v] {
                    None=>{
                        if children[&v]>1 {cuts.insert(v);}
                    },
                    Some(ancestor)=>{
                        let lv=low[&v];
                        let la=low[&ancestor];
                        low.insert(ancestor,la.min(lv));
                        if parent[&ancestor].is_some()
                            && lv>=discovery[&ancestor]
                        {
                            cuts.insert(ancestor);
                        }
                    },
                }
                continue;
            }
            let neighbor=adjacency[&v][*next];
            *next+=1;
            if parent[&v]==Some(neighbor) {continue;}
            if let Some(&seen)=discovery.get(&neighbor) {
                let value=low[&v].min(seen);
                low.insert(v,value);
                continue;
            }
            parent.insert(neighbor,Some(v));
            children.insert(neighbor,0);
            *children.get_mut(&v).unwrap()+=1;
            discovery.insert(neighbor,clock);
            low.insert(neighbor,clock);
            clock+=1;
            stack.push((neighbor,0));
        }
    }
    Ok(cuts.into_iter().collect())
}

pub fn prioritized_singletons(
    input:&[(i32,Vec<i32>)],
)->Result<Vec<i32>,String> {
    let adjacency=normalize_graph(input)?;
    let mut cuts=articulation_vertices(input)?;
    let membership=cuts.iter().copied().collect::<BTreeSet<_>>();
    cuts.sort_by(|a,b|
        adjacency[b].len().cmp(&adjacency[a].len()).then_with(||a.cmp(b))
    );
    cuts.extend(adjacency.keys().filter(|v|!membership.contains(v)).copied());
    Ok(cuts)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn disconnected_path_and_cycle_exact_order() {
        let graph=vec![
            (1,vec![2]),(2,vec![1,3]),(3,vec![2]),
            (4,vec![5,6]),(5,vec![4,6]),(6,vec![4,5]),
            (7,vec![]),
        ];
        assert_eq!(articulation_vertices(&graph).unwrap(),vec![2]);
        assert_eq!(
            prioritized_singletons(&graph).unwrap(),
            vec![2,1,3,4,5,6,7]
        );
        assert!(articulation_vertices(&[(1,vec![2])]).is_err());
    }
}
