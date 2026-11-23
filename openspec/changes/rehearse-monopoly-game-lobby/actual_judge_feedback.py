"""Forward genuine independent reasoning omitted by the generic repair summary."""
from __future__ import annotations
from hashlib import sha256
import json
from pathlib import Path
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from unity_coder.core.local_executor import LocalExecutionServices


def validate_finding(request: dict,effect: dict,receipt: dict,sdk: dict,charge: dict,unit: str,*,grant: dict | None=None) -> str:
    request=json.loads(json.dumps(request))
    result=effect.get('result',{});decision=json.loads(receipt.get('reply',{}).get('text','{}'))
    identity=receipt.get('identity',{});reply=receipt.get('reply',{})
    effort=identity.get('effort','')
    if effort!='medium' and (effort!='low' or not grant or grant.get('judge_effort')!='low'
        or grant.get('judge_policy_sha256')!=identity.get('backend_policy_sha256')):
        raise ValueError('Explicit matching low-effort Judge grant required')
    if (effect.get('identity')!={'request':request,'unit':unit}
        or result.get('classification') not in ('implementation','contract')
        or not isinstance(result.get('reason'),str) or not result['reason'].strip()
        or decision!={'defect_class':result['classification'],'explanation':result['reason']}
        or identity.get('model')!='gpt-6.1-sol'
        or identity.get('role')!='judge' or reply.get('model')!='gpt-6.1-sol'
        or sdk.get('text')!=reply.get('text') or sdk.get('policy_sha256')!=identity.get('backend_policy_sha256')
        or charge.get('actual')!=[sdk.get('input_tokens'),sdk.get('output_tokens')]):
        raise ValueError('Matching actual independent Judge finding and settled usage required')
    return '\nACTUAL independent Judge finding for '+unit+' ('+result['classification']+'):\n'+result['reason']+'\nA claim of logical equivalence or an unchanged proposal does not resolve the reported mechanical failure. Repair the actual owned source and retain all frozen tests.'


def feedback(state: Path,services: LocalExecutionServices,unit: str) -> str:
    evidence=services.state.get('verification') or {};request=evidence.get('request',{})
    if evidence.get('status')!='failed' or not request.get('request_id'):return ''
    operation=request['request_id'];effect=services.effects.read('judge-'+operation+'-'+unit)
    if not effect:return ''
    call=operation+'-judge-'+unit;key=sha256(call.encode()).hexdigest()
    verdict=state/'context-verdicts'/(key+'.json')
    if verdict.exists():
        provenance=json.loads(verdict.read_bytes())
        if provenance.get('operation')!=call or provenance.get('candidate')!=request['candidate_revision']:
            raise ValueError('Expanded Judge final-call provenance changed')
        call=provenance['final_call'];key=sha256(call.encode()).hexdigest()
    run=state/'.agent/runs/monopoly-game-lobby'
    receipt=json.loads((run/'model-calls'/(key+'.json')).read_bytes())
    sdk=json.loads((state/'codex-receipts'/(key+'.json')).read_bytes())
    charge=json.loads((run/'budget.json').read_bytes())['calls'][call]
    path=state/'model-authorizations/direct-deepseek-low.json'
    grant=json.loads(path.read_bytes()) if path.exists() else None
    return validate_finding(request,effect,receipt,sdk,charge,unit,grant=grant)
