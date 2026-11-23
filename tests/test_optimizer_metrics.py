"""Reports distinguish newly paid selector usage from exact cache reuse."""
from pathlib import Path
import sys
from test_evidence_packet_manifest import packet
from unity_coder.core.ai_models import ModelReply

sys.path.insert(0,str(Path('openspec/changes/rehearse-monopoly-game-lobby').resolve()))


def test_cache_usage_is_zero_for_current_dispatch_but_retains_original_charge(tmp_path):
    from context_call_accounting import CachedSelectionCalls
    class Calls:
        def generate(self,*args,**kwargs):return ModelReply('{}',50,10,'reply','deepseek-flash')
    calls=CachedSelectionCalls(Calls(),tmp_path,'policy');p=packet()
    calls.select(p,'U','prompt')
    assert calls.last_accounting['actual_tokens']==[50,10] and not calls.last_accounting['cache_hit']
    calls.select(p,'U','prompt')
    assert calls.last_accounting['actual_tokens']==[0,0] and calls.last_accounting['original_tokens']==[50,10]


def test_deterministic_bypass_reports_why_no_model_was_used(tmp_path):
    from deepseek_context_selector import ContextOptimizer
    result=ContextOptimizer(tmp_path).run(packet(),'U')
    assert result.metrics['selector_accounting']['actual_tokens']==[0,0]
    assert result.metrics['monetary_savings_verified'] is False
    assert result.reasons and result.metrics['elapsed_seconds']>=0
