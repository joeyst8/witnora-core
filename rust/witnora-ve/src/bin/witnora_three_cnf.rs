//! W-CROSSDOMAIN-012 prospective finite 3-CNF hypergraph report.

fn main() {
    match witnora_ve::aux_three_cnf_geometry::audit() {
        Ok(report) => println!("{}", serde_json::to_string_pretty(&report)
            .expect("audit is serializable")),
        Err(error) => {
            eprintln!("W-CROSSDOMAIN-012 failed: {error}");
            std::process::exit(1);
        }
    }
}
