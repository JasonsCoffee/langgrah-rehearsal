"""Frozen pilot authorization: investigation never implies weaker budget consent."""
import importlib.util
import json
from pathlib import Path
import pytest


def gate():
    spec=importlib.util.spec_from_file_location('codex_lobby_pilot',Path('examples/codex_backend/lobby_pilot.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def inputs():
    profile={'format_version':1,'run_id':'run','contract_version':60,'contract_sha256':'contract',
        'candidate_revision':'candidate','backend':'codex_app_server','budget_enforcement':'dispatch_accounting',
        'authorization_ref':'model-authorizations/explicit.json','max_calls_per_role':200,'framing_tokens':65536,
        'timeout_seconds':60,'pilot_output_allocation':8192,
        'roles':{'coder':{'model':'coder-model','effort':'low'},'judge':{'model':'judge-model','effort':'medium'}},
        'preserve_aggregate_limits':[100000000,12000000,80,2],'activation_requires_verified_pilot':True,
        'status':'proposal_not_authorized'}
    raw=json.dumps(profile,sort_keys=True).encode()
    from hashlib import sha256
    grant={'authority':'explicit_user_session','provenance':'user explicitly approved proposed policy',
        'profile_sha256':sha256(raw).hexdigest(),'permit_dispatch_accounting':True,
        'permit_activation_after_verified_pilot':True}
    result={'outcome':'operational','contract_version':60,'contract_sha256':'contract','candidate_revision':'candidate'}
    return raw,profile,grant,result


@pytest.mark.parametrize('bad',['missing-grant','wrong-profile','same-model','not-operational','different-candidate','no-budget-consent','no-activation-consent'])
def test_policy_rejects_missing_or_changed_consent(bad):
    module=gate();raw,profile,grant,result=inputs()
    if bad=='missing-grant':grant={}
    elif bad=='wrong-profile':grant['profile_sha256']='changed'
    elif bad=='same-model':profile['roles']['judge']['model']='coder-model'
    elif bad=='not-operational':result['outcome']='awaiting_human_review'
    elif bad=='different-candidate':result['candidate_revision']='other'
    elif bad=='no-budget-consent':grant['permit_dispatch_accounting']=False
    else:grant['permit_activation_after_verified_pilot']=False
    with pytest.raises(ValueError):module.validate_authorization(raw,profile,grant,result,[100000000,12000000,80,2])


def test_exact_proposal_is_reviewable_but_requires_separate_trusted_grant():
    module=gate();raw,profile,grant,result=inputs()
    module.validate_authorization(raw,profile,grant,result,[100000000,12000000,80,2])
    with pytest.raises(ValueError):module.validate_authorization(raw,profile,grant,result,[200000000,12000000,80,2])
