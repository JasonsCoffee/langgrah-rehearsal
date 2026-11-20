"""Mechanical compiler attribution and complete repair feedback for this host."""
from dataclasses import replace,asdict
from hashlib import sha256
import json
from unity_coder.core.contracts import Contract
from unity_coder.core.verification import VerificationResult


def compile_owners(contract: Contract, violations: list[dict]) -> tuple[str,...] | None:
    owners=set();prefix='Assets/JJGame/monopoly/'
    if not violations:return None
    for violation in violations:
        path=violation.get('file','').replace('\\','/')
        if not path.startswith(prefix):return None
        owner=contract.owner_of(path[len(prefix):])
        if owner is None:return None
        owners.add(owner)
    return tuple(sorted(owners))


def attribute_compile(contract: Contract, result: VerificationResult, record) -> VerificationResult:
    if result.gate!='compile' or result.status!='failed':return result
    owners=compile_owners(contract,[asdict(v) for v in result.violations])
    if owners is None or not set(owners)<=set(result.related_units):return result
    proof={'request':asdict(result.request),'original_related_units':result.related_units,
        'compiler_file_owners':owners,'violations':[asdict(v) for v in result.violations],
        'independent_judge_required':True}
    record(sha256(json.dumps(proof,sort_keys=True).encode()).hexdigest(),proof)
    return replace(result,related_units=owners)


def mechanical_feedback(state: dict, contract_sha256: str) -> str:
    evidence=state.get('verification')
    if (not evidence or evidence.get('status')!='failed'
        or evidence.get('request',{}).get('contract_sha256')!=contract_sha256):return ''
    return '\nACTUAL VERIFICATION EVIDENCE (preserve snapshot provenance; repair within ownership):\n'+json.dumps(evidence,ensure_ascii=False)
