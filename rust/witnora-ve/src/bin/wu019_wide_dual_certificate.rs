//! WU-019 multiword dual-coordinate soundness test, independent of Xorcle C++.
//! No SAT assignment enumeration: arbitrary row spaces, trail extensions,
//! truncations and watch equations across packed-word boundaries.

fn leading(row: &[u64]) -> Option<usize> {
    row.iter().enumerate().find_map(|(i, &word)| {
        (word != 0).then(|| i * 64 + word.trailing_zeros() as usize)
    })
}

fn parity(a: &[u64], b: &[u64]) -> bool {
    a.iter().zip(b).fold(false, |acc, (&x, &y)| acc ^ ((x & y).count_ones() & 1 == 1))
}

fn reduce(mut row: Vec<u64>, basis: &[Vec<u64>]) -> Vec<u64> {
    for b in basis {
        let p = leading(b).expect("nonzero echelon row");
        if row[p / 64] & (1u64 << (p % 64)) != 0 {
            for (v, &w) in row.iter_mut().zip(b) { *v ^= w; }
        }
    }
    row
}

fn add(basis: &mut Vec<Vec<u64>>, row: Vec<u64>) {
    let row = reduce(row, basis);
    if let Some(p) = leading(&row) {
        let idx = basis.partition_point(|b| leading(b).unwrap() < p);
        basis.insert(idx, row);
    }
}

fn duals(basis: &[Vec<u64>], cols: usize, k: usize) -> Vec<Vec<u64>> {
    let words = cols.div_ceil(64);
    let pivots = basis.iter().map(|b| leading(b).unwrap()).collect::<Vec<_>>();
    let mut result = Vec::new();
    for col in (0..cols).filter(|c| !pivots.contains(c)).take(k) {
        let mut mask = vec![0u64; words];
        mask[col / 64] = 1u64 << (col % 64);
        for b in basis.iter().rev() {
            if parity(&mask, b) {
                let p = leading(b).unwrap();
                mask[p / 64] ^= 1u64 << (p % 64);
            }
        }
        assert!(basis.iter().all(|b| !parity(b, &mask)));
        result.push(mask);
    }
    result
}

fn signatures(a: &[u64], basis: &[Vec<u64>], cols: usize) -> (u8, u8) {
    let masks = duals(basis, cols, 4);
    let from_duals = masks.iter().enumerate().fold(0u8, |sig, (j, mask)| {
        sig | ((parity(a, mask) as u8) << j)
    });
    let r = reduce(a.to_vec(), basis);
    let pivots = basis.iter().map(|b| leading(b).unwrap()).collect::<Vec<_>>();
    let from_reduction = (0..cols).filter(|c| !pivots.contains(c)).take(4)
        .enumerate().fold(0u8, |sig, (j, col)| {
            sig | ((((r[col / 64] >> (col % 64)) & 1) as u8) << j)
        });
    (from_duals, from_reduction)
}

fn next(seed: &mut u64) -> u64 {
    *seed ^= *seed >> 12;
    *seed ^= *seed << 25;
    *seed ^= *seed >> 27;
    seed.wrapping_mul(0x2545f4914f6cdd1d)
}

fn random_row(seed: &mut u64, cols: usize) -> Vec<u64> {
    let words = cols.div_ceil(64);
    let mut row = (0..words).map(|_| next(seed)).collect::<Vec<_>>();
    if cols % 64 != 0 { *row.last_mut().unwrap() &= (1u64 << (cols % 64)) - 1; }
    row
}

fn check() {
    let mut seed = 0x5775_3031_395f_7769u64;
    for cols in [1, 32, 63, 64, 65, 80, 129, 192, 257] {
        let mut basis = Vec::new();
        for _ in 0..280 {
            if next(&mut seed) & 3 == 0 && !basis.is_empty() {
                let keep = next(&mut seed) as usize % basis.len();
                basis.truncate(keep);
            }
            add(&mut basis, random_row(&mut seed, cols));
            for _ in 0..4 {
                let a = random_row(&mut seed, cols);
                let b = random_row(&mut seed, cols);
                let (asig, expected_a) = signatures(&a, &basis, cols);
                let (bsig, expected_b) = signatures(&b, &basis, cols);
                assert_eq!(asig, expected_a);
                assert_eq!(bsig, expected_b);
                if asig != 0 && bsig != 0 && asig != bsig {
                    let ar = reduce(a, &basis);
                    let br = reduce(b, &basis);
                    assert!(leading(&ar).is_some() && leading(&br).is_some());
                    assert_ne!(ar, br);
                }
            }
        }
    }
}

fn main() {
    check();
    println!("WU019: 2,520 randomized multiword trail states verified");
}

#[cfg(test)]
mod tests {
    #[test]
    fn wide_dual_coordinates_match_full_reduction() {
        super::check();
    }
}
