//! R-161/R-162: independently audit emitted DRAT/RUP candidate syntax and size.
//! Does not establish RUP, DRAT or UNSAT soundness.

pub type Audit = (usize,usize,usize,Option<String>);

pub fn audit(text:&str)->Audit {
    if text.is_empty() || !text.ends_with('\n') {
        return (0,0,0,Some("proof candidate missing terminating newline".into()));
    }
    let mut count=0usize;
    let mut max_width=0usize;
    for line in text.lines() {
        let tokens=line.split_whitespace().collect::<Vec<_>>();
        if tokens.is_empty() || tokens.last()!=Some(&"0") {
            return (0,0,0,Some("invalid proof candidate clause line".into()));
        }
        for &token in &tokens[..tokens.len()-1] {
            match token.parse::<i64>() {
                Ok(lit) if lit!=0 && lit!=i64::MIN => (),
                _=>return (0,0,0,Some("invalid proof candidate literal".into())),
            }
        }
        count+=1;
        max_width=max_width.max(tokens.len()-1);
    }
    (count,max_width,text.len(),None)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn bytes_and_syntax() {
        assert_eq!(audit("0\n"),(1,0,2,None));
        assert_eq!(audit("1 -2 0\n0\n"),(2,2,9,None));
        assert!(audit("1 0").3.is_some());
        assert!(audit("d 1 0\n").3.is_some());
    }
}
