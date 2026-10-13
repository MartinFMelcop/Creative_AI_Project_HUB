using System.Globalization;
using System.Text.Json;
using Eclipse.Core;
using Eclipse.Cli;

try { Run(args); return 0; }
catch(Exception error) when(error is ArgumentException or IOException or JsonException or UnauthorizedAccessException)
{ Console.Error.WriteLine($"Error: {error.Message}");return 1; }

static void Run(string[] args)
{
    var command=args.FirstOrDefault()??"help";var options=new Dictionary<string,string>();
    for(int i=1;i<args.Length;i+=2)
    {
        if(i+1>=args.Length || !args[i].StartsWith("--") || !options.TryAdd(args[i][2..],args[i+1]))throw new ArgumentException("Options need unique --name value pairs.");
    }
    string Get(string key,string fallback)=>options.GetValueOrDefault(key,fallback);
    int Number(string key,int fallback) => int.TryParse(Get(key,fallback.ToString(CultureInfo.InvariantCulture)),out var n)?n:throw new ArgumentException($"Invalid --{key}.");
    var allowed=command switch {"play"=>new[]{"seed","rules","load"},"demo"=>["seed","rules","out","policies"],"compare"=>["seed","runs","rules","variant","out"],"replay"=>["load"],_=>Array.Empty<string>()};
    if(options.Keys.Except(allowed).Any())throw new ArgumentException("Unknown option for this command.");
    if(command=="help")
    {
        Console.WriteLine("Eclipse Fair 0.1.0 — a P01 economy trial\nplay [--seed 1] [--rules file] [--load journal]\ndemo [--seed 1] [--out folder] [--policies collector,keeper,opportunist,worker]\ncompare --variant rules.json [--runs 100] [--seed 1] [--out folder]\nreplay --load journal.json\nCompare runs are seeds, with four policy/seat rotations each.\nPlay: numbered plan, hint, auto, save <path>, help, quit. Paths are relative to the current directory.");return;
    }
    Rules ReadRules(string path)=>JsonSerializer.Deserialize<Rules>(File.ReadAllText(path),Journal.Json)??throw new ArgumentException("Invalid rules.");
    var rules=options.TryGetValue("rules",out var rulesFile)?ReadRules(rulesFile):new Rules();rules.Validate();
    var seed=Number("seed",1);
    if(command=="compare")
    {
        if(!options.TryGetValue("variant",out var variant))throw new ArgumentException("Provide --variant rules.json.");
        Compare(rules,ReadRules(variant),seed,Number("runs",100),Get("out","out/compare"));return;
    }
    string[] policies=Get("policies","collector,keeper,opportunist,collector").Split(',');Agents.ValidatePolicies(policies);
    Game game;
    if(options.TryGetValue("load",out var load))
    {
        if(options.ContainsKey("rules") || options.ContainsKey("seed"))throw new ArgumentException("Loaded journals already specify rules and seed.");
        (game,policies)=Journal.Load(load);
    }
    else {if(command=="replay")throw new ArgumentException("Provide --load journal.json.");game=new(seed,rules);}
    if(command=="replay") {foreach(var record in game.Journal)Console.WriteLine(record.Description);Show(game);return;}
    if(command=="demo")
    {
        Agents.Finish(game,policies);foreach(var record in game.Journal)Console.WriteLine(record.Description);
        var folder=Get("out","out/demo");Directory.CreateDirectory(folder);Journal.Save(game,policies,Path.Combine(folder,"journal.json"));
        File.WriteAllText(Path.Combine(folder,"result.json"),JsonSerializer.Serialize(new {game.Seed,game.Rules,game.Result,game.Ledger,turns=game.Journal.Count,policies},Journal.Json));Show(game);return;
    }
    if(command!="play")throw new ArgumentException("Unknown command; use help.");
    Console.WriteLine("ECLIPSE FAIR — you are Vaelis. Three agents share the fair.\nBuy three sigils, cleanse your curse, then claim the Gate before the fair closes.\nMove up to one edge and take one action per turn; movement costs obols.\nMarkets: 0/4. Chapel: 2. Gate: 7. Shortcuts: 0↔4, 2↔6.\nAt closure, rank by sigils, least curse, then obols; exact ties share the result.\nType help for tactics or save <path> to pause your match.");
    while(game.Result==null)
    {
        if(game.Current!=0) {game.Apply(Agents.Choose(game,policies[game.Current],policies),out var story);Console.WriteLine(story);continue;}
        Show(game);var plans=game.Legal();
        for(int i=0;i<plans.Count;i++)Console.WriteLine($"{i+1,2}. {Describe(game,plans[i])}");
        Console.Write("Plan > ");var line=Console.ReadLine()?.Trim();
        if(line==null || line=="quit") {Console.WriteLine("Match left without an automatic save. Use save <path> before leaving to continue later.");return;}
        if(line.StartsWith("save "))
        {
            try {Journal.Save(game,policies,line[5..].Trim());Console.WriteLine("Journal saved; replay validates its actions when loaded.");}
            catch(Exception error) when(error is ArgumentException or IOException or UnauthorizedAccessException)
            {Console.WriteLine($"Save failed: {error.Message} Match is still active and unchanged.");}
            continue;
        }
        if(line=="hint") {var suggestion=Agents.Choose(game,policies[0],policies);var label=char.ToUpperInvariant(policies[0][0])+policies[0][1..];Console.WriteLine($"{label} suggestion: plan {plans.ToList().IndexOf(suggestion)+1}. It uses public policy information; it is not an optimal solver.");continue;}
        if(line=="auto") {game.Apply(Agents.Choose(game,policies[0],policies),out var automatic);Console.WriteLine("Assisted turn: "+automatic);continue;}
        if(line=="help") {Console.WriteLine("Work follows this round's forecast; curse reduces income. Buying adds curse. Chapel rites remove up to two.\nA two-obol raven ward blocks one co-located theft. Successful stealing transfers up to three obols and adds curse.\nSeals cost more as you collect them; late prices rise by one. Returning to the Chapel and Gate costs turns.\nProtect a purchase reserve, compare routes, and watch opponents' positions. Saving replaces the specified file atomically.");continue;}
        if(!int.TryParse(line,out var index) || index<1 || index>plans.Count){Console.WriteLine("Choose a displayed plan; nothing changed.");continue;}
        game.Apply(plans[index-1],out var feedback);Console.WriteLine(feedback);
    }
    Show(game);
}
static string Describe(Game game,Intent plan)
{
    var p=game.People[game.Current];var preview=game.Fork();preview.Apply(plan,out _);var after=preview.People[p.Id];
    var target=plan.Target>=0?$" from {game.People[plan.Target].Name}":"";
    return $"{Game.Board[plan.Destination].Name}: {plan.Action}{target} | obols {p.Gold}→{after.Gold}, curse {p.Curse}→{after.Curse}, sigils {after.Sigils}/{game.Rules.Goal}";
}
static void Show(Game game)
{
    Console.WriteLine($"\nROUND {game.Round}/{game.Rules.RoundLimit} · {game.Forecast(game.Round)} · next: {game.Forecast(game.Round+1)}");
    foreach(var p in game.People)Console.WriteLine($"{p.Name,-7} {p.Gold,3} obols · sigils {p.Sigils}/{game.Rules.Goal} · curse {p.Curse} · ward {p.Ward} · {Game.Board[p.Position].Name}");
    if(game.Result!=null)Console.WriteLine($"RESULT: {game.Result.Reason}. Winner(s): {string.Join(", ",game.Result.Winners.Select(i=>game.People[i].Name))}. Turns: {game.Journal.Count}. Minted {game.Ledger.Minted}, spent {game.Ledger.Spent}, stolen {game.Ledger.Stolen}.");
}
static void Compare(Rules baseline,Rules variant,int start,int count,string folder)
{
    variant.Validate();if(count is <1 or >1000 || start<0 || start+count>1_000_001)throw new ArgumentException("Use 1–1000 matches with seeds in 0–1000000.");
    Directory.CreateDirectory(folder);var lines=new List<string>{"scenario,seed,rotation,policy,seat,win_credit,sigils,curse,gold,finish,turns,minted,spent,stolen"};
    var summaries=new List<object>();
    foreach(var (label,rules) in new[]{("baseline",baseline),("variant",variant)})
    {
        int claimed=0;double turns=0;var wins=Agents.Names.ToDictionary(n=>n,_=>0.0);
        for(int i=0;i<count;i++)
        for(int rotation=0;rotation<4;rotation++)
        {
            var policies=Enumerable.Range(0,4).Select(seat=>Agents.Names[(seat+rotation)%4]).ToArray();var game=Agents.Finish(new Game(start+i,rules),policies);var result=game.Result!;
            if(result.Reason=="gate claimed")claimed++;turns+=game.Journal.Count;
            foreach(var p in game.People)
            {
                double credit=result.Winners.Contains(p.Id)?1.0/result.Winners.Length:0;wins[policies[p.Id]]+=credit;
                lines.Add(string.Join(',',label,game.Seed,rotation,policies[p.Id],p.Id,credit.ToString(CultureInfo.InvariantCulture),p.Sigils,p.Curse,p.Gold,result.Reason=="gate claimed"?"gate":"deadline",game.Journal.Count,game.Ledger.Minted,game.Ledger.Spent,game.Ledger.Stolen));
            }
        }
        summaries.Add(new {scenario=label,rules,matches=count*4,gateClaims=claimed,meanTurns=turns/(count*4),winCredits=wins});
        Console.WriteLine($"{label}: {claimed}/{count*4} gate claims; mean {turns/(count*4):F1} turns; {string.Join(", ",wins.Select(w=>$"{w.Key} {w.Value:F1}"))}");
    }
    File.WriteAllLines(Path.Combine(folder,"matches.csv"),lines);
    File.WriteAllText(Path.Combine(folder,"summary.json"),JsonSerializer.Serialize(new {version=Game.Version,startSeed=start,seeds=count,matchesPerScenario=count*4,seatRotation="all four rotations for each seed; relative policy order retained",assessment="Synthetic strategies and common-seed scenarios; not human balance or market evidence.",scenarios=summaries},Journal.Json));
    Console.WriteLine($"Wrote {folder}/matches.csv and summary.json.");
}
