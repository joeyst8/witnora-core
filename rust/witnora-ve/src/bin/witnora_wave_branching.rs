//! W-CROSSDOMAIN-016: prospective cost-aware statistical-wave DPLL audit.

fn main() {
    match witnora_ve::aux_wave_branching::audit() {
        Ok(report) => println!("{}", serde_json::to_string_pretty(&report)
            .expect("W016 JSON is serializable")),
        Err(error) => {
            eprintln!("W-CROSSDOMAIN-016 failure: {error}");
            std::process::exit(1);
        }
    }
}
