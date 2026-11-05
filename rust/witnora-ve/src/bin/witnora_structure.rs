//! W-STRUCT-001: exact bounded primal-graph separator diagnostic for source DIMACS.
//! Diagnostic only: no SAT, UNSAT, model count, or complexity claim.

use serde_json::json;
use std::{env, fs, process};

const MAX_VARS: usize = 128;
const MAX_CLAUSES: usize = 20_000;
const MAX_WIDTH: usize = 32;

#[derive(Debug)]
struct Cnf {
    n: usize,
    clauses: Vec<Vec<usize>>,
}

fn parse_dimacs(source: &str) -> Result<Cnf, String> {
    let mut header: Option<(usize, usize)> = None;
    let mut clauses = Vec::new();
    let mut current = Vec::new();
    for line in source.lines() {
        let line = line.trim();
        if line.is_empty() || line.starts_with('c') { continue; }
        if header.is_none() {
            let fields: Vec<_> = line.split_whitespace().collect();
            if fields.len() != 4 || fields[0] != "p" || fields[1] != "cnf" {
                return Err("expected 'p cnf VARIABLES CLAUSES' header".into());
            }
            let n = fields[2].parse::<usize>().map_err(|_| "invalid variable count")?;
            let m = fields[3].parse::<usize>().map_err(|_| "invalid clause count")?;
            if n > MAX_VARS || m > MAX_CLAUSES {
                return Err("source exceeds explicit diagnostic caps".into());
            }
            header = Some((n, m));
            continue;
        }
        for token in line.split_whitespace() {
            let signed = token.parse::<i64>().map_err(|_| "invalid signed literal")?;
            if signed == 0 {
                current.sort_unstable();
                current.dedup();
                clauses.push(std::mem::take(&mut current));
                if clauses.len() > header.unwrap().1 {
                    return Err("more clauses than declared".into());
                }
            } else {
                let abs = signed.unsigned_abs();
                if abs > header.unwrap().0 as u64 {
                    return Err("literal outside declared variable universe".into());
                }
                current.push((abs - 1) as usize);
                if current.len() > MAX_WIDTH {
                    return Err("clause width exceeds explicit cap".into());
                }
            }
        }
    }
    let (n, expected) = header.ok_or("missing DIMACS header")?;
    if !current.is_empty() || clauses.len() != expected {
        return Err("unterminated clause or declared count mismatch".into());
    }
    Ok(Cnf { n, clauses })
}

fn primal_graph(cnf: &Cnf) -> (Vec<Vec<bool>>, usize) {
    let mut graph = vec![vec![false; cnf.n]; cnf.n];
    let mut edges = 0;
    for clause in &cnf.clauses {
        for (i, &u) in clause.iter().enumerate() {
            for &v in &clause[i + 1..] {
                if !graph[u][v] {
                    graph[u][v] = true;
                    graph[v][u] = true;
                    edges += 1;
                }
            }
        }
    }
    (graph, edges)
}

fn components(graph: &[Vec<bool>], removed: &[usize]) -> Vec<usize> {
    let n = graph.len();
    let mut seen = vec![false; n];
    for &v in removed { seen[v] = true; }
    let mut sizes = Vec::new();
    for start in 0..n {
        if seen[start] { continue; }
        seen[start] = true;
        let mut stack = vec![start];
        let mut size = 0;
        while let Some(u) = stack.pop() {
            size += 1;
            for v in 0..n {
                if graph[u][v] && !seen[v] {
                    seen[v] = true;
                    stack.push(v);
                }
            }
        }
        sizes.push(size);
    }
    sizes
}

/// First mod-2 Betti number of the graph's flag (clique) complex.
/// At n<=16 there are at most 120 edges, so u128 holds every 1-boundary.
/// beta1 = E - V + beta0 - rank(boundary_2); triangles are 2-simplices.
fn flag_beta1(graph: &[Vec<bool>], edges: usize, beta0: usize) -> Option<(usize, usize)> {
    let n = graph.len();
    if n > 16 { return None; }
    let mut index = vec![vec![0usize; n]; n];
    let mut next = 0usize;
    for a in 0..n {
        for b in a + 1..n {
            if graph[a][b] {
                index[a][b] = next;
                index[b][a] = next;
                next += 1;
            }
        }
    }
    debug_assert_eq!(next, edges);
    let mut basis = [0u128; 128];
    let mut rank = 0usize;
    let mut triangles = 0usize;
    for a in 0..n {
        for b in a + 1..n {
            if !graph[a][b] { continue; }
            for c in b + 1..n {
                if !graph[a][c] || !graph[b][c] { continue; }
                triangles += 1;
                let mut column = (1u128 << index[a][b])
                    ^ (1u128 << index[a][c]) ^ (1u128 << index[b][c]);
                while column != 0 {
                    let pivot = 127 - column.leading_zeros() as usize;
                    if basis[pivot] == 0 {
                        basis[pivot] = column;
                        rank += 1;
                        break;
                    }
                    column ^= basis[pivot];
                }
            }
        }
    }
    Some((edges + beta0 - n - rank, triangles))
}

fn profile(cnf: &Cnf) -> serde_json::Value {
    let (graph, edges) = primal_graph(cnf);
    let initial = components(&graph, &[]);
    let topology = flag_beta1(&graph, edges, initial.len());
    let mut witness: Vec<usize> = Vec::new();
    let mut residual = initial.clone();
    let mut order: Option<usize> = if initial.len() >= 2 { Some(0) } else { None };
    if order.is_none() {
        'search: for k in 1..=2 {
            for a in 0..cnf.n {
                if k == 1 {
                    let sizes = components(&graph, &[a]);
                    if sizes.len() >= 2 {
                        witness = vec![a + 1];
                        residual = sizes;
                        order = Some(1);
                        break 'search;
                    }
                } else {
                    for b in a + 1..cnf.n {
                        let sizes = components(&graph, &[a, b]);
                        if sizes.len() >= 2 {
                            witness = vec![a + 1, b + 1];
                            residual = sizes;
                            order = Some(2);
                            break 'search;
                        }
                    }
                }
            }
        }
    }
    json!({
        "variable_count": cnf.n,
        "clause_count": cnf.clauses.len(),
        "primal_edges": edges,
        "possible_primal_edges": cnf.n.saturating_mul(cnf.n.saturating_sub(1)) / 2,
        "initial_components": initial.len(),
        "separator_order_le2": order,
        "separator_variables": witness,
        "residual_components": residual.len(),
        "largest_residual_component": residual.iter().copied().max().unwrap_or(0),
        "primal_flag_beta1_mod2": topology.map(|(beta, _)| beta),
        "primal_flag_triangle_count": topology.map(|(_, triangles)| triangles),
        "scope": "source-primal-graph-only; no SAT or complexity certificate"
    })
}

fn main() {
    let args: Vec<_> = env::args().skip(1).collect();
    if args.len() != 1 {
        eprintln!("usage: witnora_structure SOURCE.cnf");
        process::exit(2);
    }
    let result = fs::read_to_string(&args[0])
        .map_err(|e| format!("source read failed: {e}"))
        .and_then(|source| parse_dimacs(&source))
        .map(|cnf| profile(&cnf));
    match result {
        Ok(value) => println!("{}", value),
        Err(error) => { eprintln!("{error}"); process::exit(2); }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn disconnected_and_connected_controls() {
        let disconnected = parse_dimacs("p cnf 4 2\n1 2 0\n3 4 0\n").unwrap();
        assert_eq!(profile(&disconnected)["separator_order_le2"], json!(0));
        let path = parse_dimacs("p cnf 4 3\n1 2 0\n2 3 0\n3 4 0\n").unwrap();
        assert_eq!(profile(&path)["separator_variables"], json!([2]));
        let triangle = parse_dimacs("p cnf 3 3\n1 2 0\n2 3 0\n1 3 0\n").unwrap();
        assert!(profile(&triangle)["separator_order_le2"].is_null());
        assert_eq!(profile(&triangle)["primal_flag_beta1_mod2"], json!(0));
        let square = parse_dimacs("p cnf 4 4\n1 2 0\n2 3 0\n3 4 0\n1 4 0\n").unwrap();
        assert_eq!(profile(&square)["primal_flag_beta1_mod2"], json!(1));
    }

    #[test]
    fn malformed_sources_fail_closed() {
        for source in ["p cnf 2 1\n1 0\n2 0", "p cnf 2 1\n3 0", "p cnf 2 1\n1",
                       "p cnf 2 1\n1 2", "p cnf 129 0", "p cnf 2 1\nfoo 0"] {
            assert!(parse_dimacs(source).is_err(), "{source}");
        }
    }
}
