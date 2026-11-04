//! R-066: bounded, independent support-hypergraph separator oracle.
//! Enumerates cuts; no claim of efficient general graph decomposition.
use std::collections::{BTreeSet, VecDeque};

fn component_count(supports: &[BTreeSet<u32>], deleted: &BTreeSet<u32>) -> usize {
    let mut unseen: BTreeSet<usize> = (0..supports.len()).collect();
    let mut count = 0;
    while let Some(&start) = unseen.iter().next() {
        unseen.remove(&start);
        count += 1;
        let mut queue = VecDeque::from([start]);
        while let Some(i) = queue.pop_front() {
            let neighbors: Vec<usize> = unseen.iter().copied().filter(|&j| {
                supports[i].iter().any(|v|!deleted.contains(v) && supports[j].contains(v))
            }).collect();
            for j in neighbors { unseen.remove(&j); queue.push_back(j); }
        }
    }
    count
}

fn first_cut(
    supports: &[BTreeSet<u32>], shared: &[u32], needed: usize,
    start: usize, selected: &mut Vec<u32>, baseline: usize,
) -> bool {
    if selected.len()==needed {
        return component_count(supports, &selected.iter().copied().collect())>baseline;
    }
    for i in start..shared.len() {
        selected.push(shared[i]);
        if first_cut(supports,shared,needed,i+1,selected,baseline) { return true; }
        selected.pop();
    }
    false
}

pub fn independent_parity_cut_width(
    supports: &[Vec<u32>], limit: usize,
) -> Result<Option<usize>,String> {
    if supports.len()>64 || limit>4 {return Err("finite cut budget exceeded".into());}
    let sets: Vec<BTreeSet<u32>> = supports.iter().map(|s|s.iter().copied().collect()).collect();
    let mut frequency=std::collections::BTreeMap::<u32,usize>::new();
    for row in &sets { for &v in row { *frequency.entry(v).or_default()+=1; } }
    let shared:Vec<u32>=frequency.iter().filter_map(|(&v,&count)|
        if count>=2 {Some(v)} else {None}).collect();
    if shared.len()>16 {return Err("shared variable budget exceeded".into());}
    let baseline=component_count(&sets,&BTreeSet::new());
    for size in 1..=limit.min(shared.len()) {
        if first_cut(&sets,&shared,size,0,&mut vec![],baseline) {return Ok(Some(size));}
    }
    Ok(None)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn simple_cut_and_no_cut() {
        assert_eq!(independent_parity_cut_width(&[vec![1,2],vec![2,3]],3),Ok(Some(1)));
        assert_eq!(independent_parity_cut_width(&[vec![1],vec![3]],3),Ok(None));
        assert_eq!(independent_parity_cut_width(&[],3),Ok(None));
    }
}
