"""Prepare only the missing asset binding from the currently imported baseline."""
from hashlib import sha256
import json
import os
from pathlib import Path
import time
from overlay_host import OverlayHost
from lobby_preparation_host import reconcile_import,compile_shells
from unity_coder.adapters.unity.transport import local_http
from unity_coder.core.storage import atomic_write
from unity_coder.core.workspaces import git

root=Path(os.environ['LOBBY_RUN_ROOT']).resolve(strict=True);state=root/'trusted-state'
directory=Path(__file__).parent;source=root/'worktrees/architect-assets-v15'
operation='shop-preparation-v15'
if source.exists() or (state/operation).exists():raise ValueError('Preserve prior preparation; inspect receipts before any replay')
host=OverlayHost(architect_preparation=True);host.lease.acquire(owner_alive=lambda _:True)
try:
    host.preflight();overlay=host.overlay.read();host.overlay.assert_ready(overlay['candidate'])
    git(root/'module','worktree','add','-b','codex/lobby-shop-preparation-v15',str(source),overlay['candidate'])
    atomic_write(state,operation+'/start.json',json.dumps({'candidate':overlay['candidate'],'baseline_sha256':overlay['baseline_sha256'],'original_files':len(overlay['baseline'])}).encode())
    script='Editor/Script/LobbyRehearsal/LobbyShopPreparation.cs'
    if (source/script).exists():raise ValueError('Preparation script path already exists')
    atomic_write(source,script,(directory/'LobbyShopPreparation.cs').read_bytes())
    git(source,'add',script)
    git(source,'-c','user.name=Lobby Rehearsal','-c','user.email=rehearsal@example.invalid','commit','-m','Prepare dedicated shop asset command without game behavior')
    previous=state/'prepared-shell-compile.json'
    if previous.exists():atomic_write(state,operation+'/previous-compile-receipt.json',previous.read_bytes())
    compile_shells(host,source)
    overlay=host.overlay.read();candidate=overlay['candidate']
    path='Assets/JJGame/monopoly/Runtime/Resource/monopoly/UI/Prefabs/LobbyRehearsal/LobbyView_placeHolder.prefab'
    before=(host.host/path).read_bytes()
    atomic_write(state,operation+'/before.prefab',before)
    atomic_write(state,operation+'/intent.json',json.dumps({'candidate':candidate,'changed':[path],'before_sha256':sha256(before).hexdigest()}).encode())
    report=state/operation/'editor-report.json'
    reply=local_http(host.port,'POST','/execute',{'command':'PrepareMonopolyLobbyShop','reportPath':str(report)},10)
    atomic_write(state,operation+'/submission.json',json.dumps(reply).encode())
    deadline=time.monotonic()+180
    while not report.exists() and time.monotonic()<deadline:
        if reply.get('status')=='error':raise ValueError('Editor command rejected; inspect receipt')
        if reply.get('taskId'):
            task=local_http(host.port,'GET','/task/'+str(reply['taskId']),None,5)
            atomic_write(state,operation+'/task.json',json.dumps(task).encode())
            if task.get('status')=='error':raise ValueError('Editor task failed; inspect receipt')
        time.sleep(1)
    if not report.exists():raise ValueError('Editor result missing; do not replay blindly')
    host.restore_preparation_effects(operation)
    actual=host.overlay.scan();expected=overlay['baseline']|overlay['managed']
    differences={p for p,h in expected.items() if actual.get(p)!=h};added=set(actual)-set(expected)
    if differences!={path} or added:raise ValueError('Unexpected preparation drift: '+str(sorted(differences|added)))
    after=(host.host/path).read_bytes();atomic_write(state,operation+'/after.prefab',after)
    atomic_write(host.host,path,before);host.overlay.assert_ready(candidate)
    atomic_write(source,path.removeprefix('Assets/JJGame/monopoly/'),after)
    git(source,'add','Runtime/Resource/monopoly/UI/Prefabs/LobbyRehearsal/LobbyView_placeHolder.prefab')
    git(source,'-c','user.name=Lobby Rehearsal','-c','user.email=rehearsal@example.invalid','commit','-m','Prepare dedicated lobby Shop binding beside the wallet')
    final=reconcile_import(host,source)
    record={'candidate':final,'previous_candidate':candidate,'changed':{path:sha256(after).hexdigest()},
        'original_files_checked':len(overlay['baseline']),'baseline_sha256':overlay['baseline_sha256'],
        'trusted_overlay_changed':False,'business_logic_written':False,'editor_report':json.loads(report.read_bytes())}
    atomic_write(state,operation+'/complete.json',json.dumps(record,ensure_ascii=False,indent=2).encode())
    (directory/'evidence/shop-preparation-v15.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8',newline='')
    print(json.dumps(record,ensure_ascii=False),flush=True)
finally:host.lease.release()
