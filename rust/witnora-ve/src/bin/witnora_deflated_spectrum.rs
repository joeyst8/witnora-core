//! W-CROSSDOMAIN-023: gauge-deflated finite-iteration spectral diagnostics.
//! The W022 parser and normalized B^T B operation are reused unchanged.
#[path = "witnora_spectral_profile.rs"]
mod previous;

use serde_json::{json, Value};
use std::io::{self, Read};
use std::time::Instant;

fn dot(a:&[f64],b:&[f64])->f64 {
    a.iter().zip(b).map(|(x,y)|x*y).sum()
}

fn remove_mode(x:&mut [f64],g:&[f64])->bool {
    let coefficient=dot(x,g);
    for (item,axis) in x.iter_mut().zip(g) {*item-=coefficient*axis;}
    previous::norm(x)
}

fn features(cnf:&previous::Cnf)->Value {
    let mut result=previous::profile(cnf);
    result["research_id"]=json!("W-CROSSDOMAIN-023");
    result["claim"]=json!("diagnostic spectral features only; no SAT/UNSAT inference");
    let mut pos=vec![0usize;cnf.nvars];
    let mut neg=vec![0usize;cnf.nvars];
    for clause in &cnf.clauses {
        for &lit in clause {
            let v=lit.unsigned_abs() as usize-1;
            if lit>0 {pos[v]+=1;}else{neg[v]+=1;}
        }
    }
    let degrees=pos.iter().zip(&neg).map(|(a,b)|a+b).collect::<Vec<_>>();
    let mut g=(0..cnf.nvars).map(|i| {
        if degrees[i]==0 {0.0}
        else{(pos[i] as f64-neg[i] as f64)/(degrees[i] as f64).sqrt()}
    }).collect::<Vec<_>>();
    if !previous::norm(&mut g) {
        result["gauge_frustration"]=Value::Null;
        result["deflated_rayleigh"]=Value::Null;
        result["deflated_iterations"]=json!(12);
        return result;
    }
    let tg=previous::project(cnf,&degrees,&g);
    let gauge_energy=(1.0-dot(&g,&tg)).clamp(0.0,1.0);
    result["gauge_frustration"]=json!(gauge_energy);
    let mut x=g.iter().enumerate().map(|(i,v)|v*((i%5) as f64-2.0))
        .collect::<Vec<_>>();
    if !remove_mode(&mut x,&g) {
        x=g.iter().enumerate().map(|(i,v)|v*((i%7) as f64-3.0))
            .collect::<Vec<_>>();
        if !remove_mode(&mut x,&g) {
            result["deflated_rayleigh"]=Value::Null;
            result["deflated_iterations"]=json!(12);
            return result;
        }
    }
    for _ in 0..12 {
        let mut y=previous::project(cnf,&degrees,&x);
        if !remove_mode(&mut y,&g) {break;}
        x=y;
    }
    let tx=previous::project(cnf,&degrees,&x);
    result["deflated_rayleigh"]=json!(dot(&x,&tx).clamp(0.0,1.0));
    result["deflated_iterations"]=json!(12);
    result
}

fn run()->Result<(),String> {
    let args:Vec<_>=std::env::args().skip(1).collect();
    if args.len()>1 {return Err("usage: witnora_deflated_spectrum [FILE.cnf]".into());}
    let mut input=String::new();
    if let Some(path)=args.first() {
        input=std::fs::read_to_string(path).map_err(|e|e.to_string())?;
    }else{io::stdin().read_to_string(&mut input).map_err(|e|e.to_string())?;}
    let start=Instant::now();
    let source=previous::parse(&input)?;
    let mut values=features(&source);
    values["parse_and_profile_ns"]=json!(start.elapsed().as_nanos().min(u64::MAX as u128) as u64);
    println!("{}",serde_json::to_string(&values).map_err(|e|e.to_string())?);
    Ok(())
}

fn main(){if let Err(e)=run(){eprintln!("W023: {e}");std::process::exit(2);}}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn gauge_flips_preserve_all_scalar_features() {
        let source=previous::parse("p cnf 4 5\n1 -2 3 0\n-1 2 4 0\n1 3 0\n-2 -4 0\n2 3 4 0\n").unwrap();
        let flip=previous::parse("p cnf 4 5\n-1 -2 3 0\n1 2 4 0\n-1 3 0\n-2 -4 0\n2 3 4 0\n").unwrap();
        let first=features(&source);
        let second=features(&flip);
        for key in ["gauge_frustration","deflated_rayleigh","spectral_rayleigh"] {
            let a=first[key].as_f64().unwrap();
            let b=second[key].as_f64().unwrap();
            assert!((a-b).abs()<1e-10,"{key}: {a} != {b}");
        }
    }
    #[test]
    fn pure_source_has_zero_gauge_frustration() {
        let source=previous::parse("p cnf 3 3\n1 2 3 0\n1 2 0\n2 3 0\n").unwrap();
        let report=features(&source);
        assert!(report["gauge_frustration"].as_f64().unwrap().abs()<1e-12);
    }
}
