"""Production repair must include implicated prior units and retain mixed blame."""
import json

from test_contracts import bundle
from test_workspaces import workspace
from test_local_executor import local
from unity_coder.core.verification import VerificationRequest, VerificationResult


def failure(services):
    contract=services.contract
    request=VerificationRequest('shared','run1',1,contract.sha256,'candidate',
        contract.presentation_ref.sha256,contract.coding_profile_ref.sha256,contract.environment_ref.sha256,
        tuple(t.test_id for t in contract.test_links),True)
    services.state.update(group=['U2-system'],evidence_ref='evidence/shared.json')
    return VerificationResult(request,'tests','failed',related_units=('U1-state','U2-system'),
        failed_tests=request.test_selection,behavioral=True)


def test_shared_failure_repairs_implicated_unit_outside_current_batch(local):
    _,services,_,_,_,_=local
    result=services._failed(failure(services),'final_verify','shared')
    assert result.next_stage=='code'
    assert set(services.state['group'])=={'U1-state','U2-system'}
    assert services.tdd.state('U1-state').stage=='green_coding'


def test_mixed_dossier_retains_implementation_and_contract_findings(local):
    executor,services,workers,_,_,_=local
    workers.judge=lambda unit,*args:('contract' if unit.id=='U1-state' else 'implementation','Evidence-based finding')
    result=services._failed(failure(services),'final_verify','mixed')
    assert result.result['outcome']=='rework'
    dossier=json.loads((executor.root/executor.prefix/'dossier-v1.json').read_bytes())
    assert {u['id']:u['defect_class'] for u in dossier['failed_units']}=={
        'U1-state':'contract','U2-system':'implementation'}
