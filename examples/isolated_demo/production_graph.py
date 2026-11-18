"""Opt-in exported-graph rehearsal on the existing isolated host fixture."""

from dataclasses import asdict
import json
import os
from pathlib import Path

import run as demo
from unity_coder.core.ai_models import load_ai_config, ModelClient
from unity_coder.core.budget import BudgetLedger
from unity_coder.core.coding_workers import ModelCodingWorkers
from unity_coder.core.executor import ProductionExecutor
from unity_coder.core.lifecycle import RunLease, RunLifecycle
from unity_coder.core.local_executor import LocalExecutionServices
from unity_coder.core.model_calls import ModelCalls
from unity_coder.core.review import ReviewGate
from unity_coder.core.verification import VerificationLadder
from unity_coder.graph import graph


def main() -> None:
    run_id = "production-graph-" + demo.ATTEMPT
    settings = load_ai_config(Path("ai.local.toml"))
    baseline = json.loads((demo.ROOT / "baseline.json").read_bytes())
    frozen = json.loads((demo.ROOT / "freeze.json").read_bytes())
    rules = demo.UnityAdapter()
    contract = demo.load_contract((demo.REPO / "specs/demo/contract.v1.json").read_bytes(),demo.REPO,rules)
    manager = demo.WorkspaceManager(demo.REPO,demo.ROOT / "worktrees",contract,rules,run_id=run_id,
        imported_roots=(demo.HOST / "Assets",),frozen_paths=tuple(frozen))
    resume = os.environ.get("DEMO_RESUME") == "1"
    integration = (manager.reopen_integration if resume else manager.create_integration)(1,baseline["commit"])
    state = demo.ROOT / "production-state"
    budget = BudgetLedger(state,run_id,input_limit=100000,output_limit=32768,max_cycles=3,max_added_units=2)
    workers = ModelCodingWorkers(contract,ModelCalls(ModelClient(settings.coder,timeout=120),budget,run_id),
                                  ModelCalls(ModelClient(settings.judge,timeout=120),budget,run_id))
    transport = demo.BridgeTransport(demo.HOST,ports=(demo.PORT,),timeout=180)
    ladder = VerificationLadder(rules,transport)
    def preflight():
        for path, expected in frozen.items():
            if demo.digest((integration.path / path).read_bytes()) != expected:
                raise ValueError("Frozen fixture input changed")
        health = demo.local_http(demo.PORT,"GET","/",None,5)
        if Path(health["projectPath"]).resolve() != demo.HOST:
            raise ValueError("Wrong dedicated host")
    def verify(request,source,patches):
        for path in (source / demo.PREFIX).rglob("*"):
            if path.is_file():
                relative = path.relative_to(source).as_posix()
                target = demo.GAME / relative
                if not target.exists() or target.read_bytes() != path.read_bytes():
                    demo.write(demo.GAME,relative,path.read_bytes())
        demo.refresh()
        snapshot = demo.snapshot(source)
        if demo.snapshot(demo.GAME) != snapshot:
            raise ValueError("Fixture host differs from committed candidate")
        paths = demo.git(source,"ls-tree","-r","--name-only","-z","HEAD").decode().split("\0")
        files = {p:(source / p).read_bytes() for p in paths if p}
        evidence = ladder.verify(request,contract,source,patches,files,frozen_paths=tuple(frozen))
        if demo.snapshot(demo.GAME) != snapshot:
            raise ValueError("Fixture changed during verification")
        demo.emit(run_id + "-" + request.request_id,asdict(evidence))
        print(request.request_id,evidence.status,"failed",len(evidence.failed_tests),flush=True)
        return evidence
    review = ReviewGate(RunLifecycle(state,run_id,contract_version=1,contract_sha256=contract.sha256),
                        authenticate_human=lambda _:None)
    services = LocalExecutionServices(manager,integration,budget,workers,verify,review,
                                       preflight=preflight,test_config_paths=tuple(frozen))
    lease = RunLease(state,run_id,"host-" + str(os.getpid()))
    lease.acquire(owner_alive=lambda _:True)
    executor = ProductionExecutor(state,run_id,contract,budget,lease,services)
    try:
        if resume:
            preflight()
            demo.refresh()
            executor.resume_operational(reconcile=lambda:True)
        result = graph.invoke({"run_id":run_id,"contract_sha256":contract.sha256},
                              config={"configurable":{"executor":executor},"recursion_limit":100})
        demo.emit(run_id + "-summary",{"run_id":run_id,"outcome":result.get("outcome"),
            "coder":settings.coder.model,"judge":settings.judge.model,"usage":budget.totals(),
            "integration_commit":demo.git(integration.path,"rev-parse","HEAD").decode().strip(),
            "stages":services._statuses(),"exported_graph_exercised":True,"human_accepted":False})
        print("Graph outcome:",result.get("outcome"),flush=True)
    finally:
        lease.release()


if __name__ == "__main__":
    main()
