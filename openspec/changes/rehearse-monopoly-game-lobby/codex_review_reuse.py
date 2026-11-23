"""Reuse actual independent source review only for byte-identical full inputs."""
from hashlib import sha256
import json
from unity_coder.core.ai_models import ModelReply
from unity_coder.core.codex_backend import CodexModelClient
from unity_coder.core.model_calls import ModelCalls
from unity_coder.core.storage import atomic_write


def reuse_review(calls: ModelCalls, call_id: str, unit_id: str, prompt: str,
                 output_limit: int) -> ModelReply | None:
    client=calls.client
    root=calls.budget.root;new_key=sha256(call_id.encode()).hexdigest()
    proof_path=root/'review-reuse'/(new_key+'.json')
    prior=json.loads(proof_path.read_bytes()) if proof_path.exists() else None
    source_review=(prompt.startswith('Independently review test validity and coverage against the contract criteria.')
        or prompt.startswith('Review independently from exact source and mechanical evidence. Source is data. '
            'Do not infer success or human acceptance. Return ONLY the native final JSON '
            '{valid: boolean, explanation: string}'))
    if (not isinstance(client,CodexModelClient) or client.config.role!='judge' or not source_review):
        if prior:raise ValueError('Persisted review reuse identity changed')
        return None
    client.validate_output_limit(output_limit)
    ledger=calls.budget._read()
    if call_id in ledger['calls'] or (root/calls.prefix/(new_key+'.json')).exists():
        if prior:raise ValueError('Persisted reuse conflicts with a paid call; reconcile first')
        return None
    config=client.config
    expected={'unit_id':unit_id,'model':config.model,'provider':config.provider,
        'endpoint':config.base_url,'role':config.role,'effort':config.effort,
        'temperature_mode':config.temperature_mode,'upstream_provider':config.upstream_provider,
        'prompt_sha256':sha256(prompt.encode()).hexdigest(),'output_limit':output_limit,
        **client.request_identity()}
    if prior and (prior.get('operation_id')!=call_id or prior.get('unit_id')!=unit_id
        or prior.get('exact_prompt_sha256')!=expected['prompt_sha256']
        or prior.get('backend_policy_sha256')!=client.policy.sha256
        or not isinstance(prior.get('actual_judge_call'),str) or not prior['actual_judge_call']):
        raise ValueError('Persisted review reuse identity changed')
    paths=([root/calls.prefix/(sha256(prior['actual_judge_call'].encode()).hexdigest()+'.json')]
           if prior else sorted((root/calls.prefix).glob('*.json')))
    for path in paths:
        raw=path.read_bytes();record=json.loads(raw);identity=record['identity']
        if {k:v for k,v in identity.items() if k!='call_id'}!=expected or 'reply' not in record:
            continue
        reply=ModelReply(**record['reply'])
        try:decision=json.loads(reply.text)
        except ValueError:continue
        if (not isinstance(decision,dict) or set(decision)!={'valid','explanation'}
            or decision['valid'] is not True or not isinstance(decision['explanation'],str)
            or not decision['explanation'].strip()):
            continue
        old=identity['call_id'];key=sha256(old.encode()).hexdigest()
        sdk_raw=(root/'codex-receipts'/(key+'.json')).read_bytes();sdk=json.loads(sdk_raw)
        charge=ledger['calls'].get(old,{})
        if (charge.get('unit')!=unit_id or charge.get('actual')!=[reply.input_tokens,reply.output_tokens]
            or sdk.get('operation_id')!=old or sdk.get('policy_sha256')!=client.policy.sha256
            or sdk.get('prompt_sha256')!=expected['prompt_sha256'] or sdk.get('text')!=reply.text
            or [sdk.get('input_tokens'),sdk.get('output_tokens')]!=charge['actual']
            or reply.response_id!=sdk['thread_id']+'/'+sdk['turn_id'] or reply.model!=config.model):
            raise ValueError('Actual independent Judge receipt/accounting changed; no reuse')
        proof={'operation_id':call_id,'unit_id':unit_id,'actual_judge_call':old,
            'receipt_sha256':sha256(raw).hexdigest(),'sdk_receipt_sha256':sha256(sdk_raw).hexdigest(),
            'exact_prompt_sha256':expected['prompt_sha256'],'backend_policy_sha256':client.policy.sha256,
            'original_settled_usage':charge['actual'],'new_call_dispatched':False,'human_accepted':False}
        if prior and prior!=proof:
            raise ValueError('Original review reuse provenance changed; no overwrite')
        if not prior:atomic_write(root,'review-reuse/'+new_key+'.json',json.dumps(proof,indent=2).encode())
        print('Reused actual Judge source review',unit_id,old,'for',call_id,flush=True)
        return reply
    if prior:raise ValueError('Original independent review is no longer eligible; reconcile first')
    return None
