//! W-CROSSDOMAIN-014: bounded Fourier character versus cheap conflict baseline.

fn main() {
    match witnora_ve::aux_three_cnf_geometry::audit_wave_proxy() {
        Ok(report) => println!("{}", serde_json::to_string_pretty(&report)
            .expect("wave report is serializable")),
        Err(error) => {
            eprintln!("W-CROSSDOMAIN-014 failed: {error}");
            std::process::exit(1);
        }
    }
}
