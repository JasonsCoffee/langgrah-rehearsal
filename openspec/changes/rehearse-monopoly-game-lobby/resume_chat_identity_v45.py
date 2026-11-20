"""Reconcile settled, wholly unadmitted identity responses at one exact stop."""
from hashlib import sha256
import json
from operational_transport import retained_run_reservations
from unity_coder.core.storage import atomic_write
from unity_coder.core.workspaces import git

def reconcile(state,contract,budget,services,integration,settings,workers):
    run=state/'.agent/runs/monopoly-game-lobby'
    result=json.loads((run/'result.json').read_bytes())
    transaction=services.effects.read('transaction')
    if (contract.contract_version!=45
        or contract.sha256!='68275e43607b06d92165a1c536d6e978f2af3465a1a5c282bb867da24832862e'
        or result['outcome']!='operational'
        or result['candidate_revision']!='3dbeead885fe94f94e2a74e23460b3f5376c25f9'
        or git(integration,'rev-parse','HEAD').decode().strip()!=result['candidate_revision']
        or git(integration,'status','--porcelain') or services.tdd.frozen
        or not transaction['complete'] or transaction['operation']!='v45-step5-prepare'
        or settings.coder.model!='deepseek/deepseek-v4.1-flash'
        or settings.judge.model!='openai/gpt-6.1-sol'):
        raise ValueError('Exact settled identity-response stop changed')
    ledger=budget._read();retained_run_reservations(state,ledger)
    unit=next(u for u in contract.units if u.id=='TEST-CHAT')
    sources={p:(integration/p).read_bytes() for p in unit.owns if p.endswith('.cs')}
    receipts=[]
    for suffix,digest in (
        ('','a1f785747dcf93181beac684b095d16473e2bf3ef79e93c795da418e17131402'),
        ('-required-csharp','685a06d939c85c6b31831bad0aa6592d525cb56261a2bd123169b779f0e366a1')):
        call='v45-step5-prepare-TEST-CHAT-TEST-CHAT'+suffix
        raw=(run/'model-calls'/(sha256(call.encode()).hexdigest()+'.json')).read_bytes()
        if sha256(raw).hexdigest()!=digest:raise ValueError('Settled response changed')
        reply=json.loads(raw)['reply'];patch=json.loads(reply['text'])
        if ledger['calls'][call]['actual']!=[reply['input_tokens'],reply['output_tokens']]:
            raise ValueError('Settled charge changed')
        if not set(patch['files']).issubset(unit.owns):raise ValueError('Unexpected ownership')
        if any(p not in patch['files'] or patch['files'][p].encode()!=body for p,body in sources.items()):
            raise ValueError('Expected entirely unchanged C# response')
        receipts.append({'call_id':call,'sha256':digest})
    if services.tdd.state(unit.id).preparation_attempts!=2:
        raise ValueError('Preparation count changed')
    expected={'format_version':1,'model':'deepseek/deepseek-v4.1-flash',
        'stage':'test_authoring','owned_csharp_path':'Tests/Runtime/Script/LobbyRehearsal/LobbySocialChatTests.cs',
        'effort':'low','explicit_effort_precedence':True}
    if json.loads((state/'author-chat-effort-policy.json').read_bytes())!=expected:
        raise ValueError('Approved scoped policy not active')
    workers.authoring_clarifications={unit.id:'\nEXACT RECONCILIATION: Your two last paid responses copied the entire failing C# byte-for-byte while the reason claimed repairs. Neither was applied. Write the actual changed C# now. Updating notes or a reason is not a repair. All five selected named test bodies must exercise the stated clauses, including the visible self avatar override, arranged successful messages with cooldown advancement, independent channel scroll positions, multi-peer unread decrement, real expansion clicks, measured row geometry and two-click A-to-B friend requests. Tests against nonfunctional stubs are required and expected to fail; implement assertions, never business results. Preserve read-only peer helpers and all mapped tests. Sol will independently inspect the actual code.'}
    atomic_write(state,'recovery-authorizations/v45-chat-identity-reconciled.json',json.dumps({
        'candidate':result['candidate_revision'],'contract_sha256':contract.sha256,
        'settled_calls':receipts,'usage':budget.totals(),'preparation_attempts':2,
        'source_sha256':{p:sha256(b).hexdigest() for p,b in sources.items()},
        'human_accepted':False,'effect':'No response admitted; public resume with all charges retained and actual Sol review required'},indent=2).encode())
    return True
