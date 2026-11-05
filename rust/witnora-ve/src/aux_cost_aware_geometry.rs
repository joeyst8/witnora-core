//! W-CROSSDOMAIN-021: modular prefilter for exact covariance certificates,
//! compared with end-to-end degree-static DPLL and exact-first routing.
//! Descriptive small-instance timing only; no general solver claim.

use crate::aux_hybrid_refutation::{verify_xor,xor_certificate,Equation};
use crate::aux_zero_variance_refutation::{covariance,kernel_certificate,verify};
use serde_json::{json,Value};
use std::time::Instant;

const N:usize=16;
const CASES:usize=12;
const CLAUSES:usize=68;
const STEP:u32=0x9E37_79B9;
const P:u64=65521;

#[derive(Clone,Copy,PartialEq,Eq)]
enum Family {Planted,Boundary,EightCore,PaddedTwoSat,XorCycle}
impl Family {
    fn seed(self)->u32 {
        match self {
            Self::Planted=>0xD21C_0DE1,Self::Boundary=>0xD21C_0DE2,
            Self::EightCore=>0xD21C_0DE3,Self::PaddedTwoSat=>0xD21C_0DE4,
            Self::XorCycle=>0xD21C_0DE5,
        }
    }
    fn name(self)->&'static str {
        match self {
            Self::Planted=>"planted_sat_16_68",Self::Boundary=>"uniform_boundary_16_68",
            Self::EightCore=>"eight_core_unsat_16_68",
            Self::PaddedTwoSat=>"padded_2sat_unsat_16_68",
            Self::XorCycle=>"xor_cycle_unsat_16_68",
        }
    }
}

fn next(state:&mut u32)->u32 {
    *state^=*state<<13;
    *state^=*state>>17;
    *state^=*state<<5;
    *state
}

fn random_clause(state:&mut u32)->Vec<i32> {
    let mut seen=[false;N];
    let mut clause=Vec::new();
    while clause.len()<3 {
        let v=next(state) as usize%N;
        if seen[v] {continue;}
        seen[v]=true;
        let lit=v as i32+1;
        clause.push(if next(state)&1==0 {lit} else {-lit});
    }
    clause
}

fn source(family:Family,index:usize)->Vec<Vec<i32>> {
    let mut state=family.seed() ^ (index as u32+1).wrapping_mul(STEP);
    let mut clauses=Vec::with_capacity(CLAUSES);
    if family==Family::EightCore {
        for bits in 0..8 {
            clauses.push((0..3).map(|j| {
                let lit=j+1;
                if bits&(1<<j)!=0 {-lit} else {lit}
            }).collect());
        }
    }
    if family==Family::PaddedTwoSat {
        for a in 0..=1 {
            for b in 0..=1 {
                let x=if a==0 {1} else {-1};
                let y=if b==0 {2} else {-2};
                let z=3+a*2+b;
                clauses.push(vec![x,y,z]);
                clauses.push(vec![x,y,-z]);
            }
        }
    }
    if family==Family::XorCycle {
        for (vars,desired) in [([1i32,2,3],0u32),([1,4,5],0),
                               ([2,4,6],0),([3,5,6],1)] {
            for bits in 0u32..8 {
                if bits.count_ones()&1==desired {continue;}
                clauses.push(vars.iter().enumerate().map(|(j,&v)| {
                    if bits&(1u32<<j)!=0 {-v} else {v}
                }).collect());
            }
        }
    }
    while clauses.len()<CLAUSES {
        let clause=random_clause(&mut state);
        if family==Family::Planted && clause.iter().all(|&lit|lit>0){continue;}
        clauses.push(clause);
    }
    let mut permutation:[i32;N]=std::array::from_fn(|i|i as i32+1);
    for i in (1..N).rev(){let j=next(&mut state) as usize%(i+1);permutation.swap(i,j);}
    let flips:[bool;N]=std::array::from_fn(|_|next(&mut state)&1!=0);
    for clause in &mut clauses {
        for lit in clause {
            let v=lit.unsigned_abs() as usize-1;
            let negative=(*lit<0)^flips[v];
            let mapped=permutation[v];
            *lit=if negative {-mapped} else {mapped};
        }
    }
    for i in (1..clauses.len()).rev() {
        let j=next(&mut state) as usize%(i+1);
        clauses.swap(i,j);
    }
    clauses
}

// Exact DPLL using unit propagation and deterministic degree order.
#[derive(Clone,Copy,PartialEq,Eq,Debug)]
struct Search {sat:bool,nodes:u64,scans:u64}

fn dpll(clauses:&[Vec<i32>])->Search {
    let mut degree=[0usize;N];
    for clause in clauses {
        for &lit in clause {degree[lit.unsigned_abs() as usize-1]+=1;}
    }
    let mut order:[usize;N]=std::array::from_fn(|i|i);
    order.sort_by(|&a,&b|degree[b].cmp(&degree[a]).then(a.cmp(&b)));
    fn recurse(clauses:&[Vec<i32>],order:&[usize;N],mut assignment:[i8;N],
               out:&mut Search)->bool {
        out.nodes+=1;
        loop {
            let mut changed=false;
            for clause in clauses {
                out.scans+=1;
                let (mut free,mut last,mut sat)=(0usize,0i32,false);
                for &lit in clause {
                    let val=assignment[lit.unsigned_abs() as usize-1];
                    if val<0 {free+=1;last=lit;}
                    else if (val==1)==(lit>0){sat=true;break;}
                }
                if sat {continue;}
                if free==0 {return false;}
                if free==1 {
                    assignment[last.unsigned_abs() as usize-1]=if last>0{1}else{0};
                    changed=true;
                }
            }
            if !changed {break;}
        }
        let mut all_satisfied=true;
        for clause in clauses {
            out.scans+=1;
            if !clause.iter().any(|&lit| {
                let val=assignment[lit.unsigned_abs() as usize-1];
                val>=0&&(val==1)==(lit>0)
            }){all_satisfied=false;break;}
        }
        if all_satisfied{return true;}
        let branch=*order.iter().find(|&&v|assignment[v]<0)
            .expect("unresolved clause must have free literal");
        let mut left=assignment;
        left[branch]=0;
        if recurse(clauses,order,left,out){return true;}
        assignment[branch]=1;
        recurse(clauses,order,assignment,out)
    }
    let mut result=Search{sat:false,nodes:0,scans:0};
    let sat=recurse(clauses,&order,[-1;N],&mut result);
    result.sat=sat;
    result
}

fn modulo(v:i32)->u64 {
    (i64::from(v).rem_euclid(P as i64)) as u64
}

fn power(mut base:u64,mut exp:u64)->u64 {
    let mut acc=1u64;
    while exp>0 {
        if exp&1==1{acc=acc*base%P;}
        base=base*base%P;
        exp>>=1;
    }
    acc
}

fn rank_mod(matrix:&[Vec<i32>],append_ones:bool)->usize {
    let m=matrix.len();
    let mut basis:Vec<Option<Vec<u64>>>=vec![None;m];
    let mut rank=0usize;
    for row_index in 0..(m+usize::from(append_ones)) {
        let mut row=if row_index==m {vec![1u64;m]}
            else {matrix[row_index].iter().map(|&v|modulo(v)).collect::<Vec<_>>()};
        loop {
            let Some(pivot)=row.iter().position(|&v|v!=0) else {break;};
            if let Some(ref existing)=basis[pivot] {
                let coeff=row[pivot];
                for j in pivot..m {
                    row[j]=(P+row[j]-(coeff*existing[j])%P)%P;
                }
            } else {
                let inv=power(row[pivot],P-2);
                for x in &mut row {*x=*x*inv%P;}
                basis[pivot]=Some(row);
                rank+=1;
                break;
            }
        }
    }
    rank
}

fn modular_candidate(k:&[Vec<i32>])->bool {
    rank_mod(k,true)>rank_mod(k,false)
}

#[derive(Clone,Copy,PartialEq,Eq,Debug)]
enum Route {Dpll,Covariance,Xor}

struct ResultRun {sat:bool,route:Route,scans:u64,candidate:bool}

#[derive(Clone,Copy)]
enum Method {DpllOnly,ExactFirst,ModularScreen}

fn solve(clauses:&[Vec<i32>],method:Method)->Result<ResultRun,String> {
    if matches!(method,Method::DpllOnly) {
        let found=dpll(clauses);
        return Ok(ResultRun{sat:found.sat,route:Route::Dpll,
            scans:found.scans,candidate:false});
    }
    let k=covariance(clauses);
    let candidate=if matches!(method,Method::ExactFirst) {true}
        else {modular_candidate(&k)};
    if candidate {
        if let Some(w)=kernel_certificate(&k) {
            verify(&k,clauses,&w)?;
            return Ok(ResultRun{sat:false,route:Route::Covariance,
                scans:0,candidate});
        }
    }
    if let Some(equations)=xor_certificate(clauses)? {
        verify_xor(clauses,&equations)?;
        return Ok(ResultRun{sat:false,route:Route::Xor,scans:0,candidate});
    }
    let found=dpll(clauses);
    Ok(ResultRun{sat:found.sat,route:Route::Dpll,
        scans:found.scans,candidate})
}

fn time_case(clauses:&[Vec<i32>],method:Method)->Result<(u128,ResultRun),String> {
    let mut times=Vec::new();
    let mut initial=None;
    for _ in 0..3 {
        let start=Instant::now();
        let result=solve(clauses,method)?;
        let elapsed=start.elapsed().as_nanos();
        if let Some(ref prior)=initial {
            let p:&ResultRun=prior;
            if p.sat!=result.sat||p.route!=result.route||p.scans!=result.scans {
                return Err("W021 nondeterministic result".into());
            }
        }else{initial=Some(result);}
        times.push(elapsed);
    }
    times.sort_unstable();
    Ok((times[1],initial.expect("three repetitions")))
}

fn family_report(family:Family)->Result<Value,String> {
    let mut sat=0;
    let (mut cov,mut xor,mut fallback,mut candidates,mut missed)=(0,0,0,0,0);
    let mut controls=Vec::new();
    let (mut baseline,mut exact,mut gated)=(Vec::new(),Vec::new(),Vec::new());
    for index in 0..CASES {
        let clauses=source(family,index);
        let (a,reference)=time_case(&clauses,Method::DpllOnly)?;
        let (b,full)=time_case(&clauses,Method::ExactFirst)?;
        let (c,screened)=time_case(&clauses,Method::ModularScreen)?;
        if reference.sat!=full.sat||reference.sat!=screened.sat {
            return Err(format!("W021 decision mismatch {} {index}",family.name()));
        }
        if family==Family::Planted&&!reference.sat {
            return Err("W021 planted unsat".into());
        }
        if matches!(family,Family::EightCore|Family::PaddedTwoSat|Family::XorCycle)
            && reference.sat {return Err("W021 constructed contradiction SAT".into());}
        if reference.sat {sat+=1;}
        match screened.route {
            Route::Covariance=>cov+=1,Route::Xor=>xor+=1,Route::Dpll=>fallback+=1,
        }
        if screened.candidate {candidates+=1;}
        if full.route==Route::Covariance&&screened.route!=Route::Covariance {missed+=1;}
        baseline.push(a);
        exact.push(b);
        gated.push(c);
        if [0,1,11].contains(&index) {
            let k=covariance(&clauses);
            let weights=kernel_certificate(&k);
            if let Some(ref w)=weights {verify(&k,&clauses,w)?;}
            let equations=xor_certificate(&clauses)?;
            if let Some(ref eqs)=equations {verify_xor(&clauses,eqs)?;}
            controls.push(json!({"index":index,"source":clauses,
                "sat":reference.sat,"dpll_scans":reference.scans,
                "exact_route":format!("{:?}",full.route),
                "gated_route":format!("{:?}",screened.route),
                "modular_candidate":screened.candidate,
                "covariance_weights":weights.map(|w|w.iter()
                    .map(|x|x.to_string()).collect::<Vec<_>>()),
                "xor_equations":equations.map(|eqs|eqs.iter()
                    .map(Equation::json).collect::<Vec<_>>())}));
        }
    }
    let average=|xs:&[u128]|xs.iter().sum::<u128>()/xs.len() as u128;
    Ok(json!({"family":family.name(),"cases":CASES,"satisfiable":sat,
        "unsatisfiable":CASES-sat,"covariance_proofs":cov,"xor_proofs":xor,
        "dpll_fallbacks":fallback,"modular_candidates":candidates,
        "missed_exact_covariance_witnesses":missed,
        "mean_case_median_dpll_ns":average(&baseline),
        "mean_case_median_exact_first_ns":average(&exact),
        "mean_case_median_modular_screen_ns":average(&gated),
        "controls":controls}))
}

pub fn audit()->Result<Value,String> {
    let mut families=Vec::new();
    for f in [Family::Planted,Family::Boundary,Family::EightCore,
              Family::PaddedTwoSat,Family::XorCycle] {
        families.push(family_report(f)?);
    }
    Ok(json!({"research_id":"W-CROSSDOMAIN-021",
        "scope":"cost-aware modular prefilter for exact bounded UNSAT proofs",
        "prime":P,"timing_repetitions":3,"families":families}))
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn modular_screen_can_find_hidden_eight_core() {
        let source=source(Family::EightCore,0);
        let k=covariance(&source);
        assert!(modular_candidate(&k));
        assert!(kernel_certificate(&k).is_some());
        let a=solve(&source,Method::DpllOnly).unwrap();
        let b=solve(&source,Method::ModularScreen).unwrap();
        assert!(!a.sat&&!b.sat);
    }
}
