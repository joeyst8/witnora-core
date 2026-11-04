//! R-059: fixed-axiom syntactic graph implication triage.
//! A successful derivation is relative to these rules, never a Lean proof.

use std::collections::{BTreeSet, VecDeque};

const BOUNDS: [(&str, &str); 11] = [
    ("alpha", "n"), ("tau", "n"), ("tau", "m"),
    ("omega", "chi"), ("omega", "n"), ("chi", "n"),
    ("nu", "n"), ("nu", "tau"), ("nu", "m"),
    ("delta", "n"), ("delta", "m"),
];

pub fn bound_path(smaller: &str, larger: &str) -> Option<Vec<String>> {
    if smaller == larger { return Some(vec![]); }
    let mut queue = VecDeque::from([(smaller.to_owned(), Vec::<String>::new())]);
    let mut seen = BTreeSet::from([smaller.to_owned()]);
    let mut bounds = BOUNDS;
    bounds.sort();
    while let Some((current, path)) = queue.pop_front() {
        for (a, b) in bounds {
            if a != current || seen.contains(b) { continue; }
            let mut updated = path.clone();
            updated.push(format!("{a}<={b}"));
            if b == larger { return Some(updated); }
            seen.insert(b.to_owned());
            queue.push_back((b.to_owned(), updated));
        }
    }
    None
}

pub fn normalize(op: &str, a: &str, b: &str, label: &str) -> (String, Vec<String>) {
    if op == "atom" { return (a.to_owned(), vec![]); }
    if op == "+" && ((a == "alpha" && b == "tau") || (a == "tau" && b == "alpha")) {
        return ("n".into(), vec!["alpha+tau=n".into()]);
    }
    if op == "-" && a == "n" && b == "tau" {
        return ("alpha".into(), vec!["n-tau=alpha".into()]);
    }
    if op == "-" && a == "n" && b == "alpha" {
        return ("tau".into(), vec!["n-alpha=tau".into()]);
    }
    if op == "min" || op == "max" {
        if let Some(path) = bound_path(a, b) {
            return ((if op == "min" { a } else { b }).into(), path);
        }
        if let Some(path) = bound_path(b, a) {
            return ((if op == "min" { b } else { a }).into(), path);
        }
    }
    (label.to_owned(), vec![])
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn fixed_derived_and_unresolved() {
        assert_eq!(bound_path("nu", "chi"), None);
        assert_eq!(bound_path("nu", "n"), Some(vec!["nu<=n".into()]));
        assert_eq!(normalize("+", "tau", "alpha", "(tau+alpha)"),
                   ("n".into(), vec!["alpha+tau=n".into()]));
        assert_eq!(normalize("max", "alpha", "n", "max(alpha,n)"),
                   ("n".into(), vec!["alpha<=n".into()]));
    }
}
