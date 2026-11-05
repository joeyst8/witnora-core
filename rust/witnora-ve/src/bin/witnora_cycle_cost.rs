//! Emit the W-CROSSDOMAIN-010 finite signed-graph search-cost audit as JSON.

fn main() {
    match witnora_ve::aux_cycle_cost::audit() {
        Ok(report) => println!("{}", serde_json::to_string_pretty(&report)
            .expect("audit JSON serializable")),
        Err(error) => {
            eprintln!("W-CROSSDOMAIN-010 audit failed: {error}");
            std::process::exit(1);
        }
    }
}
