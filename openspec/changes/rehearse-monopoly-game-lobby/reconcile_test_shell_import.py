"""Reconcile only Unity-deleted orphan metadata, then supply real test shells."""
from hashlib import sha256
import json
import os
from pathlib import Path
from overlay_host import OverlayHost
from unity_coder.core.storage import atomic_write
from unity_coder.core.workspaces import git

root=Path(os.environ['LOBBY_RUN_ROOT']).resolve()
source=root/'worktrees/architect-v2'
names=('LobbyEconomyTests','LobbyMatchTests','LobbySocialTests','LobbyRecordsSettingsTests')
for name in names:
    relative='Tests/Runtime/Script/LobbyRehearsal/'+name+'.cs'
    path=source/relative
    if path.exists():
        raise ValueError('Test shell exists; reconcile rather than overwrite')
    path.write_text('// Compilable preparation shell; assertions belong to its delegated test author.\nnamespace jj.Monopoly.Tests.LobbyRehearsal\n{\n    public sealed class '+name+' { }\n}\n',encoding='utf-8',newline='')
    git(source,'add','--',relative)
git(source,'-c','user.name=Lobby Rehearsal','-c','user.email=rehearsal@example.invalid','commit','-m','Prepare imported test shells before delegated assertion authoring')
host=OverlayHost(architect_preparation=True)
host.lease.acquire(owner_alive=lambda owner:owner!='lobby-overlay-68128',reclaim_stale=True)
try:
    host.preflight()
    value=host.overlay.read()
    restored=[]
    for name in names:
        relative='Tests/Runtime/Script/LobbyRehearsal/'+name+'.cs.meta'
        target='Assets/JJGame/monopoly/'+relative
        expected=value['managed'][target]
        original=git(source,'show',value['candidate']+':'+relative)
        if sha256(original).hexdigest()!=expected:
            raise ValueError('Original candidate metadata identity changed')
        current=host.host/target
        if current.exists():
            raise ValueError('Expected the observed deletion, not replacement metadata')
        atomic_write(host.host,target,original)
        restored.append({'path':target,'sha256':expected,'reason':'Unity removed orphan metadata before its test source existed'})
    atomic_write(host.state,'orphan-test-metadata-reconciliation.json',json.dumps({'candidate':value['candidate'],'restored':restored,'known_dead_owner':'lobby-overlay-68128','overlay_unchanged':True},indent=2).encode())
    host.restore_preparation_effects('reconcile-test-shell-import')
    host.overlay.check(value)
    print('Restored four exact candidate metadata files; complete baseline check passed')
finally:
    host.lease.release()
