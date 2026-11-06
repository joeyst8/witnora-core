"""W036 deterministic prefix-only signed-incidence neighborhood selector.

All selections reference indices of original source clauses. No derived
constraints or approximate model statements are introduced. The caller is
responsible for verifying any UNSAT proof using those source clauses.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path


def read_prefix(path: str | Path, clause_limit: int) -> dict:
    """Parse at most clause_limit complete original source clauses.

    Does not seek or read later lines. Records byte reads including a possible
    partially consumed final line, making physical I/O visible.
    """
    if clause_limit <= 0:
        raise ValueError("prefix budget must be positive")
    clauses=[]
    pending=[]
    variables=None
    declared=None
    bytes_read=0
    with Path(path).open('rb') as source:
        for raw_line in source:
            bytes_read+=len(raw_line)
            line=raw_line.strip()
            if not line or line.startswith(b'c'):
                continue
            tokens=line.split()
            if tokens[0]==b'p':
                if variables is not None or len(tokens)!=4 or tokens[1]!=b'cnf':
                    raise ValueError('invalid or duplicate DIMACS header')
                variables=int(tokens[2]);declared=int(tokens[3])
                if variables<0 or declared<0:
                    raise ValueError('negative DIMACS size')
                continue
            if variables is None:
                raise ValueError('clause before DIMACS header')
            for token in tokens:
                lit=int(token)
                if lit==0:
                    clauses.append(tuple(pending));pending=[]
                    if len(clauses)==min(clause_limit,declared):
                        return {'variables':variables,'declared_clauses':declared,
                                'read_clauses':len(clauses),'read_bytes':bytes_read,
                                'clauses':clauses,'last_line_completed':True}
                else:
                    if abs(lit)>variables:
                        raise ValueError('out-of-universe source literal')
                    pending.append(lit)
    if pending or variables is None or len(clauses)!=declared:
        raise ValueError('truncated input before declared number of clauses')
    return {'variables':variables,'declared_clauses':declared,
            'read_clauses':len(clauses),'read_bytes':bytes_read,
            'clauses':clauses,'last_line_completed':True}


def neighborhoods(prefix: dict, max_anchors: int = 3,
                  max_clauses: int = 64) -> list[dict]:
    """Three ranked deterministic local hypergraph neighborhoods at most.

    Rank anchors by min(positive,negative) incidence, then total incidence.
    Collect its source clauses first, with sign-balanced round robin, then
    fill from immediate variable-sharing clauses in source order.
    """
    if max_anchors<1 or max_clauses<1:
        raise ValueError('invalid neighborhood budget')
    clauses=prefix['clauses']
    incidence=defaultdict(list)
    pos=defaultdict(int);neg=defaultdict(int)
    for i,clause in enumerate(clauses):
        signs={}
        for lit in clause:
            variable=abs(lit)
            signs.setdefault(variable,set()).add(lit>0)
        for variable,polarities in signs.items():
            incidence[variable].append(i)
            if True in polarities: pos[variable]+=1
            if False in polarities: neg[variable]+=1
    anchors=sorted((v for v in incidence if pos[v] and neg[v]),
                   key=lambda v:(-min(pos[v],neg[v]),-(pos[v]+neg[v]),v))[:max_anchors]
    result=[]
    for anchor in anchors:
        positives=[idx for idx in incidence[anchor] if anchor in clauses[idx]]
        negatives=[idx for idx in incidence[anchor] if -anchor in clauses[idx]]
        ordered=[]
        for k in range(max(len(positives),len(negatives))):
            if k<len(positives): ordered.append(positives[k])
            if k<len(negatives): ordered.append(negatives[k])
        selected=[];seen=set()
        for idx in ordered:
            if idx not in seen:
                seen.add(idx);selected.append(idx)
            if len(selected)>=max_clauses: break
        # One graph hop beyond the anchor-star; chosen by earliest source
        # position. No part of the unobserved source is consulted.
        if len(selected)<max_clauses:
            linked={abs(lit) for idx in selected for lit in clauses[idx]}
            for idx,clause in enumerate(clauses):
                if idx not in seen and any(abs(lit) in linked for lit in clause):
                    seen.add(idx);selected.append(idx)
                    if len(selected)>=max_clauses: break
        chosen=sorted(selected)
        result.append({'anchor':anchor,'source_indices':chosen,
                       'clauses':[list(clauses[i]) for i in chosen],
                       'variables':prefix['variables']})
    return result


def unit_propagation_contradiction(clauses: list[list[int]]) -> bool:
    """Simple exact root-level unit propagation sufficient UNSAT check."""
    assignment={}
    while True:
        updates=[]
        for clause in clauses:
            if any(abs(lit) in assignment and assignment[abs(lit)]==(lit>0)
                   for lit in clause):
                continue
            open_lits=[lit for lit in clause if abs(lit) not in assignment]
            if not open_lits:
                return True
            if len(open_lits)==1:
                updates.append(open_lits[0])
        changed=False
        for lit in updates:
            variable=abs(lit);value=lit>0
            if variable in assignment and assignment[variable]!=value:
                return True
            if variable not in assignment:
                assignment[variable]=value;changed=True
        if not changed:
            return False


def bounded_dpll(clauses: list[list[int]], max_nodes: int = 128,
                 max_clause_scans: int = 16000) -> dict:
    """Exact source-only DPLL, returning UNKNOWN if the budget is exhausted.

    An UNSAT result means every branch was closed before the budget. A SAT
    result is deliberately scoped to the *selected subformula* only.
    """
    if max_nodes<1 or max_clause_scans<1:
        raise ValueError('invalid DPLL budget')
    counters={'nodes':0,'clause_scans':0}

    def recurse(partial):
        counters['nodes']+=1
        if counters['nodes']>max_nodes:
            return 'UNKNOWN_BUDGET'
        while True:
            units=[];first_open=None;all_satisfied=True
            for clause in clauses:
                counters['clause_scans']+=1
                if counters['clause_scans']>max_clause_scans:
                    return 'UNKNOWN_BUDGET'
                remaining=[];satisfied=False
                for literal in clause:
                    assigned=partial.get(abs(literal))
                    if assigned is None:
                        remaining.append(literal)
                    elif assigned==(literal>0):
                        satisfied=True;break
                if satisfied:continue
                all_satisfied=False
                if not remaining:return 'UNSAT_CERTIFIED'
                if first_open is None:first_open=remaining[0]
                if len(remaining)==1:units.append(remaining[0])
            if all_satisfied:return 'SAT_SUBFORMULA'
            if not units:break
            changed=False
            for lit in units:
                idx=abs(lit);value=lit>0
                if idx in partial and partial[idx]!=value:
                    return 'UNSAT_CERTIFIED'
                if idx not in partial:
                    partial[idx]=value;changed=True
            if not changed:raise RuntimeError('bounded DPLL stalled')
        variable=abs(first_open)
        for value in (True,False):
            next_assignment=dict(partial)
            next_assignment[variable]=value
            outcome=recurse(next_assignment)
            if outcome=='SAT_SUBFORMULA':return outcome
            if outcome=='UNKNOWN_BUDGET':return outcome
        return 'UNSAT_CERTIFIED'

    return {'status':recurse({}), **counters}
