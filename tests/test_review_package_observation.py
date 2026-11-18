"""Architect reconnect exposes the exact validated production review guidance."""
from test_contracts import bundle
from test_workspaces import workspace
from test_local_executor import local
from test_architect_boundary import planning
from unity_coder.core.architect_boundary import ArchitectBoundary, discover_context
from unity_coder.cli import invoke_local


def test_architect_receives_guidance_on_offer_and_reconnect(local,planning):
    executor,services,workers,_,_,review=local
    payload,sources,_,root=planning
    boundary=ArchitectBoundary(root,executor.root,executor.run_id,executor.contract,
        discover_context(root,payload,sources=sources))
    report=invoke_local(boundary,executor)
    assert report['review_package']==review.state()['package']
    calls=list(workers.calls)
    resumed=invoke_local(boundary,executor)
    assert resumed['review_package']==report['review_package']
    assert resumed['next_action']=='wait' and workers.calls==calls
