using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using NorthStar.Combat;
using NorthStar.CombatStudy;

static class Program
{
    static readonly List<string> controls=new();
    static readonly List<object> traces=new();
    static JsonElement J(object value)=>JsonSerializer.SerializeToElement(value);
    static JsonElement State(Trial t)=>J(t.Snapshot());
    static JsonElement View(Room r)=>J(r.Snapshot());
    static JsonElement Act(Room r,string command)=>J(r.Execute(J(new{command})));
    static int N(JsonElement s,string key)=>s.GetProperty(key).GetInt32();
    static string T(JsonElement s,string key)=>s.GetProperty(key).GetString()!;
    static bool B(JsonElement s,string key)=>s.GetProperty(key).GetBoolean();
    static string Facts(JsonElement s)=>JsonSerializer.Serialize(s.EnumerateObject().Where(p=>p.Name!="last").ToDictionary(p=>p.Name,p=>p.Value));
    static string Classic(JsonElement s)=>JsonSerializer.Serialize(s.EnumerateObject().Where(p=>!new[]{"responsePractice","wardAvailable","pending","resolution"}.Contains(p.Name)).ToDictionary(p=>p.Name,p=>p.Value));
    static void Check(string label,bool value){if(!value)throw new Exception(label);controls.Add(label);}
    static void Refuses(string label,System.Action action){try{action();}catch(Exception e)when(e is ArgumentException or InvalidOperationException or NotSupportedException){Check(label,true);return;}throw new Exception("Did not refuse: "+label);}
    static JsonElement Journey(string name,params string[] commands)
    {
        var t=new Trial("toxic",responses:true);var steps=new List<object>();
        foreach(string command in commands){bool accepted=t.Execute(command);steps.Add(new{command,accepted,state=t.Snapshot()});}
        var last=State(t);traces.Add(new{name,steps,last});return last;
    }
    static int Main(string[] args)
    {
        if(args.Length!=1)throw new ArgumentException("Usage: OUTPUT_JSON");
        var unwarded=new ResponseChain(48,false);Check("Unwarded chain has one pending item",unwarded.PendingCount==1&&unwarded.Pending&&!unwarded.HasWard);
        Refuses("Missing ward cannot be countered",()=>unwarded.Resolve(true));Check("Invalid counter leaves pending chain",unwarded.Pending);
        var plain=unwarded.Resolve(false);Check("Unwarded committed strike resolves once",plain.Damage==48&&plain.Entries.Count==1&&plain.Entries[0].Kind==ResponseKind.CommittedStrike);
        Refuses("Duplicate resolution rejected",()=>unwarded.Resolve(false));
        var warded=new ResponseChain(48,true);var blocked=warded.Resolve(false);Check("Ward resolves before strike and counters damage",blocked.Damage==0&&blocked.Entries.Select(x=>x.Kind).SequenceEqual(new[]{ResponseKind.Ward,ResponseKind.CommittedStrike})&&blocked.Entries[0].Applied&&!blocked.Entries[1].Applied);
        var broken=new ResponseChain(48,true).Resolve(true);Check("Break resolves before ward before strike",broken.Damage==48&&broken.Entries.Select(x=>x.Kind).SequenceEqual(new[]{ResponseKind.BreakWard,ResponseKind.Ward,ResponseKind.CommittedStrike}));
        Check("Countered ward has no effect",broken.Entries[0].Applied&&!broken.Entries[1].Applied&&broken.Entries[2].Applied);
        Refuses("Returned resolution cannot be rewritten",()=>((IList<ResponseEntry>)broken.Entries).Clear());
        Refuses("Negative committed amount refused",()=>new ResponseChain(-1,true));Refuses("Oversize committed amount refused",()=>new ResponseChain(1000001,true));
        var baseline=new Trial();var before=Facts(State(baseline));Check("Classic encounter cannot commit",!baseline.Execute("commit")&&Facts(State(baseline))==before);
        var t=new Trial("toxic",responses:true);Check("Commit accepted in response mode",t.Execute("commit"));var cast=State(t);
        Check("Cast debits exactly one shared treatment charge",N(cast,"charges")==1);
        Check("Cast does not deal damage or advance global round",N(cast,"round")==0&&N(cast,"hp")==100&&N(cast,"enemyHp")==96);
        Check("One actual ward reserve commits with the cast",!B(cast,"wardAvailable")&&B(cast.GetProperty("pending"),"ward")&&N(cast.GetProperty("pending"),"items")==2);
        var frozen=Facts(cast);State(t);State(t);Check("Reads cannot resolve or refund pending cast",Facts(State(t))==frozen);
        foreach(var command in new[]{"strike","bash","guard","treat","cleanse","retreat","commit"})Check("Pending chain refuses old action "+command,!t.Execute(command)&&Facts(State(t))==frozen);
        Check("Release resolves committed ward",t.Execute("release"));var released=State(t);
        Check("Countered cast never refunds its cost",N(released,"charges")==1&&N(released,"enemyHp")==96);
        Check("Whole response chain resolves one contact and one global DOT round",N(released,"round")==1&&N(released,"hp")==71&&released.GetProperty("pending").ValueKind==JsonValueKind.Null);
        var after=Facts(released);Check("Release replay cannot act again",!t.Execute("release")&&Facts(State(t))==after);
        Check("Second cast consumes remaining charge",t.Execute("commit")&&N(State(t),"charges")==0);
        Check("Ward reserve is not recreated on second cast",!B(State(t).GetProperty("pending"),"ward"));
        frozen=Facts(State(t));Check("Break without actual ward is atomic",!t.Execute("break-ward")&&Facts(State(t))==frozen);
        Check("Unwarded second release actually damages",t.Execute("release")&&N(State(t),"enemyHp")==48&&N(State(t),"round")==2);
        after=Facts(State(t));Check("Exhausted charge refuses cast atomically",!t.Execute("commit")&&Facts(State(t))==after);
        var winning=Journey("paid-break-win","commit","break-ward","strike","strike");
        Check("Paid break policy actually secures encounter",T(winning,"outcome")=="secured"&&N(winning,"enemyHp")==0&&N(winning,"charges")==0&&N(winning,"round")==3&&N(winning,"hp")==33);
        var yielding=Journey("yield-then-free-strikes-loss","commit","release","strike","strike","strike","strike");
        Check("Yielding failed burst can lose without refund",T(yielding,"outcome")=="defeated"&&N(yielding,"charges")==1&&N(yielding,"enemyHp")>0);
        var hot=new Trial("heated",responses:true);before=Facts(State(hot));Check("Disarm refuses commitment without spending",!hot.Execute("commit")&&Facts(State(hot))==before);
        hot.Execute("bash");hot.Execute("guard");Check("Actual disarm expiry allows later cast",hot.Execute("commit"));Check("Burn freezes committed amount using existing attack multiplier",hot.Execute("break-ward")&&N(State(hot),"enemyHp")==52);
        var room=new Room();var prepared=Act(room,"prepare responses toxic");Check("Room explicitly prepares response mode without encounter",prepared.GetProperty("state").ValueKind==JsonValueKind.Null&&B(prepared.GetProperty("preparation"),"responses"));
        Check("Room begins explicit response preparation",B(Act(room,"begin"),"accepted"));Act(room,"commit");var current=View(room);Check("Room rejects passive swap during pending combat",!B(Act(room,"equip lining heavy"),"accepted")&&Facts(View(room).GetProperty("state"))==Facts(current.GetProperty("state")));
        var restart=Act(room,"restart toxic");Check("Explicit fresh baseline restart is not a live refund",!B(restart.GetProperty("state"),"responsePractice")&&N(restart.GetProperty("state"),"charges")==2&&N(restart.GetProperty("state"),"round")==0);
        foreach(var profile in new[]{"toxic","heated"})
        {
            var a=new Trial(profile);var b=new Trial(profile,responses:true);
            foreach(string command in new[]{"strike","cleanse","bash","guard","strike","treat","strike","strike","retreat"})
            {bool aa=a.Execute(command),bb=b.Execute(command);Check("No-commit policy preserves original gameplay "+profile+" "+controls.Count,aa==bb&&Classic(State(a))==Classic(State(b)));}
        }
        File.WriteAllText(args[0],JsonSerializer.Serialize(new{schema_version=1,kind="actual_owned_response_chain",checks=new{passed=controls.Count,failed=0},controls,traces,cast,released,winning,yielding,heated=State(hot),limits="Bounded original software controls, not full battle stack/initiative, Ruby/RMXP, participants, balance or Unity/Windows/Steam."},new JsonSerializerOptions{WriteIndented=true})+"\n");
        Console.WriteLine("PASS: "+controls.Count+" actual response-chain controls");return 0;
    }
}
