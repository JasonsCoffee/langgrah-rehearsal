"""Persistent first-ten review observation and one canonical low-effort audit."""
from __future__ import annotations
from collections.abc import Callable
from dataclasses import asdict
import json
from pathlib import Path
from evidence_packet import Packet,canonical
from evidence_context_guard import OptimizationResult
from unity_coder.core.ai_models import ModelError
from unity_coder.core.storage import atomic_write,file_guard


def packet_class(mode: str,mechanical: dict) -> str:
    gate=str(mechanical.get('gate','source'))
    if mode=='defect' and gate=='tests' and mechanical.get('behavioral') is False:gate='mixed'
    return mode+':'+gate


class LiveReviewAudit:
    ref='context-optimization/live-audit.json'

    def __init__(self,state: Path) -> None:
        self.state=state

    def read(self) -> dict:
        path=self.state/self.ref
        return json.loads(path.read_bytes()) if path.exists() else {'reviews':[],'disabled_classes':[]}

    def selection_allowed(self,category: str,*,audit_fits: bool) -> bool:
        value=self.read()
        return category not in value['disabled_classes'] and (any(
            row.get('audit',{}).get('routing_agrees') is True for row in value['reviews']) or audit_fits)

    def observe(self,operation: str,category: str,packet: Packet,result: OptimizationResult,
                decision: dict,shadow: Callable[[],dict] | None,*,force_audit: bool=False) -> dict:
        with file_guard(self.state,self.ref+'.guard'):
            value=self.read()
            if any(row.get('audit',{}).get('state')=='intent' for row in value['reviews']):
                raise ModelError('Canonical shadow intent requires reconciliation; no replay')
            previous=next((r for r in value['reviews'] if r['operation']==operation),None)
            if previous:
                if previous['canonical_sha256']!=packet.canonical_sha256 or previous['decision']!=decision:
                    raise ModelError('Live review identity changed')
                return decision
            row={'operation':operation,'class':category,'canonical_sha256':packet.canonical_sha256,
                'optimized_sha256':result.optimized_sha256,'check_results':list(result.check_results),
                'canonical_bytes':len(packet.canonical_input.encode()),
                'delivered_bytes':len((result.optimized_input or '').encode()),'decision':decision}
            pending=not any(r.get('audit',{}).get('routing_agrees') is True for r in value['reviews'])
            if len(value['reviews'])<10 or pending:
                value['reviews'].append(row)
            if (pending or force_audit) and shadow is not None:
                row['audit']={'state':'intent'}
                atomic_write(self.state,self.ref,canonical(value).encode())
                compared=shadow() # All paid accounting stays in caller's native ModelCalls.
                key='defect_class' if 'defect_class' in decision else 'valid'
                agrees=key in compared and compared[key]==decision[key]
                row['audit']={'state':'complete','decision':compared,'routing_agrees':agrees}
                if not agrees and category not in value['disabled_classes']:value['disabled_classes'].append(category)
                atomic_write(self.state,self.ref,canonical(value).encode())
                if not agrees:raise ModelError('Canonical and optimized Judge routing disagree; class disabled')
            else:
                row['audit']={'state':'not_scheduled' if not pending else 'pending_budget'}
                atomic_write(self.state,self.ref,canonical(value).encode())
            return decision
