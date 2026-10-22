using System;
using System.Collections.Generic;

namespace NorthStar.Domain
{
    /// <summary>Original portable contract adapted from legacy XP lookup/budget semantics.</summary>
    public sealed class LevelDefinition
    {
        public int Level { get; }
        public long TotalXp { get; }
        public int Main { get; }
        public int Health { get; }
        public int Resolve { get; }
        public LevelDefinition(int level, long totalXp, int main, int health, int resolve)
        { Level = level; TotalXp = totalXp; Main = main; Health = health; Resolve = resolve; }
    }

    public sealed class Budget
    {
        public long Main { get; }
        public long Health { get; }
        public long Resolve { get; }
        public Budget(long main, long health, long resolve)
        { Main = main; Health = health; Resolve = resolve; }
    }

    public sealed class ProgressionCurve
    {
        public const long MaximumXp = 1_000_000_000_000;
        private readonly long[] thresholds;
        private readonly long[] main, health, resolve;
        public int MaximumLevel => thresholds.Length;
        public ProgressionCurve(IReadOnlyList<LevelDefinition> levels)
        {
            if (levels == null || levels.Count < 1 || levels.Count > 4096)
                throw new ArgumentException("A curve requires 1–4096 consecutive levels.");
            thresholds = new long[levels.Count];
            main = new long[levels.Count + 1]; health = new long[levels.Count + 1]; resolve = new long[levels.Count + 1];
            for (int i = 0; i < levels.Count; i++)
            {
                var row = levels[i];
                if (row == null || row.Level != i + 1 || row.TotalXp < 0 || row.TotalXp > MaximumXp ||
                    (i == 0 ? row.TotalXp != 0 : row.TotalXp <= thresholds[i - 1]))
                    throw new ArgumentException("Levels must be consecutive with strictly increasing XP from zero.");
                if (row.Main < 0 || row.Main > 1_000_000 || row.Health < 0 || row.Health > 1_000_000 || row.Resolve < 0 || row.Resolve > 1_000_000)
                    throw new ArgumentException("Level budgets must be nonnegative and at most 1000000 per axis.");
                thresholds[i] = row.TotalXp;
                main[i + 1] = checked(main[i] + row.Main);
                health[i + 1] = checked(health[i] + row.Health);
                resolve[i + 1] = checked(resolve[i] + row.Resolve);
            }
        }
        public int LevelForXp(long xp)
        {
            ValidateXp(xp);
            int low = 0, high = thresholds.Length - 1;
            while (low < high)
            {
                int middle = (low + high + 1) / 2;
                if (thresholds[middle] <= xp) low = middle; else high = middle - 1;
            }
            return low + 1;
        }
        public Budget GainedBetween(int previousLevel, int nextLevel)
        {
            if (previousLevel < 1 || nextLevel < previousLevel || nextLevel > MaximumLevel)
                throw new ArgumentException("Invalid budget interval.");
            return new Budget(main[nextLevel] - main[previousLevel], health[nextLevel] - health[previousLevel], resolve[nextLevel] - resolve[previousLevel]);
        }
        internal static void ValidateXp(long xp)
        {
            if (xp < 0 || xp > MaximumXp) throw new ArgumentOutOfRangeException(nameof(xp), "XP must be in 0..1000000000000.");
        }
    }

    public enum Allocation { Vitality, Focus }
    public sealed class GrantResult
    {
        public bool Applied { get; }
        public int LevelsGained { get; }
        public Budget Budget { get; }
        internal GrantResult(bool applied, int levelsGained, Budget budget)
        { Applied = applied; LevelsGained = levelsGained; Budget = budget; }
    }

    /// <summary>Immutable public projection; callers cannot mutate a session's owned progression.</summary>
    public sealed class ProgressionView
    {
        public long TotalXp { get; }
        public int Level { get; }
        public long EarnedMain { get; }
        public long BonusHealth { get; }
        public long BonusResolve { get; }
        public long Vitality { get; }
        public long Focus { get; }
        public long SpentMain { get; }
        public long UnspentMain { get; }
        public int RewardCount { get; }
        public ProgressionView(ProgressionState state)
        {
            if (state == null) throw new ArgumentNullException(nameof(state));
            TotalXp = state.TotalXp; Level = state.Level; EarnedMain = state.EarnedMain;
            BonusHealth = state.BonusHealth; BonusResolve = state.BonusResolve;
            Vitality = state.Vitality; Focus = state.Focus; SpentMain = state.SpentMain;
            UnspentMain = state.UnspentMain; RewardCount = state.RewardCount;
        }
    }

    /// <summary>Single-owner in-memory state. No persistence, authentication or network trust claim.</summary>
    public sealed class ProgressionState
    {
        private readonly ProgressionCurve curve;
        private readonly Dictionary<string, long> rewards = new Dictionary<string, long>(StringComparer.Ordinal);
        public long TotalXp { get; private set; }
        public int Level { get; private set; }
        public long EarnedMain { get; private set; }
        public long BonusHealth { get; private set; }
        public long BonusResolve { get; private set; }
        public long Vitality { get; private set; }
        public long Focus { get; private set; }
        public long SpentMain => Vitality + Focus;
        public long UnspentMain => EarnedMain - SpentMain;
        public int RewardCount => rewards.Count;
        // Initial XP determines the baseline level; budgets are earned only by subsequent grants.
        public ProgressionState(ProgressionCurve curve, long initialXp = 0)
        {
            this.curve = curve ?? throw new ArgumentNullException(nameof(curve));
            Level = curve.LevelForXp(initialXp); TotalXp = initialXp;
        }
        public GrantResult Grant(string rewardId, long amount)
        {
            if (rewardId == null || rewardId.Length < 1 || rewardId.Length > 64)
                throw new ArgumentException("Reward ID must contain 1–64 ASCII identifier characters.");
            foreach (char c in rewardId)
                if (!(c >= 'a' && c <= 'z' || c >= 'A' && c <= 'Z' || c >= '0' && c <= '9' || c == '_' || c == '-'))
                    throw new ArgumentException("Invalid reward ID.");
            ProgressionCurve.ValidateXp(amount);
            if (rewards.TryGetValue(rewardId, out long previous))
            {
                if (previous != amount) throw new InvalidOperationException("Reward identity cannot be reused with a different amount.");
                return new GrantResult(false, 0, new Budget(0, 0, 0));
            }
            if (rewards.Count >= 10000) throw new InvalidOperationException("Session reward ledger is full.");
            if (amount > ProgressionCurve.MaximumXp - TotalXp) throw new OverflowException("XP grant exceeds the bounded total.");
            long total = TotalXp + amount;
            int level = curve.LevelForXp(total);
            Budget budget = curve.GainedBetween(Level, level);
            long earned = checked(EarnedMain + budget.Main);
            long hp = checked(BonusHealth + budget.Health), sp = checked(BonusResolve + budget.Resolve);
            var result = new GrantResult(true, level - Level, budget);
            // Validate and calculate the entire transaction before committing any field.
            rewards.Add(rewardId, amount); TotalXp = total; Level = level;
            EarnedMain = earned; BonusHealth = hp; BonusResolve = sp;
            return result;
        }
        public void Allocate(Allocation stat, long amount)
        {
            if (stat != Allocation.Vitality && stat != Allocation.Focus) throw new ArgumentException("Unknown allocation axis.");
            if (amount <= 0 || amount > UnspentMain) throw new ArgumentOutOfRangeException(nameof(amount), "Spend positive earned points only.");
            long next = checked((stat == Allocation.Vitality ? Vitality : Focus) + amount);
            if (stat == Allocation.Vitality) Vitality = next; else Focus = next;
        }
    }
}
