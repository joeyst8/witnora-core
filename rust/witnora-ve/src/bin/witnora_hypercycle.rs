//! W-CROSSDOMAIN-013: prospective GF(2) hypercycle selection research report.

fn main() {
    match witnora_ve::aux_three_cnf_geometry::audit_hypercycles() {
        Ok(report) => println!("{}", serde_json::to_string_pretty(&report)
            .expect("report is serializable")),
        Err(error) => {
            eprintln!("W-CROSSDOMAIN-013 failed: {error}");
            std::process::exit(1);
        }
    }
}
