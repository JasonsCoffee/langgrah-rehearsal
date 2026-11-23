"""Code-verified optimizer result; model claims never authorize delivery."""
from __future__ import annotations
from dataclasses import asdict,dataclass
from hashlib import sha256
from evidence_packet import Packet,assert_packet
from context_packing import pack

REQUIRED_KINDS=frozenset(('patched','test','helper','spec','diagnostic','interface','dependency','binding'))
UNCERTAIN_KINDS=frozenset(('dynamic','reflection','partial_unknown'))


@dataclass(frozen=True)
class OptimizationResult:
    optimized_input: str | None
    check_results: tuple[dict,...]
    decision: str
    canonical_sha256: str
    optimized_sha256: str | None
    included: tuple[str,...]
    omitted: tuple[str,...]
    metrics: dict
    reasons: tuple[str,...]


def mandatory_ids(packet: Packet) -> set[str]:
    assert_packet(packet)
    byid={s.id:s for s in packet.sources}
    if any(s.kind in UNCERTAIN_KINDS for s in packet.sources):return set(byid)
    required=set(packet.required)|{s.id for s in packet.sources if s.kind in REQUIRED_KINDS}
    todo=list(required)
    while todo:
        current=byid[todo.pop()]
        for dep in current.dependencies:
            if dep not in byid:return set(byid)
            if dep not in required:required.add(dep);todo.append(dep)
    return required


def optimize(packet: Packet,selection: dict,*,min_reduction: float=.2,budget_known: bool=True,
             capacity_chars: int | None=None) -> OptimizationResult:
    assert_packet(packet)
    required=mandatory_ids(packet);all_ids={s.id for s in packet.sources}
    checks=[];reasons=[]
    def check(name: str,status: str,detail: str) -> None:
        checks.append({'id':name,'status':status,'verifier':'code_verified','evidence':[packet.canonical_sha256],'reason':detail})
    check('budget','pass' if budget_known else 'unknown','Ledger reconciled' if budget_known else 'Unknown paid usage; reconcile before dispatch')
    chosen={s.id:[[0,len(s.content.encode())]] for s in packet.sources if s.id in required}
    valid=True
    try:
        if set(selection)!={'canonical_sha256','selected'} or selection['canonical_sha256']!=packet.canonical_sha256:
            raise ValueError('Selector schema or canonical identity mismatch')
        if not isinstance(selection['selected'],list):raise ValueError('Selection must be a list')
        used=set();byid={s.id:s for s in packet.sources}
        for item in selection['selected']:
            if not isinstance(item,dict) or set(item)!={'id','sha256','ranges'}:raise ValueError('Unexpected selector fields')
            identity=item['id']
            if not isinstance(identity,str) or identity not in byid or identity in used:raise ValueError('Unknown or duplicate selection')
            source=byid[identity];raw=source.content.encode();ranges=item['ranges'];used.add(identity)
            if item['sha256']!=source.sha256 or not isinstance(ranges,list) or not ranges:raise ValueError('Source hash or range mismatch')
            last=-1
            for span in ranges:
                if (not isinstance(span,list) or len(span)!=2 or any(type(x) is not int for x in span)
                    or not 0<=span[0]<span[1]<=len(raw) or span[0]<last):raise ValueError('Invalid or overlapping span')
                raw[span[0]:span[1]].decode('utf-8');last=span[1]
            # Required bodies always bypass selection; optional dependencies are full.
            if identity not in required:chosen[identity]=ranges
        todo=list(chosen)
        while todo:
            for dep in byid[todo.pop()].dependencies:
                if dep not in byid:raise ValueError('Unresolved optional dependency')
                if dep not in chosen:chosen[dep]=[[0,len(byid[dep].content.encode())]];todo.append(dep)
    except (ValueError,TypeError,KeyError,UnicodeError) as error:
        valid=False;reasons.append(str(error))
    for name in ['completeness','integrity','dependencies','filtering','identity']:
        check(name,'pass' if valid else 'fail','Exact required evidence and validated source references' if valid else reasons[0])
    text=pack(packet,chosen) if valid else packet.canonical_input
    old=len(packet.canonical_input.encode());new=len(text.encode());reduction=1-new/max(1,old)
    worthwhile=valid and (min_reduction==0 or reduction>=min_reduction)
    check('savings','pass' if worthwhile else 'fail','Measured byte reduction; token count remains an estimate')
    if not valid or not worthwhile:text=packet.canonical_input
    decision='use_optimized' if valid and worthwhile else 'use_original'
    if not budget_known:decision='blocked';text=None
    if text is not None and capacity_chars is not None and len(text)>capacity_chars:
        decision='blocked';text=None;reasons.append('Complete required context exceeds configured capacity')
    included=tuple(sorted(chosen if decision=='use_optimized' else all_ids))
    return OptimizationResult(text,tuple(checks),decision,packet.canonical_sha256,
        sha256(text.encode()).hexdigest() if text is not None else None,included,
        tuple(sorted(all_ids-set(included))),{'canonical_bytes':old,'delivered_bytes':len(text.encode()) if text else 0,
            'estimated_canonical_tokens':old,'estimated_delivered_tokens':len(text.encode()) if text else 0,
            'token_estimate':'conservative UTF-8 byte bound, not tokenizer count','byte_reduction':reduction},tuple(reasons))


def validate_delivery(packet: Packet,result: OptimizationResult) -> None:
    assert_packet(packet)
    if (result.canonical_sha256!=packet.canonical_sha256 or result.decision=='blocked'
        or result.optimized_input is None or sha256(result.optimized_input.encode()).hexdigest()!=result.optimized_sha256):
        raise ValueError('Blocked or inconsistent optimizer delivery identity')
    checks={c['id']:c for c in result.check_results}
    required_checks={'completeness','integrity','dependencies','filtering','identity','savings','budget'}
    if not required_checks<=set(checks) or any(c.get('verifier')!='code_verified' for c in result.check_results):
        raise ValueError('Model self-certification cannot authorize delivery')
    if result.decision=='use_original':
        if result.optimized_input!=packet.canonical_input or checks['budget']['status']!='pass':
            raise ValueError('Original fallback must retain exact canonical bytes and known budget')
    elif result.decision=='use_optimized':
        if any(checks[k]['status']!='pass' for k in required_checks):raise ValueError('Required optimization checks did not pass')
        for source in packet.sources:
            if source.id in mandatory_ids(packet) and source.content not in result.optimized_input:
                raise ValueError('Required full source missing at consumer boundary')
    else:raise ValueError('Unknown optimizer decision')
