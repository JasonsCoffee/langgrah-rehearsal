"""Explicit exact-call recovery of a settled, wholly unadmitted coder error."""
from hashlib import sha256
import json
from unity_coder.core.storage import atomic_write
from unity_coder.core.workspaces import git
from operational_transport import retained_run_reservations

def reconcile(state,contract,budget,services,integration,settings):
 run=state/'.agent/runs/monopoly-game-lobby';result=json.loads((run/'result.json').read_bytes())
 call='v59-step3-prepare-TEST-CHAT-TEST-CHAT'
 if (contract.contract_version!=59 or contract.sha256!='25344b0fef96e823b862aefc95dcd0365bb75934c90e746eab7f5756da145847'
  or result['outcome']!='operational' or result['candidate_revision']!='65b2b8ebdf0d5d9975faa7cbb8d32798c68a6c40'
  or git(integration,'rev-parse','HEAD').decode().strip()!=result['candidate_revision'] or git(integration,'status','--porcelain')
  or services.tdd.frozen or settings.coder.model!='deepseek/deepseek-v4.1-flash' or settings.judge.model!='openai/gpt-6.1-sol'):
  raise ValueError('Exact settled coder-error recovery required')
 raw=(run/'model-calls'/(sha256(call.encode()).hexdigest()+'.json')).read_bytes();receipt=json.loads(raw)
 ledger=budget._read();retained_run_reservations(state,ledger)
 if (sha256(raw).hexdigest()!='31f75b0fbef6424ed50617b877077c9ed71d4ec106dba86fb81d5f3494e97415'
  or 'reply' in receipt or {k:v for k,v in receipt['failure'].items() if k!='partial_content'}!={'input_tokens':170308,'output_tokens':6599,'finish_reason':'error'}
  or ledger['calls'][call].get('actual')!=[170308,6599]):raise ValueError('Exact fully settled failed receipt changed')
 worker=services.effects.read('worker-'+call);transaction=services.effects.read('transaction')
 if (not worker or 'result' in worker or services.effects.read('apply-'+call) is not None
  or transaction['operation']!='v59-step3-prepare' or not transaction['complete']):raise ValueError('Failure was not wholly unadmitted/completed')
 plan=services.effects.read('code-v59-step3-prepare-TEST-CHAT')
 for path,encoded in plan['snapshots']['TEST-CHAT'].items():
  actual=(integration/path).read_bytes() if (integration/path).is_file() else None
  if actual!=(bytes.fromhex(encoded) if encoded is not None else None):raise ValueError('Author snapshot changed')
 atomic_write(state,'recovery-authorizations/v59-settled-coder-error.json',json.dumps({'failed_call':call,'receipt_sha256':sha256(raw).hexdigest(),'retained_candidate':result['candidate_revision'],'retained_usage':budget.totals(),'partial_applied':False,'same_configured_models':True,'normal_independent_review_required':True,'human_accepted':False},indent=2).encode())
 return True
