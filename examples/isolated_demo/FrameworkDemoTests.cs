using NUnit.Framework;
using FrameworkDemo;

namespace FrameworkDemo.Tests
{
    public class Acceptance
    {
        [Test] public void CreditsAreAdded() => Assert.AreEqual(13, new CreditCalculator().Calculate(10, 3));
        [Test] public void NegativeCreditsAreIgnored() => Assert.AreEqual(10, new CreditCalculator().Calculate(10, -3));
        [Test] public void ScoresAreAdded() => Assert.AreEqual(60, new ScoreCalculator().Calculate(40, 20));
        [Test] public void ScoresAreCapped() => Assert.AreEqual(100, new ScoreCalculator().Calculate(90, 20));
        [Test] public void SharedRewardUsesBothComponents() => Assert.AreEqual(73,
            new CreditCalculator().Calculate(10, 3) + new ScoreCalculator().Calculate(40, 20));
    }
}
