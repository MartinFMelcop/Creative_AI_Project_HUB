using System;

namespace NorthStar.Reputation
{
    /// <summary>Selected six-level source arithmetic only; no region, background, social policy or effect catalog.</summary>
    public static class Standing
    {
        public static bool IsLevel(int value) => value >= -3 && value <= 3 && value != 0;

        /// <summary>The inspected source Set normalizes zero to positive one before clamping.</summary>
        public static int Set(int value)
        {
            if (value == 0) return 1;
            return value < -3 ? -3 : value > 3 ? 3 : value;
        }

        /// <summary>Add preserves the source crossing/zero rules for a legal current level and any Int32 delta.</summary>
        public static int Add(int current, int delta)
        {
            // The source also accepts unknown region keys and coercions; this typed adaptation does not.
            if (!IsLevel(current)) throw new ArgumentOutOfRangeException(nameof(current), "Current standing must be one of -3,-2,-1,1,2,3.");
            if (current == -3 && delta < 0 || current == 3 && delta > 0) return current;
            long change = delta;
            long tentative = current + change;
            long magnitude = Math.Abs(change);
            if ((current < 0 && tentative > 0 || current > 0 && tentative < 0) && magnitude < 2) return current;
            if (tentative == 0)
            {
                if (magnitude < 2) return current;
                tentative = change > 0 ? 1 : -1;
            }
            return tentative < -3 ? -3 : tentative > 3 ? 3 : (int)tentative;
        }
    }
}
