using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using NorthStar.Memory;
using NorthStar.MemoryStudy;

static class Program
{
    static readonly List<string> controls=new();
    static void Check(string id,bool condition){if(!condition)throw new Exception(id);if(controls.Contains(id))throw new Exception("Duplicate native control");controls.Add(id);}
    static JsonElement View(Room r)=>JsonSerializer.SerializeToElement(r.Snapshot());
    static JsonElement Bench(Room r,string name)=>View(r).GetProperty("benches").EnumerateArray().Single(b=>b.GetProperty("id").GetString()==name);
    static JsonElement Send(Room r,string command,string? bench=null)
    {var d=new Dictionary<string,object?>{{"command",command},{"revision",View(r).GetProperty("sequence").GetInt32()}};if(bench!=null)d.Add("bench",bench);return JsonSerializer.SerializeToElement(r.Execute(JsonSerializer.SerializeToElement(d)));}
    static bool Ok(JsonElement o)=>o.GetProperty("accepted").GetBoolean();
    static bool B(Room r,string bench,string key)=>Bench(r,bench).GetProperty(key).GetBoolean();
    static void RefusedWithoutFacts(Room r,string cmd,string bench,string label)
    {var before=View(r);var after=Send(r,cmd,bench);Check(label,!Ok(after)&&before.GetProperty("turn").GetInt64()==after.GetProperty("turn").GetInt64()&&before.GetProperty("parts").GetInt32()==after.GetProperty("parts").GetInt32()&&before.GetProperty("coins").GetInt32()==after.GetProperty("coins").GetInt32()&&before.GetProperty("benches").GetRawText()==after.GetProperty("benches").GetRawText()&&before.GetProperty("history").GetRawText()==after.GetProperty("history").GetRawText());}
    static object Native()
    {
        var f=new FlagMemory(new[]{new FlagDefinition("known",FlagScope.Npc,3)});
        f.Set("known",true,"west");Check("Named flag cannot leak to another subject",f.Exact("known",FlagScope.Npc,"west")&&!f.Exact("known",FlagScope.Npc,"east"));
        f.Set("known",true,null,FlagScope.Global);f.Set("known",false,"west");Check("Explicit source union retains global despite false local",f.Any("known","west")&&!f.Exact("known",FlagScope.Npc,"west"));
        f.Clear("known",null,FlagScope.Global);Check("Exact clear cannot resurrect false local",!f.Any("known","west"));
        try{f.Set("known",true);throw new Exception("Missing context granted");}catch(ArgumentException){}Check("Missing named context refuses without advancing",f.Turn==0&&!f.Any("known","east"));
        try{f.Set("unknown",true);throw new Exception("Unknown granted");}catch(ArgumentException){}Check("Unknown flag cannot silently create global authority",!f.Any("known"));
        f.Set("known",true,"east",ttlOverride:0);Check("Zero TTL inactive at insertion boundary",!f.Exact("known",FlagScope.Npc,"east"));
        f.Set("known",true,"east");f.Tick(2);Check("TTL still active immediately before expiry",f.Exact("known",FlagScope.Npc,"east"));f.Tick();Check("TTL inactive at exact expiry",!f.Exact("known",FlagScope.Npc,"east"));
        var events=new RecentMemory(new[]{new EventDefinition("seen",3)});events.Push("seen");Check("Source global event wildcard is retained explicitly",events.Any("seen","west")&&events.Any("seen","east"));Check("Strict witness excludes that same global wildcard",!events.Exact("seen","west")&&!events.Exact("seen","east"));
        events.Push("seen","west");events.Clear("seen","west");Check("Named event clear preserves separate source-global event",events.Any("seen","west")&&!events.Exact("seen","west"));
        events.Clear("seen");events.Push("seen","west");events.Tick(0);Check("Typed nonpositive source turn increment clamps to one",events.Turn==1&&events.Exact("seen","west"));events.Tick(2);Check("Recent event uses same strict expiry boundary",!events.Any("seen","west"));
        var r=new Room();Check("Initial service has no witness or output",!B(r,"west","helped")&&!B(r,"west","delivered")&&!B(r,"east","eligible"));
        RefusedWithoutFacts(r,"serve","west","An unobserved service cannot charge or supply");
        RefusedWithoutFacts(r,"demonstrate","west","Demonstration cannot manufacture past help");
        Send(r,"help","west");Check("Actual help pays then records local history and window",View(r).GetProperty("parts").GetInt32()==3&&View(r).GetProperty("turn").GetInt64()==1&&B(r,"west","helped")&&B(r,"west","support")&&B(r,"west","recent")&&Bench(r,"west").GetProperty("expires").GetInt64()==4);
        RefusedWithoutFacts(r,"serve","east","Another bench cannot use private observation");
        Send(r,"wait");Send(r,"wait");Check("Opportunity remains before exact boundary",B(r,"west","eligible")&&View(r).GetProperty("turn").GetInt64()==3);
        Send(r,"serve","west");Check("Service gate precedes actual turn cost and survives expiry",View(r).GetProperty("turn").GetInt64()==4&&!B(r,"west","recent")&&B(r,"west","delivered")&&B(r,"west","helped")&&View(r).GetProperty("coins").GetInt32()==1);
        RefusedWithoutFacts(r,"serve","west","Actual output cannot be minted twice");
        Send(r,"help","east");Send(r,"serve","east");Check("Independent actual second service completes with finite stock",View(r).GetProperty("complete").GetBoolean()&&View(r).GetProperty("coins").GetInt32()==0&&View(r).GetProperty("parts").GetInt32()==2);
        var stable=View(r).GetRawText();Check("Repeated reads own no clock or outcome",View(r).GetRawText()==stable);
        var expired=new Room();Send(expired,"help","west");Send(expired,"wait");Send(expired,"wait");Send(expired,"wait");Check("Expiry retains actual past help and current relation support",B(expired,"west","helped")&&B(expired,"west","support")&&!B(expired,"west","recent")&&!B(expired,"west","delivered"));
        RefusedWithoutFacts(expired,"serve","west","Expired opportunity cannot consume coin or claim output");
        int past=View(expired).GetProperty("history").GetArrayLength();Send(expired,"demonstrate","west");Check("Fresh observed demonstration pays another real part and turn",B(expired,"west","eligible")&&View(expired).GetProperty("parts").GetInt32()==2&&View(expired).GetProperty("turn").GetInt64()==5&&View(expired).GetProperty("history").GetArrayLength()==past+1);
        Send(expired,"decline","west");Check("Withdrawal clears opportunity without erasing past work or paying turn",B(expired,"west","helped")&&!B(expired,"west","support")&&!B(expired,"west","recent")&&View(expired).GetProperty("turn").GetInt64()==5);
        Send(expired,"demonstrate","west");Send(expired,"serve","west");Check("Explicit paid re-demonstration restores support and allows actual output",B(expired,"west","support")&&B(expired,"west","delivered")&&View(expired).GetProperty("parts").GetInt32()==1);
        Send(expired,"decline","west");Check("Later withdrawal cannot erase an acquired fitting",B(expired,"west","delivered")&&B(expired,"west","helped"));
        var losing=new Room();Send(losing,"help","west");for(int i=0;i<3;i++)Send(losing,"demonstrate","west");Check("Repetition can exhaust parts without making another bench witnessed",View(losing).GetProperty("parts").GetInt32()==0&&!B(losing,"east","helped"));
        RefusedWithoutFacts(losing,"help","east","Spent demonstration parts cannot be refunded into second work");
        for(int i=0;i<3;i++)Send(losing,"wait");RefusedWithoutFacts(losing,"demonstrate","west","Exhausted expired policy cannot fabricate a replacement part");
        var before=View(losing).GetRawText();var stale=JsonSerializer.SerializeToElement(new{command="wait",revision=0});Check("Old queued intent refuses without stored observation mutation",!Ok(JsonSerializer.SerializeToElement(losing.Execute(stale)))&&View(losing).GetRawText()==before);
        try{losing.Execute(JsonSerializer.SerializeToElement(new{command="help",revision=View(losing).GetProperty("sequence").GetInt32(),bench="other"}));throw new Exception("Unknown bench accepted");}catch(ArgumentException){}
        Check("Unknown actual recipient leaves every observation field exact",View(losing).GetRawText()==before);
        return new{schema_version=1,kind="memory_native_consumer",checks=new{passed=controls.Count,failed=0},controls,complete=View(r),expired=View(expired),losing=View(losing),limits="Software controls overlap outcomes; not Ruby/RGSS, human witnesses, participants, Unity, Windows or Steam."};
    }
    static int Main(string[] args)
    {
        if(args.Length==2&&args[0]=="--native")
        {File.WriteAllText(args[1],JsonSerializer.Serialize(Native(),new JsonSerializerOptions{WriteIndented=true})+"\n");Console.WriteLine($"PASS: {controls.Count} memory native controls");return 0;}
        if(args.Length==3&&args[0]=="--cases")return Cases(args[1],args[2]);
        Console.Error.WriteLine("Usage: --native OUTPUT | --cases INPUT OUTPUT");return 2;
    }
    static int Cases(string input,string output)
    {
        using var doc=JsonDocument.Parse(File.ReadAllText(input));var results=new List<object>();
        foreach(var c in doc.RootElement.EnumerateArray())
        {
            var d=c.GetProperty("definition");string id=d.GetProperty("id").GetString()!;
            int? ttl=d.GetProperty("ttl").ValueKind==JsonValueKind.Null?null:d.GetProperty("ttl").GetInt32();
            bool flag=c.GetProperty("kind").GetString()=="flag";
            FlagScope declared=flag?Enum.Parse<FlagScope>(d.GetProperty("scope").GetString()!):FlagScope.Global;
            FlagMemory? f=flag?new FlagMemory(new[]{new FlagDefinition(id,declared,ttl)}):null;
            RecentMemory? e=flag?null:new RecentMemory(new[]{new EventDefinition(id,ttl)});
            var observations=new List<bool>();
            foreach(var op in c.GetProperty("operations").EnumerateArray())
            {
                string action=op.GetProperty("op").GetString()!;string? subject=op.TryGetProperty("subject",out var sub)&&sub.ValueKind!=JsonValueKind.Null?sub.GetString():null;
                FlagScope scope=op.TryGetProperty("scope",out var sc)?Enum.Parse<FlagScope>(sc.GetString()!):declared;
                if(action=="tick"){if(flag)f!.Tick(op.GetProperty("count").GetInt32());else e!.Tick(op.GetProperty("count").GetInt32());}
                else if(flag)
                {
                    if(action=="set")f!.Set(id,op.GetProperty("value").GetBoolean(),subject,scope);
                    else if(action=="clear")f!.Clear(id,subject,scope);
                    else if(action=="any")observations.Add(f!.Any(id,subject));
                    else if(action=="exact")observations.Add(f!.Exact(id,scope,subject));
                    else throw new ArgumentException("Unknown flag operation.");
                }
                else
                {
                    if(action=="push")e!.Push(id,subject);
                    else if(action=="clear")e!.Clear(id,subject);
                    else if(action=="any")observations.Add(e!.Any(id,subject));
                    else if(action=="exact")observations.Add(e!.Exact(id,subject!));
                    else throw new ArgumentException("Unknown event operation.");
                }
            }
            results.Add(new{id=c.GetProperty("id").GetString(),observations,turn=flag?f!.Turn:e!.Turn});
        }
        File.WriteAllText(output,JsonSerializer.Serialize(results,new JsonSerializerOptions{WriteIndented=true})+"\n");return 0;
    }
}
