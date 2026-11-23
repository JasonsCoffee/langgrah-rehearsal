"""Independent protocol expectations are fixed before paired paid comparison."""
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path('openspec/changes/rehearse-monopoly-game-lobby').resolve()))


def test_paired_corpus_has_four_distinct_classes_and_coverage_before_dispatch():
    from mixed_backend_pilot import build_case
    cases=json.loads(Path('tests/fixtures/context_optimization/paired_pilot.json').read_text(encoding='utf-8'))
    assert len({c['class'] for c in cases})==4
    for case in cases:
        p=build_case(case,'candidate','contract','policy')
        assert p.identity['fixture_scope']=='protocol_only_not_game_verification'
        assert all(s.content in p.canonical_input for s in p.sources)
        assert 'expected' not in p.canonical_input
