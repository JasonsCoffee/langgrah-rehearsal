"""Reconcile complete paid model output by dropping proven identity edits only."""
from hashlib import sha256
import json
from pathlib import Path
from anchored_author import parse_anchored_patch
from noop_transport import normalize_identity_edits
from operational_transport import retained_run_reservations
from unity_coder.adapters.unity import UnityAdapter
from unity_coder.core.storage import atomic_write
from unity_coder.core.workspaces import git


def reconcile(state,contract,budget,services,integration,settings,workers):
    run=state/'.agent/runs/monopoly-game-lobby';result=json.loads((run/'result.json').read_bytes())
    transaction=services.effects.read('transaction')
    if (contract.contract_version!=29 or contract.sha256!='bd3a914c6d189ae3ba2d3c12ea9827d9918bf876fe9e01b780bc8d19406a3e4e'
        or result['outcome']!='operational' or result['candidate_revision']!='eff5fb3af1ecde9e8d8bd861de62b6d68bdcb1af'
        or git(integration,'rev-parse','HEAD').decode().strip()!=result['candidate_revision']
        or git(integration,'status','--porcelain') or services.tdd.frozen
        or not transaction['complete'] or transaction['operation']!='v29-step13-prepare'
        or settings.judge.model!='openai/gpt-6.1-sol' or settings.coder.model!='deepseek/deepseek-v4.1-flash'):
        raise ValueError('Identity-edit recovery identity changed')
    unit=next(u for u in contract.units if u.id=='TEST-SOCIAL')
    if services.tdd.state(unit.id).preparation_attempts!=2:raise ValueError('Preparation counter changed')
    sources={p:(integration/p).read_bytes().decode('utf-8') for p in unit.owns if p.endswith('.cs')}
    source_hashes={p:sha256(v.encode()).hexdigest() for p,v in sources.items()}
    ledger=budget._read();retained=retained_run_reservations(state,ledger)
    operation='v29-step13-prepare-TEST-SOCIAL-TEST-SOCIAL'
    expected={operation:'0d2903f5338ce4a0b75dc947a9a9fc773fa26d24d4142529cf830decb78326a1',
        operation+'-anchor-format-1':'20ba2175be8c741da0ee49d4880992e13a32ab2c710c85484891905de8e9dc0e'}
    if (state/('anchored-author/'+operation+'.complete.json')).exists():raise ValueError('Raw failed response has admission proof')
    for call_id,digest in expected.items():
        raw=(run/'model-calls'/(sha256(call_id.encode()).hexdigest()+'.json')).read_bytes();record=json.loads(raw);reply=record['reply']
        if sha256(raw).hexdigest()!=digest or ledger['calls'][call_id].get('actual')!=[reply['input_tokens'],reply['output_tokens']]:raise ValueError('Settled model response changed')
        try:parse_anchored_patch(reply['text'],unit.owns,sources)
        except ValueError as error:
            if str(error)!='Anchor is absent, ambiguous or unchanged':raise
        else:raise ValueError('Raw response was already admissible')
    canonical,removed=normalize_identity_edits(reply['text'],sources)
    files,reason=parse_anchored_patch(canonical,unit.owns,sources)
    if (not removed or not any(p.endswith('.cs') and files[p]!=(integration/p).read_bytes() for p in files)
        or any(not (integration/p).exists() and p not in files for p in unit.owns)
        or UnityAdapter().parse_check({p:v for p,v in files.items() if p.endswith('.cs')})):
        raise ValueError('Canonical patch is absent, incomplete or invalid')
    next_operation='v29-step14-prepare-TEST-SOCIAL-TEST-SOCIAL'
    workers.reconciled_worker_patch={'unit':unit.id,'operation':next_operation,
        'source_sha256':source_hashes,'files':files,'reason':reason+'; exact identity edits mechanically omitted from settled '+call_id}
    proof={'contract_sha256':contract.sha256,'unit':unit.id,'operation':next_operation,
        'source_sha256':source_hashes,'actual_calls':[call_id],'reconciled_from_operation':operation,
        'canonical_transport_sha256':sha256(canonical.encode()).hexdigest(),'identity_replacements_removed':removed,
        'file_sha256':{p:sha256(v).hexdigest() for p,v in files.items()},'human_accepted':False}
    atomic_write(state,'anchored-author/'+next_operation+'.complete.json',json.dumps(proof,indent=2).encode())
    atomic_write(state,'recovery-authorizations/v29-exact-identity-edit-removal.json',json.dumps(proof|{
        'settled_receipts':expected,'usage':budget.totals(),'retained_uncertain':retained,
        'config_sha256':sha256(Path('ai.local.toml').read_bytes()).hexdigest(),
        'normalizer_sha256':sha256(Path(__file__).with_name('noop_transport.py').read_bytes()).hexdigest(),
        'strict_parser_sha256':sha256(Path(__file__).with_name('anchored_author.py').read_bytes()).hexdigest()},indent=2).encode())
    return True
