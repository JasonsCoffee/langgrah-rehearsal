"""Frozen same-run activation gates; no provider or Unity calls."""
import importlib.util
import json
from hashlib import sha256
from pathlib import Path
import pytest


def module():
    path=Path('openspec/changes/rehearse-monopoly-game-lobby/codex_lobby.py')
    spec=importlib.util.spec_from_file_location('codex_lobby',path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value)
    return value


def inputs():
    p={'roles':{'coder':{'model':'gpt-6.2-sol','effort':'low'},'judge':{'model':'gpt-6.1-sol','effort':'medium'}},
       'preserve_aggregate_limits':[100000000,12000000,80,2],
       'candidate_revision':'candidate','contract_sha256':'contract'}
    raw=json.dumps(p).encode();digest=sha256(raw).hexdigest()
    grant={'authority':'explicit_user_session','provenance':'approved in user session',
        'profile_sha256':digest,'permit_dispatch_accounting':True,'permit_activation_after_verified_pilot':True}
    pilot={'profile_sha256':digest,'retained_candidate':'candidate','contract_sha256':'contract',
        'canonical_plan_sha256':'plan','outputs':{'coder':{'value':'HELLO LOBBY','plan_sha256':'plan'},
        'judge':{'valid':True,'plan_sha256':'plan'}},'human_acceptance_granted':False}
    return raw,p,grant,pilot


def test_exact_grant_and_two_model_pilot_can_activate():
    raw,p,g,t=inputs()
    module().validate_activation(raw,p,g,t,[100000000,12000000,80,2])


@pytest.mark.parametrize('bad',['grant','profile','pilot','candidate','contract','judge','plan','limits','human'])
def test_changed_or_unverified_activation_fails(bad):
    raw,p,g,t=inputs();limits=[100000000,12000000,80,2]
    if bad=='grant':g['permit_dispatch_accounting']=False
    elif bad=='profile':g['profile_sha256']='other'
    elif bad=='pilot':t={}
    elif bad=='candidate':t['retained_candidate']='other'
    elif bad=='contract':t['contract_sha256']='other'
    elif bad=='judge':t['outputs']['judge']['valid']=False
    elif bad=='plan':t['outputs']['judge']['plan_sha256']='other'
    elif bad=='limits':limits[0]+=1
    else:t['human_acceptance_granted']=True
    with pytest.raises(ValueError):module().validate_activation(raw,p,g,t,limits)


def test_legacy_transport_remains_explicit_alternative():
    source=Path('openspec/changes/rehearse-monopoly-game-lobby/lobby_production_host.py').read_text()
    assert "LOBBY_MODEL_BACKEND" in source
    assert "load_ai_config(framework/'ai.local.toml')" in source
    assert 'LOBBY_RESUME_CODEX_V60' in source
