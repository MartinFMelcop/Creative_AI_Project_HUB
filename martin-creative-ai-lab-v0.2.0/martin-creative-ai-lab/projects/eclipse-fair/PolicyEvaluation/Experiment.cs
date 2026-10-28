using System.Collections.Immutable;
using System.Diagnostics;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using Eclipse.Core;
namespace Eclipse.PolicyEvaluation;

// Policies receive no engine reference, seed, journal, future result or configured opponents.
public sealed record Option(Intent Intent, ImmutableArray<Participant> People, int MintedDelta, int SpentDelta, ImmutableArray<int> NextWages);
public sealed record Observation(int Actor, int Round, Rules Rules, string Forecast, string NextForecast,
    ImmutableArray<Participant> People, int Price, ImmutableArray<int> NextWages, ImmutableArray<Option> Options);
public interface IPolicy { Intent Choose(Observation observation); }
public sealed class Heuristic(string name) : IPolicy
{
    public static readonly string[] Names = ["collector-v1", "route-v1", "income-v1", "keeper-v1", "interdict-v1"];
    public Intent Choose(Observation o)
    {
        if (!Names.Contains(name)) throw new ArgumentException("Unknown frozen policy.");
        var me=o.People[o.Actor];
        double Score(Option option)
        {
            var a=option.Intent; var after=option.People[o.Actor];
            var funds=after.Gold-me.Gold;
            if(name=="income-v1") return a.Action==ActionKind.Work ? funds*10 : -10000;
            if(a.Action==ActionKind.Claim)return 100000;
            var target=me.Curse>=2 || me.Sigils>=o.Rules.Goal && me.Curse>0 ? 2 :
                me.Sigils>=o.Rules.Goal ? 7 : Distance(me.Position,0)<=Distance(me.Position,4)?0:4;
            double distanceWeight=me.Gold>=o.Price+o.Rules.MoveCost*2 || me.Curse>=2 || me.Sigils>=o.Rules.Goal?12:3;
            double score=(after.Sigils-me.Sigils)*75+(me.Curse-after.Curse)*9+funds*2-Distance(after.Position,target)*distanceWeight;
            if(a.Action==ActionKind.Work)score+=option.NextWages[after.Position]*2;
            if(a.Action==ActionKind.Steal)
            {
                var victim=o.People[a.Target];
                score+=name=="interdict-v1"?(victim.Sigils>=me.Sigils?12:4):-6;
                if(victim.Ward>0)score-=8;
            }
            if(name=="keeper-v1")
            {
                var nearby=o.People.Count(p=>p.Id!=me.Id && (p.Position==after.Position||Game.Board[p.Position].Neighbors.Contains(after.Position)));
                score+=(after.Ward-me.Ward)*(nearby>0&&me.Gold>=o.Price?14:2)+(me.Curse-after.Curse)*3;
            }
            if(name=="route-v1")
            {
                // Public route budget: prefer getting to a useful wage hub when not purchase-ready,
                // and stop accumulating avoidable curse once the objective is nearly attainable.
                if(me.Sigils<o.Rules.Goal && me.Gold<o.Price+o.Rules.MoveCost*2 && me.Curse<2)
                {
                    var incomeTarget=Enumerable.Range(0,8).OrderByDescending(v=>o.NextWages[v]-Distance(me.Position,v)*o.Rules.MoveCost).ThenBy(v=>v).First();
                    score-=Distance(after.Position,incomeTarget)*5;
                }
                if(me.Curse>0 && after.Curse==0)score+=10;
                if(me.Sigils>=o.Rules.Goal)score-=Distance(after.Position,me.Curse>0?2:7)*12;
                if(a.Action==ActionKind.Steal)score-=8;
            }
            return score;
        }
        return o.Options.OrderByDescending(Score).ThenBy(x=>x.Intent.Destination).ThenBy(x=>x.Intent.Action).ThenBy(x=>x.Intent.Target).First().Intent;
    }
    public static int Distance(int start,int end)
    {
        var queue=new Queue<(int,int)>();queue.Enqueue((start,0));var seen=new HashSet<int>();
        while(queue.TryDequeue(out var n)){if(n.Item1==end)return n.Item2;if(!seen.Add(n.Item1))continue;foreach(var v in Game.Board[n.Item1].Neighbors)queue.Enqueue((v,n.Item2+1));}
        throw new InvalidOperationException("Disconnected board.");
    }
}
public sealed record Scenario(string Id, Rules Rules);
public sealed record Roster(string Id, string[] Opponents, bool HeldOut);
public sealed record Configuration(string ExperimentId, string Baseline, string Candidate, int[] Seeds,
    Scenario[] Scenarios, Roster[] Rosters, int MaxActions=160);
public sealed record Step(int Index,int Actor,Intent Intent,string Before,string After);
public sealed record Match(string Id,string Scenario,string Roster,bool HeldOut,int Seed,int FocalSeat,int Rotation,string Arm,
    string[] Policies,string Status,string? Error,Step[] Actions,string FinalHash,int[] Winners,
    bool ExclusiveWin,bool MultiwinnerTie,bool WinnerMember,double FractionalCredit,string? Reason);
public sealed record Report(string Schema,string ConfigurationHash,string SourceHash,Configuration Configuration,Match[] Games);
public static class Evaluation
{
    public static long SelectionCount { get; private set; }
    public static double TotalSelectionMilliseconds { get; private set; }
    public static double MaxSelectionMilliseconds { get; private set; }
    public static readonly JsonSerializerOptions Json=new(){PropertyNamingPolicy=JsonNamingPolicy.SnakeCaseLower,WriteIndented=true,UnmappedMemberHandling=JsonUnmappedMemberHandling.Disallow,Converters={new JsonStringEnumConverter(JsonNamingPolicy.SnakeCaseLower)}};
    public static string Hash(string value)=>Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(value))).ToLowerInvariant();
    public static string State(Game g)=>JsonSerializer.Serialize(new{g.Round,g.Current,g.People,g.Ledger,g.Result,g.Journal},Json);
    public static string StateHash(Game g)=>Hash(State(g));
    public static Observation Observe(Game g)
    {
        if(g.Result!=null)throw new ArgumentException("No policy observation after terminal state.");
        var before=State(g);
        var options=g.Legal().Select(i=>{var fork=g.Fork();if(!fork.Apply(i,out _))throw new InvalidOperationException("Legal action rejected.");return new Option(i,fork.People.ToImmutableArray(),fork.Ledger.Minted-g.Ledger.Minted,fork.Ledger.Spent-g.Ledger.Spent,Enumerable.Range(0,8).Select(v=>fork.Wage(v,fork.People[g.Current],g.Round+1)).ToImmutableArray());}).ToImmutableArray();
        if(State(g)!=before)throw new InvalidOperationException("Observation mutated source.");
        return new(g.Current,g.Round,g.Rules,g.Forecast(g.Round),g.Forecast(g.Round+1),g.People.ToImmutableArray(),g.Price(g.People[g.Current]),Enumerable.Range(0,8).Select(v=>g.Wage(v,g.People[g.Current],g.Round+1)).ToImmutableArray(),options);
    }
    public static void Validate(Configuration c)
    {
        if(string.IsNullOrWhiteSpace(c.ExperimentId)||c.ExperimentId.Length>120||!Heuristic.Names.Contains(c.Baseline)||!Heuristic.Names.Contains(c.Candidate)||c.Baseline==c.Candidate)throw new ArgumentException("Invalid experiment/policy identity.");
        if(c.Seeds.Length is <1 or >1000||c.Seeds.Distinct().Count()!=c.Seeds.Length||c.Seeds.Any(s=>s<0||s>1000000))throw new ArgumentException("Invalid declared seeds.");
        if(c.Scenarios.Length is <1 or >16||c.Scenarios.Select(s=>s.Id).Distinct().Count()!=c.Scenarios.Length)throw new ArgumentException("Invalid scenarios.");
        foreach(var s in c.Scenarios){if(string.IsNullOrWhiteSpace(s.Id))throw new ArgumentException("Missing scenario identity.");s.Rules.Validate();if(c.MaxActions<4*s.Rules.RoundLimit||c.MaxActions>160)throw new ArgumentException("Budget cannot truncate supported full games.");}
        if(c.Rosters.Length is <2 or >16||!c.Rosters.Any(r=>r.HeldOut)||!c.Rosters.Any(r=>!r.HeldOut)||c.Rosters.Select(r=>r.Id).Distinct().Count()!=c.Rosters.Length)throw new ArgumentException("Need distinct development and held-out rosters.");
        if((long)c.Seeds.Length*c.Scenarios.Length*c.Rosters.Length*24>10000)throw new ArgumentException("Declared complete-game budget exceeds10000.");
        foreach(var r in c.Rosters)if(string.IsNullOrWhiteSpace(r.Id)||r.Opponents.Length!=3||r.Opponents.Any(p=>!Heuristic.Names.Contains(p)))throw new ArgumentException("Need three supported independent opponents.");
    }
    public static Match Run(Scenario scenario,Roster roster,int seed,int seat,string arm,string policy,int budget,int rotation=0,Func<int,IPolicy>? factory=null)
    {
        var policies=new string[4];int next=0;for(int i=0;i<4;i++)policies[i]=i==seat?policy:roster.Opponents[(next+++rotation)%3];
        var agents=policies.Select((p,i)=>factory?.Invoke(i)??new Heuristic(p)).ToArray();
        var game=new Game(seed,scenario.Rules);var steps=new List<Step>();string? error=null;
        try
        {
            while(game.Result==null)
            {
                if(steps.Count>=budget)throw new InvalidOperationException("Action budget interrupted game.");
                int actor=game.Current;var before=StateHash(game);var observation=Observe(game);var clock=Stopwatch.StartNew();var action=agents[actor].Choose(observation);clock.Stop();SelectionCount++;TotalSelectionMilliseconds+=clock.Elapsed.TotalMilliseconds;MaxSelectionMilliseconds=Math.Max(MaxSelectionMilliseconds,clock.Elapsed.TotalMilliseconds);
                if(StateHash(game)!=before)throw new InvalidOperationException("Policy mutated source.");
                if(!game.Legal().Contains(action))throw new InvalidOperationException("Policy returned illegal action.");
                if(!game.Apply(action,out _))throw new InvalidOperationException("Authoritative application refused legal action.");
                if(game.People.Sum(p=>p.Gold)!=4*scenario.Rules.StartingGold+game.Ledger.Minted-game.Ledger.Spent)throw new InvalidOperationException("Currency not conserved.");
                if(game.People.Any(p=>p.Gold<0||p.Curse<0||p.Ward<0||p.Ward>2||p.Sigils<0||p.Sigils>scenario.Rules.Goal))throw new InvalidOperationException("Resource bounds failed.");
                steps.Add(new(steps.Count,actor,action,before,StateHash(game)));
            }
        }
        catch(Exception e){error=e.GetType().Name+": "+e.Message;}
        var winners=error==null&&game.Result!=null?game.Result.Winners.ToArray():[];
        bool member=winners.Contains(seat);var status=error==null&&game.Result!=null?"complete":"interrupted";
        return new($"{scenario.Id}/{roster.Id}/{seed}/{seat}/{rotation}/{arm}",scenario.Id,roster.Id,roster.HeldOut,seed,seat,rotation,arm,policies,status,error,steps.ToArray(),StateHash(game),winners,
            member&&winners.Length==1,winners.Length>1,member,member?1.0/winners.Length:0,error==null?game.Result?.Reason:null);
    }
    public static Report Execute(Configuration c,string sourceHash)
    {
        Validate(c);SelectionCount=0;TotalSelectionMilliseconds=0;MaxSelectionMilliseconds=0;var matches=new List<Match>();
        foreach(var scenario in c.Scenarios)foreach(var roster in c.Rosters)foreach(int seed in c.Seeds)for(int seat=0;seat<4;seat++)for(int rotation=0;rotation<3;rotation++)
        {
            matches.Add(Run(scenario,roster,seed,seat,"baseline",c.Baseline,c.MaxActions,rotation));
            matches.Add(Run(scenario,roster,seed,seat,"candidate",c.Candidate,c.MaxActions,rotation));
        }
        var report=new Report("eclipse-policy-evaluation-v1",Hash(JsonSerializer.Serialize(c,Json)),sourceHash,c,matches.ToArray());Verify(report);return report;
    }
    public static void Verify(Report report)
    {
        var c=report.Configuration;Validate(c);
        if(report.Schema!="eclipse-policy-evaluation-v1"||report.ConfigurationHash!=Hash(JsonSerializer.Serialize(c,Json))||report.SourceHash.Length!=64||report.SourceHash.Any(x=>!Uri.IsHexDigit(x)))throw new ArgumentException("Report provenance mismatch.");
        int expected=c.Scenarios.Length*c.Rosters.Length*c.Seeds.Length*24;
        if(report.Games.Length!=expected||report.Games.Select(g=>g.Id).Distinct().Count()!=expected)throw new ArgumentException("Missing/duplicate complete game units.");
        var expectedIds=(from s in c.Scenarios from r in c.Rosters from seed in c.Seeds from seat in Enumerable.Range(0,4) from rotation in Enumerable.Range(0,3) from arm in new[]{"baseline","candidate"} select $"{s.Id}/{r.Id}/{seed}/{seat}/{rotation}/{arm}").ToHashSet();
        foreach(var m in report.Games)
        {
            if(m.Id!=$"{m.Scenario}/{m.Roster}/{m.Seed}/{m.FocalSeat}/{m.Rotation}/{m.Arm}"||!expectedIds.Remove(m.Id))throw new ArgumentException("Unexpected game unit.");
            var scenario=c.Scenarios.Single(s=>s.Id==m.Scenario);var roster=c.Rosters.Single(r=>r.Id==m.Roster);
            if(m.HeldOut!=roster.HeldOut||!c.Seeds.Contains(m.Seed)||m.FocalSeat is <0 or >3||m.Rotation is <0 or >2||m.Arm is not ("baseline" or "candidate"))throw new ArgumentException("Game assignment mismatch.");
            var policies=new string[4];int next=0;for(int i=0;i<4;i++)policies[i]=i==m.FocalSeat?(m.Arm=="baseline"?c.Baseline:c.Candidate):roster.Opponents[(next+++m.Rotation)%3];
            if(!m.Policies.SequenceEqual(policies))throw new ArgumentException("Policy assignment mismatch.");
            var g=new Game(m.Seed,scenario.Rules);
            foreach(var step in m.Actions)
            {
                if(g.Result!=null||new Heuristic(m.Policies[g.Current]).Choose(Observe(g))!=step.Intent||step.Index!=g.Journal.Count||step.Actor!=g.Current||step.Before!=StateHash(g)||!g.Apply(step.Intent,out _)||step.After!=StateHash(g))throw new ArgumentException("Accepted-action replay mismatch.");
            }
            if(StateHash(g)!=m.FinalHash)throw new ArgumentException("Forged final state.");
            var complete=m.Status=="complete";
            if(m.Status is not ("complete" or "interrupted")||complete!=(g.Result!=null&&m.Error==null)||!complete&&string.IsNullOrWhiteSpace(m.Error))throw new ArgumentException("Terminal/interruption accounting mismatch.");
            int[] winners=complete?g.Result!.Winners.ToArray():[];bool member=winners.Contains(m.FocalSeat);
            if(!m.Winners.SequenceEqual(winners)||m.ExclusiveWin!=(member&&winners.Length==1)||m.MultiwinnerTie!=(winners.Length>1)||m.WinnerMember!=member||m.FractionalCredit!=(member?1.0/winners.Length:0)||m.Reason!=(complete?g.Result!.Reason:null))throw new ArgumentException("Winner/tie/fractional endpoint mismatch.");
        }
    }
}
