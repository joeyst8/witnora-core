//! W-CROSSDOMAIN-017: exact signed covariance geometry and physical-cycle pilot.

fn main() {
    match witnora_ve::aux_signed_covariance::audit() {
        Ok(report) => println!("{}", serde_json::to_string_pretty(&report)
            .expect("W017 JSON is serializable")),
        Err(error) => {
            eprintln!("W-CROSSDOMAIN-017 failure: {error}");
            std::process::exit(1);
        }
    }
}
