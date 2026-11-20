"""Capture a bounded Editor asset revision without changing trusted overlay code."""
from hashlib import sha256
import json
import os
from pathlib import Path
import time
from overlay_host import OverlayHost
from lobby_preparation_host import reconcile_import
from unity_coder.adapters.unity.transport import local_http
from unity_coder.core.storage import atomic_write
from unity_coder.core.workspaces import git


def main() -> None:
    root=Path(os.environ['LOBBY_RUN_ROOT']).resolve(strict=True)
    source=root/'worktrees/architect-v5'
    state=root/'trusted-state'
    host=OverlayHost(architect_preparation=True)
    prefix='Assets/JJGame/monopoly/'
    resources=prefix+'Runtime/Resource/monopoly/UI/Prefabs/LobbyRehearsal/'
    changed=[resources+screen+'View_placeHolder.prefab' for screen in ('Lobby','Recharge')]
    added=[resources+'SharedWallet_placeHolder.prefab',resources+'SharedWallet_placeHolder.prefab.meta']
    repair='presentation-repair-v5'
    intent_path=state/repair/'intent.json'
    report=state/repair/'editor-report.json'
    host.lease.acquire(owner_alive=lambda _:True)
    try:
        host.preflight()
        candidate=git(source,'rev-parse','HEAD').decode().strip()
        compiled=json.loads((state/'prepared-shell-compile.json').read_bytes())
        if compiled['candidate']!=candidate or not compiled['evidence']['compilation']['passed']:
            raise ValueError('Exact compiled preparation candidate required')
        overlay=host.overlay.read()
        if intent_path.exists():raise ValueError('Existing repair intent requires explicit receipt reconciliation; no replay')
        host.overlay.assert_ready(candidate)
        before={p:(host.host/p).read_bytes() for p in changed}
        intent={'candidate':candidate,'changed':{p:sha256(v).hexdigest() for p,v in before.items()},'added':added}
        for p,content in before.items():
            atomic_write(state,repair+'/before/'+p.removeprefix(prefix),content)
        atomic_write(state,repair+'/intent.json',json.dumps(intent,indent=2).encode())
        print('EDITOR preparing shared wallet and missing serialized actions',flush=True)
        response=local_http(host.port,'POST','/execute',{'command':'RepairMonopolyLobbyBindings','reportPath':str(report)},10)
        atomic_write(state,repair+'/submission.json',json.dumps(response).encode())
        deadline=time.monotonic()+180
        while not report.exists() and time.monotonic()<deadline:
            if response.get('status')=='error':raise ValueError('Editor repair rejected; inspect submission receipt')
            if response.get('taskId'):
                task=local_http(host.port,'GET','/task/'+str(response['taskId']),None,5)
                atomic_write(state,repair+'/task.json',json.dumps(task).encode())
                if task.get('status')=='error':raise ValueError('Editor repair task failed; inspect durable receipt')
            time.sleep(1)
        if not report.exists():raise ValueError('No durable Editor repair report; never replay blindly')
        # Reconcile only previously proven shared Editor cache/font side effects.
        host.restore_preparation_effects('binding-repair-v5')
        print('CHECK auditing every original file before adopting asset revisions',flush=True)
        actual=host.overlay.scan()
        expected=overlay['baseline']|overlay['managed']
        differences={p for p,h in expected.items() if actual.get(p)!=h}
        additions=set(actual)-set(expected)
        if differences!=set(changed) or additions!=set(added):
            raise ValueError('Editor repair drift differs from exact declared inventory: '+str(sorted(differences|additions)))
        repaired={p:(host.host/p).read_bytes() for p in changed+added}
        for p,content in repaired.items():
            atomic_write(state,repair+'/after/'+p.removeprefix(prefix),content)
        # The overlay is intentionally unchanged. Restore the exact managed
        # originals before its additive preparation capture; the committed new
        # revision is later applied exclusively through normal materialization.
        for p,content in before.items():
            if sha256((host.host/p).read_bytes()).hexdigest()!=sha256(repaired[p]).hexdigest():
                raise ValueError('Editor asset changed during capture')
            atomic_write(host.host,p,content)
        print('CAPTURE registering only the new shared-wallet prefab and metadata',flush=True)
        captured=host.overlay.capture_preparation(candidate,tuple(added))
        if set(captured)!=set(added):raise ValueError('Preparation capture inventory differs')
        for p,content in repaired.items():atomic_write(source,p.removeprefix(prefix),content)
        git(source,'add','Runtime/Resource/monopoly/UI/Prefabs/LobbyRehearsal')
        git(source,'-c','user.name=Lobby Rehearsal','-c','user.email=rehearsal@example.invalid','commit','-m','Prepare shared wallet, outside input and unread badge bindings')
        print('IMPORT materializing the exact committed asset revision',flush=True)
        final=reconcile_import(host,source)
        receipt={'candidate':final,'previous_candidate':candidate,'changed':{p:sha256(repaired[p]).hexdigest() for p in changed},
            'added':{p:sha256(repaired[p]).hexdigest() for p in added},'baseline_sha256':overlay['baseline_sha256'],
            'original_files_checked':len(overlay['baseline']),'trusted_overlay_changed':False,'business_logic_written':False}
        atomic_write(state,repair+'/complete.json',json.dumps(receipt,indent=2).encode())
        (Path(__file__).parent/'evidence/presentation-repair-v5.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8',newline='')
        print(json.dumps(receipt),flush=True)
    finally:host.lease.release()


if __name__=='__main__':main()
