//! W-CROSSDOMAIN-011: report the predeclared graph-heldout replication,
//! including negative outcomes, with no claim about general SAT hardness.

fn main() {
    match witnora_ve::aux_cycle_cost::audit_holdouts() {
        Ok(report) => println!("{}", serde_json::to_string_pretty(&report)
            .expect("audit JSON serializable")),
        Err(error) => {
            eprintln!("W-CROSSDOMAIN-011 audit failed: {error}");
            std::process::exit(1);
        }
    }
}
