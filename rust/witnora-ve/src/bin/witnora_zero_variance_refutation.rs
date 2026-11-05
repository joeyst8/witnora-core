fn main() {
    match witnora_ve::aux_zero_variance_refutation::audit() {
        Ok(value) => println!("{}",serde_json::to_string_pretty(&value)
            .expect("W018 JSON serialization")),
        Err(e) => {eprintln!("W018 failed: {e}");std::process::exit(1);}
    }
}
