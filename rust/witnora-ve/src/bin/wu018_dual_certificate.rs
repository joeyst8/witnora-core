//! WU-018 algebra-only cross-check for current-trail four-bit dual witnesses.
//! The production experiment is a separate patch of Xorcle's C++ engine.
//! This Rust checker uses no assignment enumeration and has no solver claims.

fn pivot(row: u64) -> u32 {
    assert!(row != 0);
    row.trailing_zeros()
}

fn reduce(mut word: u64, rows: &[u64]) -> u64 {
    for &row in rows {
        if (word >> pivot(row)) & 1 == 1 {
            word ^= row;
        }
    }
    word
}

fn insert(rows: &mut Vec<u64>, word: u64) {
    let reduced = reduce(word, rows);
    if reduced == 0 {
        return;
    }
    let idx = rows.partition_point(|&row| pivot(row) < pivot(reduced));
    rows.insert(idx, reduced);
}

fn free_columns(rows: &[u64], cols: usize) -> Vec<usize> {
    (0..cols)
        .filter(|&col| !rows.iter().any(|&r| pivot(r) as usize == col))
        .collect()
}

fn dual_masks(rows: &[u64], cols: usize, max_bits: usize) -> Vec<u64> {
    assert!((1..=64).contains(&cols));
    let mut masks = Vec::new();
    for col in free_columns(rows, cols).into_iter().take(max_bits) {
        let mut dual = 1u64 << col;
        for &row in rows.iter().rev() {
            if (row & dual).count_ones() & 1 == 1 {
                dual ^= 1u64 << pivot(row);
            }
        }
        assert!(rows.iter().all(|&r| (r & dual).count_ones() & 1 == 0));
        masks.push(dual);
    }
    masks
}

fn dual_signature(word: u64, masks: &[u64]) -> u64 {
    masks.iter().enumerate().fold(0, |value, (i, &mask)| {
        value | (((word & mask).count_ones() as u64 & 1) << i)
    })
}

fn reduction_signature(word: u64, rows: &[u64], cols: usize, k: usize) -> u64 {
    let reduced = reduce(word, rows);
    free_columns(rows, cols).into_iter().take(k).enumerate()
        .fold(0, |value, (i, col)| value | (((reduced >> col) & 1) << i))
}

fn next(seed: &mut u64) -> u64 {
    *seed ^= *seed >> 12;
    *seed ^= *seed << 25;
    *seed ^= *seed >> 27;
    seed.wrapping_mul(0x2545f4914f6cdd1d)
}

fn check_many() {
    let mut seed = 0x5774_3031_385f_646f_u64;
    for cols in 1..=64 {
        let domain = if cols == 64 { u64::MAX } else { (1u64 << cols) - 1 };
        let mut rows = Vec::new();
        for _ in 0..200 {
            // Alternating trail extension and rewind, with fresh independent rows.
            if next(&mut seed) & 7 == 0 && !rows.is_empty() {
                rows.truncate((next(&mut seed) as usize) % rows.len());
            }
            insert(&mut rows, next(&mut seed) & domain);
            let masks = dual_masks(&rows, cols, 4);
            for _ in 0..4 {
                let a = next(&mut seed) & domain;
                let b = next(&mut seed) & domain;
                let asig = dual_signature(a, &masks);
                let bsig = dual_signature(b, &masks);
                assert_eq!(asig, reduction_signature(a, &rows, cols, 4));
                assert_eq!(bsig, reduction_signature(b, &rows, cols, 4));
                if asig != 0 && bsig != 0 && asig != bsig {
                    let ar = reduce(a, &rows);
                    let br = reduce(b, &rows);
                    assert!(ar != 0 && br != 0 && ar != br);
                }
            }
        }
    }
}

fn main() {
    check_many();
    println!("WU018 dual masks matched canonical quotient signatures through 12,800 trial trail states");
}

#[cfg(test)]
mod tests {
    #[test]
    fn canonical_quotient_and_incremental_trail_states() {
        super::check_many();
    }

    #[test]
    fn one_known_nontrivial_basis() {
        let rows = vec![0b101, 0b110];
        let masks = super::dual_masks(&rows, 4, 4);
        assert_eq!(masks.len(), 2);
        assert_eq!(masks[0], 0b111);
        assert_eq!(masks[1], 0b1000);
        assert_eq!(super::dual_signature(0b0011, &masks),
                   super::reduction_signature(0b0011, &rows, 4, 4));
    }
}
