"""Fixed size-normalized signed-incidence and exact Fourier features."""

from __future__ import annotations

import math

import numpy as np

from scripts.w033_walsh_bound import walsh_bound


FEATURE_NAMES=('degree_imbalance','pair_overlap','polarity_conflict',
               'walsh_l1_to_mean','signed_interaction_spectral_radius')


def features(nvars: int,clauses: list[list[int]]) -> dict:
    if nvars<1 or not clauses:
        raise ValueError('W037 pilot requires nonempty CNF')
    positive=[0]*nvars
    negative=[0]*nvars
    literals=[]
    interaction=np.zeros((nvars,nvars),dtype=float)
    for clause in clauses:
        if not (1<=len(clause)<=3):
            raise ValueError('pilot supports 1-to-3 clause width only')
        signs={}
        for lit in clause:
            if lit==0 or abs(lit)>nvars:
                raise ValueError('invalid source literal')
            if abs(lit) in signs:
                raise ValueError('source repeats a variable in one clause')
            signs[abs(lit)]=1 if lit>0 else -1
            (positive if lit>0 else negative)[abs(lit)-1]+=1
        literals.append(signs)
        vars_=sorted(signs)
        for i,a in enumerate(vars_):
            for b in vars_[i+1:]:
                signed=signs[a]*signs[b]/len(clauses)
                interaction[a-1,b-1]+=signed
                interaction[b-1,a-1]+=signed
    total_literals=sum(positive)+sum(negative)
    n_pairs=0;shared_sum=0;opposite=0
    for i,a in enumerate(literals):
        for b in literals[i+1:]:
            n_pairs+=1
            common=a.keys() & b.keys()
            if common:
                shared_sum+=len(common)
                opposite+=any(a[v]!=b[v] for v in common)
    overlap_pairs=sum(bool(a.keys()&b.keys()) for i,a in enumerate(literals) for b in literals[i+1:])
    spectral=walsh_bound(nvars,clauses,max_width=3)
    return dict(zip(FEATURE_NAMES,(
        sum(abs(p-n) for p,n in zip(positive,negative))/total_literals,
        shared_sum/(3*n_pairs) if n_pairs else 0.0,
        opposite/overlap_pairs if overlap_pairs else 0.0,
        spectral['nonconstant_l1_numerator']/max(1,spectral['constant_numerator']),
        float(np.max(np.abs(np.linalg.eigvalsh(interaction)))))))
