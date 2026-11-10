//! HV-003: normalize nonstandard *trailing* metadata on combinational binary
//! AIGER 1.0 files from the public IWLS'05 synthesis benchmark distribution.
//!
//! This is a file-format compatibility shim, not a logic transformation.
//! It copies the entire header, output list and exactly two delta varints
//! per AND gate byte-for-byte, dropping only bytes after the last gate.
//! Latches and extended AIGER properties are deliberately rejected.
//!
//! Usage: rustc --edition=2021 -O research/hv003_strip_aiger_suffix.rs -o hv003-strip
//!        hv003-strip SOURCE.aig NORMALIZED.aig

use std::{env, fs, process};

fn error(message: &str) -> ! {
    eprintln!("HV-003 AIGER normalization rejected: {message}");
    process::exit(1)
}

fn take_line(input: &[u8], offset: &mut usize) -> Vec<u8> {
    let start = *offset;
    let end = input[start..]
        .iter()
        .position(|&b| b == b'\n')
        .map(|relative| start + relative)
        .unwrap_or_else(|| error("truncated ASCII header/output line"));
    *offset = end + 1;
    input[start..end].to_vec()
}

fn take_delta(input: &[u8], offset: &mut usize) {
    let mut done = false;
    for _ in 0..5 {
        let byte = *input
            .get(*offset)
            .unwrap_or_else(|| error("truncated AND-gate delta varint"));
        *offset += 1;
        if byte & 0x80 == 0 {
            done = true;
            break;
        }
    }
    if !done {
        error("gate varint exceeded five bytes");
    }
}

fn main() {
    let args: Vec<_> = env::args().collect();
    if args.len() != 3 || args[1] == args[2] {
        error("usage: hv003-strip SOURCE.aig NEW_NORMALIZED.aig");
    }
    let input = fs::read(&args[1]).unwrap_or_else(|_| error("unable to read source"));
    let mut offset = 0_usize;
    let header = take_line(&input, &mut offset);
    let header = std::str::from_utf8(&header).unwrap_or_else(|_| error("non-UTF8 header"));
    let fields: Vec<_> = header.split_whitespace().collect();
    if fields.len() != 6 || fields[0] != "aig" {
        error("requires binary AIGER with exactly M I L O A header fields");
    }
    let params: Vec<usize> = fields[1..]
        .iter()
        .map(|s| s.parse::<usize>().unwrap_or_else(|_| error("invalid numeric header")))
        .collect();
    let (maximum, inputs, latches, outputs, ands) =
        (params[0], params[1], params[2], params[3], params[4]);
    if latches != 0 || maximum != inputs + ands {
        error("latches or unsupported/noncanonical variable numbering");
    }
    for _ in 0..outputs {
        let output_line = take_line(&input, &mut offset);
        let text = std::str::from_utf8(&output_line)
            .unwrap_or_else(|_| error("non-UTF8 output literal"));
        let value = text.parse::<usize>().unwrap_or_else(|_| error("invalid output literal"));
        if value > 2 * maximum + 1 {
            error("output literal exceeds AIGER variable range");
        }
    }
    for _ in 0..ands {
        take_delta(&input, &mut offset);
        take_delta(&input, &mut offset);
    }
    fs::write(&args[2], &input[..offset])
        .unwrap_or_else(|_| error("unable to write normalized output"));
    eprintln!(
        "AIGER: M={maximum} I={inputs} L={latches} O={outputs} A={ands}; logic_prefix_bytes={offset}; stripped_trailer_bytes={}",
        input.len() - offset
    );
}
