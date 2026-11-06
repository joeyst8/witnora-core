//! W026: cost-accounted source-only 3-XOR recovery in controlled mixed CNF.
//! Not a CDCL runtime claim. Ordinary distractors have unique variable supports.
use serde_json::{json,Value};
use std::collections::{BTreeMap,BTreeSet};

const TRIPLES:[[usize;3];5]=[[1,2,3],[1,4,5],[2,4,6],[3,5,6],[7,8,9]];
const SAT:[bool;5]=[false,false,false,false,true];
const UNSAT:[bool;5]=[false,false,false,true,false];
const NOISE:[usize;6]=[0,32,256,1024,4096,8192];
type Clause=[i32;3];

fn next(s:&mut u32)->u32 {
    *s ^= *s<<13;
    *s ^= *s>>17;
    *s ^= *s<<5;
    *s
}

fn encode(rhs:[bool;5])->Vec<Clause> {
    let mut out=Vec::new();
    for (vars,b) in TRIPLES.iter().zip(rhs) {
        for pattern in 0u8..8u8 {
            if pattern.count_ones()%2!=(b as u32) {
                out.push(vars.map(|v| v as i32));
                let last=out.last_mut().unwrap();
                for j in 0..3 {
                    if (pattern>>j)&1==1 {last[j] = -last[j];}
                }
            }
        }
    }
    assert_eq!(out.len(),20);
    out
}

fn planted(lit:i32)->bool {
    let value=lit.unsigned_abs()==7;
    value == (lit>0)
}
fn seeded_noise(d:usize,r:usize)->(u32,Vec<Clause>) {
    let seed=0x0260_0260u32
        ^ ((r as u32+1).wrapping_mul(0x9E37_79B9))
        ^ ((d as u32+1).wrapping_mul(0x85EB_CA6B));
    let mut state=seed;
    let mut supports:BTreeSet<[usize;3]>=TRIPLES.into_iter().collect();
    let mut decoys=Vec::with_capacity(d);
    while decoys.len()<d {
        let mut key=[0usize;3];
        for v in &mut key {
            *v=next(&mut state) as usize%64+1;
        }
        key.sort_unstable();
        if key[0]==key[1]||key[1]==key[2]||!supports.insert(key) {continue;}
        let mut clause=[0i32;3];
        for i in 0..3 {
            let negative=next(&mut state)&1==1;
            clause[i]=if negative{-(key[i] as i32)}else{key[i] as i32};
        }
        if !clause.iter().any(|&lit|planted(lit)) {
            clause[0] = -clause[0];
        }
        assert!(clause.iter().any(|&lit|planted(lit)));
        decoys.push(clause);
    }
    (seed,decoys)
}

fn signature(clauses:&[Clause])->u64 {
    let mut h=0xcbf29ce484222325u64;
    for c in clauses {
        for &lit in c {
            h ^= (lit+64) as u64;
            h=h.wrapping_mul(0x100000001b3u64);
        }
    }
    h
}

fn recover(clauses:&[Clause])->(usize,Vec<(u64,bool)>) {
    let mut groups:BTreeMap<[usize;3],Vec<[i8;3]>>=BTreeMap::new();
    for clause in clauses {
        let mut terms:Vec<(usize,i8)>=clause.iter().map(|&l|
            (l.unsigned_abs() as usize,if l>0 {1} else {-1})).collect();
        terms.sort_unstable_by_key(|t|t.0);
        let key=[terms[0].0,terms[1].0,terms[2].0];
        assert!(key[0]<key[1] && key[1]<key[2]);
        groups.entry(key).or_default().push([terms[0].1,terms[1].1,terms[2].1]);
    }
    let n_supports=groups.len();
    let mut equations=Vec::new();
    for (key,signs) in groups {
        if signs.len()!=4 {continue;}
        let unique:BTreeSet<[i8;3]>=signs.iter().copied().collect();
        if unique.len()!=4 {continue;}
        let product=signs[0][0]*signs[0][1]*signs[0][2];
        if !signs.iter().all(|s|s[0]*s[1]*s[2]==product) {continue;}
        let mask=key.iter().fold(0u64,|m,&v|m^(1u64<<(v-1)));
        equations.push((mask,product>0));
    }
    (n_supports,equations)
}

fn contradiction(rows:&[(u64,bool)])->bool {
    let mut basis:[Option<(u64,bool)>;64]=[None;64];
    for &(source_mask,source_rhs) in rows {
        let (mut mask,mut rhs)=(source_mask,source_rhs);
        for p in (0..64).rev() {
            if (mask>>p)&1==0 {continue;}
            if let Some((m,b))=basis[p] {
                mask^=m;
                rhs^=b;
            } else {
                basis[p]=Some((mask,rhs));
                break;
            }
        }
        if mask==0&&rhs {return true;}
    }
    false
}

fn one(d:usize,r:usize)->Value {
    let (seed,noise)=seeded_noise(d,r);
    let mut sat=encode(SAT);
    let mut unsat=encode(UNSAT);
    sat.extend(noise.iter().copied());
    unsat.extend(noise.iter().copied());
    assert!(sat.iter().all(|c|c.iter().any(|&l|planted(l))));
    let (sat_groups,sat_eqs)=recover(&sat);
    let (unsat_groups,unsat_eqs)=recover(&unsat);
    assert_eq!(sat_groups,d+5);
    assert_eq!(unsat_groups,d+5);
    assert_eq!(sat_eqs.len(),5);
    assert_eq!(unsat_eqs.len(),5);
    assert!(!contradiction(&sat_eqs));
    assert!(contradiction(&unsat_eqs));
    let m=d+20;
    json!({
        "noise":d,"replicate":r,"seed":seed,
        "literal_clauses_each":m,
        "supports_indexed":sat_groups,
        "recovered_exact_xor_blocks_sat":sat_eqs.len(),
        "recovered_exact_xor_blocks_unsat":unsat_eqs.len(),
        "sat_planted_witness_valid":true,
        "unsat_xor_contradiction":true,
        "sat_xor_consistent":true,
        "noise_fingerprint_fnv64":signature(&noise).to_string(),
        "first_four_noise_clauses":noise.iter().take(4).collect::<Vec<_>>(),
        "one_pass_clause_visits":m,
        "rescan_clause_visits_q1":m,
        "rescan_clause_visits_q2":m*2,
        "rescan_clause_visits_q8":m*8,
        "rescan_clause_visits_q32":m*32,
        "cached_initial_clause_visits":m
    })
}

fn report()->Value {
    let cases=NOISE.into_iter().flat_map(|d|(0..16).map(move|r|one(d,r))).collect::<Vec<_>>();
    assert_eq!(cases.len(),96);
    json!({
        "study":"W-CROSSDOMAIN-026",
        "protocol":"docs/W_CROSSDOMAIN_026_MIXED_CNF_XOR_RECOVERY_PROTOCOL.md",
        "variable_domain":64,
        "noise_sizes":NOISE,"replicates_per_noise":16,
        "case_count":96,
        "claim_boundary":"reliable recognition in synthetic unique-support noise; no net solver runtime or P vs NP claim",
        "cases":cases
    })
}
fn main() {
    let args:Vec<String>=std::env::args().skip(1).collect();
    if !args.is_empty() && !(args.len()==1 && args[0]=="--json") {
        eprintln!("usage: witnora_mixed_xor_recovery [--json]");
        std::process::exit(2);
    }
    println!("{}",serde_json::to_string_pretty(&report()).unwrap());
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn all_96_source_extractions() {
        let r=report();
        assert_eq!(r["case_count"],96);
    }
    #[test]
    fn core_parity_proof() {
        assert!(!contradiction(&recover(&encode(SAT)).1));
        assert!(contradiction(&recover(&encode(UNSAT)).1));
    }
}
