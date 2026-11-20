"""Route an observed test/catalog conflict to its delegated owner."""
from hashlib import sha256
import json
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5


def prepare(source: Path, current: dict) -> None:
    if current['contract_version'] != 23:
        raise ValueError('Bound to the recorded cycle-twenty-two observation')
    test='Tests/Runtime/Script/LobbyRehearsal/LobbyEconomyRechargeTests.cs'
    config='Runtime/Script/UI/LobbyRehearsal/LobbyConfiguration.cs'
    raw=(source/test).read_bytes()
    if 'Does.Contain("入场费折扣")'.encode() not in raw:
        return
    if '入场优惠介绍：演练入场费保持不变。'.encode() not in (source/config).read_bytes():
        raise ValueError('Reconcile changed catalog rather than applying stale findings')
    guide='specs/monopoly-game-lobby/architect-findings.v22.md'
    (source/guide).write_bytes(Path(__file__).with_name('architect-findings.v22.md').read_bytes())
    proof='specs/monopoly-game-lobby/catalog-consistency.v23.json'
    (source/proof).write_text(json.dumps({'test_path':test,'test_sha256':sha256(raw).hexdigest(),'catalog_path':config,'catalog_sha256':sha256((source/config).read_bytes()).hexdigest(),'observation':guide,'assertions_changed_by_architect':False,'human_accepted':False},indent=2)+'\n',encoding='utf-8',newline='')
    unit=next(u for u in current['units'] if u['id']=='TEST-CARDS')
    note=test.removesuffix('.cs')+'.catalog-consistency-v23.md'
    unit['owns'] += [note,note+'.meta']
    guid=uuid5(NAMESPACE_URL,'monopoly-game-lobby/'+note).hex
    unit['instructions']+=' Also repair the actual unsupported literal documented in architect-findings.v22.md and catalog-consistency.v23.json. Keep the approved catalog immutable; assert its actual category/key/localized values with a private sentinel proving the entry-benefit rendered data path. Preserve all effective assertions, eleven IDs and informational fee invariance. This is a source inconsistency observation, not approval; independent review remains mandatory. Write '+note+' with the effective clause mapping and '+note+'.meta exactly fileFormatVersion: 2 newline guid: '+guid+' newline.'
    def ref(path):return {'path':path,'sha256':sha256((source/path).read_bytes()).hexdigest()}
    profile=json.loads((source/current['coding_profile_ref']['path']).read_bytes())
    profile['rules'] += [ref(guide),ref(proof)]
    profile['protected_paths'] += [guide,proof]
    path='specs/monopoly-game-lobby/coding-profile.v23.json'
    (source/path).write_text(json.dumps(profile,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='')
    current['coding_profile_ref']=ref(path)
