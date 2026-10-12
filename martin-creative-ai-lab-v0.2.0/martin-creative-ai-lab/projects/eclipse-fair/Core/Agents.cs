using System.Collections.Immutable;
namespace Eclipse.Core;

public static class Agents
{
    public static readonly ImmutableArray<string> Names = ["collector","keeper","opportunist","worker"];
    public static Intent Choose(Game game, string policy)
    {
        if (!Names.Contains(policy)) throw new ArgumentException($"Unknown policy: {policy}");
        var before=game.People[game.Current];
        int Target(Participant p) => p.Curse>=2 || (p.Sigils>=game.Rules.Goal && p.Curse>0) ? 2 :
            p.Sigils>=game.Rules.Goal ? 7 : (game.Distance(p.Position,0)<=game.Distance(p.Position,4)?0:4);
        double Score(Intent plan)
        {
            var copy=game.Fork();copy.Apply(plan,out _);var after=copy.People[before.Id];
            if(copy.Result?.Reason=="gate claimed")return 10000;
            var funds=after.Gold-before.Gold;
            if(policy=="worker")return plan.Action==ActionKind.Work ? funds*10+game.Wage(after.Position,after,game.Round+1) : -1000;
            double score=(after.Sigils-before.Sigils)*75+(before.Curse-after.Curse)*9+funds*2;
            var goal=Target(before);
            double distanceWeight = before.Gold >= game.Price(before)+game.Rules.MoveCost*2 || before.Curse>=2 || before.Sigils>=game.Rules.Goal ? 12 : 3;
            score-=copy.Distance(after.Position,goal)*distanceWeight;
            if(plan.Action==ActionKind.Work)score+=copy.Wage(after.Position,after,game.Round+1)*2;
            if(policy=="keeper")
            {
                var nearby=game.People.Count(p=>p.Id!=before.Id && (p.Position==after.Position || Game.Board[p.Position].Neighbors.Contains(after.Position)));
                score+=(after.Ward-before.Ward)*(nearby>0 && before.Gold>=game.Price(before)?14:2);
                score+=(before.Curse-after.Curse)*3;
            }
            if(plan.Action==ActionKind.Steal)
            {
                var victim=game.People[plan.Target];
                score+=policy=="opportunist" ? (victim.Sigils>=before.Sigils?12:4) : -6;
                if(victim.Ward>0)score-=8;
            }
            return score;
        }
        // Stable ties are intentional; agents never consult another player's future input.
        return game.Legal().OrderByDescending(Score).ThenBy(p=>p.Destination).ThenBy(p=>p.Action).ThenBy(p=>p.Target).First();
    }
    public static Game Finish(Game game, string[] policies)
    {
        ValidatePolicies(policies);
        while(game.Result==null)if(!game.Apply(Choose(game,policies[game.Current]),out _))throw new InvalidOperationException("Agent chose an illegal plan.");
        return game;
    }
    public static void ValidatePolicies(string[] policies)
    {
        if(policies.Length!=4 || policies.Any(p=>!Names.Contains(p)))throw new ArgumentException("Choose four policies: collector, keeper, opportunist, worker.");
    }
}
