"""Explicit, lossless late-artifact and SDK excerpt inclusion for this target."""
from pathlib import Path
import re

LATE_GUIDES=(
    'chat-presentation.v46.md','chat-observation.v48.md','chat-transitions.v52.md',
    'chat-row-observation.v54.md','records-oracles.v55.md','records-observation.v57.md',
    'framework-quality-context.v58.md','records-sdk-guidance.v58.md',
)

def late_guidance(root: Path, prefix: str) -> dict[str,str]:
    return {prefix+name:(root/prefix/name).read_text(encoding='utf-8')
        for name in LATE_GUIDES if (root/prefix/name).is_file()}

def framework_api_for_test(source: str, key: str) -> str:
    names=('INavigator.cs','IUserDefault.cs')
    if key=='RECORDS':
        names+=('IDeviceRatingService.cs','IQualityMatchingService.cs','IQualityModifyService.cs')
    return ''.join(section for section in re.split(r'(?=^## )',source,flags=re.M)
        if any(section.split('\n',1)[0].endswith('/'+name) for name in names))
