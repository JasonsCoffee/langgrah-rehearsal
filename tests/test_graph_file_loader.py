"""Frozen deployment loader regression: langgraph.json uses a file entry point."""
import runpy


def test_file_entry_point_loads_production_stages_without_package_context():
    exported=runpy.run_path("src/unity_coder/graph.py")["graph"]
    nodes=exported.get_graph().nodes
    assert {"prepare","red","code","verify","refactor","review","finalize"} <= nodes.keys()
