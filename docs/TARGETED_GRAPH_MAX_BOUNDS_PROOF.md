# Two chromatic maximum equalities — mathematical proof sketch

Status: **mathematical argument recorded; not Lean-kernel verified**.
No claim of novelty or priority; a literature review is still required.

For every finite simple graph \(G\), let \(m\) be its edge count,
\(\tau\) its minimum vertex-cover size, \(\omega\) its clique number,
and \(\chi\) its chromatic number. Adopt \(\chi=\omega=0\) for the
empty graph.

## Main bound

**Claim:** \(\chi(G)\le \max\{\tau(G),\omega(G)\}\).

Choose a minimum vertex cover \(S\) with \(|S|=\tau\). Its complement
\(I=V\setminus S\) is independent.

Color each vertex of \(S\) with a distinct color and color all of
\(I\) with one additional color. Therefore \(\chi\le\tau+1\).

If \(\chi\le\tau\), the claim is immediate. Otherwise
\(\chi=\tau+1\). For a nonempty graph this implies \(\tau\ge1\).

If \(S\) contained two nonadjacent vertices, they could share a color,
the other \(\tau-2\) vertices of \(S\) could receive distinct colors,
and \(I\) could receive one additional color. This would use
\(\tau\) colors, a contradiction. Consequently \(S\) is a clique.

If every \(v\in I\) missed at least one neighbor in \(S\), give each
\(v\) the color of one of its nonneighbors in \(S\). Since \(I\) is
independent, this would be a proper \(\tau\)-coloring, another
contradiction. Thus some \(v\in I\) is adjacent to every vertex of
\(S\). Therefore \(S\cup\{v\}\) is a clique of size \(\tau+1\), so
\(\omega\ge\tau+1=\chi\). This proves the main bound.

The empty graph and edgeless nonempty graphs satisfy the bound directly.

## Corollaries

Since any clique needs distinct colors, \(\omega\le\chi\). The main
bound yields

\[
\max(\tau,\omega)=\max(\tau,\chi).
\]

Choosing one endpoint from each edge gives a vertex cover of size at
most \(m\), hence \(\tau\le m\). Thus
\(\chi\le\max(m,\omega)\) and therefore

\[
\max(m,\omega)=\max(m,\chi).
\]

## Lean formalization obligations

1. Define simple finite graph and exact invariants \(\chi,\omega,\tau,m\).
2. Prove complement of vertex cover is an independent set.
3. Construct the \(\tau+1\) coloring.
4. Prove a nonclique vertex cover yields a \(\tau\)-coloring.
5. Prove absence of a common neighbor from \(I\) yields a \(\tau\)-coloring.
6. Deduce the clique of size \(\tau+1\), the main bound and corollaries.
7. Check a complete formal proof with the Lean kernel, without `sorry`
   or new unproved axioms.

Current Lean status: **NOT_FORMALIZED**. Finite experiments are independent
support only, not substitutes for the proof.
