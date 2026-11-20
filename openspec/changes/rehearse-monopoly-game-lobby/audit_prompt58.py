"""Read-only real host context audit; never instantiates paid clients."""
import json,os,subprocess
from pathlib import Path
from hashlib import sha256
from unity_coder.adapters.unity import UnityAdapter
from unity_coder.core.contracts import load_contract
from lobby_production_host import ContextWorkers,SPEC
from prompt_guidance import LATE_GUIDES
root=Path(os.environ['LOBBY_RUN_ROOT'])/'worktrees/architect-v58'
contracts=[]
for n in range(1,59):contracts.append(load_contract((root/SPEC/('contract.v'+str(n)+'.json')).read_bytes(),root,UnityAdapter(),previous=contracts[-1] if contracts else None,max_cycles=60))
paths=subprocess.check_output(['git','ls-files','-z'],cwd=root).decode().split('\0')
files={}
for name in paths:
 if not name:continue
 try:files[name]=(root/name).read_text(encoding='utf-8')
 except UnicodeError:pass
contract=contracts[-1];workers=ContextWorkers(contract,None,None,root)
unit=next(u for u in contract.units if u.id=='TEST-RECORDS')
context=workers.context(unit,files)
assert all(SPEC+n in context for n in LATE_GUIDES)
for name in LATE_GUIDES:assert context[SPEC+name]==(root/SPEC/name).read_text(encoding='utf-8')
api=context[SPEC+'framework-context.md']
for name in ('IDeviceRatingService','IQualityMatchingService','IQualityModifyService'):assert name in api
assert 'public jj.Core.Runtime.IDeviceRatingService DeviceRatingService' in context['Runtime/Script/UI/LobbyRehearsal/LobbyShellBindings.cs']
report={'contract_sha256':contract.sha256,'candidate':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root).decode().strip(),'paid_calls':0,'context_bytes':len(json.dumps(context,ensure_ascii=False).encode()),'late_guides':{n:sha256(context[SPEC+n].encode()).hexdigest() for n in LATE_GUIDES},'quality_api_present':True,'declared_quality_slots_present':True}
Path(__file__).with_name('evidence').joinpath('prompt-context-v58.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='')
print(json.dumps(report))
