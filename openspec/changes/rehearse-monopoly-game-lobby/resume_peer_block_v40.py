"""Retain rejected peer edits and route real source failure to native rework."""
from hashlib import sha256
import json
from operational_transport import retained_run_reservations
from unity_coder.core.storage import atomic_write
from unity_coder.core.workspaces import git


def reconcile(state,contract,budget,services,integration,settings,workers):
    run=state/'.agent/runs/monopoly-game-lobby'
    result=json.loads((run/'result.json').read_bytes());tx=services.effects.read('transaction')
    if (contract.contract_version!=40 or contract.sha256!='a0289951700127c2c1ac42cd1235f3dbf3359f7e7407c533025dba7c913ea15c'
        or result['outcome']!='operational' or result['candidate_revision']!='7821b1ce2a50362f87a0be7aaaddc3656e6d6dac'
        or git(integration,'rev-parse','HEAD').decode().strip()!=result['candidate_revision']
        or git(integration,'status','--porcelain') or services.tdd.frozen
        or not tx['complete'] or tx['operation']!='v40-step5-prepare'
        or services.tdd.state('TEST-SOCIAL').preparation_attempts!=1
        or settings.coder.model!='deepseek/deepseek-v4.1-flash' or settings.judge.model!='openai/gpt-6.1-sol'):
        raise ValueError('Peer-block recovery identity changed')
    ledger=budget._read();retained_run_reservations(state,ledger)
    peer='Tests/Runtime/Script/LobbyRehearsal/LobbyChatMessageTests.cs'
    owner=next(u for u in contract.units if peer in u.owns)
    if owner.id!='TEST-CHAT-MSG':raise ValueError('Peer ownership changed')
    receipts=[]
    operation='v40-step5-prepare-TEST-SOCIAL-TEST-SOCIAL'
    for suffix,digest in (('','27caa889f8846352fed310169d101f0f9d2cb2c0f00040d5e827b01505ad0dc1'),('-anchor-format-1','7b875fcbe1cb220ff60dff918a47b2fef925731089ab28f16b91dd46fe311b69')):
        call=operation+suffix;raw=(run/'model-calls'/(sha256(call.encode()).hexdigest()+'.json')).read_bytes()
        if sha256(raw).hexdigest()!=digest:raise ValueError('Rejected response changed')
        reply=json.loads(raw)['reply'];patch=json.loads(reply['text'])
        if ledger['calls'][call].get('actual')!=[reply['input_tokens'],reply['output_tokens']]:raise ValueError('Charge changed')
        if len(patch['edits'])!=1 or patch['edits'][0]['path']!=peer:raise ValueError('Unexpected rejected source')
        receipts.append({'call_id':call,'sha256':digest})
    if (state/('anchored-author/'+operation+'.complete.json')).exists():raise ValueError('Unexpected patch admission')
    reviews=[]
    for path in (run/'model-calls').glob('*.json'):
        record=json.loads(path.read_bytes());identity=record['identity']
        if identity['unit_id']=='TEST-SOCIAL' and identity['role']=='judge' and identity['call_id'].startswith('v40-') and 'reply' in record:
            decision=json.loads(record['reply']['text'])
            if decision.get('valid') is False and 'ChatFocusInput' in decision.get('explanation',''):reviews.append(sha256(path.read_bytes()).hexdigest())
    if not reviews:raise ValueError('Actual independent peer compilation finding required')
    workers.blocked_author_notes={'TEST-SOCIAL'}
    atomic_write(state,'recovery-authorizations/v40-readonly-peer-block.json',json.dumps({
        'candidate':result['candidate_revision'],'contract_sha256':contract.sha256,'usage':budget.totals(),
        'rejected_paid_calls':receipts,'actual_judge_findings':reviews,'peer_owner':owner.id,
        'route':'Coder may document only the real owned-unit blocker; C# is unchanged, actual Sol review remains required, native preparation failures escalate normally',
        'human_accepted':False},indent=2).encode())
    return True
