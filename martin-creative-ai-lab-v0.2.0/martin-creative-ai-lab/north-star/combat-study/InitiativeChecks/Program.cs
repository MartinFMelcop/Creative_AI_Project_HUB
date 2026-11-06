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
    static void Check(string name,bool ok){if(!ok)throw new Exception(name);if(controls.Contains(name))throw new Exception("Duplicate control");controls.Add(name);}
    static JsonElement State(Trial t)=>JsonSerializer.SerializeToElement(t.Snapshot());
    static JsonElement Send(Room r,string c)=>JsonSerializer.SerializeToElement(r.Execute(JsonSerializer.SerializeToElement(new{command=c})));
    static object Order(Initiative i)=>new{round=i.Current.Round,playerScore=i.Current.PlayerScore,targetScore=i.Current.TargetScore,seedState=i.Current.SeedState,order=i.Current.Order};
    static object Vectors(JsonElement inputs)
    {
        var result=new List<object>();
        foreach(var input in inputs.EnumerateArray())
        {
            string style=input.GetProperty("style").GetString()!;uint seed=input.GetProperty("seed").GetUInt32();int count=input.GetProperty("rounds").GetInt32();
            if(count<1||count>1000)throw new ArgumentException("Bounded rounds required");
            var i=new Initiative(style,seed);var rounds=new List<object>();for(int n=0;n<count;n++){rounds.Add(Order(i));if(n<count-1)i.Advance();}
            result.Add(new{style,seed,rounds});
        }
        return result;
    }
    static void Main(string[] args)
    {
        if(args.Length!=1&&args.Length!=3)throw new ArgumentException("OUTPUT [--vectors INPUT] required");
        var sample=new Initiative("heavy");string before=JsonSerializer.Serialize(Order(sample));var prior=sample.Current;for(int n=0;n<100;n++)_ =JsonSerializer.Serialize(Order(sample));Check("Queue reads preserve exact scores RNG round and immutable order",before==JsonSerializer.Serialize(Order(sample)));sample.Advance();Check("Advance replaces immutable prior queue once",prior.Round==1&&sample.Current.Round==2&&prior.SeedState!=sample.Current.SeedState);
        foreach(string style in new[]{"heavy","quick"})
        {
            var a=new Initiative(style);var b=new Initiative(style);bool replay=true,bounds=true,changed=false;string first=string.Join(",",a.Current.Order);
            for(int n=0;n<200;n++)
            {
                replay &= JsonSerializer.Serialize(Order(a))==JsonSerializer.Serialize(Order(b));
                bounds &= a.Current.Order.Count==2&&a.Current.Order.Distinct().Count()==2&&a.Current.PlayerScore>=a.PlayerAgility-6&&a.Current.PlayerScore<=a.PlayerAgility+6&&a.Current.TargetScore>=6&&a.Current.TargetScore<=18;
                changed |= string.Join(",",a.Current.Order)!=first;a.Advance();b.Advance();
            }
            Check(style+" seeded rounds replay exactly without extra actor turns",replay&&bounds&&changed);
        }
        bool invalid=false;try{_ =new Initiative("Heavy");}catch(ArgumentException){invalid=true;}Check("Unknown tempo never falls back",invalid);
        var classic=new Trial();Check("Classic carries no initiative policy",State(classic).GetProperty("initiative").ValueKind==JsonValueKind.Null);
        var room=new Room();Check("Tempo unavailable in classic state",!Send(room,"tempo quick").GetProperty("accepted").GetBoolean());
        Send(room,"prepare initiative toxic");var prep=JsonSerializer.SerializeToElement(room.Snapshot());Check("Explicit initiative preparation defaults heavy without active owner",prep.GetProperty("phase").GetString()=="preparation"&&prep.GetProperty("state").ValueKind==JsonValueKind.Null&&prep.GetProperty("preparation").GetProperty("tempo").GetString()=="heavy");
        Check("Explicit quick tempo requires prepared initiative mode",Send(room,"tempo quick").GetProperty("accepted").GetBoolean());Send(room,"begin");
        string owner=JsonSerializer.SerializeToElement(room.Snapshot()).GetProperty("state").GetRawText();Check("Live tempo changes refuse without owner mutation",!Send(room,"tempo heavy").GetProperty("accepted").GetBoolean()&&JsonSerializer.SerializeToElement(room.Snapshot()).GetProperty("state").GetRawText()==owner);
        var quick=new Trial("toxic",initiativeMode:true,tempo:"quick");var heavy=new Trial("toxic",initiativeMode:true);quick.Execute("guard");heavy.Execute("guard");
        Check("Earlier guard halves contact while late guard cannot retroactively protect",State(quick).GetProperty("hp").GetInt32()==81&&State(heavy).GetProperty("hp").GetInt32()==71&&State(quick).GetProperty("lastHit").GetProperty("incoming").GetInt32()==10&&State(heavy).GetProperty("lastHit").GetProperty("incoming").GetInt32()==20);
        Check("Both initial guards close exactly one DOT round",State(quick).GetProperty("round").GetInt32()==1&&State(heavy).GetProperty("round").GetInt32()==1&&State(quick).GetProperty("effects").EnumerateArray().All(e=>e.GetProperty("remaining").GetInt32()==2));
        var refused=new Trial("heated",initiativeMode:true);string queue=State(refused).GetProperty("initiative").GetRawText();Check("Unavailable disarmed strike refuses before RNG contact charge or round",!refused.Execute("strike")&&State(refused).GetProperty("initiative").GetRawText()==queue&&State(refused).GetProperty("round").GetInt32()==0&&State(refused).GetProperty("hp").GetInt32()==100&&State(refused).GetProperty("charges").GetInt32()==2);
        foreach(string command in new[]{"treat","retreat","strike"})
        {
            var dying=new Trial("toxic",initiativeMode:true);foreach(string c in new[]{"bash","bash","treat","strike"})Check("Death setup "+command+" "+c+" "+State(dying).GetProperty("round").GetInt32(),dying.Execute(c));
            var d=State(dying);Check("Later "+command+" cannot happen after lethal earlier contact",d.GetProperty("hp").GetInt32()==9&&dying.Execute(command)&&State(dying).GetProperty("outcome").GetString()=="defeated"&&State(dying).GetProperty("charges").GetInt32()==1&&State(dying).GetProperty("enemyHp").GetInt32()==28);
            string ended=State(dying).GetProperty("initiative").GetRawText();Check("Ended "+command+" refuses replay without new initiative",!dying.Execute(command)&&State(dying).GetProperty("initiative").GetRawText()==ended);
        }
        var escapeHeavy=new Trial("toxic",initiativeMode:true);var escapeQuick=new Trial("toxic",initiativeMode:true,tempo:"quick");escapeHeavy.Execute("retreat");escapeQuick.Execute("retreat");
        Check("Withdrawal occurs in real slot and cannot evade an earlier target",State(escapeHeavy).GetProperty("hp").GetInt32()==80&&State(escapeQuick).GetProperty("hp").GetInt32()==100&&State(escapeHeavy).GetProperty("round").GetInt32()==0&&State(escapeHeavy).GetProperty("outcome").GetString()=="withdrawn");
        var paid=new Trial("toxic",initiativeMode:true);paid.Execute("cleanse");Check("Cleanse spends one actual charge and no identity progression is fabricated",State(paid).GetProperty("charges").GetInt32()==1&&State(paid).GetProperty("hp").GetInt32()==80&&State(paid).GetProperty("enemyHp").GetInt32()==96);
        string paidQueue=State(paid).GetProperty("initiative").GetRawText();Check("Unavailable cleanse cannot consume next queue",!paid.Execute("cleanse")&&State(paid).GetProperty("initiative").GetRawText()==paidQueue&&State(paid).GetProperty("round").GetInt32()==1);
        var rescue=new Trial("toxic",Passive.LastThread,Armor.Light,initiativeMode:true);foreach(string c in new[]{"bash","bash","treat","strike"})rescue.Execute(c);rescue.Execute("treat");Check("Real fatal-hit passive may rescue before the later treatment slot",State(rescue).GetProperty("charges").GetInt32()==0&&State(rescue).GetProperty("rescueSpent").GetBoolean()&&State(rescue).GetProperty("hp").GetInt32()>0);
        var samples=new List<object>();
        foreach(string style in new[]{"heavy","quick"})foreach(string profile in new[]{"toxic","heated"})
        {
            foreach(var policy in new[]{new[]{"cleanse","strike","strike","strike","strike","strike","strike"},new[]{"bash","bash","treat","strike","strike","strike","strike"},new[]{"guard","guard","guard","guard","guard","guard","guard"}})
            {
                var t=new Trial(profile,initiativeMode:true,tempo:style);var steps=new List<object>();foreach(string c in policy){if(!t.Active)break;bool accepted=t.Execute(c);steps.Add(new{command=c,accepted,state=t.Snapshot()});}samples.Add(new{style,profile,policy,steps,final=t.Snapshot()});
                if(profile=="toxic"&&policy[0]=="cleanse")Check(style+" complete fixed toxic policy retains its observed outcome",State(t).GetProperty("outcome").GetString()==(style=="heavy"?"secured":"defeated")&&State(t).GetProperty("hp").GetInt32()==(style=="heavy"?8:0));
            }
        }
        var causal=new List<object>();
        foreach(uint seed in new[]{Initiative.DefaultSeed,6u})
        {
            var t=new Trial("toxic",initiativeMode:true,initiativeSeed:seed);var steps=new List<object>();
            foreach(string c in new[]{"cleanse","strike","strike","strike"}){t.Execute(c);steps.Add(new{command=c,state=t.Snapshot()});}
            var final=State(t);Check("Actual lethal slot causal policy seed "+seed,final.GetProperty("outcome").GetString()=="secured"&&final.GetProperty("hp").GetInt32()==(seed==6?28:8)&&final.GetProperty("charges").GetInt32()==1&&final.GetProperty("round").GetInt32()==4);
            if(seed==6)Check("Lethal player slot skips target contact while closing global round once",final.GetProperty("lastHit").ValueKind==JsonValueKind.Null&&final.GetProperty("events").EnumerateArray().All(e=>!e.GetString()!.StartsWith("Target contact:"))&&final.GetProperty("initiative").GetProperty("order")[0].GetString()=="player");
            causal.Add(new{seed,policy=new[]{"cleanse","strike","strike","strike"},steps,final=t.Snapshot()});
        }
        object vectors=Array.Empty<object>();if(args.Length==3){if(args[1]!="--vectors")throw new ArgumentException("Exact vectors option required");using var d=JsonDocument.Parse(File.ReadAllBytes(args[2]));vectors=Vectors(d.RootElement);}
        File.WriteAllText(args[0],JsonSerializer.Serialize(new{schema_version=1,checks=new{passed=controls.Count,failed=0},controls,vectors,samples,causal},new JsonSerializerOptions{WriteIndented=true})+"\n");Console.WriteLine($"PASS: {controls.Count} initiative native controls");
    }
}
