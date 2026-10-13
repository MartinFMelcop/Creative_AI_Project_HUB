using System.Collections.Immutable;

namespace Eclipse.Core;

public sealed record PlanAdvice(Intent First, ImmutableArray<Intent> Route, string Purpose, int Examined);
public sealed record ReplyForecast(Game After, ImmutableArray<TurnRecord> Replies);

public static class Planning
{
    public static readonly ImmutableArray<string> Names = ["planner", "warden", "raider"];
    public static readonly ImmutableArray<string> NativePolicies = ["planner", "warden", "raider", "planner"];

    public static string Purpose(Game game, int actor, string policy)
    {
        var p = game.People[actor];
        if (p.Sigils >= game.Rules.Goal) return p.Curse > 0 ? "Cleanse, then race to the Gate" : "Reach and claim the Gate";
        if (p.Curse >= 2) return "Recover wages at the Chapel before buying again";
        return policy switch {
            "warden" => "Build sigils while protecting the travel budget",
            "raider" => "Buy sigils and interrupt a nearby leader's budget",
            _ => "Plan wages, purchases and the route to the Chapel"
        };
    }

    // Compare every legal first action by playing its public policy model to the
    // real Gate/deadline. There is no recursive search or hidden future input.
    public static PlanAdvice Analyze(Game game, string policy, IReadOnlyList<string>? policies = null)
    {
        if (!Names.Contains(policy)) throw new ArgumentException("Unknown planning profile.");
        if (game.Result != null) throw new ArgumentException("The fair has ended.");
        var profiles = policies?.ToArray() ?? NativePolicies.ToArray(); Agents.ValidatePolicies(profiles);
        int actor = game.Current, examined = 0;
        var baseline = Agents.Choose(game, Model(policy));
        double bestValue = double.NegativeInfinity; PlanAdvice? best = null;
        foreach (var intent in game.Legal().OrderBy(i => i == baseline ? 0 : 1).ThenBy(i => i.Destination).ThenBy(i => i.Action).ThenBy(i => i.Target))
        {
            var copy = game.Fork(); copy.Apply(intent, out _); examined++;
            var route = ImmutableArray.CreateBuilder<Intent>(); route.Add(intent);
            while (copy.Result == null)
            {
                var next = Agents.Choose(copy, Model(copy.Current == actor ? policy : profiles[copy.Current]));
                if (copy.Current == actor && route.Count < 3) route.Add(next);
                copy.Apply(next, out _); examined++;
            }
            var value = Evaluate(copy, actor);
            if (value <= bestValue) continue;
            bestValue = value; best = new(intent, route.ToImmutable(), Purpose(game, actor, policy), 0);
        }
        return best! with { Examined = examined };
    }

    // Unlike the search approximation, this one-cycle forecast executes the actual
    // configured profiles. Its result is a conditional forecast, never live state.
    public static ReplyForecast Forecast(Game game, Intent intent, IReadOnlyList<string> policies)
    {
        Agents.ValidatePolicies(policies.ToArray());
        var actor = game.Current; var copy = game.Fork();
        if (!copy.Apply(intent, out _)) throw new ArgumentException("Choose a legal plan before forecasting replies.");
        int start = copy.Journal.Count;
        Advance(copy, actor, policies, exact: true);
        return new(copy, copy.Journal.Skip(start).ToImmutableArray());
    }

    private static string Model(string policy) => policy switch {
        "planner" => "collector", "warden" => "keeper", "raider" => "opportunist", _ => policy
    };
    private static void Advance(Game copy, int actor, IReadOnlyList<string> policies, bool exact)
    {
        // Rotating initiative can give a participant two turns between ours.
        int turns = 0;
        while (copy.Result == null && copy.Current != actor)
        {
            if (++turns > 6) throw new InvalidOperationException("Unexpected turn rotation.");
            var policy = policies[copy.Current];
            copy.Apply(Agents.Choose(copy, exact ? policy : Model(policy), policies), out _);
        }
    }
    private static double Evaluate(Game game, int actor)
    {
        var me = game.People[actor];
        var result = game.Result!;
        if (result.Winners.Contains(actor)) return 1e9 / result.Winners.Length
            + 10000 * (4 * game.Rules.RoundLimit - game.Journal.Count) + me.Gold * .001;
        int better = game.People.Count(p => p.Sigils > me.Sigils || p.Sigils == me.Sigils &&
            (p.Curse < me.Curse || p.Curse == me.Curse && p.Gold > me.Gold));
        return -1e9 + (3 - better) * 1e6 + me.Sigils * 10000 - me.Curse * 100 + me.Gold * .001;
    }
}
