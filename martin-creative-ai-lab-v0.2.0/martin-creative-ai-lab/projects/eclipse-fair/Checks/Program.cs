using System.Text.Json;
using System.Text.Json.Nodes;
using Eclipse.Core;
using Eclipse.Cli;

int checks=0;var failures=new List<string>();
void Check(string name,Action body)
{
    checks++;try{body();Console.WriteLine($"PASS {name}");}catch(Exception e){failures.Add(name+": "+e.Message);Console.WriteLine($"FAIL {name}: {e.Message}");}
}
void Assert(bool condition,string message){if(!condition)throw new InvalidOperationException(message);}
void Turn(Game game,int seat)
{
    while(game.Current!=seat && game.Result==null)game.Apply(new(game.People[game.Current].Position,ActionKind.Work),out _);
    Assert(game.Result==null,"Fixture ended early.");
}
void Do(Game game,int seat,Intent plan){Turn(game,seat);Assert(game.Apply(plan,out var error),error);}
string State(Game game)=>JsonSerializer.Serialize(new {game.Round,game.Current,people=game.People,game.Ledger,game.Result,trace=game.Journal},Journal.Json);

Check("unavailable complete plan is atomic",()=>{
    var game=new Game(0);var before=State(game);
    foreach(var plan in new[]{new Intent(99,ActionKind.Work),new(0,ActionKind.Buy),new(0,(ActionKind)99),new(0,ActionKind.Steal,0)})
        Assert(!game.Apply(plan,out _) && State(game)==before,"Invalid plan mutated the game.");
});
Check("initiative rotates and every participant acts once per round",()=>{
    var game=new Game(0);var actors=new List<int>();
    for(int i=0;i<8;i++){actors.Add(game.Current);game.Apply(new(game.People[game.Current].Position,ActionKind.Work),out _);}
    Assert(actors.SequenceEqual(new[]{0,1,2,3,1,2,3,0}),"Seat order changed or skipped an actor.");
});
Check("purchase price, curse and wages have connected consequences",()=>{
    var game=new Game(0,new(StartingGold:30));Do(game,0,new(0,ActionKind.Buy));
    Assert(game.People[0].Gold==24 && game.Price(game.People[0])==8 && game.People[0].Curse==1,"Purchase settlement incorrect.");
    Assert(game.Wage(0,game.People[0])==1,"Curse did not affect income.");
    Do(game,0,new(0,ActionKind.Buy));Assert(game.People[0].Sigils==2 && game.Price(game.People[0])==10,"Second purchase curve incorrect.");
});
Check("ward blocks one co-located theft; successful theft transfers existing currency",()=>{
    var game=new Game(0);Do(game,0,new(0,ActionKind.Guard));Do(game,3,new(7,ActionKind.Work));Turn(game,3);
    var gold=game.People[0].Gold;var minted=game.Ledger.Minted;
    Assert(game.Apply(new(0,ActionKind.Steal,0),out _),"Protected theft must be a legal risky plan.");
    Assert(game.People[0].Gold==gold && game.People[0].Ward==0 && game.Ledger.Blocked==1 && game.Ledger.Minted==minted,"Ward settlement minted/stole currency.");
    Turn(game,3);gold=game.People[0].Gold;var attacker=game.People[3].Gold;minted=game.Ledger.Minted;
    game.Apply(new(0,ActionKind.Steal,0),out _);
    Assert(game.People[0].Gold==gold-3 && game.People[3].Gold==attacker+3 && game.People[3].Curse==1 && game.Ledger.Minted==minted,"Theft transfer incorrect.");
});
Check("rites and a real route enable a gate claim",()=>{
    var game=new Game(0,new(StartingGold:30,Goal:1,RoundLimit:8));
    Do(game,0,new(0,ActionKind.Buy));Do(game,0,new(1,ActionKind.Work));Do(game,0,new(2,ActionKind.Rite));
    Assert(game.People[0].Curse==0,"Chapel did not cleanse.");Do(game,0,new(6,ActionKind.Work));Do(game,0,new(7,ActionKind.Claim));
    Assert(game.Result?.Reason=="gate claimed" && game.Result.Winners.SequenceEqual(new[]{0}),"Legal claim did not end the match.");
    Assert(game.Legal().Count==0 && !game.Apply(new(7,ActionKind.Work),out _),"Ended match accepted more actions.");
});
Check("deadline is bounded and exact tied rankings share the outcome",()=>{
    var game=new Game(0,new(RoundLimit:4));while(game.Result==null)game.Apply(new(game.People[game.Current].Position,ActionKind.Work),out _);
    Assert(game.Journal.Count==16 && game.Result.Winners.SequenceEqual(new[]{0,2}),"Deadline or tie handling incorrect.");
});
Check("forks support previews without modifying the original match",()=>{
    var game=new Game(7);var before=State(game);var fork=game.Fork();fork.Apply(fork.Legal()[0],out _);
    Assert(State(game)==before && fork.Journal.Count==1,"Preview altered original state.");
});
Check("default strategies complete gate claims and conserve currency through each turn",()=>{
    int gates=0;
    for(int seed=0;seed<100;seed++)
    {
        var game=new Game(seed);var policies=Enumerable.Range(0,4).Select(i=>Agents.Names[(i+seed)%4]).ToArray();
        while(game.Result==null)
        {
            game.Apply(Agents.Choose(game,policies[game.Current]),out _);
            Assert(game.People.Sum(p=>p.Gold)==game.Rules.StartingGold*4+game.Ledger.Minted-game.Ledger.Spent,"Currency conservation failed.");
            Assert(game.People.All(p=>p.Gold>=0 && p.Curse>=0 && p.Ward is >=0 and <=2 && p.Sigils<=game.Rules.Goal),"Resource bounds failed.");
        }
        if(game.Result.Reason=="gate claimed")gates++;
        Assert(game.Journal.Count<=80,"Match exceeded its turn budget.");
    }
    Assert(gates>0,"No default match can complete the intended gate objective.");Console.WriteLine($"OBSERVED gate claims {gates}/100 synthetic matches");
});
Check("journal replays every fact; rejects unavailable actions and forged snapshots",()=>{
    var folder=Path.Combine(Path.GetTempPath(),"eclipse-check-"+Guid.NewGuid());Directory.CreateDirectory(folder);
    try
    {
        var game=new Game(19);string[] policies=["collector","keeper","opportunist","worker"];
        for(int i=0;i<10;i++)game.Apply(Agents.Choose(game,policies[game.Current]),out _);
        var path=Path.Combine(folder,"journal.json");Journal.Save(game,policies,path);var loaded=Journal.Load(path);
        Assert(State(game)==State(loaded.Game),"Partial replay changed state/trace/economy.");
        Agents.Finish(game,policies);Agents.Finish(loaded.Game,loaded.Policies);Assert(State(game)==State(loaded.Game),"Resumed agents diverged.");
        var original=File.ReadAllText(path);var json=JsonNode.Parse(original)!;json["actions"]![0]!["destination"]=99;File.WriteAllText(path,json.ToJsonString());
        bool refused=false;try{Journal.Load(path);}catch(ArgumentException){refused=true;}Assert(refused,"Invalid action accepted.");
        json=JsonNode.Parse(original)!;json["gold"]=999;File.WriteAllText(path,json.ToJsonString());
        refused=false;try{Journal.Load(path);}catch(JsonException){refused=true;}Assert(refused,"Trusted supplied state snapshot.");
        Journal.Save(game,policies,path);Assert(Journal.Load(path).Game.Result!=null && Directory.GetFiles(folder,"*.tmp").Length==0,"Atomic saved result failed.");
    }
    finally{Directory.Delete(folder,true);}
});
Check("rules and seeds reject unsupported scenarios",()=>{
    foreach(var rules in new[]{new Rules(Goal:0),new(RoundLimit:100),new(SealBase:-1),new(WorkBonus:100)})
    {bool refused=false;try{new Game(1,rules);}catch(ArgumentException){refused=true;}Assert(refused,"Invalid rules accepted.");}
    bool seedRefused=false;try{new Game(-1);}catch(ArgumentException){seedRefused=true;}Assert(seedRefused,"Invalid seed accepted.");
});
Console.WriteLine(JsonSerializer.Serialize(new{checks,failures}));return failures.Count==0?0:1;
