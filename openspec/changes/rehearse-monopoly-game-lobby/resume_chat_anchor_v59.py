"""Exact settled Chat anchor recovery; no peer-owned source is modified."""
from hashlib import sha256
import json
from unity_coder.core.storage import atomic_write
from unity_coder.core.workspaces import git
from operational_transport import retained_run_reservations
from anchored_author import parse_anchored_patch
from noop_transport import normalize_identity_edits

def reconcile(state,contract,budget,services,integration,settings,workers):
 run=state/'.agent/runs/monopoly-game-lobby';result=json.loads((run/'result.json').read_bytes())
 operation='v59-step4-prepare-TEST-CHAT-TEST-CHAT'
 if (contract.contract_version!=59 or contract.sha256!='25344b0fef96e823b862aefc95dcd0365bb75934c90e746eab7f5756da145847'
  or result['outcome']!='operational' or result['candidate_revision']!='65b2b8ebdf0d5d9975faa7cbb8d32798c68a6c40'
  or git(integration,'rev-parse','HEAD').decode().strip()!=result['candidate_revision'] or git(integration,'status','--porcelain')
  or services.tdd.frozen or settings.coder.model!='deepseek/deepseek-v4.1-flash' or settings.judge.model!='openai/gpt-6.1-sol'):
  raise ValueError('Exact Chat anchor recovery required')
 ledger=budget._read();retained_run_reservations(state,ledger)
 transaction=services.effects.read('transaction');worker=services.effects.read('worker-'+operation)
 if (transaction['operation']!='v59-step4-prepare' or not transaction['complete'] or not worker or 'result' in worker
  or services.effects.read('apply-'+operation) is not None or (state/('anchored-author/'+operation+'.complete.json')).exists()):raise ValueError('Expected wholly unadmitted complete formatting stop')
 unit=next(u for u in contract.units if u.id=='TEST-CHAT');sources={p:(integration/p).read_bytes().decode('utf-8') for p in unit.owns if p.endswith('.cs')}
 proof=[];last=''
 for suffix,digest in [('', 'd63d56818f613f6e194321d2b70a42c8e78e0ceba4d999a069926222af17480b'),('-anchor-format-1','f7c6bce674f345b39dbf807ed0ee59963c1d41da7e2ed01037601d6a3e289ca6')]:
  call=operation+suffix;raw=(run/'model-calls'/(sha256(call.encode()).hexdigest()+'.json')).read_bytes();record=json.loads(raw);reply=record.get('reply')
  if sha256(raw).hexdigest()!=digest or not reply or ledger['calls'][call].get('actual')!=[reply['input_tokens'],reply['output_tokens']]:raise ValueError('Settled receipt changed')
  try:parse_anchored_patch(normalize_identity_edits(reply['text'],sources)[0],unit.owns,sources)
  except ValueError as error:
   if 'Anchor is absent' not in str(error):raise
  else:raise ValueError('Expected unadmitted absent anchor')
  last=reply['text'];proof.append({'call':call,'sha256':digest})
 plan=services.effects.read('code-v59-step4-prepare-TEST-CHAT')
 for path,encoded in plan['snapshots']['TEST-CHAT'].items():
  body=(integration/path).read_bytes() if (integration/path).is_file() else None
  if body!=(bytes.fromhex(encoded) if encoded is not None else None):raise ValueError('Author source changed')
 workers.rejected_transport={unit.id:last}
 workers.authoring_clarifications={unit.id:'\nOWNERSHIP DIAGNOSIS: UnreadAppliedObservation is declared in peer-owned LobbyChatStateTests.cs, NOT in your owned LobbySocialChatTests.cs. Its declaration is therefore absent from your anchor source. Do not modify, anchor or shadow that shared helper or any peer file. Add a distinct, uniquely named observer within your OWNED Chat file if needed, using a unique anchor from the supplied actual source, and update only your owned callers. Observe the real Shell.UnreadSnapshotApplied payload for the active synthetic account; record actual delivered values, never fabricate unread data. Preserve the shared helper and other source bytes. Repair both latest Judge findings: an uncapped live unread badge transition with actual snapshot values before extra refresh/navigation, and no forbidden navigation/add effects from already-friend avatar click. Rejected patch text is supplied only as rejected evidence; none was applied. Keep strict source hashes, nonoverlap, all five methods and all effective assertions.'}
 atomic_write(state,'recovery-authorizations/v59-chat-anchor-reconciled.json',json.dumps({'contract_sha256':contract.sha256,'candidate':result['candidate_revision'],'paid_receipts':proof,'usage':budget.totals(),'peer_files_changed':False,'partial_applied':False,'human_accepted':False},indent=2).encode())
 return True
