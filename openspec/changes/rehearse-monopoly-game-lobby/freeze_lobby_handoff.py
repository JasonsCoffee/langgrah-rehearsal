"""Freeze the validated first-cycle handoff without running implementation."""
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
from unity_coder.adapters.unity import UnityAdapter
from unity_coder.core.contracts import load_contract
from unity_coder.core.target_profiles import load_profile

root=Path(os.environ['LOBBY_RUN_ROOT']).resolve()
module=root/'module'
spec=module/'specs/monopoly-game-lobby'
if (root/'trusted-state/execution-baseline.json').exists():
    raise ValueError('Execution baseline already exists; freezing cannot be replayed')
rules=UnityAdapter()
contract=load_contract((spec/'contract.draft.json').read_bytes(),module,rules)
profile=load_profile((spec/'coding-profile.json').read_bytes(),module,rules=rules,allowed_mount='Assets/JJGame/monopoly',implementation_roots=('Runtime/Script',),test_roots=('Tests/Runtime/Script/LobbyRehearsal',))
profile.validate_contract(contract)
target=spec/'contract.v1.json'
raw=(spec/'contract.draft.json').read_bytes()
if target.exists() and target.read_bytes()!=raw:
    raise ValueError('Frozen first-cycle contract already exists with different bytes')
target.write_bytes(raw)
subprocess.check_call(['git','-C',str(module),'add','.'])
subprocess.check_call(['git','-C',str(module),'-c','user.name=Lobby Rehearsal','-c','user.email=rehearsal@example.invalid','commit','-m','Freeze lobby execution contract and prepared presentation inputs'])
revision=subprocess.check_output(['git','-C',str(module),'rev-parse','HEAD']).decode().strip()
record={'candidate':revision,'contract_sha256':contract.sha256,'units':len(contract.units),'selected_tests':len(contract.test_links),'behavioral_tests_frozen':False,'human_accepted':False}
state=root/'trusted-state'
path=state/'execution-baseline.json'
if path.exists():
    raise ValueError('Existing execution baseline must be reconciled, never replaced')
path.write_text(json.dumps(record,indent=2),encoding='utf-8')
wiring=state/'host-wiring/prepared-v1'
wiring.mkdir(parents=True,exist_ok=True)
sources=('trusted_overlay.py','overlay_host.py','lobby_production_host.py')
hashes={}
for name in sources:
    data=(Path(__file__).parent/name).read_bytes()
    destination=wiring/name
    if destination.exists() and destination.read_bytes()!=data:
        raise ValueError('Trusted wiring version exists with different bytes')
    destination.write_bytes(data)
    hashes[name]=sha256(data).hexdigest()
(wiring/'hashes.json').write_text(json.dumps(hashes,indent=2),encoding='utf-8')
print(json.dumps(record))
