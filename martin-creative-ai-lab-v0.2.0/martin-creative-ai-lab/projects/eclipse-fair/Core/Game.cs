using System.Collections.Immutable;
namespace Eclipse.Core;

public sealed record Rules(int StartingGold = 4, int Goal = 3, int RoundLimit = 20,
    int SealBase = 6, int SealStep = 2, int MoveCost = 1, int RiteCost = 2, int WorkBonus = 0)
{
    public void Validate()
    {
        if (StartingGold is < 0 or > 30 || Goal is < 1 or > 6 || RoundLimit is < 4 or > 40 ||
            SealBase is < 1 or > 30 || SealStep is < 0 or > 10 || MoveCost is < 0 or > 5 ||
            RiteCost is < 0 or > 10 || WorkBonus is < -1 or > 5)
            throw new ArgumentException("Rules are outside the documented scenario bounds.");
    }
}

public enum ActionKind { Work, Buy, Rite, Guard, Steal, Claim }
public sealed record Intent(int Destination, ActionKind Action, int Target = -1);
public sealed record Participant(int Id, string Name, int Position, int Gold, int Sigils, int Curse, int Ward);
public sealed record Venue(int Id, string Name, int Wage, ImmutableArray<int> Neighbors);
public sealed record TurnRecord(int Round, int Actor, Intent Intent, string Description);
public sealed record Economy(int Minted, int Spent, int Stolen, int Blocked, int Purchased, int Rites);
public sealed record Outcome(string Reason, ImmutableArray<int> Winners, ImmutableArray<Participant> Standings);

public sealed class Game
{
    public const string Version = "0.1.0";
    public static readonly ImmutableArray<Venue> Board = [
        new(0,"Eclipse Market",2,[1,4,7]), new(1,"Foundry",4,[0,2]),
        new(2,"Chapel",1,[1,3,6]), new(3,"Wharf",3,[2,4]),
        new(4,"Veil Bazaar",2,[0,3,5]), new(5,"Orchard",4,[4,6]),
        new(6,"Raven Spire",1,[2,5,7]), new(7,"Eclipse Gate",2,[0,6])
    ];
    public static readonly ImmutableArray<string> Events = ["Foundry rush", "Orchard blight", "Pilgrim procession", "Wharf contracts", "Quiet fair"];
    private readonly Participant[] people;
    private readonly List<TurnRecord> journal = [];
    private int turn, minted, spent, stolen, blocked, purchased, rites;
    public Rules Rules { get; }
    public int Seed { get; }
    public int Round { get; private set; } = 1;
    public int Current => (Seed % 4 + Round - 1 + turn) % 4;
    public IReadOnlyList<Participant> People => Array.AsReadOnly(people);
    public IReadOnlyList<TurnRecord> Journal => journal.AsReadOnly();
    public Economy Ledger => new(minted,spent,stolen,blocked,purchased,rites);
    public Outcome? Result { get; private set; }
    public string Forecast(int round) => Events[(int)((unchecked((uint)Seed * 1103515245u + (uint)round * 12345u) >> 16) % 5)];
    public int Price(Participant p) => Rules.SealBase + Rules.SealStep * p.Sigils + (Round >= 11 ? 1 : 0);
    public int Wage(int venue, Participant p, int? round = null)
    {
        var weather = Forecast(round ?? Round);
        var bonus = venue == 1 && weather == Events[0] ? 2 : venue == 5 && weather == Events[1] ? -2 : venue == 3 && weather == Events[3] ? 2 : 0;
        return Math.Max(1, Board[venue].Wage + Rules.WorkBonus + bonus - Math.Min(2,p.Curse));
    }
    private int RitePrice => Forecast(Round) == Events[2] ? 0 : Rules.RiteCost;

    public Game(int seed = 1, Rules? rules = null)
    {
        if (seed < 0 || seed > 1_000_000) throw new ArgumentException("Seed must be 0–1000000.");
        Rules = rules ?? new(); Rules.Validate(); Seed = seed;
        string[] names = ["Vaelis","Madra","Nira","Morrak"];
        people = names.Select((name,i) => new Participant(i,name,(i*2+seed%8)%8,Rules.StartingGold,0,0,0)).ToArray();
    }
    public IReadOnlyList<Intent> Legal()
    {
        if (Result != null) return [];
        var p = people[Current]; var choices = new List<Intent>();
        foreach (var dest in Board[p.Position].Neighbors.Prepend(p.Position).Order())
        {
            var available = p.Gold - (dest == p.Position ? 0 : Rules.MoveCost);
            if (available < 0) continue;
            choices.Add(new(dest,ActionKind.Work));
            if ((dest == 0 || dest == 4) && p.Sigils < Rules.Goal && available >= Price(p)) choices.Add(new(dest,ActionKind.Buy));
            if (dest == 2 && p.Curse > 0 && available >= RitePrice) choices.Add(new(dest,ActionKind.Rite));
            if (p.Ward < 2 && available >= 2) choices.Add(new(dest,ActionKind.Guard));
            foreach (var victim in people.Where(v => v.Id != p.Id && v.Position == dest && (v.Gold > 0 || v.Ward > 0)))
                choices.Add(new(dest,ActionKind.Steal,victim.Id));
            if (dest == 7 && p.Sigils >= Rules.Goal && p.Curse == 0) choices.Add(new(dest,ActionKind.Claim));
        }
        return choices;
    }
    public bool Apply(Intent intent, out string explanation)
    {
        // Validate the complete transaction before movement, currency or clock changes.
        if (!Legal().Contains(intent)) { explanation = "Unavailable plan; position, resources and turn are unchanged."; return false; }
        var actor = Current; var p = people[actor];
        int toll = intent.Destination == p.Position ? 0 : Rules.MoveCost;
        p = p with { Position = intent.Destination, Gold = p.Gold-toll }; spent += toll;
        var actionText = "";
        switch (intent.Action)
        {
            case ActionKind.Work:
                var income = Wage(p.Position,p); p = p with { Gold=p.Gold+income };minted+=income;
                actionText=$"earned {income} obols";break;
            case ActionKind.Buy:
                var price=Price(p);p=p with {Gold=p.Gold-price,Sigils=p.Sigils+1,Curse=p.Curse+1};spent+=price;purchased++;
                actionText=$"bought sigil {p.Sigils}/{Rules.Goal} for {price}; curse rose to {p.Curse}";break;
            case ActionKind.Rite:
                var fee=RitePrice;p=p with {Gold=p.Gold-fee,Curse=Math.Max(0,p.Curse-2)};spent+=fee;rites++;
                actionText=$"performed a rite for {fee}; curse now {p.Curse}";break;
            case ActionKind.Guard:
                p=p with {Gold=p.Gold-2,Ward=p.Ward+1};spent+=2;actionText=$"raised a raven ward ({p.Ward}/2)";break;
            case ActionKind.Steal:
                var victim=people[intent.Target];
                if (victim.Ward>0) {people[victim.Id]=victim with {Ward=victim.Ward-1};blocked++;actionText=$"broke {victim.Name}'s ward; no obols stolen";}
                else {var take=Math.Min(3,victim.Gold);people[victim.Id]=victim with {Gold=victim.Gold-take};p=p with {Gold=p.Gold+take,Curse=p.Curse+1};stolen+=take;actionText=$"stole {take} from {victim.Name}; curse rose to {p.Curse}";}
                break;
            case ActionKind.Claim:
                actionText="claimed the Eclipse Gate";break;
        }
        people[actor]=p;
        explanation=$"R{Round} {p.Name} → {Board[p.Position].Name}: {actionText}.";
        journal.Add(new(Round,actor,intent,explanation));
        if (intent.Action == ActionKind.Claim) Result=new("gate claimed",[actor],Standings().ToImmutableArray());
        else if (++turn == 4)
        {
            turn=0;
            if (Round == Rules.RoundLimit)
            {
                var ordered=Standings();var best=ordered[0];
                var winners=ordered.Where(v=>v.Sigils==best.Sigils && v.Curse==best.Curse && v.Gold==best.Gold).Select(v=>v.Id).ToArray();
                Result=new("fair closed; sigils, then least curse, then obols",winners.ToImmutableArray(),ordered.ToImmutableArray());
            }
            else Round++;
        }
        return true;
    }
    private Participant[] Standings() => people.OrderByDescending(p=>p.Sigils).ThenBy(p=>p.Curse).ThenByDescending(p=>p.Gold).ThenBy(p=>p.Id).ToArray();
    public Game Fork()
    {
        var copy=new Game(Seed,Rules) {Round=Round,turn=turn,minted=minted,spent=spent,stolen=stolen,
            blocked=blocked,purchased=purchased,rites=rites,Result=Result};
        Array.Copy(people,copy.people,people.Length);
        copy.journal.AddRange(journal);
        return copy;
    }
    public int Distance(int start, int destination)
    {
        var queue=new Queue<(int Place,int Depth)>();queue.Enqueue((start,0));var seen=new HashSet<int>();
        while(queue.TryDequeue(out var next)) {if(next.Place==destination)return next.Depth;if(!seen.Add(next.Place))continue;foreach(var neighbor in Board[next.Place].Neighbors)queue.Enqueue((neighbor,next.Depth+1));}
        throw new InvalidOperationException("Board must be connected.");
    }
}
