"""Target-only lossless curation of required author evidence."""
from collections.abc import Mapping
from hashlib import sha256
import json
from pathlib import PurePosixPath
from tree_sitter import Language,Parser
import tree_sitter_c_sharp


def compact_author_context(unit_id: str, owns: tuple[str,...], files: Mapping[str,str]) -> dict[str,str]:
    result=dict(files)
    primary=PurePosixPath(owns[0]).stem
    omitted={}
    for path in tuple(result):
        duplicate=path.endswith(('proposal.md','selected-original-stories.md','test-preparation-findings.v4.json'))
        historical=(path in owns and PurePosixPath(path).name.startswith('LobbyPresentationTests.'))
        historical=historical or (path.startswith('Tests/') and path.endswith('.acceptance.md') and path not in owns)
        if duplicate or historical:
            omitted[path]=sha256(result.pop(path).encode()).hexdigest()
    if unit_id!='TEST-HARNESS':
        for path in tuple(result):
            if not path.endswith('LobbyHarness.cs'):continue
            raw=result[path].encode()
            tree=Parser(Language(tree_sitter_c_sharp.language())).parse(raw)
            if tree.root_node.has_error:raise ValueError('Invalid harness evidence cannot be curated')
            spans=[]
            def visit(node):
                if node.type=='class_declaration' and node.child_by_field_name('name').text==b'LobbyHarnessTests':
                    spans.append((node.start_byte,node.end_byte));return
                for child in node.children:visit(child)
            visit(tree.root_node)
            for start,end in reversed(spans):raw=raw[:start]+b'\n'+raw[end:]
            result[path]=raw.decode()
    result['context-omissions.json']=json.dumps({'historical_or_duplicate_source_sha256':omitted,
        'primary_fixture':primary,'note':'Read-only prompt curation only. Original acceptance clauses, current code, adapter implementation and full verification selection are unchanged.'})
    return result
