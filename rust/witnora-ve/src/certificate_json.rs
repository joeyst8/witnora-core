//! R-025: Python-compatible stable JSON serialization for proof certificate
//! values in the explicit null/bool/signed-64-bit/string/list/tuple/dict subset.
//! Reject unsupported types rather than silently changing proof bytes.

#[cfg(feature = "python")]
use pyo3::{exceptions::PyValueError, prelude::*, types::{PyBool, PyDict, PyList, PyInt, PyString, PyTuple}};
use sha2::{Digest, Sha256};

pub fn sha256_hex(bytes: &[u8]) -> String {
    let digest = Sha256::digest(bytes);
    digest.iter().map(|byte| format!("{byte:02x}")).collect()
}

fn quoted(s: &str) -> String {
    let mut out = String::from("\"");
    for c in s.chars() {
        match c {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            '\u{0008}' => out.push_str("\\b"),
            '\u{000c}' => out.push_str("\\f"),
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            '\t' => out.push_str("\\t"),
            c if (c as u32) < 0x20 => out.push_str(&format!("\\u{:04x}", c as u32)),
            c if (c as u32) < 0x7f => out.push(c),
            c if (c as u32) <= 0xffff => out.push_str(&format!("\\u{:04x}", c as u32)),
            c => {
                let x = (c as u32) - 0x10000;
                out.push_str(&format!("\\u{:04x}\\u{:04x}",
                    0xd800 + (x >> 10), 0xdc00 + (x & 0x3ff)));
            }
        }
    }
    out.push('"');
    out
}

#[cfg(feature = "python")]
fn sequence_text(items: Vec<Bound<'_, PyAny>>, level: usize) -> PyResult<String> {
    if items.is_empty() {
        return Ok("[]".into());
    }
    let mut s = String::from("[\n");
    for (i, item) in items.iter().enumerate() {
        s.push_str(&"  ".repeat(level + 1));
        s.push_str(&serialize(item, level + 1)?);
        if i + 1 < items.len() {
            s.push(',');
        }
        s.push('\n');
    }
    s.push_str(&"  ".repeat(level));
    s.push(']');
    Ok(s)
}

#[cfg(feature = "python")]
fn serialize(value: &Bound<'_, PyAny>, level: usize) -> PyResult<String> {
    if level > 64 {
        return Err(PyValueError::new_err("native certificate JSON maximum depth exceeded"));
    }
    if value.is_none() {
        return Ok("null".into());
    }
    if value.is_instance_of::<PyBool>() {
        return Ok(if value.extract::<bool>()? { "true" } else { "false" }.into());
    }
    if value.is_instance_of::<PyInt>() {
        return Ok(value.extract::<i64>().map_err(|_| {
            PyValueError::new_err("native certificate JSON integer must fit i64")
        })?.to_string());
    }
    if let Ok(s) = value.downcast::<PyString>() {
        return Ok(quoted(&s.to_str()?));
    }
    if let Ok(items) = value.downcast::<PyList>() {
        return sequence_text(items.iter().collect(), level);
    }
    if let Ok(items) = value.downcast::<PyTuple>() {
        return sequence_text(items.iter().collect(), level);
    }
    if let Ok(dict) = value.downcast::<PyDict>() {
        if dict.is_empty() {
            return Ok("{}".into());
        }
        let mut ordered = Vec::new();
        for (key, val) in dict.iter() {
            let key: String = key.extract().map_err(|_| {
                PyValueError::new_err("native certificate JSON requires string object keys")
            })?;
            ordered.push((key, val));
        }
        ordered.sort_by(|a, b| a.0.cmp(&b.0));
        let mut out = String::from("{\n");
        for (i, (key, val)) in ordered.iter().enumerate() {
            out.push_str(&"  ".repeat(level + 1));
            out.push_str(&quoted(key));
            out.push_str(": ");
            out.push_str(&serialize(val, level + 1)?);
            if i + 1 < ordered.len() {
                out.push(',');
            }
            out.push('\n');
        }
        out.push_str(&"  ".repeat(level));
        out.push('}');
        return Ok(out);
    }
    Err(PyValueError::new_err("unsupported native certificate JSON value type"))
}

#[cfg(feature = "python")]
pub fn stable_json(value: &Bound<'_, PyAny>) -> PyResult<(String, String)> {
    let serialized = format!("{}\n", serialize(value, 0)?);
    let hash = sha256_hex(serialized.as_bytes());
    Ok((serialized, hash))
}

#[cfg(feature = "python")]
fn compact(value: &Bound<'_, PyAny>, depth: usize) -> PyResult<String> {
    if depth > 64 {
        return Err(PyValueError::new_err("native certificate JSON maximum depth exceeded"));
    }
    if value.is_none() {
        return Ok("null".into());
    }
    if value.is_instance_of::<PyBool>() {
        return Ok(if value.extract::<bool>()? { "true" } else { "false" }.into());
    }
    if value.is_instance_of::<PyInt>() {
        return Ok(value.extract::<i64>().map_err(|_| {
            PyValueError::new_err("native certificate JSON integer must fit i64")
        })?.to_string());
    }
    if let Ok(s) = value.downcast::<PyString>() {
        return Ok(quoted(&s.to_str()?));
    }
    if let Ok(items) = value.downcast::<PyList>() {
        let parts = items.iter().map(|item| compact(&item, depth + 1))
            .collect::<PyResult<Vec<_>>>()?;
        return Ok(format!("[{}]", parts.join(",")));
    }
    if let Ok(items) = value.downcast::<PyTuple>() {
        let parts = items.iter().map(|item| compact(&item, depth + 1))
            .collect::<PyResult<Vec<_>>>()?;
        return Ok(format!("[{}]", parts.join(",")));
    }
    if let Ok(dict) = value.downcast::<PyDict>() {
        let mut ordered = Vec::new();
        for (key, val) in dict.iter() {
            let key: String = key.extract().map_err(|_| {
                PyValueError::new_err("native certificate JSON requires string object keys")
            })?;
            ordered.push((key, val));
        }
        ordered.sort_by(|a, b| a.0.cmp(&b.0));
        let mut parts = Vec::new();
        for (key, val) in ordered.iter() {
            parts.push(format!("{}:{}", quoted(key), compact(val, depth + 1)?));
        }
        return Ok(format!("{{{}}}", parts.join(",")));
    }
    Err(PyValueError::new_err("unsupported native certificate JSON value type"))
}

#[cfg(feature = "python")]
pub fn compact_certificate_hash(value: &Bound<'_, PyAny>) -> PyResult<(String, String)> {
    let text = compact(value, 0)?;
    let hash = sha256_hex(text.as_bytes());
    Ok((text, hash))
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn digest_empty_and_ascii_escaping() {
        assert_eq!(quoted("a\n\t\u{0001}\"\\é😀"),
                   "\"a\\n\\t\\u0001\\\"\\\\\\u00e9\\ud83d\\ude00\"");
        assert_eq!(sha256_hex(b"").len(), 64);
    }
}
