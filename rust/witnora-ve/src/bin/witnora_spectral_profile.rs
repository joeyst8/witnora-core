//! W-CROSSDOMAIN-022: bounded-cost, non-solving spectral CNF profiler.
//! No SAT/UNSAT inference is made here; results are observables, not proofs.
use serde_json::json;
use std::io::{self, Read};
use std::time::Instant;

#[derive(Debug)]
pub(crate) struct Cnf {
    pub(crate) nvars: usize,
    pub(crate) clauses: Vec<Vec<i32>>,
    pub(crate) edges: usize,
}

pub(crate) fn parse(input: &str) -> Result<Cnf, String> {
    let mut header = None;
    let mut clauses = Vec::new();
    let mut current = Vec::new();
    let mut edges = 0usize;
    for raw in input.lines() {
        let line = raw.trim();
        if line.is_empty() || line.starts_with('c') { continue; }
        if line.starts_with('p') {
            if header.is_some() || !clauses.is_empty() || !current.is_empty() {
                return Err("duplicate or misplaced DIMACS header".into());
            }
            let parts: Vec<_> = line.split_whitespace().collect();
            if parts.len()!=4 || parts[0]!="p" || parts[1]!="cnf" {
                return Err("expected p cnf N M header".into());
            }
            let n:usize=parts[2].parse().map_err(|_|"invalid variable count")?;
            let m:usize=parts[3].parse().map_err(|_|"invalid clause count")?;
            if n>1_000_000 || m>5_000_000 {return Err("DIMACS size limit".into());}
            header=Some((n,m));
            continue;
        }
        let (n,m)=header.ok_or("missing DIMACS header")?;
        for word in line.split_whitespace() {
            let lit:i32=word.parse().map_err(|_|"noninteger DIMACS literal")?;
            if lit==0 {
                if clauses.len()>=m {return Err("too many clauses".into());}
                clauses.push(std::mem::take(&mut current));
            } else {
                if lit.unsigned_abs() as usize>n || lit==i32::MIN {
                    return Err("literal outside declared universe".into());
                }
                if clauses.len()>=m || edges>=20_000_000 {
                    return Err("clause or literal count limit".into());
                }
                current.push(lit);
                edges+=1;
            }
        }
    }
    let (n,m)=header.ok_or("missing DIMACS header")?;
    if !current.is_empty() {return Err("unterminated DIMACS clause".into());}
    if clauses.len()!=m {return Err("DIMACS clause count mismatch".into());}
    Ok(Cnf{nvars:n,clauses,edges})
}

pub(crate) fn norm(vec:&mut [f64])->bool {
    let n=vec.iter().map(|x|x*x).sum::<f64>().sqrt();
    if !n.is_finite() || n<=0.0 {return false;}
    for x in vec {*x/=n;}
    true
}

pub(crate) fn project(cnf:&Cnf,degree:&[usize],x:&[f64])->Vec<f64> {
    let mut y=vec![0.0;cnf.nvars];
    for clause in &cnf.clauses {
        if clause.is_empty(){continue;}
        let width=(clause.len() as f64).sqrt();
        let mut z=0.0;
        for &lit in clause {
            let v=lit.unsigned_abs() as usize-1;
            let a=if lit>0 {1.0}else{-1.0};
            z+=a*x[v]/(width*(degree[v] as f64).sqrt());
        }
        for &lit in clause {
            let v=lit.unsigned_abs() as usize-1;
            let a=if lit>0 {1.0}else{-1.0};
            y[v]+=a*z/(width*(degree[v] as f64).sqrt());
        }
    }
    y
}

pub(crate) fn profile(cnf:&Cnf)->serde_json::Value {
    let mut degree=vec![0usize;cnf.nvars];
    let mut positive=vec![0usize;cnf.nvars];
    let mut negative=vec![0usize;cnf.nvars];
    for clause in &cnf.clauses {
        for &lit in clause {
            let i=lit.unsigned_abs() as usize-1;
            degree[i]+=1;
            if lit>0 {positive[i]+=1;} else {negative[i]+=1;}
        }
    }
    let total_conflicts=positive.iter().zip(&negative)
        .map(|(p,n)|(*p).min(*n)).sum::<usize>();
    let conflict=if cnf.edges>0 {
        2.0*(total_conflicts as f64)/(cnf.edges as f64)
    } else {0.0};

    let mut x=(0..cnf.nvars).map(|i| {
        if degree[i]==0 {0.0}
        else {(positive[i] as f64-negative[i] as f64)/(degree[i] as f64).sqrt()}
    }).collect::<Vec<_>>();
    if !norm(&mut x) && cnf.nvars>0 {
        for (i,t) in x.iter_mut().enumerate(){*t=if i%2==0 {1.0}else{-1.0};}
        let _=norm(&mut x);
    }
    for _ in 0..8 {
        let mut next=project(cnf,&degree,&x);
        if !norm(&mut next) {break;}
        x=next;
    }
    let y=project(cnf,&degree,&x);
    let rayleigh=x.iter().zip(&y).map(|(a,b)|a*b).sum::<f64>();
    let ipr=x.iter().map(|a|a.powi(4)).sum::<f64>();
    json!({
        "variables":cnf.nvars,"clauses":cnf.clauses.len(),"literal_occurrences":cnf.edges,
        "mean_clause_width":if cnf.clauses.is_empty(){0.0}else{cnf.edges as f64/cnf.clauses.len() as f64},
        "polarity_conflict_fraction":conflict,
        "spectral_rayleigh":rayleigh,"spectral_inverse_participation":ipr,
        "iterations":8,"research_id":"W-CROSSDOMAIN-022",
        "claim":"bounded spectral observable only; no SAT proof and no solver speedup"
    })
}

fn run()->Result<(),String> {
    let args:Vec<_>=std::env::args().skip(1).collect();
    if args.len()>1 {return Err("usage: witnora_spectral_profile [FILE.cnf]".into());}
    let mut input=String::new();
    if let Some(path)=args.first() {
        input=std::fs::read_to_string(path).map_err(|e|e.to_string())?;
    }else {io::stdin().read_to_string(&mut input).map_err(|e|e.to_string())?;}
    let start=Instant::now();
    let cnf=parse(&input)?;
    let mut result=profile(&cnf);
    result["parse_and_profile_ns"]=json!(start.elapsed().as_nanos().min(u64::MAX as u128) as u64);
    println!("{}",serde_json::to_string(&result).map_err(|e|e.to_string())?);
    Ok(())
}

fn main(){if let Err(e)=run(){eprintln!("W022: {e}");std::process::exit(2);}}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn rejects_bad_source_and_supports_wrapping() {
        let cnf=parse("c banner\np cnf 3 3\n1 -2\n3 0\n0\n-3 0\n").unwrap();
        assert_eq!((cnf.nvars,cnf.clauses.len(),cnf.edges),(3,3,4));
        assert_eq!(cnf.clauses[1],Vec::<i32>::new());
        for bad in ["", "p cnf 2 1\n3 0", "p cnf 2 1\n1", "p cnf 2 1\n1 0\n-1 0"] {
            assert!(parse(bad).is_err(),"{bad}");
        }
    }
    #[test]
    fn expected_bounded_features() {
        let r=profile(&parse("p cnf 2 2\n1 -2 0\n-1 2 0\n").unwrap());
        assert_eq!(r["polarity_conflict_fraction"],1.0);
        assert!(r["spectral_rayleigh"].as_f64().unwrap()>=0.0);
        assert!(r["spectral_inverse_participation"].as_f64().unwrap()<=1.0);
    }
}
