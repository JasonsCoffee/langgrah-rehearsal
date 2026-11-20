"""Keep current compiler evidence separate from unrelated behavioral bodies."""
from hashlib import sha256
import json


def curate(gate: str, status: str, files: dict[str,str], owned: tuple[str,...]) -> dict[str,str]:
    if gate!='compile' or status!='failed':return files
    if any(p not in files for p in owned):raise ValueError('Compiler context must retain every owned source')
    omitted={p:sha256(text.encode()).hexdigest() for p,text in files.items()
             if p not in owned and p.startswith(('Tests/','readonly-retained-proposal/'))}
    result={p:text for p,text in files.items() if p not in omitted}
    result['readonly-compile-context/provenance.json']=json.dumps({
        'gate':'compile','no_tests_executed':True,'all_current_owned_sources_preserved':True,
        'omitted_provided_text_sha256':omitted,
        'note':'Only read-only test bodies and historical proposals are omitted from this compiler-only prompt. Actual files, frozen hashes, criteria, specification, coding rules and mechanical diagnostics remain unchanged. These are hashes of provided text, not the physical frozen-file manifest.'},ensure_ascii=False)
    return result
