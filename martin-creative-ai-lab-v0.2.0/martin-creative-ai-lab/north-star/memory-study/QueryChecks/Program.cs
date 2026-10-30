using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using NorthStar.Conditions;
using NorthStar.MemoryStudy;

static class Program
{
    static readonly List<string> controls=new();
    static readonly Dictionary<string,ConditionType> Empty=new(StringComparer.Ordinal);
    static readonly Dictionary<string,ConditionValue> NoFacts=new(StringComparer.Ordinal);
    static void Check(string id,bool result){if(!result)throw new Exception(id);controls.Add(id);}
    static void Refuses(string id,Action action){try{action();}catch(ArgumentException){Check(id,true);return;}throw new Exception("Did not refuse: "+id);}
    static QueryReference Q(QueryKind kind,string argument)=>new(kind,argument);
    static QuerySnapshot Snapshot(string context,params QueryObservation[] values)=>new(context,values);
    static QueryObservation Obs(QueryKind kind,string argument,bool value)=>new(Q(kind,argument),value);
    static CompiledCondition Compile(string text,params QueryReference[] queries)=>ConditionCompiler.Compile(text,Empty,"west",queries);
    static JsonElement Json(object value)=>JsonSerializer.SerializeToElement(value);
    static JsonElement State(Room room)=>Json(room.Snapshot());
    static JsonElement Act(Room room,string command,string? bench=null)
    {var sequence=State(room).GetProperty("sequence").GetInt32();return Json(room.Execute(bench==null?Json(new{command,revision=sequence}):Json(new{command,revision=sequence,bench})));}
    static bool Bool(JsonElement value,string name)=>value.GetProperty(name).GetBoolean();
    static int Number(JsonElement value,string name)=>value.GetProperty(name).GetInt32();
    static JsonElement Bench(JsonElement state,string id)=>state.GetProperty("benches").EnumerateArray().Single(x=>x.GetProperty("id").GetString()==id);
    static string Facts(JsonElement state)=>JsonSerializer.Serialize(new{turn=Number(state,"turn"),parts=Number(state,"parts"),coins=Number(state,"coins"),benches=state.GetProperty("benches"),history=state.GetProperty("history")});
    static QueryKind Kind(string function)=>function switch{"HasTag"=>QueryKind.Tag,"HasFlag"=>QueryKind.Flag,"HasRecentEvent"=>QueryKind.RecentEvent,_=>throw new ArgumentException("Unsupported source query function")};
    static int Main(string[] args)
    {
        if(args.Length!=2)throw new ArgumentException("Usage: SOURCE_PROTOCOL OUTPUT_NATIVE");
        var flag=Q(QueryKind.Flag,"ready");var tag=Q(QueryKind.Tag,"ready");var recent=Q(QueryKind.RecentEvent,"ready");
        var negative=Compile("HasFlag(ready)=false",flag);
        Check("Known false can satisfy an exact negative",negative.Evaluate(NoFacts,Snapshot("west",new QueryObservation(flag,false))).Satisfied);
        Check("Known true does not satisfy negative",!negative.Evaluate(NoFacts,Snapshot("west",new QueryObservation(flag,true))).Satisfied);
        var missing=negative.Evaluate(NoFacts,Snapshot("west"));Check("Missing observation is incomplete not false",!missing.Complete&&!missing.Satisfied);
        missing=negative.Evaluate(NoFacts);Check("Missing provider is incomplete",!missing.Complete&&!missing.Satisfied);
        missing=negative.Evaluate(NoFacts,Snapshot("east",new QueryObservation(flag,false)));Check("Foreign exact context is incomplete",!missing.Complete&&!missing.Satisfied);
        missing=negative.Evaluate(NoFacts,Snapshot("West",new QueryObservation(flag,false)));Check("Context spelling is ordinal",!missing.Complete&&!missing.Satisfied);
        missing=negative.Evaluate(NoFacts,Snapshot("west",new QueryObservation(tag,false)));Check("Query kinds are separate identity namespaces",!missing.Complete&&!missing.Satisfied);
        var or=ConditionCompiler.Compile("Allowed=true | HasFlag(ready)=false",new Dictionary<string,ConditionType>{{"Allowed",ConditionType.Boolean}},"west",new[]{flag});
        missing=or.Evaluate(new Dictionary<string,ConditionValue>{{"Allowed",ConditionValue.Boolean(true)}},Snapshot("west"));Check("OR cannot bypass missing query",!missing.Complete&&!missing.Satisfied);
        var and=Compile("HasTag(ready)=false & HasFlag(ready)=false",tag,flag);
        missing=and.Evaluate(NoFacts,Snapshot("west",new QueryObservation(tag,true)));Check("False AND cannot bypass missing query",!missing.Complete&&!missing.Satisfied);
        Refuses("Unknown function rejected",()=>Compile("HasGrant(ready)=true",flag));
        Refuses("Unknown exact query ID rejected",()=>Compile("HasFlag(missing)=false",flag));
        Refuses("Unknown case variant ID rejected",()=>Compile("HasFlag(Ready)=false",flag));
        Refuses("Function names are exact",()=>Compile("hasflag(ready)=false",flag));
        Refuses("Suffix is not silently stripped",()=>Compile("HasRecentEvent(ready@3)=true",recent));
        Refuses("Trailing query text rejected",()=>Compile("HasFlag(ready)=false garbage",flag));
        Refuses("Nonboolean query comparison rejected",()=>Compile("HasFlag(ready)=0",flag));
        Refuses("Unsupported query operator rejected",()=>Compile("HasFlag(ready)!=true",flag));
        Refuses("Multiple arguments rejected",()=>Compile("HasFlag(ready other)=true",flag));
        Refuses("Legacy scalar compiler does not acquire query permissions",()=>ConditionCompiler.Compile("HasFlag(ready)=true",new Dictionary<string,ConditionType>{{"Ready",ConditionType.Boolean}}));
        Refuses("Duplicate query declaration rejected",()=>Compile("HasFlag(ready)=true",flag,Q(QueryKind.Flag,"ready")));
        Refuses("Duplicate observation rejected",()=>Snapshot("west",new QueryObservation(flag,false),new QueryObservation(Q(QueryKind.Flag,"ready"),true)));
        Refuses("Invalid query enum rejected",()=>Q((QueryKind)99,"ready"));
        var declarations=new List<QueryReference>{flag};var compiled=ConditionCompiler.Compile("HasFlag(ready)=true",Empty,"west",declarations);declarations.Clear();
        var observations=new List<QueryObservation>{new QueryObservation(flag,true)};var immutable=new QuerySnapshot("west",observations);observations.Clear();Check("Compiled declarations and observation lists are copied",compiled.Evaluate(NoFacts,immutable).Satisfied);
        Check("Scalar API remains exact",ConditionCompiler.Compile("Count>=2",new Dictionary<string,ConditionType>{{"Count",ConditionType.Integer}}).Evaluate(new Dictionary<string,ConditionValue>{{"Count",ConditionValue.Integer(2)}}).Satisfied);
        Check("Bare declared Boolean query remains true test",Compile("HasFlag(ready)",flag).Evaluate(NoFacts,Snapshot("west",new QueryObservation(flag,true))).Satisfied);
        var strict=new Room("single-offer");var original=new Room("independent");
        Check("Initial unsupported withdrawal refuses",!Bool(Act(strict,"decline","west"),"accepted"));
        foreach(var room in new[]{strict,original}){Check("Actual help accepted "+(room==strict?"strict":"original"),Bool(Act(room,"help","west"),"accepted"));Act(room,"decline","west");Act(room,"demonstrate","west");}
        var st=State(strict);var old=State(original);Check("Renewed support and recent are real even when offer closed",Bool(Bench(st,"west"),"support")&&Bool(Bench(st,"west"),"recent")&&Bool(Bench(st,"west"),"offer_closed"));
        Check("Same actual preparation cost under both policies",Number(st,"parts")==2&&Number(st,"turn")==2&&Number(st,"coins")==2&&Number(old,"parts")==2&&Number(old,"turn")==2&&Number(old,"coins")==2);
        var before=Facts(st);Check("Closed offer repeat withdrawal refuses",!Bool(Act(strict,"decline","west"),"accepted"));Check("Repeated closed withdrawal does not change paid facts or history",Facts(State(strict))==before);
        before=Facts(State(strict));var denied=Act(strict,"serve","west");Check("Real typed negative query alone prevents reopened service",!Bool(denied,"accepted")&&!Bool(Bench(denied,"west"),"condition_satisfied")&&Bool(Bench(denied,"west"),"condition_complete"));
        Check("Denied service spends nothing and writes no receipt",Facts(State(strict))==before);
        var supplied=Act(original,"serve","west");Check("Original policy still supplies after paid renewal",Bool(supplied,"accepted")&&Bool(Bench(supplied,"west"),"delivered")&&Number(supplied,"coins")==1);
        Act(strict,"help","east");supplied=Act(strict,"serve","east");Check("West closure does not close other actual bench",Bool(supplied,"accepted")&&Bool(Bench(supplied,"east"),"delivered")&&!Bool(Bench(supplied,"east"),"offer_closed"));
        var delivered=new Room("single-offer");Act(delivered,"help","west");Act(delivered,"serve","west");var closed=Act(delivered,"decline","west");Check("Decline after acquisition retains actual fitting",Bool(closed,"accepted")&&Bool(Bench(closed,"west"),"delivered")&&Bool(Bench(closed,"west"),"offer_closed"));
        for(int i=0;i<4;i++)Act(delivered,"wait");Check("Elapsed action turns cannot erase acquired fitting or reopen offer",Bool(Bench(State(delivered),"west"),"delivered")&&Bool(Bench(State(delivered),"west"),"offer_closed"));
        var reads=Facts(State(delivered));State(delivered);State(delivered);Check("Reads do not tick or change offer",reads==Facts(State(delivered)));
        var sourceResults=new List<object>();using var document=JsonDocument.Parse(File.ReadAllText(args[0]));
        foreach(var c in document.RootElement.GetProperty("cases").EnumerateArray())
        {
            var symbols=new Dictionary<string,ConditionType>(StringComparer.Ordinal);var facts=new Dictionary<string,ConditionValue>(StringComparer.Ordinal);
            foreach(var f in c.GetProperty("facts").EnumerateArray())
            {string name=f.GetProperty("name").GetString()!,type=f.GetProperty("type").GetString()!;ConditionType t=Enum.Parse<ConditionType>(type);symbols.Add(name,t);var v=f.GetProperty("value");facts.Add(name,t==ConditionType.String?ConditionValue.Text(v.GetString()!):t==ConditionType.Boolean?ConditionValue.Boolean(v.GetBoolean()):ConditionValue.Integer(v.GetInt64()));}
            var q=c.GetProperty("queries").EnumerateArray().Select(x=>new QueryObservation(Q(Kind(x.GetProperty("function").GetString()!),x.GetProperty("argument").GetString()!),x.GetProperty("value").GetBoolean())).ToArray();
            var expression=ConditionCompiler.Compile(c.GetProperty("expression").GetString()!,symbols,"source",q.Select(x=>x.Reference));var result=expression.Evaluate(facts,new QuerySnapshot("source",q));sourceResults.Add(new{id=c.GetProperty("id").GetString(),complete=result.Complete,satisfied=result.Satisfied});
        }
        var output=new{schema_version=1,kind="actual_csharp_typed_queries_and_owned_offer",checks=new{passed=controls.Count,failed=0},controls,source_results=sourceResults,states=new{strict=State(strict),original=State(original),delivered=State(delivered)}};
        File.WriteAllText(args[1],JsonSerializer.Serialize(output,new JsonSerializerOptions{WriteIndented=true})+"\n");Console.WriteLine("PASS: "+controls.Count+" native query/consumer controls and "+sourceResults.Count+" source cases");return 0;
    }
}
