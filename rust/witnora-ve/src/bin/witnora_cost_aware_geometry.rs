fn main() {
    match witnora_ve::aux_cost_aware_geometry::audit() {
        Ok(report)=>println!("{}",serde_json::to_string_pretty(&report)
            .expect("W021 report serialization")),
        Err(error)=>{eprintln!("W021 failed: {error}");std::process::exit(1);}
    }
}
