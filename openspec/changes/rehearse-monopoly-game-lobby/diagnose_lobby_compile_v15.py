"""Compile-only preparation diagnostic; no test execution or implementation."""
from hashlib import sha256
import json
import os
from pathlib import Path
from overlay_host import OverlayHost
from lobby_preparation_host import compile_shells
from unity_coder.core.storage import atomic_write
from unity_coder.core.workspaces import git

root=Path(os.environ['LOBBY_RUN_ROOT']).resolve(strict=True);state=root/'trusted-state'
run=state/'.agent/runs/monopoly-game-lobby';operation='compile-diagnostic-after-v15'
source=root/'worktrees/architect-compile-after-v15'
if source.exists() or (state/operation).exists():raise ValueError('Preserve existing diagnostic; inspect receipts before replay')
result=json.loads((run/'result.json').read_bytes())
if result['outcome']!='rework' or result['contract_version']!=15:raise ValueError('Actual version-fifteen rework required')
budget_before=sha256((run/'budget.json').read_bytes()).hexdigest()
host=OverlayHost(architect_preparation=True);host.lease.acquire(owner_alive=lambda _:True)
try:
    host.preflight();overlay=host.overlay.read();host.overlay.assert_ready(overlay['candidate'])
    git(root/'module','worktree','add','-b','codex/lobby-compile-after-v15',str(source),result['candidate_revision'])
    atomic_write(state,operation+'/intent.json',json.dumps({'retained_candidate':result['candidate_revision'],
        'materialized_before':overlay['candidate'],'budget_sha256':budget_before,'selected_tests':[]}).encode())
    previous=state/'prepared-shell-compile.json'
    if previous.exists():atomic_write(state,operation+'/previous-compile-receipt.json',previous.read_bytes())
    error=None
    try:compile_shells(host,source)
    except ValueError as failure:error=str(failure)
    receipt=json.loads((state/'prepared-shell-compile.json').read_bytes())
    candidate=git(source,'rev-parse','HEAD').decode().strip()
    if receipt['candidate']!=candidate:raise ValueError('No exact diagnostic compile receipt; inspect pending effects')
    if sha256((run/'budget.json').read_bytes()).hexdigest()!=budget_before:raise ValueError('Unexpected model accounting change')
    record={'scope':'Architect compile-only diagnostic, not native Red/Green or test execution',
        'retained_candidate':result['candidate_revision'],'diagnostic_candidate':candidate,
        'error':error,'compile_receipt':receipt,'budget_unchanged':True,'selected_tests_executed':0,
        'human_accepted':False,'baseline_sha256':overlay['baseline_sha256']}
    atomic_write(state,operation+'/complete.json',json.dumps(record,ensure_ascii=False,indent=2).encode())
    (Path(__file__).parent/'evidence/compile-diagnostic-after-v15.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8',newline='')
    print(json.dumps(record,ensure_ascii=False),flush=True)
finally:host.lease.release()
