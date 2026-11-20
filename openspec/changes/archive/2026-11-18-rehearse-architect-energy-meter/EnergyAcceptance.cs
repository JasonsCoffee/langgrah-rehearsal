using System;
using NUnit.Framework;

namespace FrameworkArchitectDemo.Tests
{
    public sealed class EnergyAcceptance
    {
        [Test]
        public void SpendBounds()
        {
            var spend = new EnergySpend();
            Assert.That(spend.Apply(7, 10, 3), Is.EqualTo(4));
            Assert.That(spend.Apply(7, 10, 8), Is.Zero);
            Assert.That(spend.Apply(7, 10, -3), Is.EqualTo(7));
            Assert.That(spend.Apply(7, 10, 0), Is.EqualTo(7));
            Assert.That(spend.Apply(0, 0, 1), Is.Zero);
            Assert.That(spend.Apply(7, 10, int.MaxValue), Is.Zero);
            AssertInvalidState(spend.Apply);
        }

        [Test]
        public void RechargeBounds()
        {
            var recharge = new EnergyRecharge();
            Assert.That(recharge.Apply(7, 10, 2), Is.EqualTo(9));
            Assert.That(recharge.Apply(7, 10, 8), Is.EqualTo(10));
            Assert.That(recharge.Apply(7, 10, int.MaxValue), Is.EqualTo(10));
            Assert.That(recharge.Apply(int.MaxValue - 1, int.MaxValue, int.MaxValue), Is.EqualTo(int.MaxValue));
            Assert.That(recharge.Apply(7, 10, -3), Is.EqualTo(7));
            Assert.That(recharge.Apply(7, 10, 0), Is.EqualTo(7));
            Assert.That(recharge.Apply(0, 0, 1), Is.Zero);
            AssertInvalidState(recharge.Apply);
        }

        [Test]
        public void SharedSequence()
        {
            int afterSpend = new EnergySpend().Apply(7, 10, 3);
            Assert.That(afterSpend, Is.EqualTo(4));
            int afterRecharge = new EnergyRecharge().Apply(afterSpend, 10, 8);
            Assert.That(afterRecharge, Is.EqualTo(10));
        }

        private static void AssertInvalidState(Func<int, int, int, int> apply)
        {
            Assert.That(Assert.Throws<ArgumentOutOfRangeException>(() => apply(0, -1, 1)).ParamName,
                Is.EqualTo("capacity"));
            Assert.That(Assert.Throws<ArgumentOutOfRangeException>(() => apply(-1, 10, 1)).ParamName,
                Is.EqualTo("current"));
            Assert.That(Assert.Throws<ArgumentOutOfRangeException>(() => apply(11, 10, 1)).ParamName,
                Is.EqualTo("current"));
            Assert.That(Assert.Throws<ArgumentOutOfRangeException>(() => apply(-1, -1, -1)).ParamName,
                Is.EqualTo("capacity"));
            Assert.That(Assert.Throws<ArgumentOutOfRangeException>(() => apply(11, 10, -1)).ParamName,
                Is.EqualTo("current"));
        }
    }
}
