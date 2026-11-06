"""Precommitted polarity conflict, Walsh energy and frustrated signed triangles."""

from __future__ import annotations

import numpy as np

from scripts.w033_walsh_bound import walsh_bound


FEATURE_NAMES=('polarity_conflict','walsh_l1_to_mean','signed_triangle_frustration')


def interaction_features(nvars,clauses):
    if nvars<1 or not clauses:
        raise ValueError('require positive variable count and nonempty CNF')
    incidence=[]
    signed=np.zeros((nvars,nvars),dtype=float)
    m=len(clauses)
    for clause in clauses:
        if not 1<=len(clause)<=3:
            raise ValueError('require width 1 through 3')
        signs={}
        for lit in clause:
            if not isinstance(lit,int) or lit==0 or abs(lit)>nvars or abs(lit) in signs:
                raise ValueError('invalid or repeated source literal')
            signs[abs(lit)]=1 if lit>0 else -1
        incidence.append(signs)
        variables=sorted(signs)
        for i,a in enumerate(variables):
            for b in variables[i+1:]:
                weight=signs[a]*signs[b]/m
                signed[a-1,b-1]+=weight
                signed[b-1,a-1]+=weight
    overlapping=0
    conflicting=0
    for i,a in enumerate(incidence):
        for b in incidence[i+1:]:
            common=a.keys() & b.keys()
            if common:
                overlapping+=1
                conflicting+=any(a[v]!=b[v] for v in common)
    negative=0.0;total=0.0
    for i in range(nvars):
        for j in range(i+1,nvars):
            if signed[i,j]==0.0:
                continue
            for k in range(j+1,nvars):
                w=signed[i,j]*signed[j,k]*signed[k,i]
                aw=abs(w)
                total+=aw
                if w<0:
                    negative+=aw
    walsh=walsh_bound(nvars,clauses,max_width=3)
    return {'polarity_conflict':conflicting/overlapping if overlapping else 0.0,
            'walsh_l1_to_mean':walsh['nonconstant_l1_numerator']/max(1,walsh['constant_numerator']),
            'signed_triangle_frustration':negative/total if total else 0.0}
