//! R-061: conservative fixed-grammar conjecture identity normalization.
//! No output from this module constitutes a theorem or novelty claim.

use std::collections::BTreeSet;

pub fn normalize_expression(expr: &str) -> Result<String, String> {
    let expr = expr.trim();
    for op in ['+', '*'] {
        if expr.starts_with('(') && expr.ends_with(')') && expr.matches(op).count() == 1 {
            let inner = &expr[1..expr.len() - 1];
            let (a, b) = inner.split_once(op).ok_or("malformed binary expression")?;
            let mut parts = [a, b];
            parts.sort();
            return Ok(format!("({}{}{})", parts[0], op, parts[1]));
        }
    }
    for op in ["min", "max"] {
        if expr.starts_with(&format!("{op}(")) && expr.ends_with(')') {
            let inner = &expr[op.len() + 1..expr.len() - 1];
            let mut parts = inner.split(',');
            let a = parts.next().ok_or("malformed binary function")?;
            let b = parts.next().ok_or("malformed binary function")?;
            if parts.next().is_some() { return Err("malformed binary function".into()); }
            let mut sorted = [a, b];
            sorted.sort();
            return Ok(format!("{op}({},{})", sorted[0], sorted[1]));
        }
    }
    Ok(expr.to_owned())
}

pub fn identity_key(statement: &str) -> Result<(String, String), String> {
    let (left, right) = statement.split_once(" = ")
        .ok_or("statement requires ' = ' delimiter")?;
    let mut sides = [normalize_expression(left)?, normalize_expression(right)?];
    sides.sort();
    Ok((sides[0].clone(), sides[1].clone()))
}

pub fn known_identity_keys() -> BTreeSet<(String, String)> {
    let mut catalog: Vec<String> = [
        "n = (alpha+tau)", "alpha = (n-tau)", "tau = (n-alpha)",
        "chi = max(omega,chi)", "alpha = min(n,alpha)",
        "chi = min(n,chi)", "delta = min(n,delta)",
        "delta = min(m,delta)", "m = max(m,delta)",
        "m = max(m,nu)", "m = max(m,tau)",
    ].iter().map(|s|s.to_string()).collect();
    for metric in ["alpha", "tau", "omega", "chi", "nu", "delta"] {
        catalog.push(format!("{metric} = min(n,{metric})"));
        catalog.push(format!("n = max(n,{metric})"));
    }
    catalog.iter().map(|s|identity_key(s).expect("static identity catalog"))
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn symmetric_and_fail_closed() {
        assert_eq!(normalize_expression(" (tau+alpha) ").unwrap(), "(alpha+tau)");
        assert_eq!(normalize_expression("max(n,alpha)").unwrap(), "max(alpha,n)");
        assert_eq!(identity_key("n = (tau+alpha)").unwrap(),
                   identity_key("(alpha+tau) = n").unwrap());
        assert!(normalize_expression("min(a,b,c)").is_err());
        assert!(known_identity_keys().contains(&identity_key("n = (tau+alpha)").unwrap()));
    }
}
