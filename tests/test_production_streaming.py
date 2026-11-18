"""Independent candidates verify while peers code; shared dependencies serialize."""
from dataclasses import replace
from threading import Event
from test_contracts import bundle
from test_workspaces import workspace
from test_local_executor import local, run
from unity_coder.core.local_executor import WorkerPatch
from unity_coder.core.evidence import TestResult as Evidence
from unity_coder.core.verification import VerificationResult
from unity_coder.core.tdd import TDDCoordinator


def test_fast_independent_candidate_verifies_while_slow_coder_is_active(local):
    executor,services,workers,_,_,_=local
    units=list(services.contract.units)
    first,second='Independent.Fast','Independent.Slow'
    units[0]=replace(units[0],acceptance=(first,second))
    units[1]=replace(units[1],acceptance=(first,))
    units[2]=replace(units[2],acceptance=(second,),depends_on=())
    links=tuple(replace(services.contract.test_links[0],test_id=name,implementing_units=(unit,))
        for name,unit in ((first,'U1-state'),(second,'U2-system')))
    contract=replace(services.contract,units=tuple(units),test_links=links)
    services.contract=services.manager.contract=executor.contract=contract
    services.tdd=TDDCoordinator(contract,services.integration.path,services.manager.rules)
    slow_started,verified_fast=Event(),Event()
    def code(unit,stage,files,feedback,operation):
        if stage=='refactor':return WorkerPatch({},'No cleanup required')
        if unit.id=='U2-system':
            slow_started.set()
            assert verified_fast.wait(5),'Verifier waited for the entire coding batch'
        else:assert slow_started.wait(3)
        return WorkerPatch({p:b'implemented' for p in unit.owns},'Implement')
    workers.code=code
    def verify(request,root,patches):
        passed=[];failed=[]
        for test in request.test_selection:
            unit=units[1] if test==first else units[2]
            (passed if all((root/p).read_bytes()==b'implemented' for p in unit.owns) else failed).append(test)
        if request.test_selection==(first,) and not failed:
            assert slow_started.is_set()
            verified_fast.set()
        result=Evidence(request.test_selection,request.test_selection,tuple(passed),tuple(failed))
        return VerificationResult(request,'tests','failed' if failed else 'passed',test_result=result,
            failed_tests=tuple(failed),behavioral=True,full_suite_verified=request.full_suite and not failed)
    services.verifier=verify
    assert run(executor)['outcome']=='awaiting_human_review'
    assert verified_fast.is_set()


def test_shared_acceptance_with_serial_dependency_waits_for_both_candidates(local):
    executor,services,workers,_,_,_=local
    units=tuple(replace(u,interfaces=()) for u in services.contract.units)
    contract=replace(services.contract,units=units)
    services.contract=services.manager.contract=executor.contract=contract
    services.tdd=TDDCoordinator(contract,services.integration.path,services.manager.rules)
    calls=[]
    def code(unit,stage,files,feedback,operation):
        if stage=='refactor':return WorkerPatch({},'No cleanup required')
        calls.append(unit.id)
        if unit.id=='U2-system':assert files[units[1].owns[0]]=='implemented'
        return WorkerPatch({p:b'implemented' for p in unit.owns},'Implement')
    workers.code=code
    assert run(executor)['outcome']=='awaiting_human_review'
    assert calls==['U1-state','U2-system']
