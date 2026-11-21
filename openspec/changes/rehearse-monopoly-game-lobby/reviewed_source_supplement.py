"""New coverage after a real review rejection, preserving all existing bytes."""
from hashlib import sha256
import json
from pathlib import Path
from unity_coder.core.ownership import portable_path
from unity_coder.core.workspaces import git


def validate_append(old: dict,new: dict,digest: str,author: str,paths: list[str],links: list[dict]) -> None:
    previous_paths={p for u in old['units'] for p in u['owns']}
    previous_ids={link['test_id'] for link in old['test_links']}
    known_impl={u['id'] for u in old['units'] if u['role']=='impl'}
    if (not paths or not links or len(set(paths))!=len(paths) or set(paths)&previous_paths
        or any(not any(portable_path(p).startswith(root+'/') for root in old['test_roots']) for p in paths)
        or len({l['test_id'] for l in links})!=len(links)
        or any(l['test_id'] in previous_ids or l['author_unit']!=author or not l['implementing_units']
               or not set(l['implementing_units'])<=known_impl for l in links)
        or len(old['units'])!=len(new['units'])):
        raise ValueError('Only new owned test-root files and mapped coverage may be appended')
    for previous,current in zip(old['units'],new['units']):
        expected=dict(previous)
        additions=[l['test_id'] for l in links if previous['id']==author or previous['id'] in l['implementing_units']]
        if additions:expected['acceptance']=previous['acceptance']+additions
        if previous['id']==author:
            if previous['role']!='test':raise ValueError('Supplement must have a test author')
            expected.update(owns=previous['owns']+paths,instructions=current['instructions'])
        if current!=expected:raise ValueError('Append changed existing ownership, behavior or coverage')
    expected=old|{'contract_version':old['contract_version']+1,'previous_contract_sha256':digest,
        'units':new['units'],'test_links':old['test_links']+links}
    if new!=expected:raise ValueError('Append changed protected contract fields')


def protect(state: Path,source: Path,version: int,manifest: dict) -> tuple[str,...]:
    from frozen_budget_continuation import check_frozen_sources
    run=state/'.agent/runs/monopoly-game-lobby';old=version-1
    result_raw=(run/('cycles/v'+str(old)+'/result.json')).read_bytes()
    dossier_raw=(run/('dossier-v'+str(old)+'.json')).read_bytes()
    result=json.loads(result_raw);dossier=json.loads(dossier_raw)
    spec=source/'specs/monopoly-game-lobby'
    previous=(spec/('contract.v'+str(old)+'.json')).read_bytes();current=(spec/('contract.v'+str(version)+'.json')).read_bytes()
    previous_contract=json.loads(previous)
    transition=json.loads((run/('transitions/v'+str(version)+'.json')).read_bytes())
    receipt_raw=(state/manifest['negative_review_ref']).read_bytes();receipt=json.loads(receipt_raw)
    sdk=json.loads((state/manifest['negative_sdk_ref']).read_bytes())
    decision=json.loads(receipt['reply']['text']);ledger=json.loads((run/'budget.json').read_bytes())
    if (manifest['version']!=version or result['outcome']!='rework' or dossier['reason']!='rework'
        or result['candidate_revision']!=manifest['source_revision']
        or sha256(result_raw).hexdigest()!=manifest['previous_result_sha256']
        or sha256(dossier_raw).hexdigest()!=manifest['dossier_sha256']
        or sha256(receipt_raw).hexdigest()!=manifest['negative_review_sha256']
        or decision.get('valid') is not False or receipt['identity']['model']!='gpt-6.1-sol'
        or receipt['identity']['effort']!='medium' or sdk['text']!=receipt['reply']['text']
        or ledger['calls'][receipt['identity']['call_id']].get('actual')!=[sdk['input_tokens'],sdk['output_tokens']]
        or transition['state']!='complete' or transition['previous_sha256']!=sha256(previous).hexdigest()
        or transition['next']['contract_sha256']!=sha256(current).hexdigest()):
        raise ValueError('Supplement requires an actual negative Judge review and native transition')
    validate_append(previous_contract,json.loads(current),sha256(previous).hexdigest(),manifest['author_unit'],manifest['new_paths'],manifest['new_links'])
    expected={p for u in previous_contract['units'] if u['role']=='test' and u['status']=='active' for p in u['owns']}
    expected.update(('Tests/Runtime/Script/jj.Monopoly.Tests.Runtime.asmdef','Tests/Runtime/Script/jj.Monopoly.Tests.Runtime.asmdef.meta'))
    if set(manifest['frozen'])!=expected:raise ValueError('Complete previous test/configuration inventory required')
    for path,digest in manifest['frozen'].items():
        if sha256(git(source,'show',manifest['source_revision']+':'+path)).hexdigest()!=digest:
            raise ValueError('Historical test source identity changed')
    return check_frozen_sources(source,manifest['frozen'])
