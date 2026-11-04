//! R-026: byte-exact SHA-256 manifest for certificate bundle text files.
//! File bytes are UTF-8 to preserve the original .wcert text contract.

use std::collections::BTreeMap;
use crate::certificate_json::sha256_hex;

pub fn file_digests(files: &[(String, String)]) -> Result<Vec<(String, String)>, String> {
    let mut ordered = BTreeMap::new();
    for (name, text) in files {
        if name.is_empty() || name.contains('\0') {
            return Err("invalid empty or NUL-containing certificate file name".into());
        }
        if ordered.insert(name.clone(), sha256_hex(text.as_bytes())).is_some() {
            return Err("duplicate certificate bundle file name".into());
        }
    }
    Ok(ordered.into_iter().collect())
}

/// Return the first Python-compatible file-integrity failure in manifest order.
/// The function does not claim to verify the logical proof trace.
pub fn first_digest_failure(
    expected: &[(String, String)],
    files: &[(String, String)],
) -> Result<Option<String>, String> {
    let mut present = BTreeMap::new();
    for (name, contents) in files {
        if present.insert(name.clone(), contents.as_str()).is_some() {
            return Err("duplicate physical certificate file name".into());
        }
    }
    for (name, digest) in expected {
        let Some(contents) = present.get(name) else {
            return Ok(Some(format!("missing file {name}")));
        };
        if &sha256_hex(contents.as_bytes()) != digest {
            return Ok(Some(format!("file hash mismatch for {name}")));
        }
    }
    Ok(None)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn sorted_hashes_and_rejected_duplicates() {
        let result = file_digests(&[
            ("z".into(), "é😀\n".into()),
            ("a".into(), "".into()),
        ]).unwrap();
        assert_eq!(result.iter().map(|x| x.0.as_str()).collect::<Vec<_>>(),
                   vec!["a", "z"]);
        assert_eq!(result[0].1.len(), 64);
        assert_eq!(result[1].1.len(), 64);
        assert!(file_digests(&[("a".into(), "".into()),
                               ("a".into(), "x".into())]).is_err());
        assert!(file_digests(&[("".into(), "x".into())]).is_err());
        let files = vec![("x".into(), "abc".into())];
        let hashes = file_digests(&files).unwrap();
        assert_eq!(first_digest_failure(&hashes, &files).unwrap(), None);
        assert_eq!(first_digest_failure(&hashes, &[]).unwrap(),
                   Some("missing file x".into()));
        assert_eq!(first_digest_failure(&hashes,
                    &[("x".into(), "tampered".into())]).unwrap(),
                   Some("file hash mismatch for x".into()));
    }
}
