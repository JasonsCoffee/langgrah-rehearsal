"""Explicit recovery proof for a completed HTTP gateway failure, without refund."""
from pathlib import Path


def retained_coder_body_timeout(state: Path, call_id: str, receipt: dict, reservation: dict) -> tuple[int,int]:
    import json
    from hashlib import sha256
    raw=(state/'.agent/runs/monopoly-game-lobby/model-calls'/(sha256(call_id.encode()).hexdigest()+'.json')).read_bytes()
    if (call_id!='v29-step7-prepare-TEST-PARTY-TEST-PARTY'
        or sha256(raw).hexdigest()!='3f739cc850d46297eddbf24ab3c559f6c0e3347d935ddc0457e07ac98e04a91e'
        or json.loads(raw)!=receipt or receipt.get('failure')!={'transport':'direct_preconnect','phase':'request','failure_kind':'timeout','request_stage':'body'}
        or 'reply' in receipt or receipt['identity'].get('model')!='deepseek/deepseek-v4.1-flash'
        or reservation!={'reserved':[367803,65536],'unit':'TEST-PARTY','version':29}):
        raise ValueError('Coder body-timeout reservation changed')
    return 367803,65536


def retained_sol_request_failure(state: Path, call_id: str, receipt: dict, reservation: dict) -> tuple[int,int]:
    import json
    from hashlib import sha256
    raw=(state/'.agent/runs/monopoly-game-lobby/model-calls'/(sha256(call_id.encode()).hexdigest()+'.json')).read_bytes()
    if (call_id!='v29-step2-prepare-review-TEST-VIP'
        or sha256(raw).hexdigest()!='e00a6b19c99a742278e6a2551ecf1863be056dee7c0a380c468ca05ae1227591'
        or json.loads(raw)!=receipt or receipt.get('failure')!={'transport':'direct_preconnect','phase':'request','failure_kind':'timeout'}
        or 'reply' in receipt or receipt['identity'].get('model')!='openai/gpt-6.1-sol'
        or reservation!={'reserved':[325238,32768],'unit':'TEST-VIP','version':29}):
        raise ValueError('Sol timeout reservation changed')
    return 325238,32768


def retained_coder_request_failure(state: Path, call_id: str, receipt: dict, reservation: dict) -> tuple[int,int]:
    import json
    from hashlib import sha256
    raw=(state/'.agent/runs/monopoly-game-lobby/model-calls'/(sha256(call_id.encode()).hexdigest()+'.json')).read_bytes()
    if (call_id!='v28-step5-prepare-TEST-QUEUE-TEST-QUEUE'
        or sha256(raw).hexdigest()!='130aa37c0952627bbdefe219d35ae7fcfd93ef71fb6ddf135400614c94d165eb'
        or json.loads(raw)!=receipt or receipt.get('failure')!={'transport':'direct_preconnect','phase':'request'}
        or 'reply' in receipt or receipt['identity'].get('model')!='deepseek/deepseek-v4.1-flash'
        or reservation!={'reserved':[371097,65536],'unit':'TEST-QUEUE','version':28}):
        raise ValueError('Unknown post-request reservation changed')
    return 371097,65536


def retained_run_reservations(state: Path, ledger: dict) -> list[str]:
    import json
    from hashlib import sha256
    retained=[];codex_uncertain=0
    for call_id,charge in ledger['calls'].items():
        if 'actual' in charge:continue
        record=json.loads((state/'.agent/runs/monopoly-game-lobby/model-calls'/(sha256(call_id.encode()).hexdigest()+'.json')).read_bytes())
        if call_id=='v8-step3-prepare-review-TEST-PRES-CORE':retained_transport_failure(record,charge,8)
        elif call_id=='v16-step1-prepare-review-TEST-APPEAR':retained_key_limit_failure(record,charge,16)
        elif call_id.startswith('judge-switch-v23-glm-json-review'):retained_calibration_failure(state,call_id,record,charge)
        elif call_id.startswith('tls-recovery-v23-glm-json-review'):retained_tls_probe_failure(state,call_id,record,charge)
        elif call_id=='v25-step8-prepare-TEST-MATCH-TEST-MATCH':retained_coder_connection_failure(state,call_id,record,charge)
        elif call_id=='v28-step5-prepare-TEST-QUEUE-TEST-QUEUE':retained_coder_request_failure(state,call_id,record,charge)
        elif call_id=='v29-step2-prepare-review-TEST-VIP':retained_sol_request_failure(state,call_id,record,charge)
        elif call_id=='v29-step7-prepare-TEST-PARTY-TEST-PARTY':retained_coder_body_timeout(state,call_id,record,charge)
        elif call_id=='v51-step4-prepare-review-TEST-SOCIAL':retained_sol_key_limit_v51(state,call_id,record,charge)
        elif call_id=='v60-step4-prepare-review-TEST-CHAT-STATE':retained_judge_key_limit_v60(state,call_id,record,charge)
        elif record['identity'].get('worker_backend')=='codex_app_server':
            from codex_lobby import retained_codex_call
            proof=json.loads((state/'model-authorizations/codex-retained-calls.json').read_bytes())['calls'][call_id]
            retained_codex_call(state,call_id,charge,proof)
            codex_uncertain+=1
        else:retained_sol_review_failure(state,call_id,record,charge)
        retained.append(call_id)
    expected=15 if 'v51-step4-prepare-review-TEST-SOCIAL' in ledger['calls'] else 14
    if 'v60-step4-prepare-review-TEST-CHAT-STATE' in ledger['calls']:expected+=1
    expected+=codex_uncertain
    if len(retained)!=expected:raise ValueError('Uncertain reservation set changed')
    return retained


def retained_sol_key_limit_v51(state: Path, call_id: str, receipt: dict, reservation: dict) -> tuple[int,int]:
    """Keep the entire inspected HTTP-403 charge without assuming zero usage."""
    import json
    from hashlib import sha256
    raw=(state/'.agent/runs/monopoly-game-lobby/model-calls'/(sha256(call_id.encode()).hexdigest()+'.json')).read_bytes()
    if (call_id!='v51-step4-prepare-review-TEST-SOCIAL'
        or sha256(raw).hexdigest()!='f3bddc0076be670fd5c460efc59ac348c78cb7ad0919541bb6887c95eb95a3b4'
        or json.loads(raw)!=receipt or receipt.get('failure')!={
            'transport':'direct_preconnect','http_status':403,'limit_source':'openrouter_key_limit'}
        or 'reply' in receipt or receipt['identity'].get('model')!='openai/gpt-6.1-sol'
        or reservation!={'reserved':[512698,32768],'unit':'TEST-SOCIAL','version':51}):
        raise ValueError('Exact Sol key-limit reservation changed')
    return 512698,32768


def retained_judge_key_limit_v60(state: Path, call_id: str, receipt: dict, reservation: dict) -> tuple[int,int]:
    """Keep the entire inspected HTTP-403 charge without assuming zero usage."""
    import json
    from hashlib import sha256
    raw=(state/'.agent/runs/monopoly-game-lobby/model-calls'/(sha256(call_id.encode()).hexdigest()+'.json')).read_bytes()
    if (call_id!='v60-step4-prepare-review-TEST-CHAT-STATE'
        or sha256(raw).hexdigest()!='081babbbeaee02ff9aa21f1d56db3ab5a4075f155cb41be598b668682f53adf8'
        or json.loads(raw)!=receipt or receipt.get('failure')!={
            'transport':'direct_preconnect','http_status':403,'limit_source':'openrouter_key_limit'}
        or 'reply' in receipt or receipt['identity'].get('model')!='openai/gpt-6.1-sol'
        or reservation!={'reserved':[703310,32768],'unit':'TEST-CHAT-STATE','version':60}):
        raise ValueError('Exact Judge key-limit reservation changed')
    return 703310,32768


def retained_coder_connection_failure(state: Path, call_id: str, receipt: dict, reservation: dict) -> tuple[int,int]:
    import json
    from hashlib import sha256
    raw=(state/'.agent/runs/monopoly-game-lobby/model-calls'/(sha256(call_id.encode()).hexdigest()+'.json')).read_bytes()
    if (call_id!='v25-step8-prepare-TEST-MATCH-TEST-MATCH'
        or sha256(raw).hexdigest()!='a2d316759d8ce3bdb9b45a5fea9412d655df355a170e3029f19b248da57dfc65'
        or json.loads(raw)!=receipt or receipt.get('failure')!={} or 'reply' in receipt
        or receipt['identity'].get('model')!='deepseek/deepseek-v4.1-flash'
        or reservation!={'reserved':[340587,65536],'unit':'TEST-MATCH','version':25}):
        raise ValueError('Coder unknown connection reservation changed')
    return 340587,65536


def retained_sol_review_failure(state: Path, call_id: str, receipt: dict, reservation: dict) -> tuple[int,int]:
    """Keep the exact unknown charge from the first native Sol connection stop."""
    import json
    from hashlib import sha256
    raw=(state/'.agent/runs/monopoly-game-lobby/model-calls'/(sha256(call_id.encode()).hexdigest()+'.json')).read_bytes()
    expected={
        'v24-step4-prepare-review-TEST-APPEAR':'382d045a304cb5fe1a011c556ff418995ff909855b86ac5238417609f7bc1d8d',
        'v24-step5-prepare-review-TEST-APPEAR':'d8b8efa5e3f9eb39221c9e736528fcf55bef2a67c070db180a60543a72d6eba0',
        'v25-step2-prepare-review-TEST-APPEAR':'f2b1928e1fca90fd184f05ce43e4686c8ef5f30f6e728179dd95a11e462af07c',
        'v25-step3-prepare-review-TEST-APPEAR':'f5bda024166d229c35d21e5655695a0b0af7355053cb38aa3fcb1a47be15b69b',
    }
    if (call_id not in expected
        or sha256(raw).hexdigest()!=expected[call_id]
        or json.loads(raw)!=receipt or receipt.get('failure')!=({'transport':'schannel','curl_exit_code':35} if call_id.startswith('v25-') else {}) or 'reply' in receipt
        or receipt['identity'].get('model')!='openai/gpt-6.1-sol'
        or reservation!={'reserved':[422802 if call_id.startswith('v25-') else 421858,32768],'unit':'TEST-APPEAR','version':25 if call_id.startswith('v25-') else 24}):
        raise ValueError('Unknown Sol review failure differs from inspected receipt')
    return reservation['reserved'][0],32768

def retained_tls_probe_failure(state: Path, call_id: str, receipt: dict, reservation: dict) -> tuple[int,int]:
    """Bind known TLS-calibration effects to their exact retained reservations."""
    from hashlib import sha256
    import json
    expected={
        'tls-recovery-v23-glm-json-review':{'http_status':429,'retry_after_seconds':2,'provider_name':'Wafer','limit_source':'upstream_provider_shared_pool'},
        'tls-recovery-v23-glm-json-review-retry1':{},
    }
    if call_id not in expected:raise ValueError('Unknown TLS calibration operation')
    manifest=json.loads((state/'model-authorizations/tls-probe-reservations-v23.json').read_bytes())
    item=manifest.get('calls',{}).get(call_id)
    raw=(state/'.agent/runs/monopoly-game-lobby/model-calls'/(sha256(call_id.encode()).hexdigest()+'.json')).read_bytes()
    identity=receipt.get('identity',{})
    if (manifest.get('non_mutating_calibration') is not True or manifest.get('usage_unknown_retained') is not True
        or not item or item.get('receipt_sha256')!=sha256(raw).hexdigest() or json.loads(raw)!=receipt
        or item.get('reservation')!=reservation or 'actual' in reservation or 'reply' in receipt
        or receipt.get('failure')!=expected[call_id] or identity.get('call_id')!=call_id
        or identity.get('role')!='judge' or identity.get('unit_id')!='TEST-VIP'
        or identity.get('model')!='z-ai/glm-5.3-flash' or identity.get('output_limit')!=32768):
        raise ValueError('TLS calibration evidence changed')
    counts=reservation.get('reserved')
    if not isinstance(counts,list) or len(counts)!=2 or any(type(n) is not int or n<0 for n in counts):raise ValueError('Invalid reservation')
    return counts[0],counts[1]

def retained_transport_failure(record: dict, call: dict, version: int) -> list[int]:
    identity=record['identity']
    if (record.get('failure')!={'http_status':502,'provider_name':'OpenAI'}
        or 'reply' in record or identity.get('role')!='judge'
        or not identity['call_id'].startswith('v'+str(version)+'-')
        or call.get('version')!=version or call.get('unit')!=identity['unit_id']
        or 'actual' in call):
        raise ValueError('Only the inspected unresolved judge gateway failure is recoverable')
    reserved=call.get('reserved')
    if not isinstance(reserved,list) or len(reserved)!=2 or any(type(n) is not int or n<=0 for n in reserved):
        raise ValueError('Unknown usage must retain its entire positive reservation')
    return list(reserved)

def retained_key_limit_failure(record: dict, call: dict, version: int) -> list[int]:
    identity=record['identity']
    if (record.get('failure')!={'http_status':402,'limit_source':'openrouter_key_limit'}
        or 'reply' in record or identity.get('role')!='judge'
        or not identity['call_id'].startswith('v'+str(version)+'-')
        or call.get('version')!=version or call.get('unit')!=identity['unit_id']
        or 'actual' in call):
        raise ValueError('Only the inspected unresolved judge key-limit failure is recoverable')
    reserved=call.get('reserved')
    if not isinstance(reserved,list) or len(reserved)!=2 or any(type(n) is not int or n<=0 for n in reserved):
        raise ValueError('Unknown key-limit usage must retain its full reservation')
    return list(reserved)
def retained_calibration_failure(state: Path, call_id: str, receipt: dict, reservation: dict) -> tuple[int,int]:
    """Retain exact operator-recorded, non-mutating failed probe charges."""
    from hashlib import sha256
    import json
    allowed={'judge-switch-v23-glm-json-review','judge-switch-v23-glm-json-review-retry1'}
    if call_id not in allowed:raise ValueError('Unknown calibration operation')
    manifest=json.loads((state/'model-authorizations/glm-json-probe-reservations-v23.json').read_bytes())
    item=manifest.get('calls',{}).get(call_id)
    raw=(state/'.agent/runs/monopoly-game-lobby/model-calls'/(sha256(call_id.encode()).hexdigest()+'.json')).read_bytes()
    identity=receipt.get('identity',{})
    if (manifest.get('non_mutating_calibration') is not True or manifest.get('usage_unknown_retained') is not True
        or not item or item.get('receipt_sha256')!=sha256(raw).hexdigest()
        or json.loads(raw)!=receipt or item.get('reservation')!=reservation
        or 'actual' in reservation or receipt.get('failure')!={} or 'reply' in receipt
        or identity.get('call_id')!=call_id or identity.get('role')!='judge'
        or identity.get('unit_id')!='TEST-VIP' or identity.get('model')!='z-ai/glm-5.3-flash'
        or identity.get('output_limit')!=32768):
        raise ValueError('Calibration receipt or reservation changed')
    counts=reservation.get('reserved')
    if not isinstance(counts,list) or len(counts)!=2 or any(type(n) is not int or n<0 for n in counts):raise ValueError('Invalid retained reservation')
    return counts[0],counts[1]

