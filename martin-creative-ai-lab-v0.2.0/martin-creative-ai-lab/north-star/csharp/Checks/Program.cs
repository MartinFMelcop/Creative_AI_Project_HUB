using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using NorthStar.Domain;
using NorthStar.Crossing;
using CrossingAction = NorthStar.Crossing.Action;
internal static class Program
{
    private static int passed;
    private static readonly List<string> labels=new List<string>();
    private static void Check(bool value,string label)
    { if(!value)throw new InvalidOperationException("FAIL: "+label);passed++;labels.Add(label); }
    private static void Reject(System.Action operation,string label)
    {
        try { operation(); }
        catch(Exception e) when(e is ArgumentException || e is OverflowException || e is InvalidOperationException || e is FormatException)
        { Check(true,label);return; }
        throw new InvalidOperationException("FAIL: not rejected: "+label);
    }
    private static ProgressionCurve Curve()=>new ProgressionCurve(new[]{new LevelDefinition(1,0,0,0,0),new LevelDefinition(2,10,2,3,4),new LevelDefinition(3,25,4,5,6)});
    private static object Snapshot(ProgressionState s)=>new {s.TotalXp,s.Level,s.EarnedMain,s.BonusHealth,s.BonusResolve,s.Vitality,s.Focus,s.UnspentMain,s.RewardCount};
    private static string Frozen(ProgressionState s)=>JsonSerializer.Serialize(Snapshot(s));
    private static string Frozen(ProgressionView s)=>JsonSerializer.Serialize(s);
    private static int Native(string output)
    {
        var curve=Curve();
        foreach(var sample in new[]{(0L,1),(9L,1),(10L,2),(11L,2),(24L,2),(25L,3),(26L,3),(ProgressionCurve.MaximumXp,3)})
            Check(curve.LevelForXp(sample.Item1)==sample.Item2,"XP threshold "+sample.Item1);
        var state=new ProgressionState(curve);var result=state.Grant("complete",25);
        Check(result.Applied && result.LevelsGained==2 && state.EarnedMain==6 && state.BonusHealth==8 && state.BonusResolve==10,"multi-level cumulative budgets");
        string before=Frozen(state);Check(!state.Grant("complete",25).Applied && Frozen(state)==before,"same reward replay is idempotent");
        Reject(()=>state.Grant("complete",26),"reward collision rejected");Check(Frozen(state)==before,"collision leaves all state unchanged");
        Reject(()=>state.Grant("negative",-1),"negative award rejected");Check(Frozen(state)==before,"negative award is transactional");
        Reject(()=>state.Grant("invalid id",1),"invalid reward identifier rejected");
        state.Allocate(Allocation.Vitality,2);state.Allocate(Allocation.Focus,4);
        Check(state.UnspentMain==0 && state.SpentMain==state.EarnedMain,"earned minus spent conservation");
        before=Frozen(state);Reject(()=>state.Allocate(Allocation.Focus,1),"overspend rejected");Check(Frozen(state)==before,"overspend has no partial allocation");
        Reject(()=>state.Allocate(Allocation.Focus,0),"zero allocation rejected");Reject(()=>state.Allocate((Allocation)99,1),"unknown allocation rejected");
        var ceiling=new ProgressionState(curve,ProgressionCurve.MaximumXp);before=Frozen(ceiling);
        Reject(()=>ceiling.Grant("overflow",1),"bounded XP overflow rejected");Check(Frozen(ceiling)==before,"overflow cannot reserve reward or mutate state");
        Reject(()=>curve.LevelForXp(-1),"negative lookup rejected");Reject(()=>curve.LevelForXp(ProgressionCurve.MaximumXp+1),"overbound lookup rejected");
        Reject(()=>new ProgressionState(curve,-1),"negative initial state rejected");
        var partitioned=new ProgressionState(curve);partitioned.Grant("a",9);partitioned.Grant("b",1);partitioned.Grant("c",15);
        Check(partitioned.TotalXp==25 && partitioned.EarnedMain==6 && partitioned.BonusHealth==8,"award partition preserves budget");
        var seeded=new ProgressionState(curve,10);seeded.Grant("later",15);
        Check(seeded.EarnedMain==4 && seeded.BonusHealth==5,"seeded level earns only later budgets");
        Reject(()=>new ProgressionCurve(Array.Empty<LevelDefinition>()),"empty curve rejected");
        Reject(()=>new ProgressionCurve(new[]{new LevelDefinition(1,1,0,0,0)}),"nonzero initial threshold rejected");
        Reject(()=>new ProgressionCurve(new[]{new LevelDefinition(1,0,0,0,0),new LevelDefinition(3,10,1,1,1)}),"missing level rejected");
        Reject(()=>new ProgressionCurve(new[]{new LevelDefinition(1,0,0,0,0),new LevelDefinition(2,0,1,1,1)}),"duplicate threshold rejected");
        Reject(()=>new ProgressionCurve(new[]{new LevelDefinition(1,0,-1,0,0)}),"negative budget rejected");
        Reject(()=>new ProgressionCurve(new[]{new LevelDefinition(1,0,0,1000001,0)}),"overbound budget rejected");
        var baseBudget=new ProgressionState(new ProgressionCurve(new[]{new LevelDefinition(1,0,8,30,12),new LevelDefinition(2,10,8,30,12)}));baseBudget.Grant("one",10);
        Check(baseBudget.EarnedMain==8 && baseBudget.BonusHealth==30,"level-one budget metadata is never granted twice");
        var capped=new ProgressionState(curve);capped.Grant("overcap",1000);var earned=capped.EarnedMain;capped.Grant("aftercap",1000);
        Check(capped.Level==3 && capped.TotalXp==2000 && capped.EarnedMain==earned,"maximum level retains XP without repeating budgets");
        var session=new Session();session.Prepare(Approach.Lure,Outfit.Trail);session.Begin();
        Check(!session.Prepare(Approach.Anchor,Outfit.Plate) && !session.Allocate(Allocation.Focus,1) && !session.Begin(),"active preparation and restart locked");
        foreach(var action in new[]{CrossingAction.Walk,CrossingAction.Skill,CrossingAction.Walk,CrossingAction.Skill})Check(session.Act(action),"survey action accepted "+action);
        Check(session.Won && session.Stage==1 && session.Progression.Level==2 && session.Progression.UnspentMain==2,"actual survey pays progression once");
        Check(session.Allocate(Allocation.Focus,2),"earned Focus allocated before second encounter");session.Begin();
        Check(session.MaximumResolve==15 && session.MaximumHealth==11,"allocation changes actual prepared resources");
        foreach(var action in new[]{CrossingAction.Skill,CrossingAction.Skill,CrossingAction.Dash,CrossingAction.Skill,CrossingAction.Dash,CrossingAction.Skill})Check(session.Act(action),"Focus crossing action accepted "+action);
        Check(session.Complete && session.Health==11 && session.SpentResolve==14 && session.Rejected==0 && session.Progression.Level==3,"connected Focus journey completes with actual costs and reward");
        before=Frozen(session.Progression);Check(!session.Begin() && !session.Act(CrossingAction.Wait) && Frozen(session.Progression)==before,"terminal replay cannot pay or restart");
        var vitality=AfterSurvey(Allocation.Vitality);var focus=AfterSurvey(Allocation.Focus);
        foreach(var action in new[]{CrossingAction.Walk,CrossingAction.Skill,CrossingAction.Walk,CrossingAction.Walk,CrossingAction.Walk,CrossingAction.Skill})
        { vitality.Act(action);focus.Act(action); }
        Check(vitality.Complete && vitality.Health==3 && !focus.Won && focus.Health==0,"Vitality survives the same exposed walking policy that defeats Focus");
        var scarce=AfterSurvey(Allocation.Vitality);scarce.Act(CrossingAction.Skill);scarce.Act(CrossingAction.Skill);scarce.Act(CrossingAction.Dash);scarce.Act(CrossingAction.Skill);scarce.Act(CrossingAction.Dash);
        int beat=scarce.Beat,hp=scarce.Health,x=scarce.Position,energy=scarce.Resolve;
        Check(!scarce.Act(CrossingAction.Skill) && scarce.Beat==beat && scarce.Health==hp && scarce.Position==x && scarce.Resolve==energy,"insufficient ability resolve rejects without partial turn");
        Check(scarce.Act(CrossingAction.Wait) && scarce.Complete,"alternative wait accepts damage and completes without faking extra resolve");
        var anchor=new Session();anchor.Prepare(Approach.Anchor,Outfit.Trail);anchor.Begin();anchor.Act(CrossingAction.Skill);
        var lure=new Session();lure.Prepare(Approach.Lure,Outfit.Trail);lure.Begin();lure.Act(CrossingAction.Skill);
        Check(anchor.Position==0 && lure.Position==1 && anchor.Health==lure.Health && anchor.SpentResolve==2 && lure.SpentResolve==3,"Lure buys real forward progress where Anchor protects in place");
        Check(typeof(Session).GetProperty("Progression")!.PropertyType==typeof(ProgressionView) && typeof(ProgressionView).GetMethod("Grant")==null && typeof(ProgressionView).GetMethod("Allocate")==null,"session exposes immutable progression without allocation/reward bypass");
        var frozenView=lure.Progression;lure.Act(CrossingAction.Walk);
        Check(frozenView.TotalXp==0 && frozenView.UnspentMain==0,"public progression snapshot retains its observation without live mutable state");
        var plate=new Session();plate.Prepare(Approach.Anchor,Outfit.Plate);plate.Begin();
        Check(plate.MaximumHealth==14 && plate.MaximumResolve==6 && anchor.MaximumHealth==10 && anchor.MaximumResolve==10,"outfits change actual health and resolve with a tradeoff");
        string folder=Path.Combine(Path.GetTempPath(),"northstar-protocol-"+Guid.NewGuid().ToString("N"));Directory.CreateDirectory(folder);
        try
        {
            string input=Path.Combine(folder,"input.json"),target=Path.Combine(folder,"result.json");
            string valid="{\"schema_version\":1,\"levels\":[{\"level\":1,\"total_xp\":0,\"main\":0,\"hp\":0,\"sp\":0}],\"cases\":[{\"id\":\"case\",\"start_xp\":0,\"awards\":[0]}]}";
            File.WriteAllText(input,valid);Check(Study(input,target)==0 && File.Exists(target),"complete strict study protocol executes zero grant");
            foreach(var malformed in new[]{valid.Replace("\"schema_version\":1","\"schema_version\":true"),
                valid.Replace("\"schema_version\":1","\"schema_version\":1,\"schema_version\":1"),
                valid.Replace("\"hp\":0,",""),valid.Replace("\"awards\":[0]","\"awards\":[0.5]"),
                valid.Replace("\"start_xp\":0","\"start_xp\":-1"),
                valid.Replace("\"total_xp\":0","\"total_xp\":1"),
                valid.Replace("\"main\":0","\"main\":-1"),
                valid.Replace("\"schema_version\":1","\"schema_version\":1,\"unknown\":0")})
            {
                File.WriteAllText(input,malformed);File.Delete(target);Reject(()=>Study(input,target),"strict malformed protocol rejected");
                Check(!File.Exists(target),"invalid protocol does not produce success evidence");
            }
        }
        finally { Directory.Delete(folder,true); }
        var wall=new Session();wall.Prepare(Approach.Lure,Outfit.Trail);wall.Begin();
        foreach(var action in new[]{CrossingAction.Walk,CrossingAction.Skill,CrossingAction.Walk,CrossingAction.Skill})wall.Act(action);
        wall.Allocate(Allocation.Vitality,2);wall.Prepare(Approach.Anchor,Outfit.Plate);wall.Begin();
        for(int i=0;i<4;i++)wall.Act(CrossingAction.Dash);
        Check(wall.Active && wall.Position==Session.WorldEnd && wall.Health==1,"actual journey can reach a bounded live pulse position");
        wall.Act(CrossingAction.Walk);
        Check(!wall.Won && wall.Health==0 && wall.Position==Session.WorldEnd && wall.Progression.Level==2,"clamped movement cannot fake pulse avoidance or earn a failed reward");
        var report=new {schema_version=1,kind="north_star_csharp_native_controls",passed,failed=0,controls=labels,
            focus_journey=new{health=session.Health,resolve=session.Resolve,spent_resolve=session.SpentResolve,level=session.Progression.Level,xp=session.Progression.TotalXp},
            matched_walking=new{vitality_health=vitality.Health,focus_health=focus.Health,vitality_complete=vitality.Complete,focus_complete=focus.Complete},
            limitations=new[]{"No Unity Editor, Windows player, networking, disk persistence or independent human execution."}};
        File.WriteAllText(output,JsonSerializer.Serialize(report,new JsonSerializerOptions{WriteIndented=true})+"\n");
        Console.WriteLine("PASS: "+passed+" C# domain/destination controls");return 0;
    }
    private static Session AfterSurvey(Allocation allocation)
    {
        var s=new Session();s.Prepare(Approach.Lure,Outfit.Trail);s.Begin();
        foreach(var action in new[]{CrossingAction.Walk,CrossingAction.Skill,CrossingAction.Walk,CrossingAction.Skill})s.Act(action);
        s.Allocate(allocation,2);s.Begin();return s;
    }
    private static void Exact(JsonElement element,params string[] names)
    {
        if(element.ValueKind!=JsonValueKind.Object)throw new ArgumentException("Expected object.");
        var actual=element.EnumerateObject().Select(p=>p.Name).ToArray();
        if(actual.Length!=names.Length || actual.Distinct().Count()!=names.Length || names.Any(n=>!element.TryGetProperty(n,out _)))throw new ArgumentException("Unexpected, duplicate or missing fields.");
    }
    private static int Study(string input,string output)
    {
        if(new FileInfo(input).Length>4*1024*1024)throw new ArgumentException("Study input exceeds4MiB.");
        using var document=JsonDocument.Parse(File.ReadAllText(input));var root=document.RootElement;
        Exact(root,"schema_version","levels","cases");if(root.GetProperty("schema_version").GetInt32()!=1)throw new ArgumentException("Unknown study version.");
        var levels=new List<LevelDefinition>();
        foreach(var row in root.GetProperty("levels").EnumerateArray())
        {
            Exact(row,"level","total_xp","main","hp","sp");levels.Add(new LevelDefinition(row.GetProperty("level").GetInt32(),row.GetProperty("total_xp").GetInt64(),row.GetProperty("main").GetInt32(),row.GetProperty("hp").GetInt32(),row.GetProperty("sp").GetInt32()));
        }
        var curve=new ProgressionCurve(levels);var rows=new List<object>();var identities=new HashSet<string>(StringComparer.Ordinal);
        foreach(var sample in root.GetProperty("cases").EnumerateArray())
        {
            if(rows.Count>=10000)throw new ArgumentException("Too many study cases.");
            Exact(sample,"id","start_xp","awards");string id=sample.GetProperty("id").GetString() ?? throw new ArgumentException("Missing caseID.");
            if(id.Length<1 || id.Length>100 || !identities.Add(id))throw new ArgumentException("Invalid or duplicate case ID.");
            var state=new ProgressionState(curve,sample.GetProperty("start_xp").GetInt64());int initial=state.Level,index=0;
            foreach(var award in sample.GetProperty("awards").EnumerateArray())state.Grant("award_"+index++,award.GetInt64());
            rows.Add(new{id,total_xp=state.TotalXp,level=state.Level,levels_gained=state.Level-initial,main_gained=state.EarnedMain,hp_gained=state.BonusHealth,sp_gained=state.BonusResolve});
        }
        if(rows.Count==0)throw new ArgumentException("Study requires cases.");
        File.WriteAllText(output,JsonSerializer.Serialize(new{schema_version=1,rows},new JsonSerializerOptions{WriteIndented=true})+"\n");
        Console.WriteLine("PASS: "+rows.Count+" actual C# progression cases");return 0;
    }
    private static int Main(string[] args)
    {
        try
        {
            if(args.Length==3 && args[0]=="study")return Study(args[1],args[2]);
            if(args.Length==2 && args[0]=="native")return Native(args[1]);
            Console.Error.WriteLine("Usage: NorthStar.Checks.dll native output.json | study input.json output.json");return 2;
        }
        catch(Exception e) when(e is ArgumentException || e is InvalidOperationException || e is OverflowException || e is IOException || e is JsonException || e is FormatException)
        { Console.Error.WriteLine("FAIL: "+e.Message);return 1; }
    }
}
