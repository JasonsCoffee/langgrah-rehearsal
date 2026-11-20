"""Target-only prompt curation; never writes or changes frozen source files."""
import re
from collections.abc import Mapping
from tree_sitter import Language, Parser
import tree_sitter_c_sharp


def test_excerpt(source: str, required_ids: set[str]) -> str:
    """Keep mapped NUnit methods, every non-test helper and literal semantics."""
    raw=source.encode('utf-8')
    tree=Parser(Language(tree_sitter_c_sharp.language())).parse(raw)
    if tree.root_node.has_error:
        raise ValueError('Cannot curate syntactically invalid frozen C# evidence')
    removed=[]
    def visit(node):
        if node.type=='comment':
            removed.append((node.start_byte,node.end_byte));return
        if node.type=='method_declaration':
            attributes=b''.join(child.text for child in node.children if child.type=='attribute_list').decode()
            if re.search(r'\b(?:Test|TestCase|UnityTest)(?:Attribute)?\b',attributes):
                name=node.child_by_field_name('name').text.decode()
                containers=[]; parent=node.parent
                while parent is not None:
                    if parent.type in ('class_declaration','namespace_declaration','file_scoped_namespace_declaration'):
                        containers.append(parent.child_by_field_name('name').text.decode())
                    parent=parent.parent
                identifier='.'.join(reversed(containers))+'.'+name
                if identifier not in required_ids:
                    removed.append((node.start_byte,node.end_byte));return
        for child in node.children:visit(child)
    visit(tree.root_node)
    result=[]; offset=0
    for start,end in sorted(removed):
        result.extend((raw[offset:start],b'\n'));offset=end
    result.append(raw[offset:])
    return b''.join(result).decode('utf-8')


test_excerpt.__test__=False


def refactor_context(files: Mapping[str,str], spec_path: str) -> dict[str,str]:
    """Green behavior is checked by full frozen execution, not test-body edits."""
    return {p:v for p,v in files.items() if p==spec_path or p.endswith('read-only-test-excerpts.json')
            or (p.endswith('.cs') and not p.startswith('Tests/'))}
