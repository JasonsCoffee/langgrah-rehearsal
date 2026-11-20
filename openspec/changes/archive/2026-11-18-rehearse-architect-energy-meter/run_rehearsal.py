"""Trusted composition for one new energy diagnostic run."""
from collections.abc import Mapping
from dataclasses import asdict
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import time

from unity_coder.adapters.unity import UnityAdapter
from unity_coder.adapters.unity.transport import BridgeTransport, local_http
from unity_coder.cli import invoke_local
from unity_coder.core.ai_models import ModelClient, load_ai_config
from unity_coder.core.architect_boundary import ArchitectBoundary, discover_context
from unity_coder.core.budget import BudgetLedger
from unity_coder.core.coding_workers import ModelCodingWorkers
from unity_coder.core.contracts import Unit, load_contract
from unity_coder.core.executor import ProductionExecutor
from unity_coder.core.lifecycle import RunLease, RunLifecycle
from unity_coder.core.local_executor import LocalExecutionServices, WorkerPatch
from unity_coder.core.model_calls import ModelCalls
from unity_coder.core.ownership import confined_path
from unity_coder.core.review import ReviewGate
from unity_coder.core.verification import VerificationLadder
from unity_coder.core.workspaces import WorkspaceManager, git

CHANGE = "rehearse-architect-energy-meter"
RUN = "architect-energy-meter-v1"
PREFIX = "Editor/Script/FrameworkArchitectDemo"
SPEC_DIR = "specs/001-energy-diagnostic"
TEST_PATH = PREFIX + "/Tests/EnergyAcceptance.cs"
NAMESPACE = "FrameworkArchitectDemo"
TESTS = tuple(NAMESPACE + ".Tests.EnergyAcceptance." + name
              for name in ("SpendBounds", "RechargeBounds", "SharedSequence"))
ASSEMBLY = "Framework.ArchitectEnergy.Code"

class ArchitectTestWorkers(ModelCodingWorkers):
    """Supply Architect test bytes through the ordinary test-unit transaction."""

    def code(self, unit: Unit, stage: str, files: Mapping[str, str],
             feedback: str, operation_id: str) -> WorkerPatch:
        if stage == "test_authoring":
            if unit.id != "tests" or unit.owns != (TEST_PATH,) or feedback:
                raise ValueError("Architect tests require review before resubmission")
            prepared = Path(__file__).with_name("EnergyAcceptance.cs").read_bytes()
            return WorkerPatch({TEST_PATH: prepared}, "Architect-authored acceptance for the existing contract")
        if stage == "refactor":
            # Preserve the model and paid ledger, with a smaller allowance for
            # a change-or-no-change answer after the Green implementation.
            worker = ModelCodingWorkers(self.contract, self.coder, self.judge_calls,
                                        max_output_tokens=2500)
            return worker.code(unit, stage, files, feedback, operation_id)
        return super().code(unit, stage, files, feedback, operation_id)

def write(root: Path, path: str, data: str | bytes) -> Path:
    target = confined_path(root, path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data.encode() if isinstance(data, str) else data)
    return target

def encode(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"

def code_path(name: str) -> str:
    return PREFIX + "/Code/" + name + ".cs"

def host_status(game: Path) -> set[bytes]:
    records = git(game, "status", "--short", "--untracked-files=all", "-z").split(b"\0")
    allowed = PREFIX.encode()
    return {record for record in records if record and not (
        record[3:].startswith(allowed + b"/") or record[3:] == allowed + b".meta"
    )}

def main() -> None:
    planning = Path.cwd().resolve()
    change = planning / "openspec/changes" / CHANGE
    root = Path(os.environ["ARCHITECT_DEMO_ROOT"]).resolve(strict=True)
    host = Path(os.environ["ARCHITECT_UNITY_HOST"]).resolve(strict=True)
    game = (host / "Assets/JJGame/monopoly").resolve(strict=True)
    port = int(os.environ["ARCHITECT_BRIDGE_PORT"])
    resume = os.environ.get("ARCHITECT_RECOVER_TRUNCATED") == "1"
    if (not resume and any(root.iterdir())) or (game / PREFIX).exists() or (game / (PREFIX + ".meta")).exists():
        raise ValueError("Run root and Unity destination must be unused")
    if root.is_relative_to(host) or game != host / "Assets/JJGame/monopoly":
        raise ValueError("Unexpected worktree or mount location")
    if Path(git(game, "rev-parse", "--show-toplevel").decode().strip()).resolve() != game:
        raise ValueError("Unexpected target repository identity")
    baseline_status = host_status(game)
    rule_file = game / "AGENTS.md"
    package_lock = host / "Packages/packages-lock.json"
    environment = {"package_lock_sha256": sha256(package_lock.read_bytes()).hexdigest(),
                   "mount": "Assets/JJGame/monopoly", "scope": PREFIX,
                   "target_rules_sha256": sha256(rule_file.read_bytes()).hexdigest(),
                   "bridge_protocol": 1, "verify": "explicit EditMode selections"}

    def health() -> None:
        identity = local_http(port, "GET", "/", None, 5)
        if Path(identity["projectPath"]).resolve() != host:
            raise ValueError("Bridge project identity changed")
        reply = local_http(port, "POST", "/execute", {"command": "FrameworkVerifyCapabilities"}, 5)
        caps = json.loads(reply["data"])
        if (reply["status"] != "success" or caps["protocol"] != 1
                or caps["command"] != "FrameworkVerify" or not {"compile", "tests"} <= set(caps["modes"])
                or not caps["ready"] or caps["active_ticket"]):
            raise ValueError("Dedicated Unity Bridge is unavailable or busy")
        if host_status(game) != baseline_status:
            raise ValueError("Unity module has changes outside the diagnostic scope")
        if (sha256(package_lock.read_bytes()).hexdigest() != environment["package_lock_sha256"]
                or sha256(rule_file.read_bytes()).hexdigest() != environment["target_rules_sha256"]):
            raise ValueError("Unity environment inputs changed")

    health()
    config = load_ai_config(planning / "ai.local.toml")
    instructions = subprocess.check_output(
        ["cmd.exe", "/d", "/c", "pnpm", "exec", "openspec", "instructions", "apply", "--change", CHANGE, "--json"],
        cwd=planning, shell=False,
    )
    sources = {"framework-rules": "AGENTS.md", "execution-boundary": "docs/boundary-contract.md",
               "verification": "docs/verification.md", "adapter": "docs/adapters.md",
               "retry-and-budget": "docs/loop-control.md", "decisions": "docs/decisions.md"}
    context = discover_context(planning, json.loads(instructions), sources=sources)
    repo = root / "module"
    assembly_paths = (PREFIX + "/Code/" + ASSEMBLY + ".asmdef",
                      PREFIX + "/Tests/Framework.ArchitectEnergy.Tests.asmdef")
    if not resume:
        repo.mkdir()
        git(repo, "init", "-b", "codex/architect-energy-baseline")
        git(repo, "config", "user.name", "Framework Architect Rehearsal")
        git(repo, "config", "user.email", "architect-rehearsal@example.invalid")
        git(repo, "config", "core.autocrlf", "false")
        write(repo, assembly_paths[0], encode({"name": ASSEMBLY, "includePlatforms": ["Editor"],
                                              "autoReferenced": False}))
        write(repo, assembly_paths[1], encode({"name": "Framework.ArchitectEnergy.Tests",
                                              "includePlatforms": ["Editor"], "references": [ASSEMBLY],
                                              "optionalUnityReferences": ["TestAssemblies"], "autoReferenced": False}))
        for component in ("EnergySpend", "EnergyRecharge"):
            write(repo, code_path(component), f"""namespace {NAMESPACE}
    {{
        public sealed class {component}
        {{
            public int Apply(int current, int capacity, int amount) => current;
        }}
    }}
    """)
    spec = SPEC_DIR + "/spec.md"
    if not resume:
        write(repo, spec, (change / "specs/architect-energy-diagnostic/spec.md").read_bytes() +
          b"\n## Public bindings\n\nUse FrameworkArchitectDemo.EnergySpend and EnergyRecharge with public instance int Apply(int current, int capacity, int amount). Keep the parameter names. The fixture must be FrameworkArchitectDemo.Tests.EnergyAcceptance with exactly three unparameterized NUnit Test methods named SpendBounds, RechargeBounds and SharedSequence. In each focused test cover ordinary positive, saturation, negative, zero request, zero capacity and each invalid state, including capacity-first and validation on a negative amount. In SharedSequence exercise both units, asserting 4 immediately after spending and 10 after recharging.\n")
    refs = {}
    for name, content in (
        ("presentation", {}),
        ("coding_profile", {"style": "Pure Editor-only arithmetic. Preserve public bindings. Use a block namespace. No Unity or Monopoly API dependencies."}),
        ("environment", environment),
        ("planning-provenance", context.to_dict()),
    ):
        path = SPEC_DIR + "/" + name + ".json"
        refs[name + "_ref"] = {"path": path, "sha256": sha256(((repo / path) if resume else write(repo, path, encode(content))).read_bytes()).hexdigest()}
    criterion = "Editor energy diagnostic"
    test_sets = (TESTS, (TESTS[0], TESTS[2]), (TESTS[1], TESTS[2]))
    units = []
    for index, (unit_id, component, path) in enumerate((
        ("tests", None, TEST_PATH),
        ("spend", "EnergySpend", code_path("EnergySpend")),
        ("recharge", "EnergyRecharge", code_path("EnergyRecharge")),
    )):
        note = ("Author exactly the three specified unparameterized NUnit tests. Read the specification and shells. "
                "Use Assert.Throws<ArgumentOutOfRangeException> to check invalid state and ParamName where needed."
                if component is None else f"Implement {component}.Apply per the spec. Preserve its exact declaration and namespace. "
                "Return an empty file mapping at refactor if the implementation is already minimal.")
        interfaces = [] if component is None else [
            {"symbol": f"{NAMESPACE}.{component}.Apply", "signature": "int Apply(int current, int capacity, int amount)"}
        ]
        units.append(dict(id=unit_id, title=unit_id, role="test" if component is None else "impl",
                          status="active", spec_ref=criterion, owns=[path], acceptance=test_sets[index],
                          depends_on=[], interfaces=interfaces, instructions=note))
    contract_data = dict(format_version=1, contract_version=1, module="architect-energy-diagnostic",
                         module_root=PREFIX + "/Code", test_roots=[PREFIX + "/Tests"], spec_ref=spec,
                         spec_sha256=sha256((repo / spec).read_bytes()).hexdigest(), units=units,
                         test_links=[dict(test_id=test, author_unit="tests", implementing_units=impls, criterion=criterion)
                                     for test, impls in zip(TESTS, (["spend"], ["recharge"], ["spend", "recharge"]))],
                         task_links=[dict(task_ref=f"{CHANGE}:{index}", unit_ids=owners, criteria=[criterion])
                                     for index, owners in enumerate((["tests"], ["spend"], ["recharge"], ["spend", "recharge"]), 1)],
                         ownership_migrations=[], **{k: v for k, v in refs.items() if k != "planning-provenance_ref"})
    contract_path = repo / SPEC_DIR / "contract.v1.json"
    if not resume:
        write(repo, SPEC_DIR + "/contract.v1.json", encode(contract_data))
    adapter = UnityAdapter()
    contract = load_contract(contract_path.read_bytes(), repo, adapter)
    violation = adapter.check_interfaces(
        {path: (repo / path).read_bytes() for path in (code_path("EnergySpend"), code_path("EnergyRecharge"))},
        tuple(interface for unit in contract.units for interface in unit.interfaces),
    )
    if violation:
        raise ValueError("Shell interface conformance failed")
    if not resume:
        git(repo, "add", ".")
        git(repo, "commit", "-m", "Prepare isolated code-only energy diagnostic baseline")
    baseline = git(repo, "rev-parse", "HEAD").decode().strip()
    state = root / "state"
    if not resume:
        state.mkdir()
    lease = RunLease(state, RUN, f"host-{os.getpid()}")
    lease.acquire(owner_alive=lambda _: True)
    try:
        budget = BudgetLedger(state, RUN, input_limit=100000, output_limit=24000, max_cycles=1, max_added_units=1)
        boundary = ArchitectBoundary(planning, state, RUN, contract, context)
        manager = WorkspaceManager(repo, root / "worktrees", contract, adapter, run_id=RUN,
                                   imported_roots=(host / "Assets",), frozen_paths=assembly_paths)
        integration = (manager.reopen_integration if resume else manager.create_integration)(1, baseline)
        worker_type = ArchitectTestWorkers if resume else ModelCodingWorkers
        workers = worker_type(contract, ModelCalls(ModelClient(config.coder, timeout=120), budget, RUN),
                                     ModelCalls(ModelClient(config.judge, timeout=120), budget, RUN),
                                     max_output_tokens=4800 if resume else 3000)
        ladder = VerificationLadder(adapter, BridgeTransport(host, ports=(port,), timeout=180))
        materialized = {}
        allowed = set(assembly_paths) | {p for unit in units for p in unit["owns"]}

        def verify(request, source, patches):
            health()
            if git(source, "rev-parse", "HEAD").decode().strip() != request.candidate_revision:
                raise ValueError("Candidate revision mismatch")
            paths = git(source, "ls-tree", "-r", "--name-only", "-z", "HEAD").decode().split("\0")
            files = {path: confined_path(source, path).read_bytes() for path in paths if path}
            scoped = {p: data for p, data in files.items() if p.startswith(PREFIX + "/")}
            if not set(scoped) <= allowed or not set(request.test_selection) <= set(TESTS):
                raise ValueError("Candidate or selection outside rehearsal scope")

            def snapshot():
                directory = confined_path(game, PREFIX)
                if not directory.exists():
                    return {}
                return {p.relative_to(game).as_posix(): confined_path(game, p.relative_to(game).as_posix()).read_bytes()
                        for p in directory.rglob("*") if p.is_file() and p.suffix != ".meta"}

            if snapshot() != materialized or not materialized.keys() <= scoped.keys():
                raise ValueError("Unexpected host drift or candidate deletion")
            for path, data in scoped.items():
                if materialized.get(path) != data:
                    write(game, path, data)
            materialized.update(scoped)
            reply = local_http(port, "POST", "/execute", {"command": "RefreshAssetDatabase"}, 20)
            if reply.get("status") == "error":
                raise ValueError("Unity asset refresh rejected")
            ticket = reply.get("taskId")
            idle = 0
            for _ in range(75):
                time.sleep(1)
                try:
                    if ticket:
                        status = local_http(port, "GET", "/task/" + ticket, None, 3)
                        if status.get("status") == "error" and "not found" not in str(status):
                            raise RuntimeError("Unity asset refresh failed")
                    health()
                    idle += 1
                    if idle == 3:
                        break
                except (OSError, ValueError, KeyError):
                    idle = 0
            else:
                raise TimeoutError("Unity refresh did not settle")
            if snapshot() != scoped:
                raise ValueError("Materialized Unity files differ from the candidate")
            evidence = ladder.verify(request, contract, source, patches, files, frozen_paths=assembly_paths)
            health()
            if snapshot() != scoped:
                raise ValueError("Unity sources changed during verification")
            write(root, "receipts/" + request.request_id + ".json", encode(asdict(evidence)))
            print(request.request_id, evidence.status, evidence.failed_tests, flush=True)
            return evidence

        # The rehearsal stops with pending review. A later trusted operator must
        # bind real session authentication before importing a human decision.
        review = ReviewGate(RunLifecycle(state, RUN, contract_version=1, contract_sha256=contract.sha256),
                            authenticate_human=lambda credential: None)
        services = LocalExecutionServices(manager, integration, budget, workers, verify, review,
                                           preflight=health, test_config_paths=assembly_paths, max_attempts=2)
        executor = ProductionExecutor(state, RUN, contract, budget, lease, services)
        if not resume:
            write(root, "prepared.json", encode({"baseline": baseline, "contract_sha256": contract.sha256,
                                              "coder": config.coder.model, "judge": config.judge.model,
                                              "budget": {"input": 100000, "output": 24000, "cycles": 1, "added_units": 1}}))
        if resume:
            run_state = state / ".agent/runs" / RUN
            records = [json.loads(p.read_bytes()) for p in (run_state / "model-calls").glob("*.json")]
            ledger = json.loads((run_state / "budget.json").read_bytes())
            expected = {f"v1-step{i}-prepare-tests-tests": cap for i, cap in ((1, 3000), (2, 6000))}
            reconciled = set()
            for record in records:
                call = record["identity"]["call_id"]
                failed = record.get("failure", {})
                actual = ledger["calls"].get(call, {}).get("actual")
                if (call in expected and failed.get("finish_reason") == "length"
                        and failed.get("output_tokens") == expected[call]
                        and actual == [failed.get("input_tokens"), failed.get("output_tokens")]):
                    reconciled.add(call)
            if (len(records) != len(expected) or reconciled != expected.keys()
                    or git(integration.path, "rev-parse", "HEAD").decode().strip() != baseline
                    or git(integration.path, "status", "--porcelain")):
                raise ValueError("Truncated-response recovery identity did not reconcile")
            if executor.stage() == "ended":
                executor.resume_operational(reconcile=lambda: True)
            # The old terminal receipt is retired by the next graph advance.
            from unity_coder.graph import graph
            graph.invoke({"run_id": RUN, "contract_sha256": contract.sha256},
                         config={"configurable": {"executor": executor}, "recursion_limit": 100})
            report = boundary.observe()
        else:
            report = invoke_local(boundary, executor)
        write(root, "observation.json", encode(report))
        print(encode({"run": RUN, "result": report.get("result"), "usage": budget.totals()}), flush=True)
    finally:
        lease.release()

if __name__ == "__main__":
    main()



