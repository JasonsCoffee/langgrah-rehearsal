"""Architect diagnosis of actual body errors without reclassifying evidence."""


def body_error_scope(raw: dict, contract: dict) -> dict[str,list[str]]:
    request=raw.get('request',{});selected=set(request.get('test_selection',[]))
    links={t['test_id']:t['author_unit'] for t in contract['test_links']}
    if (raw.get('mode')!='tests' or request.get('full_suite') is not True
        or selected!=set(links) or set(raw.get('executed',[]))!=selected
        or raw.get('skipped') or raw.get('inconclusive') or raw.get('suite_errors')
        or set(raw.get('passed',[])) & set(raw.get('failed',[]))
        or set(raw.get('passed',[])) | set(raw.get('failed',[]))!=selected):
        raise ValueError('Exact complete baseline execution without runner ambiguity required')
    details=raw.get('failure_details',[])
    if len(details)!=len(raw.get('failed',[])) or {d['test'] for d in details}!=set(raw['failed']):
        raise ValueError('Every failed case needs actual classified details')
    units={u['id']:u for u in contract['units']};scope={}
    for detail in details:
        if detail.get('site')!='Test':raise ValueError('Fixture/setup errors need separate diagnosis')
        if detail.get('state') in ('Failed','Failed:Failure'):continue
        if detail.get('state')!='Failed:Error' or 'NullReferenceException' not in detail.get('message',''):
            raise ValueError('Unrecognized body error needs separate diagnosis')
        case=detail['test'];author=links[case];unit=units[author]
        if unit['role']!='test' or unit['status']!='active':raise ValueError('Declared active author required')
        scope.setdefault(author,[]).append(case)
    if not scope:raise ValueError('No body errors require author repair')
    return {u:sorted(cases) for u,cases in sorted(scope.items())}
