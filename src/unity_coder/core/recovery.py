"""Authenticated cycle-budget amendments; preserve abandoned run provenance."""
from collections.abc import Callable
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
import re

from .architect_boundary import PlanningContext
from .budget import BudgetLedger
from .contracts import Contract
from .journal import run_prefix
from .lifecycle import RunLease
from .ownership import confined_path, portable_path
from .progress import ProgressStore
from .storage import atomic_write, file_guard


@dataclass(frozen=True)
class RecoveryGrant:
    """Trusted authentication result, never supplied by coding units."""
    recovery_id: str
    actor: str
    provenance: str
    run_id: str
    previous_sha256: str
    result_sha256: str
    max_cycles: int


@dataclass(frozen=True)
class TokenRecoveryGrant(RecoveryGrant):
    """Explicit total token ceilings; all existing charges remain authoritative."""
    input_limit: int
    output_limit: int


def recover_abandoned_run(planning_root: Path, state_root: Path, run_id: str,
                          previous: Contract, current: Contract, context: PlanningContext,
                          budget: BudgetLedger, lease: RunLease, *, credential: str,
                          authenticate: Callable[[str], RecoveryGrant | None],
                          workers_reconciled: Callable[[], bool],
                          candidate_reconciled: Callable[[str], bool]) -> None:
    """Recover a budget stop into the next validated contract version.

    The host authenticates explicit human authorization and reconciles retained
    Git and worker identities. Both contracts must pass the consecutive loader.
    No model invocation, Git mutation or acceptance decision occurs here. Token
    ceilings remain unchanged unless a TokenRecoveryGrant explicitly extends
    them. Paid-call records and all prior cycle histories remain unchanged.
    """
    prefix = run_prefix(run_id)
    if (lease.root.resolve() != state_root.resolve() or lease.run_id != run_id
        or budget.root.resolve() != state_root.resolve() or budget.path != prefix+'/budget.json'):
        raise ValueError('Recovery resources belong to another run')
    lease.assert_held()
    grant = authenticate(credential)
    if (not isinstance(grant, RecoveryGrant) or grant.run_id != run_id
        or grant.previous_sha256 != previous.sha256
        or not isinstance(grant.recovery_id,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,80}',grant.recovery_id)
        or not isinstance(grant.actor,str) or not grant.actor.strip()
        or type(grant.max_cycles) is not int or grant.max_cycles < current.contract_version
        or not isinstance(grant.result_sha256,str) or not re.fullmatch(r'[0-9a-f]{64}',grant.result_sha256)):
        raise ValueError('Matching authenticated recovery authorization required')
    portable_path(grant.provenance)
    if current.contract_version != previous.contract_version+1:
        raise ValueError('Recovery contract must be consecutive')
    context.validate(planning_root)
    known = {t.task_ref for t in context.tasks}
    if any(link.task_ref not in known for link in current.task_links):
        raise ValueError('Unknown recovery task')
    if not workers_reconciled():
        raise ValueError('Workers must be reconciled before recovery')
    identity = dict(format_version=1,run_id=run_id,contract_version=current.contract_version,
                    contract_sha256=current.sha256,context=context.to_dict())
    intent_path = prefix+'/recoveries/'+grant.recovery_id+'.json'
    # Match the normal boundary -> budget lock order. No worker or model callback
    # executes under these guards, and the run lease excludes another driver.
    with file_guard(state_root,prefix+'/boundary.guard'), file_guard(state_root,budget.guard):
        path = confined_path(state_root,intent_path)
        if path.exists():
            intent = json.loads(path.read_bytes())
            if intent['authorization'] != asdict(grant) or intent['next'] != identity:
                raise ValueError('Recovery intent identity changed')
        else:
            saved = {}
            names = ('invocation.json','result.json','review.json','status.json','progress.jsonl',
                     'budget.json',f'executor-v{previous.contract_version}.json',
                     f'dossier-v{previous.contract_version}.json')
            for name in names:
                source = confined_path(state_root,prefix+'/'+name)
                if source.exists(): saved[name] = source.read_bytes().hex()
            required = ('invocation.json','result.json','budget.json',names[-2],names[-1])
            if any(name not in saved for name in required):
                raise ValueError('Recovery requires complete terminal evidence')
            result_raw = bytes.fromhex(saved['result.json'])
            outcome = json.loads(result_raw)
            dossier = json.loads(bytes.fromhex(saved[names[-1]]))
            invocation = json.loads(bytes.fromhex(saved['invocation.json']))
            executor = json.loads(bytes.fromhex(saved[names[-2]]))
            for record in (outcome,dossier,invocation,executor):
                if (record.get('run_id') != run_id or record.get('contract_version') != previous.contract_version
                    or record.get('contract_sha256') != previous.sha256):
                    raise ValueError('Abandoned invocation identity mismatch')
            if (sha256(result_raw).hexdigest() != grant.result_sha256
                or outcome.get('outcome') != 'abandon' or outcome.get('reason') != 'budget'
                or dossier.get('reason') != 'budget' or executor.get('stage') != 'ended'
                or executor.get('pending') is not None or not executor.get('steps')
                or executor['steps'][-1].get('result') != outcome):
                raise ValueError('Recovery requires the exact completed budget abandonment')
            before = json.loads(bytes.fromhex(saved['budget.json']))
            used = budget._totals(before)
            old_limits = before['limits']
            if (old_limits != budget.limits or not before.get('stopped')
                or before['stopped'].get('reason') != 'budget'
                or previous.contract_version != len(before['cycles'])
                or previous.contract_version > old_limits[2]):
                raise ValueError('Stopped budget identity or cycle history mismatch')
            new_limits=list(old_limits)
            new_limits[2]=grant.max_cycles
            if isinstance(grant,TokenRecoveryGrant):
                new_limits[:2]=[grant.input_limit,grant.output_limit]
                if (any(type(n) is not int or n<1 for n in new_limits)
                    or any(new<old for new,old in zip(new_limits,old_limits))
                    or new_limits==old_limits
                    or used[0]>=new_limits[0] or used[1]>=new_limits[1]):
                    raise ValueError('Authorized bounds must grow without shrinking or resetting usage')
            elif (len(before['cycles']) != old_limits[2] or grant.max_cycles <= old_limits[2]
                  or used[0]>=old_limits[0] or used[1]>=old_limits[1]):
                raise ValueError('Only exhausted cycles with remaining token allowance can recover')
            lineages = {u.id:list(current.lineage_for(u.id)) for u in current.units}
            prior = before['cycles'][str(previous.contract_version)]
            if (prior['sha256'] != previous.sha256 or not prior['lineages'].keys() <= lineages.keys()
                or len(lineages.keys()-prior['lineages'].keys()) > old_limits[3]
                or any(lineages[u] != history for u,history in prior['lineages'].items())):
                raise ValueError('Recovery must preserve prior repair lineage and unit growth limits')
            after = json.loads(json.dumps(before))
            after['limits'] = new_limits
            after.pop('stopped')
            after['cycles'][str(current.contract_version)] = dict(sha256=current.sha256,lineages=lineages)
            intent = dict(state='pending',authorization=asdict(grant),next=identity,
                          saved=saved,budget_after=after,candidate=outcome.get('candidate_revision'))
            # Validate any prior archive collisions before creating intent.
            for name,content in saved.items():
                archive = confined_path(state_root,prefix+f'/cycles/v{previous.contract_version}/'+name)
                if archive.exists() and archive.read_bytes().hex() != content:
                    raise ValueError('Archived abandonment bytes changed')
            if not isinstance(intent['candidate'],str) or not candidate_reconciled(intent['candidate']):
                raise ValueError('Retained candidate must be reconciled')
            atomic_write(state_root,intent_path,json.dumps(intent,sort_keys=True).encode())
        if not isinstance(intent['candidate'],str) or not candidate_reconciled(intent['candidate']):
            raise ValueError('Retained candidate changed during recovery')
        active_invocation = confined_path(state_root,prefix+'/invocation.json')
        budget_path = confined_path(state_root,budget.path)
        ledger = json.loads(budget_path.read_bytes())
        if intent['state'] == 'complete':
            if (json.loads(active_invocation.read_bytes()) != identity
                or ledger['limits'] != intent['budget_after']['limits']
                or ledger['cycles'].get(str(current.contract_version)) != intent['budget_after']['cycles'][str(current.contract_version)]):
                raise ValueError('Completed recovery is no longer current')
            budget.limits = list(ledger['limits'])
            return
        before = json.loads(bytes.fromhex(intent['saved']['budget.json']))
        if ledger not in (before,intent['budget_after']):
            raise ValueError('Budget changed during pending recovery')
        invocation_raw = active_invocation.read_bytes()
        if invocation_raw.hex() != intent['saved']['invocation.json'] and json.loads(invocation_raw) != identity:
            raise ValueError('Active invocation changed during pending recovery')
        for name,content in intent['saved'].items():
            archive = prefix+f'/cycles/v{previous.contract_version}/'+name
            target = confined_path(state_root,archive)
            if target.exists() and target.read_bytes().hex() != content:
                raise ValueError('Archived abandonment bytes changed')
            # Immutable executor and dossier remain available at their original
            # paths too. Reject changes even on an interrupted recovery.
            if name.startswith(('executor-','dossier-')):
                if confined_path(state_root,prefix+'/'+name).read_bytes().hex() != content:
                    raise ValueError('Terminal evidence changed during recovery')
            atomic_write(state_root,archive,bytes.fromhex(content))
        for name in ('result.json','review.json'):
            active = confined_path(state_root,prefix+'/'+name)
            if active.exists():
                if active.read_bytes().hex() != intent['saved'].get(name):
                    raise ValueError('Active terminal receipt changed during recovery')
                active.unlink()
        ProgressStore(state_root,run_id,contract_version=current.contract_version,
                      contract_sha256=current.sha256).transition(previous.contract_version,previous.sha256)
        atomic_write(state_root,prefix+'/invocation.json',json.dumps(identity,sort_keys=True).encode())
        # Publish the amended ledger last: until then the original dispatch stop
        # remains effective. One atomic write preserves calls and adds cycle N+1.
        atomic_write(state_root,budget.path,json.dumps(intent['budget_after'],sort_keys=True).encode())
        budget.limits = list(intent['budget_after']['limits'])
        intent['state'] = 'complete'
        atomic_write(state_root,intent_path,json.dumps(intent,sort_keys=True).encode())
