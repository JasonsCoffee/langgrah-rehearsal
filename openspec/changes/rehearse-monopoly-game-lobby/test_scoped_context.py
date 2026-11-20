"""Read-only prompt excerpts preserve every mapped test and all helper code."""
from scoped_context import test_excerpt


def test_only_unmapped_test_methods_and_comments_are_omitted():
    source='''namespace Tests {
class Suite {
 // explanatory comment
 [SetUp] public void Setup() { Seed(); }
 [Test] public void Wanted() { Assert.That(Helper(), Is.EqualTo("http://safe/*literal*/")); }
 [Test] public void Other() { Assert.Fail("unrelated"); }
 public string Helper() { return "http://safe/*literal*/"; }
}
}'''
    result=test_excerpt(source,{'Tests.Suite.Wanted'})
    assert 'Wanted()' in result and 'Other()' not in result
    assert 'Setup()' in result and 'Helper()' in result
    assert 'http://safe/*literal*/' in result and 'explanatory comment' not in result
    assert 'Assert.That' in result
    assert 'Other()' in source


def test_same_method_name_in_another_fixture_is_not_kept():
    source='namespace Tests { class A { [Test] void Same(){} } class B { [Test] void Same(){} } }'
    result=test_excerpt(source,{'Tests.A.Same'})
    assert result.count('Same()')==1
