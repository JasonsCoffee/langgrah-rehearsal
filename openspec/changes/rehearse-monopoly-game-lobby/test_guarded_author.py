"""Notes alone cannot satisfy a requested delegated C# repair."""
from unity_coder.core.local_executor import WorkerPatch
from guarded_author import authored_repair


def test_notes_only_reply_gets_one_distinct_delegated_source_request():
    calls=[]
    def generate(feedback,operation):
        calls.append((feedback,operation))
        return (WorkerPatch({'note.md':b'repair claim'},'notes') if len(calls)==1 else
                WorkerPatch({'Tests.cs':b'actual delegated repair'},'source repair'))
    result=authored_repair(generate,'findings','operation',{'Tests.cs':b'old source'},True)
    assert len(calls)==2 and calls[1][1]=='operation-required-csharp'
    assert 'not frozen' in calls[0][0] and 'C#' in calls[1][0]
    assert result.files=={'note.md':b'repair claim','Tests.cs':b'actual delegated repair'}


def test_real_source_change_is_not_repeated():
    calls=[]
    def generate(feedback,operation):
        calls.append(operation);return WorkerPatch({'Tests.cs':b'changed'},'repair')
    authored_repair(generate,'','op',{'Tests.cs':b'old'},True)
    assert calls==['op']


def test_documentation_only_repair_is_not_forced_to_change_source():
    calls=[]
    def generate(feedback,operation):
        calls.append(operation);return WorkerPatch({'note.md':b'accurate map'},'map')
    authored_repair(generate,'','op',{'Tests.cs':b'valid'},False)
    assert calls==['op']
