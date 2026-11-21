"""Append-only coverage after a real frozen-test rejection; no old test edits."""
from hashlib import sha256
import json
from pathlib import Path
from unity_coder.core.ownership import portable_path


def validate_supplement(previous: dict,current: dict,digest: str,author: str,new_paths: list[str],
                        test_id: str,source_test: str,*,implementers: list[str] | None = None) -> None:
    source=next(t for t in previous['test_links'] if t['test_id']==source_test)
    implementers=source['implementing_units'] if implementers is None else implementers
    active_impl={u['id'] for u in previous['units'] if u['role']=='impl'}
    if (not set(source['implementing_units'])<=set(implementers) or not set(implementers)<=active_impl
        or len(set(implementers))!=len(implementers)):
        raise ValueError('New coverage must preserve prior implementers and use existing implementation owners')
    old_paths={p for u in previous['units'] for p in u['owns']}
    if (source['author_unit']!=author or not new_paths or len(set(new_paths))!=len(new_paths)
        or set(new_paths)&old_paths or any(not any(portable_path(p).startswith(r+'/') for r in previous['test_roots']) for p in new_paths)
        or test_id in {t['test_id'] for t in previous['test_links']}):
        raise ValueError('Supplement must introduce only new test-root paths and a new mapped case')
    if len(previous['units'])!=len(current['units']):raise ValueError('Supplement cannot change unit count')
    for old,new in zip(previous['units'],current['units']):
        expected=dict(old)
        if old['id']==author:
            expected.update(owns=old['owns']+new_paths,acceptance=old['acceptance']+[test_id],instructions=new['instructions'])
        elif old['id'] in implementers:
            expected['acceptance']=old['acceptance']+[test_id]
        if new!=expected:raise ValueError('Supplement changed existing coverage, ownership or implementation guidance')
    expected=previous|{'contract_version':previous['contract_version']+1,'previous_contract_sha256':digest,
        'units':current['units'],'test_links':previous['test_links']+[source|{'test_id':test_id,'implementing_units':implementers}]}
    if current!=expected:raise ValueError('Supplement changed protected scope')


def new_author_paths(owns: list[str],frozen: dict[str,str],planned: list[str]) -> tuple[str,...]:
    available=tuple(p for p in owns if p not in frozen)
    if not planned or set(available)!=set(planned) or set(planned)&set(frozen):
        raise ValueError('Only explicitly added, unfrozen files may be authored')
    return available


def validate_manifest(state: Path,source: Path,version: int,manifest: dict) -> dict[str,str]:
    run=state/'.agent/runs/monopoly-game-lobby';old=version-1
    prior=(run/('services-v'+str(old))/'state.json').read_bytes()
    result=(run/'cycles'/('v'+str(old))/'result.json').read_bytes()
    dossier=(run/('dossier-v'+str(old)+'.json')).read_bytes()
    old_carry=(state/'frozen-continuations'/('v'+str(old)+'.json')).read_bytes()
    transition=json.loads((run/'transitions'/('v'+str(version)+'.json')).read_bytes())
    spec=source/'specs/monopoly-game-lobby';old_raw=(spec/('contract.v'+str(old)+'.json')).read_bytes();new_raw=(spec/('contract.v'+str(version)+'.json')).read_bytes()
    review=(state/manifest['negative_review_ref']).read_bytes()
    if (manifest['version']!=version or manifest['previous_services_sha256']!=sha256(prior).hexdigest()
        or manifest['previous_result_sha256']!=sha256(result).hexdigest()
        or manifest['dossier_sha256']!=sha256(dossier).hexdigest() or json.loads(result)['outcome']!='rework'
        or manifest['previous_carry_sha256']!=sha256(old_carry).hexdigest()
        or manifest['frozen']!=json.loads(old_carry)['frozen'] or len(manifest['frozen'])!=185
        or manifest['negative_review_sha256']!=sha256(review).hexdigest()
        or json.loads(json.loads(review)['reply']['text'])['valid'] is not False
        or transition['state']!='complete' or transition['previous_sha256']!=sha256(old_raw).hexdigest()
        or transition['next']['contract_sha256']!=sha256(new_raw).hexdigest()):
        raise ValueError('Supplementary coverage lacks actual rejection and native transition provenance')
    validate_supplement(json.loads(old_raw),json.loads(new_raw),sha256(old_raw).hexdigest(),manifest['author_unit'],
        manifest['new_paths'],manifest['supplementary_test'],manifest['source_test'],implementers=manifest.get('implementing_units'))
    return manifest['frozen']


def author_scope(state: Path,version: int) -> dict[str,tuple[str,...]]:
    manifest=json.loads((state/'frozen-continuations'/('v'+str(version)+'.json')).read_bytes())
    return {manifest['author_unit']:tuple(manifest['new_paths'])} if manifest.get('kind') in ('supplemental_frozen_coverage','reviewed_source_supplement') else {}
