"""Apply the explicit 100m/12m and eighty-cycle grant at a supported native budget boundary."""
from dataclasses import asdict
from hashlib import sha256
import hmac
import json
import os
from pathlib import Path
import secrets
import subprocess

from overlay_host import OverlayHost
from operational_transport import retained_run_reservations, retained_coder_request_failure, retained_coder_connection_failure, retained_sol_review_failure, retained_key_limit_failure, retained_transport_failure, retained_calibration_failure, retained_tls_probe_failure
from unity_coder.adapters.unity import UnityAdapter
from unity_coder.core.ai_models import load_ai_config
from unity_coder.core.architect_boundary import discover_context
from unity_coder.core.budget import BudgetLedger
from unity_coder.core.contracts import load_contract
from unity_coder.core.lifecycle import RunLease
from unity_coder.core.recovery import TokenRecoveryGrant, recover_abandoned_run
from unity_coder.core.storage import atomic_write
from unity_coder.core.target_profiles import load_profile
from unity_coder.core.workspaces import git


def main() -> None:
    framework = Path.cwd().resolve()
    directory = Path(__file__).parent
    root = Path(os.environ['LOBBY_RUN_ROOT']).resolve(strict=True)
    state = root / 'trusted-state'
    run = state / '.agent/runs/monopoly-game-lobby'
    result_raw = (run / 'result.json').read_bytes()
    result = json.loads(result_raw)
    if result['outcome'] != 'abandon' or result['reason'] != 'budget':
        raise ValueError('The grant cannot amend an active, rework or operational run')
    old_version = result['contract_version']
    version = old_version + 1
    if not 55 <= old_version <= 60:
        raise ValueError('Grant requires a budget-abandoned predecessor in the authorized continuation')
    policy = json.loads((state / 'budget-policy.json').read_bytes())
    if (policy['input_limit'], policy['output_limit'], policy['max_cycles']) != (75000000, 12000000, 60):
        raise ValueError('Unexpected pre-amendment policy; do not replay a grant')
    approval=json.loads((state/'budget-amendments/input-100m-cycles80-user-approval.json').read_bytes())
    if approval['reply']!='Approve 100M input / 12M output / 80 cycles' or approval['approved_limits']!={'input_limit':100000000,'output_limit':12000000,'max_cycles':80}:
        raise ValueError('Exact explicit approval required')
    proof = json.loads((run / ('abandon-v'+str(old_version)+'.json')).read_bytes())
    source = root / 'worktrees' / ('architect-v'+str(version))
    if source.exists():
        raise ValueError('Preserve existing preparation and reconcile explicitly')
    prior_state=json.loads((run / ('services-v'+str(old_version)) / 'state.json').read_bytes())
    if prior_state['tdd']['frozen'] is not None:
        raise ValueError('This host recovery restarts preparation; frozen implementation-stage continuation needs a separately verified capability. No tests or state were unfrozen.')
    retained = result['candidate_revision']
    if git(root / 'module', 'rev-parse', proof['branch']).decode().strip() != retained:
        raise ValueError('Terminal retained candidate differs')
    git(root / 'module', 'worktree', 'add', '-b', 'codex/lobby-architect-v'+str(version), str(source), retained)
    spec = source / 'specs/monopoly-game-lobby'
    old_path = spec / ('contract.v'+str(old_version)+'.json')
    current = json.loads(old_path.read_bytes()) | {
        'contract_version': version,
        'previous_contract_sha256': sha256(old_path.read_bytes()).hexdigest(),
        'ownership_migrations': [],
    }
    (spec / ('contract.v'+str(version)+'.json')).write_text(json.dumps(current, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='')
    rules = UnityAdapter()
    contracts = []
    for n in range(1, version+1):
        contracts.append(load_contract((spec / ('contract.v'+str(n)+'.json')).read_bytes(), source, rules, previous=contracts[-1] if contracts else None, max_cycles=80))
    previous, contract = contracts[-2:]
    load_profile((source / current['coding_profile_ref']['path']).read_bytes(), source, rules=rules, allowed_mount='Assets/JJGame/monopoly', implementation_roots=('Runtime/Script',), test_roots=('Tests/Runtime/Script/LobbyRehearsal',)).validate_contract(contract)
    git(source, 'add', 'specs/monopoly-game-lobby')
    git(source, '-c', 'user.name=Lobby Rehearsal', '-c', 'user.email=rehearsal@example.invalid', 'commit', '-m', 'Prepare consecutive recovery under explicit 100m token grant')
    raw = subprocess.check_output(['pnpm.cmd', 'exec', 'openspec', 'instructions', 'apply', '--change', 'rehearse-monopoly-game-lobby', '--json'], cwd=framework)
    (framework / '.agent/lobby-apply.json').write_bytes(raw)
    context = discover_context(framework, json.loads(raw), sources=json.loads((framework / '.agent/lobby-sources.json').read_bytes()))
    budget = BudgetLedger(state, 'monopoly-game-lobby', input_limit=75000000, output_limit=12000000, max_cycles=60, max_added_units=2)
    grant = TokenRecoveryGrant('lobby-extend-100m', 'human-user', 'recovery-authorizations/extend-100m.json', 'monopoly-game-lobby', previous.sha256, sha256(result_raw).hexdigest(), 80, 100000000, 12000000)
    authorization = {
        'grant': asdict(grant),
        'authority': 'explicit user reply in active session',
        'authorization_source': 'explicit user reply to request_user_input_async call_2ce34377c75c41049cdcb494ea958db0, 2026-11-20',
        "reply": "Approve 100M input / 12M output / 80 cycles",
        'preserve_all_charges_and_reservations': True,
        'preserve_models_overlay_frozen_tests_and_independent_judge': True,
        'authorized_cycle_ceiling': 80,
        'cycle_authorization': 'Explicit user reply approves eighty cycles with the new input ceiling',
        'human_acceptance_granted': False,
    }
    for name, digest in {'trusted_overlay.py': '851246aa66bc5cb68a18ed97d6df0e29f0c63ef5071e94bf3329e45c89b5479f', 'overlay_host.py': '53301fcbc46abc2c7d316b9fd82af64e8fdc19bfbe71a23d8a0f19390ac2c190'}.items():
        if sha256((directory / name).read_bytes()).hexdigest() != digest:
            raise ValueError('Trusted overlay source changed')
    settings = load_ai_config(framework / 'ai.local.toml')
    receipts = sorted((run / 'model-calls').glob('*.json'), key=lambda p: p.stat().st_mtime, reverse=True)
    for role, config in (('coder', settings.coder), ('judge', settings.judge)):
        identity = next(json.loads(p.read_bytes())['identity'] for p in receipts if json.loads(p.read_bytes())['identity']['role'] == role)
        for key in ('model', 'provider', 'effort', 'temperature_mode', 'upstream_provider'):
            if getattr(config, key) != identity.get(key, ''):
                raise ValueError('Configured model policy changed: '+role+'/'+key)

    def candidate_reconciled(candidate: str) -> bool:
        old = root / 'worktrees' / proof['workspace']
        return (candidate == retained == proof['candidate_revision']
                and proof['state'] == 'complete'
                and git(root / 'module', 'rev-parse', proof['branch']).decode().strip() == candidate
                and git(old, 'rev-parse', 'HEAD').decode().strip() == proof['restored_revision']
                and not git(old, 'branch', '--show-current').decode().strip()
                and not git(old, 'status', '--porcelain')
                and not git(source, 'status', '--porcelain'))

    def workers_reconciled() -> bool:
        retained_run_reservations(state,json.loads((run / 'budget.json').read_bytes()))
        return json.loads((run / ('services-v'+str(old_version)) / 'effects/transaction.json').read_bytes()).get('complete') is True

    lease = RunLease(state, 'monopoly-game-lobby', 'recovery-100m-'+str(os.getpid()))
    host = OverlayHost()
    lease.acquire(owner_alive=lambda _: True)
    host.lease.acquire(owner_alive=lambda _: True)
    try:
        host.preflight()
        overlay = host.overlay.read()
        host.overlay.assert_ready(overlay['candidate'])
        atomic_write(state, grant.provenance, json.dumps(authorization, ensure_ascii=False, indent=2).encode())
        credential = secrets.token_urlsafe(32)
        digest = sha256(credential.encode()).digest()

        def authenticate(value: str) -> TokenRecoveryGrant | None:
            if not hmac.compare_digest(sha256(value.encode()).digest(), digest):
                return None
            return grant if json.loads((state / grant.provenance).read_bytes()) == authorization else None

        recover_abandoned_run(framework, state, 'monopoly-game-lobby', previous, contract, context, budget, lease, credential=credential, authenticate=authenticate, workers_reconciled=workers_reconciled, candidate_reconciled=candidate_reconciled)
        atomic_write(state, 'recovery-authorizations/budget-policy-before-100m.json', json.dumps(policy, indent=2).encode())
        policy.update(input_limit=100000000, output_limit=12000000, max_cycles=80)
        atomic_write(state, 'budget-policy.json', json.dumps(policy, indent=2).encode())
        active = {'version': version, 'candidate': git(source, 'rev-parse', 'HEAD').decode().strip(), 'contract_source': 'architect-v'+str(version), 'contract_sha256': contract.sha256}
        atomic_write(state, 'current-execution.json', json.dumps(active, indent=2).encode())
        evidence = active | {'preserved_usage': budget.totals(), 'limits': budget.limits, 'retained_candidate': retained, 'original_host_files': len(overlay['baseline']), 'baseline_sha256': overlay['baseline_sha256'], 'original_baseline_checked': True, 'human_accepted': False}
        atomic_write(state, 'recovery-authorizations/recovery-applied-100m.json', json.dumps(evidence, indent=2).encode())
        (directory / 'evidence/recovery-applied-100m.json').write_text(json.dumps(evidence, indent=2)+'\n', encoding='utf-8', newline='')
        print(json.dumps(evidence), flush=True)
    finally:
        host.lease.release()
        lease.release()


if __name__ == '__main__':
    main()
