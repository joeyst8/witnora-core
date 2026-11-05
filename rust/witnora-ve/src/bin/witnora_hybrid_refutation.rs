fn main() {
    match witnora_ve::aux_hybrid_refutation::audit() {
        Ok(report)=>println!("{}",serde_json::to_string_pretty(&report)
            .expect("W019 JSON serialization")),
        Err(error)=>{eprintln!("W019 failed: {error}");std::process::exit(1);}
    }
}
