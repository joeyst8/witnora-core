//! W-CROSSDOMAIN-017: exact clause-violation covariance, signed triangles,
//! and fixed-pilot correlation with SAT search cost. Research only.

use serde_json::{json, Value};

const N: usize = 12;
const CASES: usize = 32;
const STEP: u32 = 0x9E37_79B9;

#[derive(Clone, Copy, PartialEq, Eq)]
enum Family { Planted, Boundary, Unsat }

impl Family {
    fn seed(self) -> u32 {
        match self { Self::Planted => 0xD17C_0DE1,
                     Self::Boundary => 0xD17C_0DE2,
                     Self::Unsat => 0xD17C_0DE3 }
    }
    fn name(self) -> &'static str {
        match self { Self::Planted => "fresh_planted_sat_48",
                     Self::Boundary => "fresh_uniform_boundary_48",
                     Self::Unsat => "fresh_embedded_unsat_56" }
    }
}

fn random(state: &mut u32) -> u32 {
    *state ^= *state << 13;
    *state ^= *state >> 17;
    *state ^= *state << 5;
    *state
}

fn random_clause(state: &mut u32) -> Vec<i32> {
    let mut literals = Vec::with_capacity(3);
    let mut seen = [false; N];
    while literals.len() < 3 {
        let variable = random(state) as usize % N;
        if seen[variable] { continue; }
        seen[variable] = true;
        let negative = random(state) & 1 != 0;
        let literal = variable as i32 + 1;
        literals.push(if negative { -literal } else { literal });
    }
    literals
}

fn source(family: Family, index: usize) -> Vec<Vec<i32>> {
    let mut state = family.seed() ^ (index as u32 + 1).wrapping_mul(STEP);
    let target = if family == Family::Unsat {56} else {48};
    let mut clauses = Vec::with_capacity(target);
    if family == Family::Unsat {
        for signs in 0..8 {
            clauses.push((0..3).map(|position| {
                let lit = position + 1;
                if signs & (1 << position) != 0 {-lit} else {lit}
            }).collect());
        }
    }
    while clauses.len() < target {
        let clause = random_clause(&mut state);
        if family == Family::Planted && clause.iter().all(|&lit| lit > 0) {
            continue;
        }
        clauses.push(clause);
    }
    clauses
}

fn covariance_matrix(clauses: &[Vec<i32>]) -> Vec<Vec<i32>> {
    let m = clauses.len();
    let mut k = vec![vec![0i32; m]; m];
    for i in 0..m {
        k[i][i] = 7;
        for j in (i+1)..m {
            let (mut overlap, mut conflict) = (0u32, false);
            for &a in &clauses[i] {
                for &b in &clauses[j] {
                    if a.unsigned_abs() == b.unsigned_abs() {
                        overlap += 1;
                        if (a > 0) != (b > 0) {conflict = true;}
                    }
                }
            }
            let value = if conflict {-1} else {(1i32 << overlap) - 1};
            k[i][j] = value;
            k[j][i] = value;
        }
    }
    k
}

#[derive(Clone, Debug, PartialEq, Eq)]
struct Geometry {
    negative_pairs: usize,
    positive_mass: i64,
    negative_mass: i64,
    signed_mass: i64,
    negative_triangle_mass: i64,
    positive_triangle_mass: i64,
}

fn geometry(k: &[Vec<i32>]) -> Geometry {
    let mut result = Geometry {negative_pairs:0,positive_mass:0,negative_mass:0,
        signed_mass:0,negative_triangle_mass:0,positive_triangle_mass:0};
    for i in 0..k.len() {
        for j in (i+1)..k.len() {
            let v = i64::from(k[i][j]);
            if v < 0 {result.negative_pairs+=1;result.negative_mass-=v;}
            else {result.positive_mass+=v;}
            for h in (j+1)..k.len() {
                let cycle = v*i64::from(k[j][h])*i64::from(k[h][i]);
                if cycle < 0 {result.negative_triangle_mass-=cycle;}
                else {result.positive_triangle_mass+=cycle;}
            }
        }
    }
    result.signed_mass = result.positive_mass - result.negative_mass;
    result
}

fn energy_truth(clauses: &[Vec<i32>]) -> (u32, i128, i128) {
    let (mut models, mut sum, mut sum_squares) = (0u32,0i128,0i128);
    for assignment in 0..(1usize << N) {
        let energy = clauses.iter().filter(|clause| {
            !clause.iter().any(|&lit| {
                let bit = assignment & (1usize << (lit.unsigned_abs() as usize-1)) != 0;
                bit == (lit > 0)
            })
        }).count() as i128;
        if energy == 0 {models+=1;}
        sum += energy;
        sum_squares += energy * energy;
    }
    (models,sum,sum_squares)
}

#[derive(Debug, Clone, PartialEq, Eq)]
struct Cost {nodes:u32,clause_scans:u32,sat:bool}

fn dpll(clauses: &[Vec<i32>]) -> Cost {
    let mut degree = [0usize; N];
    for clause in clauses {
        for &lit in clause {degree[lit.unsigned_abs() as usize-1]+=1;}
    }
    let mut order: [usize;N] = std::array::from_fn(|i|i);
    order.sort_by(|&a,&b|degree[b].cmp(&degree[a]).then(a.cmp(&b)));
    fn visit(clauses:&[Vec<i32>], order:&[usize;N], mut assign:[i8;N], count:&mut Cost)->bool {
        count.nodes+=1;
        loop {
            let mut changed=false;
            for clause in clauses {
                count.clause_scans+=1;
                let (mut free,mut last,mut satisfied)=(0usize,0i32,false);
                for &lit in clause {
                    let value=assign[lit.unsigned_abs() as usize-1];
                    if value<0 {free+=1;last=lit;}
                    else if (value==1)==(lit>0) {satisfied=true;break;}
                }
                if satisfied {continue;}
                if free==0 {return false;}
                if free==1 {
                    assign[last.unsigned_abs() as usize-1]=if last>0 {1} else {0};
                    changed=true;
                }
            }
            if !changed {break;}
        }
        let mut all_satisfied=true;
        for clause in clauses {
            count.clause_scans+=1;
            if !clause.iter().any(|&lit| {
                let value=assign[lit.unsigned_abs() as usize-1];
                value>=0 && (value==1)==(lit>0)
            }) {all_satisfied=false;break;}
        }
        if all_satisfied {return true;}
        let branch=*order.iter().find(|&&i|assign[i]<0)
            .expect("unresolved clause has a free variable");
        let mut left=assign;
        left[branch]=0;
        if visit(clauses,order,left,count) {return true;}
        assign[branch]=1;
        visit(clauses,order,assign,count)
    }
    let mut count=Cost{nodes:0,clause_scans:0,sat:false};
    let sat=visit(clauses,&order,[-1;N],&mut count);
    count.sat=sat;
    count
}

// A gauge flip complements one Boolean source variable and every occurrence
// of it. This is an assignment bijection and preserves all exact statistics.
fn gauge_flip(source:&[Vec<i32>],variable:usize)->Vec<Vec<i32>> {
    source.iter().map(|clause|clause.iter().map(|&lit| {
        if lit.unsigned_abs() as usize==variable+1 {-lit} else {lit}
    }).collect()).collect()
}

fn pearson(xs:&[f64],ys:&[f64])->Option<f64> {
    let n=xs.len() as f64;
    let mx=xs.iter().sum::<f64>()/n;
    let my=ys.iter().sum::<f64>()/n;
    let mut numerator=0f64;
    let (mut xx,mut yy)=(0f64,0f64);
    for (&x,&y) in xs.iter().zip(ys) {
        numerator+=(x-mx)*(y-my);
        xx+=(x-mx).powi(2);
        yy+=(y-my).powi(2);
    }
    if xx==0.0 || yy==0.0 {None} else {Some(numerator/(xx*yy).sqrt())}
}

struct Case {index:usize, clauses:Vec<Vec<i32>>, cov:Vec<Vec<i32>>,
             geo:Geometry, models:u32, cost:Cost, scaled_variance:i64}

fn prepare(family:Family,index:usize)->Result<Case,String> {
    let clauses=source(family,index);
    let cov=covariance_matrix(&clauses);
    let geo=geometry(&cov);
    let (models,sum,sum_sq)=energy_truth(&clauses);
    let total=1i128<<N;
    let scaled_var=7i128*clauses.len() as i128+2i128*geo.signed_mass as i128;
    if 64i128*(total*sum_sq-sum*sum)!=scaled_var*total*total {
        return Err(format!("W017 variance mismatch {} {}",family.name(),index));
    }
    if sum*8!=total*clauses.len() as i128 {
        return Err(format!("W017 violation mean mismatch {} {}",family.name(),index));
    }
    let cost=dpll(&clauses);
    if cost.sat!=(models>0) {return Err("W017 DPLL/truth mismatch".into());}
    if (family==Family::Planted && models==0)||(family==Family::Unsat && models>0) {
        return Err("W017 frozen source-family class mismatch".into());
    }
    if [0,1,31].contains(&index) {
        for variable in 0..N {
            let flipped=gauge_flip(&clauses,variable);
            if covariance_matrix(&flipped)!=cov || geometry(&covariance_matrix(&flipped))!=geo {
                return Err("W017 gauge covariance mismatch".into());
            }
        }
    }
    let scaled_variance=i64::try_from(scaled_var).map_err(|_|"variance overflow")?;
    Ok(Case{index,clauses,cov,geo,models,cost,scaled_variance})
}

fn family_report(family:Family)->Result<Value,String> {
    let cases=(0..CASES).map(|index|prepare(family,index))
        .collect::<Result<Vec<_>,_>>()?;
    let targets=cases.iter().map(|c|f64::from(c.cost.clause_scans)).collect::<Vec<_>>();
    let pairs=cases.iter().map(|c|c.geo.negative_pairs as f64).collect::<Vec<_>>();
    let signed=cases.iter().map(|c|c.geo.signed_mass as f64).collect::<Vec<_>>();
    let triangles=cases.iter().map(|c|c.geo.negative_triangle_mass as f64).collect::<Vec<_>>();
    let controls=cases.iter().filter(|c|[0,1,31].contains(&c.index)).map(|c| {
        json!({"index":c.index,"source":&c.clauses,
            "covariance_top_left_8":c.cov.iter().take(8)
                .map(|row|row.iter().take(8).copied().collect::<Vec<_>>())
                .collect::<Vec<_>>(),
            "geometry":{"negative_pairs":c.geo.negative_pairs,
                "positive_mass":c.geo.positive_mass,"negative_mass":c.geo.negative_mass,
                "signed_mass":c.geo.signed_mass,
                "negative_triangle_mass":c.geo.negative_triangle_mass,
                "positive_triangle_mass":c.geo.positive_triangle_mass},
            "models":c.models,"scaled_energy_variance":c.scaled_variance,
            "degree_dpll":{"nodes":c.cost.nodes,
                "clause_scans":c.cost.clause_scans,"sat":c.cost.sat}})
    }).collect::<Vec<_>>();
    Ok(json!({"graph_family":family.name(),"formulas":cases.len(),
        "sat_count":cases.iter().filter(|c|c.models>0).count(),
        "unsat_count":cases.iter().filter(|c|c.models==0).count(),
        "mean_degree_dpll_clause_scans":targets.iter().sum::<f64>()/CASES as f64,
        "mean_negative_pairs":pairs.iter().sum::<f64>()/CASES as f64,
        "mean_signed_covariance_mass":signed.iter().sum::<f64>()/CASES as f64,
        "mean_negative_triangle_mass":triangles.iter().sum::<f64>()/CASES as f64,
        "correlation_scans_with_negative_pairs":pearson(&pairs,&targets),
        "correlation_scans_with_signed_mass":pearson(&signed,&targets),
        "correlation_scans_with_negative_triangle_mass":pearson(&triangles,&targets),
        "controls":controls}))
}

pub fn audit()->Result<Value,String> {
    let p=family_report(Family::Planted)?;
    let b=family_report(Family::Boundary)?;
    let u=family_report(Family::Unsat)?;
    Ok(json!({"research_id":"W-CROSSDOMAIN-017",
        "scope":"prospective signed clause covariance geometry; not solver speedup",
        "identity":"64*Var(total violations)=7*m+2*sum_{c<d} K_cd",
        "families":[p,b,u]}))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn exact_covariance_geometry_variance_and_gauge() {
        for family in [Family::Planted,Family::Boundary,Family::Unsat] {
            for index in [0,1,31] {
                let c=prepare(family,index).unwrap();
                assert!(c.scaled_variance>=0);
                assert_eq!(c.cov.len(),c.clauses.len());
                for i in 0..c.cov.len() {
                    assert_eq!(c.cov[i][i],7);
                    for j in 0..c.cov.len() {assert_eq!(c.cov[i][j],c.cov[j][i]);}
                }
                assert_eq!(c.cost.sat,c.models>0);
            }
        }
    }
}
