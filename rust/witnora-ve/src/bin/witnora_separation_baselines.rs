fn main() {
    match witnora_ve::aux_separation_baselines::audit() {
        Ok(report)=>println!("{}",serde_json::to_string_pretty(&report)
            .expect("W020 JSON serialization")),
        Err(error)=>{eprintln!("W020 failed: {error}");std::process::exit(1);}
    }
}
