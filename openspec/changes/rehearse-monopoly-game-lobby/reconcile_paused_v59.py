"""Reclaim only the verified dead owner's two cycle-59 leases via public API."""
import ctypes,json,os
from pathlib import Path
from hashlib import sha256
from unity_coder.core.lifecycle import RunLease
from unity_coder.core.storage import atomic_write
from unity_coder.core.workspaces import git
from operational_transport import retained_run_reservations
root=Path(os.environ['LOBBY_RUN_ROOT']);state=root/'trusted-state';run=state/'.agent/runs/monopoly-game-lobby'
host=Path(os.environ['UNITY_HOST'])
expected={'version':59,'candidate':'ba564439895c579b588bc8f9a7e471ff1487b09e','contract_source':'architect-v59','contract_sha256':'25344b0fef96e823b862aefc95dcd0365bb75934c90e746eab7f5756da145847'}
if json.loads((state/'current-execution.json').read_bytes())!=expected or (run/'result.json').exists():raise ValueError('Exact paused invocation required')
ledger=json.loads((run/'budget.json').read_bytes());retained_run_reservations(state,ledger)
if any('actual' not in c for k,c in ledger['calls'].items() if k.startswith('v59-')):raise ValueError('Current-cycle paid effect is uncertain')
transaction=json.loads((run/'services-v59/effects/transaction.json').read_bytes())
if transaction['operation']!='v59-step2-prepare' or transaction['complete']:raise ValueError('Paused transaction changed')
worker=json.loads((run/'services-v59/effects/worker-v59-step2-prepare-TEST-CHAT-TEST-CHAT.json').read_bytes())
if 'result' not in worker:raise ValueError('Paid worker result not retained; no replay allowed')
integration=root/'worktrees/monopoly-game-lobby/integration-v59'
if git(integration,'status','--porcelain') or git(integration,'rev-parse','HEAD').decode().strip()!=expected['candidate']:raise ValueError('Paused candidate changed')
kernel=ctypes.WinDLL('kernel32',use_last_error=True)
kernel.OpenProcess.argtypes=[ctypes.c_ulong,ctypes.c_int,ctypes.c_ulong];kernel.OpenProcess.restype=ctypes.c_void_p
kernel.GetExitCodeProcess.argtypes=[ctypes.c_void_p,ctypes.POINTER(ctypes.c_ulong)];kernel.CloseHandle.argtypes=[ctypes.c_void_p]
def alive(owner):
 if owner not in ('lobby-production-81464','lobby-overlay-81464'):return True
 handle=kernel.OpenProcess(0x1000,False,81464)
 if not handle:
  if ctypes.get_last_error()==87:return False
  raise ValueError('Cannot verify recorded owner absence')
 try:
  code=ctypes.c_ulong()
  if not kernel.GetExitCodeProcess(handle,ctypes.byref(code)):raise ValueError('Cannot verify owner exit')
  return code.value==259
 finally:kernel.CloseHandle(handle)
proof=[]
for directory,owner in [(state,'lobby-production-81464'),(host,'lobby-overlay-81464')]:
 saved=json.loads((directory/'.agent/run.lock').read_bytes())
 if saved!={'run_id':'monopoly-game-lobby','owner':owner} or alive(owner):raise ValueError('Only exact dead owner may be reclaimed')
 proof.append(saved)
leases=[]
try:
 for directory,owner in [(state,'lobby-production-81464'),(host,'lobby-overlay-81464')]:
  lease=RunLease(directory,'monopoly-game-lobby','paused-v59-reconcile-'+str(os.getpid()))
  lease.acquire(owner_alive=alive,reclaim_stale=True);leases.append(lease)
 atomic_write(state,'recovery-authorizations/v59-pause-leases-reconciled.json',json.dumps({'contract_sha256':expected['contract_sha256'],'retained_candidate':expected['candidate'],'previous_owners':proof,'verified_process_absent':True,'worker_reply_retained':True,'current_cycle_calls_settled':True,'budget_sha256':sha256((run/'budget.json').read_bytes()).hexdigest(),'models_dispatched':0,'human_accepted':False},indent=2).encode())
 print('Exact dead-owner leases reclaimed; retained worker output and all accounting unchanged')
finally:
 for lease in reversed(leases):lease.release()
