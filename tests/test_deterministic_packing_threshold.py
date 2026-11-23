"""Free exact packing must not inherit the paid selector's break-even gate."""
from pathlib import Path
import sys
import pytest
from test_evidence_packet_manifest import packet
sys.path.insert(0,str(Path('openspec/changes/rehearse-monopoly-game-lobby').resolve()))


@pytest.mark.parametrize('qualified',[False,True])
def test_mandatory_heavy_packet_keeps_small_free_reduction(tmp_path,qualified):
    from evidence_packet import Source
    from deepseek_context_selector import ContextOptimizer
    from evidence_context_guard import validate_delivery
    class NoPaidCall:
        def select(self,*args):pytest.fail('A mandatory-heavy packet must not pay for selection')
    p=packet((Source('large','Runtime/Large.cs','class Large { string Text="'+'x'*10000+'"; }','dependency'),))
    result=ContextOptimizer(tmp_path,NoPaidCall(),qualified=qualified).run(p,'U')
    assert 0<result.metrics['byte_reduction']<.2
    assert result.decision=='use_optimized', 'A free lossless reduction is useful below the paid 20% gate'
    assert result.metrics['delivered_bytes']<result.metrics['canonical_bytes']
    assert result.metrics['selector_accounting']['actual_tokens']==[0,0]
    for source in p.sources:
        if source.kind!='optional':assert source.content in result.optimized_input
    validate_delivery(p,result)
