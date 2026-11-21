"""Implementation rework may revise guidance/scheduling, never frozen coverage."""
from hashlib import sha256
import json
from pathlib import Path
from unity_coder.core.workspaces import git


def complete_inventory(contract: dict, prior: dict[str,str], current: dict[str,str]) -> None:
    expected={p for unit in contract['units'] if unit['role']=='test' and unit['status']=='active'
              for p in unit['owns']}
    expected.update(('Tests/Runtime/Script/jj.Monopoly.Tests.Runtime.asmdef',
                     'Tests/Runtime/Script/jj.Monopoly.Tests.Runtime.asmdef.meta'))
    if not prior or set(prior)!=expected or current!=prior:
        raise ValueError('Complete declared frozen test/configuration inventory must be unchanged')


def validate_revision(previous: dict, current: dict, digest: str) -> None:
    old_units=previous['units'];new_units=current['units']
    if len(old_units)!=len(new_units):raise ValueError('Frozen rework cannot add or remove units')
    for old,new in zip(old_units,new_units):
        allowed={'instructions','depends_on'} if old['role']=='impl' else set()
        if {k:v for k,v in old.items() if k not in allowed}!={k:v for k,v in new.items() if k not in allowed}:
            raise ValueError('Frozen rework changed ownership, tests, interfaces or criteria')
    expected=previous|{'contract_version':previous['contract_version']+1,'previous_contract_sha256':digest,'units':new_units}
    if current!=expected:raise ValueError('Frozen rework changed protected contract scope')


def validate_manifest(state: Path, source: Path, version: int, manifest: dict) -> dict[str,str]:
    run=state/'.agent/runs/monopoly-game-lobby';old=version-1
    prior=(run/('services-v'+str(old))/'state.json').read_bytes()
    result=(run/'cycles'/('v'+str(old))/'result.json').read_bytes()
    dossier=(run/('dossier-v'+str(old)+'.json')).read_bytes()
    transition=json.loads((run/'transitions'/('v'+str(version)+'.json')).read_bytes())
    spec=source/'specs/monopoly-game-lobby';previous_raw=(spec/('contract.v'+str(old)+'.json')).read_bytes()
    current_raw=(spec/('contract.v'+str(version)+'.json')).read_bytes()
    if (manifest['version']!=version or manifest['previous_services_sha256']!=sha256(prior).hexdigest()
        or manifest['previous_result_sha256']!=sha256(result).hexdigest()
        or manifest['dossier_sha256']!=sha256(dossier).hexdigest() or json.loads(result)['outcome']!='rework'
        or transition['state']!='complete' or transition['previous_sha256']!=sha256(previous_raw).hexdigest()
        or transition['next']['contract_sha256']!=sha256(current_raw).hexdigest()
        or manifest['frozen']!=json.loads(prior)['tdd']['frozen']):
        raise ValueError('Frozen implementation continuation lacks native rework provenance')
    complete_inventory(json.loads(previous_raw),json.loads(prior)['tdd']['frozen'],manifest['frozen'])
    validate_revision(json.loads(previous_raw),json.loads(current_raw),sha256(previous_raw).hexdigest())
    return manifest['frozen']


def prior_context(state: Path, module: Path, version: int) -> dict[str,dict[str,str]]:
    manifest=json.loads((state/'frozen-continuations'/('v'+str(version)+'.json')).read_bytes())
    if manifest.get('kind') not in ('implementation_rework','supplemental_frozen_coverage'):return {}
    files={}
    for path,digest in manifest['retained_proposal_files'].items():
        raw=git(module,'show',manifest['retained_candidate']+':'+path)
        if sha256(raw).hexdigest()!=digest:raise ValueError('Retained delegated proposal changed')
        files['readonly-prior-proposal/'+path]=raw.decode('utf-8')
    files['readonly-prior-proposal/actual-compiler-diagnostics.json']=json.dumps(manifest['compiler_diagnostics'],ensure_ascii=False)
    return {'SHELL':files}
