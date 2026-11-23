"""Compact supporting context while retaining exact original Judge authority."""
from __future__ import annotations
from copy import deepcopy


def finding_index(candidate: str,contract: str,findings: list[dict],budget: list[int],sources: dict[str,str]) -> dict:
    if not candidate or not contract or len(budget)!=2:raise ValueError('Complete handoff identity required')
    unresolved=[deepcopy(item) for item in findings if item.get('resolved') is not True]
    needed=set()
    for finding in unresolved:
        if (finding.get('classification') not in ('implementation','contract') or not finding.get('unit')
            or not isinstance(finding.get('explanation'),str) or not finding['explanation'].strip()):
            raise ValueError('Exact independent finding required')
        needed.update(finding.get('evidence',[]))
    if not needed<=set(sources):raise ValueError('Unresolved handoff has inaccessible evidence references')
    return {'candidate':candidate,'contract':contract,'findings':unresolved,'budget':list(budget),
        'sources':{ref:sources[ref] for ref in sorted(needed)},'authority':'original Judge verdicts; no human approval'}
