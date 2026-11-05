//! W025: exact XOR-SAT / Ising gauge-holonomy bridge.
//! All 64 pairs and 16 transformations are symmetry controls, not independent draws.
use serde_json::{json, Value};
use std::collections::BTreeMap;

const TRIPLES: [[usize; 3]; 5] =
    [[1,2,3], [1,4,5], [2,4,6], [3,5,6], [7,8,9]];
const SAT: [bool; 5] = [false,false,false,false,true];
const UNSAT: [bool; 5] = [false,false,false,true,false];
const BETAS: [f64; 6] = [0.0,0.25,0.5,1.0,2.0,4.0];

#[derive(Clone, Copy)]
struct Edge { vars: [usize;3], mask: u16, rhs: bool }

fn xorshift(s: &mut u32) -> u32 {
    *s ^= *s << 13;
    *s ^= *s >> 17;
    *s ^= *s << 5;
    *s
}

fn source(index: usize, rhs: [bool;5]) -> (u32, Vec<Edge>) {
    let seed = 0xD24F_0240u32 ^ ((index as u32 + 1).wrapping_mul(0x9E37_79B9));
    let mut s = seed;
    let mut permutation: Vec<usize> = (1..=9).collect();
    for i in (1..9).rev() {
        let j = xorshift(&mut s) as usize % (i + 1);
        permutation.swap(i,j);
    }
    let edges = TRIPLES.iter().zip(rhs).map(|(triple, b)| {
        let vars = triple.map(|v| permutation[v-1]);
        let mask = vars.iter().fold(0u16, |m, &v| m ^ (1u16 << (v-1)));
        Edge { vars, mask, rhs:b }
    }).collect();
    (seed, edges)
}

fn gauge_mask(i:usize, j:usize) -> u16 {
    (((i as u32 + 1).wrapping_mul(0x9E37_79B9)
      ^ (j as u32 + 1).wrapping_mul(0x85EB_CA6B)
      ^ 0x0250_2425) & 0x1FF) as u16
}

fn gauge(edges:&[Edge], flips:u16) -> Vec<Edge> {
    edges.iter().map(|e| {
        let mut out=*e;
        out.rhs ^= (e.mask & flips).count_ones() % 2 != 0;
        out
    }).collect()
}

fn cycles(edges:&[Edge]) -> Vec<u8> {
    (1u8..32u8).filter(|&subset| {
        edges.iter().enumerate()
            .filter(|(j,_)| subset & (1u8 << *j) != 0)
            .fold(0u16, |acc,(_,e)| acc ^ e.mask) == 0
    }).collect()
}

fn holonomy(edges:&[Edge], cycle:u8) -> i32 {
    let odd=edges.iter().enumerate()
        .filter(|(j,_)| cycle & (1u8 << *j) != 0)
        .fold(false, |acc,(_,e)| acc ^ e.rhs);
    if odd {-1} else {1}
}

fn energies(edges:&[Edge]) -> BTreeMap<i32,usize> {
    let mut hist=BTreeMap::new();
    for bits in 0u16..512u16 {
        let violated: i32=edges.iter().map(|e| {
            i32::from(((bits & e.mask).count_ones() % 2 != 0) != e.rhs)
        }).sum();
        let energy=2*violated - edges.len() as i32;
        *hist.entry(energy).or_insert(0)+=1;
    }
    assert_eq!(hist.values().sum::<usize>(),512);
    hist
}

fn exact_partition(hist:&BTreeMap<i32,usize>,beta:f64)->f64 {
    hist.iter().map(|(&energy,&count)| count as f64 * (-beta*energy as f64).exp()).sum()
}

fn analytic_partition(h:i32,beta:f64)->f64 {
    512.0*beta.cosh().powi(5)*(1.0+h as f64*beta.tanh().powi(4))
}

fn check_partitions(hist:&BTreeMap<i32,usize>,h:i32)->Vec<f64> {
    BETAS.iter().map(|&beta|{
        let computed=exact_partition(hist,beta);
        let formula=analytic_partition(h,beta);
        assert!((computed/formula-1.0).abs()<1e-10,
            "partition mismatch: beta={beta} holonomy={h} computed={computed} formula={formula}");
        computed
    }).collect()
}

fn run_case(index:usize)->Value {
    let (seed,sat)=source(index,SAT);
    let (_,unsat)=source(index,UNSAT);
    let dependencies=cycles(&sat);
    assert_eq!(dependencies,cycles(&unsat));
    assert_eq!(dependencies.len(),1);
    let cycle=dependencies[0];
    assert_eq!(cycle.count_ones(),4);
    let hs=holonomy(&sat,cycle);
    let hu=holonomy(&unsat,cycle);
    assert_eq!((hs,hu),(1,-1));
    let sh=energies(&sat);
    let uh=energies(&unsat);
    assert_eq!(sh.first_key_value(),Some((&-5,&32usize)));
    assert_eq!(uh.first_key_value(),Some((&-3,&128usize)));
    let sz=check_partitions(&sh,hs);
    let uz=check_partitions(&uh,hu);
    let mut masks=Vec::with_capacity(16);
    for j in 0..16 {
        let mask=gauge_mask(index,j);
        masks.push(mask);
        for (original,h,expected_hist,expected_z) in [
            (&sat,hs,&sh,&sz),(&unsat,hu,&uh,&uz)
        ] {
            let transformed=gauge(original,mask);
            assert_eq!(cycles(&transformed),vec![cycle]);
            assert_eq!(holonomy(&transformed,cycle),h);
            let transformed_hist=energies(&transformed);
            assert_eq!(&transformed_hist,expected_hist);
            let transformed_z=check_partitions(&transformed_hist,h);
            for (a,b) in transformed_z.iter().zip(expected_z) {
                assert!((a/b-1.0).abs()<1e-12);
            }
        }
    }
    json!({
        "index":index,"seed":seed,
        "source_triples":sat.iter().map(|e|e.vars).collect::<Vec<_>>(),
        "cycle_source_indices_zero_based":(0..5usize)
            .filter(|j|cycle & (1u8 << *j)!=0).collect::<Vec<_>>(),
        "sat_holonomy":hs,"unsat_holonomy":hu,
        "sat_energy_histogram":sh,"unsat_energy_histogram":uh,
        "sat_partitions":sz,"unsat_partitions":uz,
        "gauge_masks":masks,
        "all_gauges_exactly_energy_invariant":true,
        "all_partitions_match_analytic":true
    })
}

fn report()->Value {
    let cases:Vec<Value>=(0..64).map(run_case).collect();
    json!({
        "study":"W-CROSSDOMAIN-025",
        "protocol":"docs/W_CROSSDOMAIN_025_GAUGE_HOLONOMY_PROTOCOL.md",
        "claim_scope":"known p-spin/XOR identity; one pair, 64 relabelings, 16 gauge interventions",
        "case_count":64,"gauge_interventions_per_case":16,
        "inverse_temperatures_beta":BETAS,"claims_p_equals_np":false,
        "cases":cases
    })
}

fn main() {
    let args:Vec<String>=std::env::args().skip(1).collect();
    if !args.is_empty() && !(args.len()==1 && args[0]=="--json") {
        eprintln!("usage: witnora_spin_holonomy [--json]");
        std::process::exit(2);
    }
    println!("{}",serde_json::to_string_pretty(&report()).unwrap());
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn exact_gauge_and_partition_invariance() {
        let r=report();
        assert_eq!(r["case_count"],64);
        assert_eq!(r["cases"].as_array().unwrap().len(),64);
    }
}