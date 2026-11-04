using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;

namespace NorthStar.Audio
{
    /// <summary>Original experimental playback policy; it never accepts or resolves gameplay.</summary>
    public static class Admission
    {
        public const int MaximumVoices = 2;
        public const int Append = -2;
        public const int Suppress = -1;
        public const double Master = .8;
        public const double Ceiling = .9;

        public static int Priority(string cue)
        {
            switch (cue)
            {
                case "won": case "lost": return 3;
                case "block": case "draw": case "hurt": case "evade": return 2;
                case "bolt": case "pulse": return 1;
                default: throw new ArgumentException("Unknown consequence cue.", nameof(cue));
            }
        }

        /// <summary>Returns append, suppress, or the index to stop in creation order.
        /// Equal critical cues retain their admitted lifetime. Only threats replace peers.
        /// Admission never queues a suppressed observation for later playback.</summary>
        public static int Decide(int incoming, params int[] active)
        {
            if (incoming < 1 || incoming > 3 || active == null || active.Length > MaximumVoices)
                throw new ArgumentException("Invalid bounded voice state.");
            foreach (int rank in active)
                if (rank < 1 || rank > 3) throw new ArgumentException("Invalid voice priority.");
            if (active.Length < MaximumVoices) return Append;
            int weakest = active[1] < active[0] ? 1 : 0;
            return active[weakest] < incoming || incoming == 1 && active[weakest] == 1 ? weakest : Suppress;
        }

        /// <summary>Conservative sample-amplitude bound, not a true-peak or perception meter.</summary>
        public static double PeakBound(double quietPeak, double crossingPeak, double effectPeakSum,
            double music = 1, double effects = 1)
        {
            foreach (double value in new[] { quietPeak, crossingPeak, effectPeakSum, music, effects })
                if (double.IsNaN(value) || double.IsInfinity(value) || value < 0)
                    throw new ArgumentException("Finite nonnegative signal bounds required.");
            if (music > 1 || effects > 1) throw new ArgumentException("Unit interval bus gains required.");
            return Master * (music * Math.Sqrt(quietPeak * quietPeak + crossingPeak * crossingPeak) + effects * effectPeakSum);
        }

        private static IReadOnlyDictionary<string, object> ReadOnly(Dictionary<string, object> data) =>
            new ReadOnlyDictionary<string, object>(data);

        private static IReadOnlyDictionary<string, object> BuildContract()
        {
            var catalog = new Dictionary<string, object>(StringComparer.Ordinal);
            double quiet = 0, crossing = 0, greatestEffect = 0;
            foreach (string name in Composer.Names)
            {
                double[] samples = Composer.Samples(name);
                double peak = 0;
                foreach (double sample in samples) peak = Math.Max(peak, Math.Abs(sample));
                if (name == "quiet") quiet = peak;
                else if (name == "crossing") crossing = peak;
                else
                {
                    greatestEffect = Math.Max(greatestEffect, peak);
                    catalog.Add(name, ReadOnly(new Dictionary<string, object>
                    { { "priority", Priority(name) }, { "frames", samples.Length }, { "peak", peak } }));
                }
            }
            var rules = new Dictionary<string, object>(StringComparer.Ordinal);
            AddRule(rules, Array.Empty<int>());
            for (int first = 1; first <= 3; first++)
            {
                AddRule(rules, new[] { first });
                for (int second = 1; second <= 3; second++) AddRule(rules, new[] { first, second });
            }
            double sourceBound = PeakBound(quiet, crossing, MaximumVoices * greatestEffect);
            if (sourceBound >= Ceiling) throw new InvalidOperationException("Source voice budget exceeds reserved headroom.");
            return ReadOnly(new Dictionary<string, object>
            {
                { "version", 1 }, { "maxvoices", MaximumVoices }, { "master", Master }, { "ceiling", Ceiling },
                { "source_bound", sourceBound }, { "catalog", ReadOnly(catalog) }, { "rules", ReadOnly(rules) }
            });
        }

        private static void AddRule(Dictionary<string, object> rules, int[] active) =>
            rules.Add(string.Join(",", active), Array.AsReadOnly(new[] { Decide(1, active), Decide(2, active), Decide(3, active) }));

        // The browser uses this C# decision table with its actual live voice ordering.
        // No second admission algorithm or game outcome owner is installed in the adapter.
        public static IReadOnlyDictionary<string, object> Contract { get; } = BuildContract();
    }
}
