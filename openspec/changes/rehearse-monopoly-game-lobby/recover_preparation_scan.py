"""Explicit recovery of the identified read-only preparation scan interruption."""
import json
import os
from pathlib import Path
from unity_coder.core.lifecycle import RunLease
from unity_coder.core.storage import atomic_write
from unity_coder.adapters.unity.transport import local_http

host=Path(os.environ['UNITY_HOST']).resolve()
state=Path(os.environ['LOBBY_RUN_ROOT']).resolve()/'trusted-state'
record=json.loads((host/'.agent/run.lock').read_bytes())
if record != {'run_id':'monopoly-game-lobby','owner':'lobby-overlay-40764'}:
    raise ValueError('Unexpected lease; recovery is bound to the identified stopped process')
value=json.loads((state/'host-overlay/overlay.json').read_bytes())
if value['installing'] or value['pending']:
    raise ValueError('Unreconciled editor write; scan recovery cannot proceed')
cap=local_http(49166,'POST','/execute',{'command':'FrameworkVerifyCapabilities'},5)
data=json.loads(cap['data'])
if not data['ready'] or data['active_ticket']:
    raise ValueError('Verification is still active')
lease=RunLease(host,'monopoly-game-lobby','preparation-scan-recovery')
lease.acquire(owner_alive=lambda owner: owner != 'lobby-overlay-40764',reclaim_stale=True)
atomic_write(state,'preparation-scan-recovery.json',json.dumps({'interrupted_owner':record,'candidate':value['candidate'],'reason':'Identified serial full-file scan interrupted after idle Bridge and completed materialization; repeat all hashes with bounded parallel scanner. No test or model submission replayed.','baseline_sha256':value['baseline_sha256']}).encode())
lease.release()
print('Reconciled stopped preparation scan lease; full hash check still required')
