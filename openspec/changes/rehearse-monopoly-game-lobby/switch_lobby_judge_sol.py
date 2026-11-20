"""Apply the explicit Sol amendment and retry without replaying older calls."""
from dataclasses import replace
from hashlib import sha256
import json
import os
from pathlib import Path
import re
from rehearsal_model_transport import RehearsalTransport
from switch_lobby_judge_glm import public
from unity_coder.core.ai_models import load_ai_config,ModelClient,ModelError
from unity_coder.core.budget import BudgetLedger
from unity_coder.core.lifecycle import RunLease
from unity_coder.core.model_calls import ModelCalls
from unity_coder.core.model_workers import _object,parse_judgement
from unity_coder.core.storage import atomic_write
from unity_coder.core.workspaces import git


def main() -> None:
    directory=Path(__file__).parent;root=Path(os.environ['LOBBY_RUN_ROOT']).resolve(strict=True)
    state=root/'trusted-state';run=state/'.agent/runs/monopoly-game-lobby'
    result=json.loads((run/'result.json').read_bytes())
    if result['contract_version']!=23 or result['outcome']!='rework':raise ValueError('Expected inspected quiescent cycle 23')
    integration=root/'worktrees/monopoly-game-lobby/integration-v23'
    if git(integration,'rev-parse','HEAD').decode().strip()!=result['candidate_revision'] or git(integration,'status','--porcelain'):raise ValueError('Candidate changed')
    p=json.loads((state/'budget-policy.json').read_bytes())
    budget=BudgetLedger(state,'monopoly-game-lobby',input_limit=p['input_limit'],output_limit=p['output_limit'],max_cycles=p['max_cycles'],max_added_units=p['max_added_units'])
    lease=RunLease(state,'monopoly-game-lobby','judge-sol-'+str(os.getpid()));lease.acquire(owner_alive=lambda _:True)
    try:
        proof_path='model-authorizations/judge-gpt-6.1-sol-v23.json'
        if (state/proof_path).exists():raise ValueError('Preserve previous amendment; no replay')
        before=load_ai_config(Path('ai.local.toml'))
        if before.judge.model!='z-ai/glm-5.3-flash':raise ValueError('Unexpected previous judge')
        raw=Path('ai.local.toml').read_bytes();text=raw.decode('utf-8-sig')
        match=re.search(r'(?ms)^\[judge\][^\r\n]*\r?\n(?P<section>.*?)(?=^\[|\Z)',text)
        if match is None:raise ValueError('Judge section missing')
        section,count=re.subn(r'(?m)^(\s*model\s*=\s*)["\']z-ai/glm-5\.3-flash["\']',r'\1"openai/gpt-6.1-sol"',match['section'])
        if count!=1:raise ValueError('Expected exactly one judge assignment')
        updated=text[:match.start('section')]+section+text[match.end('section'):]
        new=(b'\xef\xbb\xbf' if raw.startswith(b'\xef\xbb\xbf') else b'')+updated.encode()
        proof={'authority':'explicit user request','request':'switch the Judge to GPT-6.1 Sol, and try again',
            'run_id':'monopoly-game-lobby','candidate_revision':result['candidate_revision'],
            'old_judge':public(before.judge),'new_judge':public(replace(before.judge,model='openai/gpt-6.1-sol')),
            'coder':public(before.coder),'usage_before':budget.totals(),'limits':budget.limits,
            'configured':False,'probe_verified':False,'human_accepted':False,'candidate_unchanged':True}
        atomic_write(state,proof_path,json.dumps(proof,indent=2).encode())
        atomic_write(Path.cwd(),'ai.local.toml',new)
        after=load_ai_config(Path('ai.local.toml'))
        if after.coder!=before.coder or after.judge!=replace(before.judge,model='openai/gpt-6.1-sol'):raise ValueError('Unrequested field changed')
        proof.update(configured=True,config_before_sha256=sha256(raw).hexdigest(),config_after_sha256=sha256(new).hexdigest())
        atomic_write(state,proof_path,json.dumps(proof,indent=2).encode())
        calls=ModelCalls(ModelClient(after.judge,transport=RehearsalTransport(state,'judge'),timeout=180),budget,'monopoly-game-lobby')
        cases=[('judge-switch-v23-sol-json-review','Independently review test validity. Return ONLY JSON with valid (boolean) and explanation. Criterion: cancelling preserves the wallet. Test: var before=ReadWallet(); CancelQueue(); Assert.That(before, Is.EqualTo(before));'),
            ('judge-switch-v23-sol-json-defect','Classify the defect as implementation or contract. Return ONLY JSON with defect_class and explanation. Complete accepted contract: cancelling leaves 500 coins unchanged. Implementation: CancelQueue(){Coins=0;}. Correct test expects 500 after cancellation and observes zero. The fixture and contract are consistent.')]
        completed=[]
        try:
            for index,(call,prompt) in enumerate(cases):
                reply=calls.generate(call,'TEST-VIP',prompt,max_output_tokens=32768)
                if reply.model!='openai/gpt-6.1-sol':raise ValueError('Unexpected response model')
                if index==0:
                    decision=_object(reply.text,{'valid','explanation'})
                    if decision['valid'] is not False or not isinstance(decision['explanation'],str) or not decision['explanation'].strip():raise ValueError('Vacuity calibration failed')
                elif parse_judgement(reply.text)[0]!='implementation':raise ValueError('Defect calibration failed')
                completed.append({'call_id':call,'model':reply.model,'input_tokens':reply.input_tokens,'output_tokens':reply.output_tokens})
                proof.update(completed_probes=completed,usage_after=budget.totals());atomic_write(state,proof_path,json.dumps(proof,indent=2).encode())
            proof['probe_verified']=True
        except (ModelError,ValueError) as error:
            proof.update(probe_error=str(error),usage_after=budget.totals())
        atomic_write(state,proof_path,json.dumps(proof,indent=2).encode())
        (directory/'evidence/judge-model-switch-sol-v23.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='')
        print(json.dumps({'judge':after.judge.model,'coder':after.coder.model,'probe_verified':proof['probe_verified'],'probe_error':proof.get('probe_error'),'completed_probes':completed,'usage':budget.totals(),'limits':budget.limits}),flush=True)
    finally:lease.release()


if __name__=='__main__':main()
