"""Frozen checks for the missing late-guidance and Records SDK prompt wiring."""
from prompt_guidance import late_guidance, framework_api_for_test, LATE_GUIDES

def test_all_declared_late_guides_are_supplied_verbatim(tmp_path):
    spec=tmp_path/'specs/monopoly-game-lobby';spec.mkdir(parents=True)
    expected={}
    for name in LATE_GUIDES:
        value='real source '+name+' 原始内容\n'
        (spec/name).write_text(value,encoding='utf-8')
        expected['specs/monopoly-game-lobby/'+name]=value
    (spec/'unrelated-secret.txt').write_text('must not include')
    assert late_guidance(tmp_path,'specs/monopoly-game-lobby/')==expected

def test_missing_future_guides_are_not_invented(tmp_path):
    assert late_guidance(tmp_path,'specs/monopoly-game-lobby/')=={}

def test_records_receives_exact_quality_and_preference_api_sections():
    names=('INavigator.cs','IUserDefault.cs','IDeviceRatingService.cs',
        'IQualityMatchingService.cs','IQualityModifyService.cs','Other.cs')
    source=''.join('## Assets/SDK/'+name+'\nSHA256 original\n'+name+' exact signature\n' for name in names)
    selected=framework_api_for_test(source,'RECORDS')
    for name in names[:-1]:assert name+' exact signature' in selected
    assert 'Other.cs' not in selected
    assert 'SHA256 original' in selected

def test_existing_card_excerpt_remains_scoped():
    source='## SDK/INavigator.cs\nnav\n## SDK/IUserDefault.cs\nprefs\n## SDK/IQualityModifyService.cs\nquality\n'
    assert framework_api_for_test(source,'CARDS')=='## SDK/INavigator.cs\nnav\n## SDK/IUserDefault.cs\nprefs\n'
