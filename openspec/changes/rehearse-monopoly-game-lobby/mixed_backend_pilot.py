"""Bounded real model qualification; protocol fixtures never verify the game."""
from __future__ import annotations
from dataclasses import asdict
from hashlib import sha256
import json
import os
from pathlib import Path
from statistics import median
from evidence_packet import Source,Packet,make_packet,canonical
from evidence_context_guard import validate_delivery
from deepseek_context_selector import ContextOptimizer
from context_call_accounting import CachedSelectionCalls,PilotEnvelope,qualification_envelope
from judge_context_adapter import review
from mixed_backend_policy import role_profile,profile_sha256,judge_policy,clients,validate_pilot_receipts,QUALIFICATION_REF
from mixed_backend_recovery import CANDIDATE,CONTRACT,verify_preservation
from unity_coder.core.ai_models import ModelError,ModelReply
from unity_coder.core.budget import BudgetLedger
from unity_coder.core.lifecycle import RunLease
from unity_coder.core.model_calls import ModelCalls
from unity_coder.core.storage import atomic_write
from unity_coder.core.workspaces import git

CORPUS_SHA256='302813b31bca446b71d777099c6c413f44b04d386fa5973f0919493b4c8ca649'
PACKING_VERSION=2
PILOT_PREFIX='v70-migration-packed-v2'


def build_case(case: dict,candidate: str,contract: str,policy: str) -> Packet:
    sources=[Source(s['id'],s['path'],s['content'],s['kind']) for s in case['sources']]
    history=''.join('Historical decorative draft '+str(n)+': border and background variants from an obsolete UI concept; not accepted requirements.\n' for n in range(300))
    sources.append(Source('obsolete-drafts','pilot-fixtures/obsolete-drafts.txt',history,'optional'))
    return make_packet({'run':'monopoly-game-lobby','contract':contract,'candidate':candidate,'unit':case['unit'],
        'stage':case['mode'],'policy':policy,'packing_format_version':PACKING_VERSION,'fixture_scope':'protocol_only_not_game_verification',
        'fixture_id':case['id'],'fixture_sha256':sha256(canonical(case).encode()).hexdigest()},tuple(sources),
        tuple(s.id for s in sources if s.kind!='optional'),case['mechanical'],
        {s.path:case['unit'] for s in sources if s.kind=='patched'},tuple(case['criteria']),case['spec'])


class EnvelopeCalls:
    def __init__(self,calls: ModelCalls,envelope: PilotEnvelope) -> None:
        self.calls,self.envelope,self.client,self.budget=calls,envelope,calls.client,calls.budget

    def generate(self,call: str,unit: str,prompt: str,*,max_output_tokens: int) -> ModelReply:
        # Already completed matching calls are read idempotently by native calls.
        if call not in self.budget._read()['calls']:
            self.envelope.check(self.client.reserve_input(prompt),max_output_tokens)
        return self.calls.generate(call,unit,prompt,max_output_tokens=max_output_tokens)


def put_new(state: Path,path: str,value: dict) -> None:
    raw=canonical(value).encode();target=state/path
    if target.exists():
        if target.read_bytes()!=raw:raise ValueError('Preserve different existing migration artifact: '+path)
    else:atomic_write(state,path,raw)


def main() -> None:
    framework=Path.cwd().resolve();root=Path(os.environ['LOBBY_RUN_ROOT']).resolve(strict=True);state=root/'trusted-state'
    from direct_deepseek_client import load_direct_config
    load_direct_config(framework/'ai.local.toml') # No state writes until local configuration is valid.
    run=state/'.agent/runs/monopoly-game-lobby';result=json.loads((run/'result.json').read_bytes())
    source=root/'worktrees/monopoly-game-lobby/integration-v70'
    if (result['outcome'] not in ('operational','rework') or result['candidate_revision']!=CANDIDATE or result['contract_sha256']!=CONTRACT
        or git(source,'rev-parse','HEAD').decode().strip()!=CANDIDATE or git(source,'status','--porcelain')):
        raise ValueError('Exact clean stopped candidate required for paid protocol qualification')
    corpus_path=Path(__file__).parents[3]/'tests/fixtures/context_optimization/paired_pilot.json'
    raw=corpus_path.read_bytes()
    if sha256(raw).hexdigest()!=CORPUS_SHA256:raise ValueError('Frozen pilot expectations changed')
    cases=json.loads(raw);budget=BudgetLedger(state,'monopoly-game-lobby',input_limit=250000000,
        output_limit=24000000,max_cycles=160,max_added_units=2)
    before=budget._read();frozen=json.loads((run/'services-v70/state.json').read_bytes())['tdd']['frozen']
    from frozen_budget_continuation import check_frozen_sources
    check_frozen_sources(source,frozen)
    lease=RunLease(state,'monopoly-game-lobby','direct-low-pilot-'+str(os.getpid()));lease.acquire(owner_alive=lambda _:True)
    try:
        preservation_ref='context-optimization/preservation-v70.json'
        if not (state/preservation_ref).exists():put_new(state,preservation_ref,{'budget':before,'frozen':frozen})
        preserved=json.loads((state/preservation_ref).read_bytes())
        verify_preservation(preserved['budget'],before,preserved['frozen'],frozen)
        profile=role_profile()
        grant={'authority':'explicit_user_session','provenance':'User approved all Coder roles direct DeepSeek Flash low, Judge GPT-6.1 Sol low, optimized input plus check results, then apply while preserving the same run and all accounting.',
            'profile_sha256':profile_sha256(),'judge_policy_sha256':judge_policy().sha256,'judge_effort':'low',
            'limits':budget.limits,'candidate':CANDIDATE,'contract_sha256':CONTRACT,'pilot_authorized':True,
            'permit_dispatch_accounting':True,'preservation_ref':preservation_ref,'human_accepted':False}
        put_new(state,profile['authorization_ref'],grant)
        settings,selected,optimizer_client=clients(framework,root,state,budget,pilot=True)
        envelope=qualification_envelope(budget,state)
        coder=EnvelopeCalls(ModelCalls(selected[0],budget,'monopoly-game-lobby'),envelope)
        judge=EnvelopeCalls(ModelCalls(selected[1],budget,'monopoly-game-lobby'),envelope)
        optimizer=EnvelopeCalls(ModelCalls(optimizer_client,budget,'monopoly-game-lobby'),envelope)
        call=PILOT_PREFIX+'-coder-low'
        reply=coder.generate(call,'SHELL','Protocol fixture only; do not implement or approve the game. Return ONLY JSON {"value":"HELLO LOBBY"}.',max_output_tokens=65536)
        if json.loads(reply.text)!={'value':'HELLO LOBBY'}:raise ModelError('Direct Coder protocol fixture failed')
        rows=[];judge_role_call=None
        for case in cases:
            packet=build_case(case,CANDIDATE,CONTRACT,profile_sha256())
            selector=CachedSelectionCalls(optimizer,state,profile_sha256())
            optimized=ContextOptimizer(state,selector,qualified=True).run(packet,case['unit'])
            validate_delivery(packet,optimized)
            initial=optimized.optimized_input
            observed={};op=PILOT_PREFIX+'-'+case['id']
            for variant,text in [('canonical',packet.canonical_input),('optimized',initial)]:
                current=op+'-'+variant
                def send(prompt: str,identity: str) -> dict:
                    response=judge.generate(identity,case['unit'],prompt,max_output_tokens=32768)
                    return json.loads(response.text)
                decision=review(packet,send,current,case['mode'],initial_input=text,max_calls=1)
                expected=case['expected']
                correct=all(decision.get(k)==v for k,v in expected.items())
                charge=budget._read()['calls'][current]
                observed[variant]={'call_id':current,'decision':decision,'correct':correct,'actual_tokens':charge['actual']}
                if judge_role_call is None:judge_role_call=current
            baseline=observed['canonical']['actual_tokens'][0];delivered=observed['optimized']['actual_tokens'][0]
            reduction=1-delivered/max(1,baseline)
            rows.append({'id':case['id'],'class':case['class'],'canonical_sha256':packet.canonical_sha256,
                'optimized_sha256':optimized.optimized_sha256,'checks':optimized.check_results,
                'correct':all(x['correct'] for x in observed.values()),'judge_input_reduction':reduction,
                'selector_accounting':optimized.metrics['selector_accounting'],'reviews':observed,
                'eligible':all(x['correct'] for x in observed.values()) and optimized.decision=='use_optimized' and reduction>=.2})
            atomic_write(state,'context-optimization/pilot-packed-v2-progress.json',canonical({'cases':rows,'usage':budget.totals(),
                'profile_sha256':profile_sha256(),'game_verified':False}).encode())
        correct=all(row['correct'] for row in rows);median_reduction=median(row['judge_input_reduction'] for row in rows)
        qualified=correct and median_reduction>=.4
        report={'profile_sha256':profile_sha256(),'candidate':CANDIDATE,'contract_sha256':CONTRACT,
            'packing_format_version':PACKING_VERSION,
            'roles_qualified':qualified,'comparison_passed':correct,'roles':{'coder':call,'judge':judge_role_call},
            'qualified_classes':sorted(row['class'] for row in rows if row['eligible']) if qualified else [],
            'cases':rows,'median_judge_input_reduction':median_reduction,'usage':budget.totals(),
            'pilot_envelope':profile['pilot_limits'],'monetary_savings_verified':False,
            'monetary_limit':'Codex subscription dollar rate unknown; direct selector overhead is separately charged',
            'corpus_sha256':CORPUS_SHA256,'fixture_scope':'protocol_only_not_game_verification',
            'game_verified':False,'human_accepted':False}
        verify_preservation(preserved['budget'],budget._read(),preserved['frozen'],frozen)
        if qualified:
            validate_pilot_receipts(state,budget._read()['calls'],report)
            put_new(state,QUALIFICATION_REF,report)
        atomic_write(state,'context-optimization/pilot-packed-v2-report.json',canonical(report).encode())
        print(json.dumps({'qualified':qualified,'median_judge_input_reduction':median_reduction,
            'qualified_classes':report['qualified_classes'],'usage':budget.totals(),'game_verified':False}),flush=True)
    finally:lease.release()


if __name__=='__main__':main()
