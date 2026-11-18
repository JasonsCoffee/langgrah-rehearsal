// Deliberately failing diagnostics, selected individually by the trusted operator.
using NUnit.Framework;

namespace FrameworkCallbackProbe
{
    public sealed class Assertion
    {
        [Test] public void FailsWithAssertion() { Assert.Fail("callback assertion probe"); }
    }
    public sealed class Setup
    {
        [SetUp] public void Before() { Assert.Fail("callback setup probe"); }
        [Test] public void CannotRun() { Assert.Pass(); }
    }
    public sealed class SuiteTeardown
    {
        [Test] public void PassesBeforeTeardown() { Assert.Pass(); }
        [OneTimeTearDown] public void After() { Assert.Fail("callback suite teardown probe"); }
    }
}
