"""Consent-gated two-call transport trial; never approves or edits the lobby."""
import argparse
from dataclasses import asdict
from hashlib import sha256
import json
import os
from pathlib import Path

from unity_coder.core.budget import BudgetLedger
from unity_coder.core.codex_backend import CodexModelClient,CodexPolicy
from unity_coder.core.codex_stdio import CodexStdioExchange
from unity_coder.core.lifecycle import RunLease
from unity_coder.core.model_calls import ModelCalls
from unity_coder.core.ownership import confined_path
from unity_coder.core.storage import atomic_write


def validate_authorization(raw: bytes, profile: dict, grant: dict, result: dict, limits: list[int]) -> None:
    """Trusted session grant must cover this exact plan and budget semantics."""
    if (grant.get('authority')!='explicit_user_session' or not grant.get('provenance')
        or grant.get('profile_sha256')!=sha256(raw).hexdigest()
        or grant.get('permit_dispatch_accounting') is not True
        or grant.get('permit_activation_after_verified_pilot') is not True
        or result.get('outcome')!='operational'
        or any(result.get(key)!=profile.get(key) for key in
               ('contract_version','contract_sha256','candidate_revision'))
        or limits!=profile.get('preserve_aggregate_limits')
        or profile.get('backend')!='codex_app_server'
        or profile.get('budget_enforcement')!='dispatch_accounting'
        or profile['roles']['coder']['model']==profile['roles']['judge']['model']):
        raise ValueError('Explicit exact Codex model and dispatch-accounting authorization required')


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument('--profile',type=Path,default=Path(__file__).resolve().parents[2]/
        'openspec/changes/rehearse-monopoly-game-lobby/codex-backend.proposed.json')
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    root=Path(os.environ['LOBBY_RUN_ROOT']).resolve(strict=True)
    state=root/'trusted-state';run=state/'.agent/runs/monopoly-game-lobby'
    raw=args.profile.read_bytes();profile=json.loads(raw)
    policy=json.loads((state/'budget-policy.json').read_bytes())
    limits=[policy[k] for k in ('input_limit','output_limit','max_cycles','max_added_units')]
    result=json.loads((run/'result.json').read_bytes())
    grant_path=confined_path(state,profile['authorization_ref'])
    grant=json.loads(grant_path.read_bytes()) if grant_path.is_file() else {}
    try:validate_authorization(raw,profile,grant,result,limits)
    except ValueError as error:
        if args.check:
            print(json.dumps({'ready':False,'reason':str(error),'model_turns_started':0,
                'checkpoint':'6ff8d8b','roles':profile['roles'],'aggregate_limits':limits}));return
        raise
    if args.check:
        print(json.dumps({'ready':True,'roles':profile['roles'],'aggregate_limits':limits,
                          'model_turns_started':0}));return
    if profile['run_id']!='monopoly-game-lobby' or profile['contract_version']!=60:
        raise ValueError('This pilot is scoped to the retained lobby cycle 60')
    budget=BudgetLedger(state,profile['run_id'],input_limit=limits[0],output_limit=limits[1],
        max_cycles=limits[2],max_added_units=limits[3])
    lease=RunLease(state,profile['run_id'],'codex-backend-pilot-'+str(os.getpid()))
    lease.acquire(owner_alive=lambda _:True)
    try:
        work=root/'codex-workers/pilot-v60'
        if work.exists() and (work.is_symlink() or any(work.iterdir())):
            raise ValueError('Preserve unexpected worker-root contents')
        work.mkdir(parents=True,exist_ok=True)
        plan={'id':'codex-backend-pilot-v60','requirement':'uppercase the supplied phrase',
              'input':'hello lobby','expected':'HELLO LOBBY','scope':'transport calibration only'}
        plan_hash=sha256(json.dumps(plan,sort_keys=True).encode()).hexdigest()
        outputs={};policies={}
        for role in ('coder','judge'):
            selected=profile['roles'][role]
            worker_policy=CodexPolicy(role,selected['model'],selected['effort'],profile['budget_enforcement'],
                profile['authorization_ref'],profile['max_calls_per_role'],profile['framing_tokens'])
            policies[role]={'policy':asdict(worker_policy),'sha256':worker_policy.sha256}
            client=CodexModelClient(worker_policy,state,work,exchange=CodexStdioExchange(),
                authorize=lambda digest:digest==worker_policy.sha256,
                timeout=profile['timeout_seconds'])
            calls=ModelCalls(client,budget,profile['run_id'])
            payload={'canonical_plan':plan,'plan_sha256':plan_hash}
            if role=='coder':
                payload['instructions']='Return only JSON with value (the transformed phrase) and plan_sha256.'
            else:
                payload['candidate']=outputs['coder']
                payload['instructions']='Independently check the candidate against the canonical plan. Return only JSON with valid (boolean), explanation, and plan_sha256. This is a transport probe, not lobby or human acceptance.'
            reply=calls.generate('codex-backend-pilot-v60-'+role,'TEST-HARNESS',
                json.dumps(payload,sort_keys=True),max_output_tokens=profile['pilot_output_allocation'])
            outputs[role]=json.loads(reply.text)
            if outputs[role].get('plan_sha256')!=plan_hash:
                raise ValueError('Worker did not use the shared canonical plan')
            if role=='coder' and outputs[role].get('value')!=plan['expected']:
                raise ValueError('Coder calibration result failed')
            if role=='judge' and (outputs[role].get('valid') is not True or not outputs[role].get('explanation')):
                raise ValueError('Independent Judge calibration failed')
        evidence={'profile_sha256':sha256(raw).hexdigest(),'canonical_plan_sha256':plan_hash,
            'roles':policies,'outputs':outputs,'accounted_tokens':budget.totals(),
            'retained_candidate':result['candidate_revision'],'contract_sha256':result['contract_sha256'],
            'lobby_source_changed':False,'lobby_tests_passed':False,'human_acceptance_granted':False}
        atomic_write(state,'codex-backend/pilot-verified-v60.json',json.dumps(evidence,indent=2).encode())
        print(json.dumps(evidence))
    finally:lease.release()


if __name__=='__main__':main()
