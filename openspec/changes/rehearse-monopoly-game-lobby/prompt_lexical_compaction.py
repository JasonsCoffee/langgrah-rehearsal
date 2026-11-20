"""Prompt-only lexical compaction; physical source and frozen tests never change."""
from hashlib import sha256
import json
from tree_sitter import Language, Parser
import tree_sitter_c_sharp


def _tokens(source: str) -> list[tuple[str, bytes, int, int]]:
    raw=source.encode('utf-8')
    tree=Parser(Language(tree_sitter_c_sharp.language())).parse(raw)
    if tree.root_node.has_error:
        raise ValueError('Prompt compaction requires valid C#')
    result=[]
    def walk(node):
        if node.type=='comment':return
        # Literal interiors, including interpolated expressions, remain byte exact.
        if 'string' in node.type or node.type=='character_literal' or not node.children:
            result.append((node.type,raw[node.start_byte:node.end_byte],node.start_byte,node.end_byte))
            return
        for child in node.children:walk(child)
    walk(tree.root_node)
    return result


def token_signature(source: str) -> tuple[tuple[str, bytes], ...]:
    return tuple((kind,value) for kind,value,_,_ in _tokens(source))


def compact_csharp(source: str) -> str:
    raw=source.encode('utf-8'); tokens=_tokens(source); parts=[]; previous=0
    for kind,value,start,end in tokens:
        gap=raw[previous:start]
        # Keep line boundaries for directives, line-sensitive syntax and diagnostics.
        separator=b'\n' if b'\n' in gap else b' '
        if parts:
            left=parts[-1][-1:];right=value[:1]
            if separator!=b'\n' and (left in (b'{',b'}',b'(',b'[',b';',b',',b'.') or right in (b'}',b')',b']',b';',b',',b'.')):
                separator=b''
            parts.append(separator)
        parts.append(value);previous=end
    result=b''.join(parts).decode('utf-8')
    if token_signature(result)!=token_signature(source):
        raise ValueError('Prompt compaction changed C# tokens')
    return result


def compact_prompt(prompt: str) -> str:
    first,separator,body=prompt.partition('\n')
    if not separator:raise ValueError('Prompt has no structured payload')
    payload,end=json.JSONDecoder().raw_decode(body)
    provenance={}
    for path,source in list(payload['files'].items()):
        if path.endswith('.cs'):
            compact=compact_csharp(source)
            digest=sha256(repr(token_signature(source)).encode()).hexdigest()
        elif path.endswith('.json'):
            try:compact=json.dumps(json.loads(source),ensure_ascii=False,separators=(',',':'))
            except ValueError:continue
            digest=None
        else:continue
        if len(compact)>=len(source):continue
        payload['files'][path]=compact
        provenance[path]={'provided_text_sha256':sha256(source.encode()).hexdigest(),
            'token_sha256':digest,'original_characters':len(source),'compact_characters':len(compact)}
    payload['files']['prompt-compaction-provenance.json']=json.dumps({
        'note':'Prompt formatting only. Provided-text hashes are not physical frozen-file hashes. All C# tokens and literal bytes are preserved.',
        'files':provenance},ensure_ascii=False,separators=(',',':'))
    return first+'\n'+json.dumps(payload,ensure_ascii=False,separators=(',',':'))+body[end:]
