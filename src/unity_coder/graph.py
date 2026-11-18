"""Production stage graph; services are injected by the trusted local host."""

from typing import TypedDict
from langchain_core.runnables import RunnableConfig

from langgraph.graph import END, START, StateGraph
from unity_coder.core.executor import ProductionExecutor, STAGES


class WorkflowState(TypedDict, total=False):
    run_id: str
    contract_sha256: str
    stage: str
    outcome: str | None


def _executor(state: WorkflowState, config: RunnableConfig) -> ProductionExecutor:
    executor = config.get("configurable", {}).get("executor")
    if not isinstance(executor, ProductionExecutor):
        raise ValueError("A trusted host must supply the production executor")
    if state.get("run_id") != executor.run_id or state.get("contract_sha256") != executor.contract.sha256:
        raise ValueError("Graph invocation differs from executor identity")
    return executor


def reconnect(state: WorkflowState, config: RunnableConfig) -> WorkflowState:
    executor = _executor(state, config)
    return {"stage":executor.stage(), "outcome":executor.outcome()}


def _node(stage: str):
    def execute(state: WorkflowState, config: RunnableConfig) -> WorkflowState:
        executor = _executor(state, config)
        report = executor.advance(stage)
        return {"stage":report.next_stage, "outcome":executor.outcome()}
    return execute


def route(state: WorkflowState) -> str:
    return state["stage"]


builder = StateGraph(WorkflowState)
builder.add_node("reconnect", reconnect)
builder.add_edge(START, "reconnect")
routes = {stage:stage for stage in STAGES} | {"ended":END}
builder.add_conditional_edges("reconnect", route, routes)
for stage in STAGES:
    builder.add_node(stage, _node(stage))
    builder.add_conditional_edges(stage, route, routes)
graph = builder.compile()
