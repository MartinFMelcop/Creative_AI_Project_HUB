using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using NorthStar.Combat;
using NorthStar.CombatStudy;
static class Program
{
    static readonly List<string> checks=new();
    static void Check(string name,bool pass){if(!pass)throw new Exception(name);checks.Add(name);}
    static JsonElement S(Trial t)=>JsonSerializer.SerializeToElement(t.Snapshot());
    static int N(JsonElement s,string k)=>s.GetProperty(k).GetInt32();
    static int Main(string[] args)
    {
        if(args.Length==3&&args[0]=="--source-vectors")
        {
            var cases=JsonDocument.Parse(File.ReadAllText(args[1])).RootElement;var output=new List<object>();
            foreach(var c in cases.EnumerateArray())
            {
                int capacity=c.GetProperty("capacity").GetInt32();var b=new Breakbar(capacity);var steps=new List<object>();
                foreach(var s in c.GetProperty("steps").EnumerateArray())
                {
                    string category=s.GetProperty("category").GetString()!;bool immune=s.GetProperty("immune").GetBoolean();
                    string before_phase=b.Protected?"Protected":"Exposed";int before_value=b.Value;
                    var result=b.Apply(Enum.Parse<ControlWeight>(category),immune);
                    steps.Add(new{category,immune,before_phase,before_value,after_phase=b.Protected?"Protected":"Exposed",after_value=b.Value,applied=result.Applied,drained=result.Drained,refilled=result.Refilled});
                }
                output.Add(new{id=c.GetProperty("id").GetString(),capacity,steps});
            }
            File.WriteAllText(args[2],JsonSerializer.Serialize(output,new JsonSerializerOptions{WriteIndented=true})+"\n");return 0;
        }
        var bar=new Breakbar(5);
        Check("hard drains three without control",!bar.Apply(ControlWeight.Hard).Applied&&bar.Value==2&&bar.Protected);
        Check("specific immunity neither drains nor applies",!bar.Apply(ControlWeight.Hard,true).Applied&&bar.Value==2);
        Check("breaking application drains only",!bar.Apply(ControlWeight.Hard).Applied&&bar.Value==0&&!bar.Protected);
        Check("exposed hard applies and refills",bar.Apply(ControlWeight.Hard).Applied&&bar.Value==3&&!bar.Protected);
        Check("positive exposed value remains vulnerable",bar.Apply(ControlWeight.Light).Applied&&bar.Value==4&&!bar.Protected);
        Check("full refill application applies before protection",bar.Apply(ControlWeight.Light).Applied&&bar.Value==5&&bar.Protected);
        Check("renewed protection drains instead of controls",!bar.Apply(ControlWeight.Light).Applied&&bar.Value==4);
        try{bar.Apply((ControlWeight)2);throw new Exception("accepted invalid weight");}catch(ArgumentOutOfRangeException){Check("invalid category rejected",true);}
        var classic=new Trial();Check("classic refuses new action",!classic.Execute("light-control")&&N(S(classic),"round")==0);
        var t=new Trial("toxic",controls:true);
        Check("hard actual cost round and contact",t.Execute("hard-control")&&N(S(t),"charges")==1&&N(S(t),"round")==1&&N(S(t),"hp")==71);
        Check("light pays contact plus DOT",t.Execute("light-control")&&N(S(t),"hp")==42);
        Check("zero crossing still pays contact",t.Execute("light-control")&&N(S(t),"hp")==13&&S(t).GetProperty("breakbar").GetProperty("phase").GetString()=="exposed");
        Check("exposed control suppresses contact but DOT payable",t.Execute("hard-control")&&N(S(t),"hp")==7&&N(S(t),"charges")==0&&N(S(t),"enemyHp")==96);
        string before=S(t).GetProperty("breakbar").ToString();int round=N(S(t),"round");
        Check("empty hard refused without advancing bar round",!t.Execute("hard-control")&&N(S(t),"round")==round&&S(t).GetProperty("breakbar").ToString()==before);
        Check("partial refill remains exposed",t.Execute("light-control")&&N(S(t),"hp")==1&&S(t).GetProperty("breakbar").GetProperty("phase").GetString()=="exposed");
        Check("full refill controls actual contact",t.Execute("light-control")&&N(S(t),"hp")==1&&S(t).GetProperty("breakbar").GetProperty("phase").GetString()=="protected");
        Check("next immune contact defeats",t.Execute("light-control")&&S(t).GetProperty("outcome").GetString()=="defeated");
        Check("terminal control refuses",!t.Execute("light-control"));
        var r=new Room();JsonElement Act(string command)=>JsonSerializer.SerializeToElement(r.Execute(JsonSerializer.SerializeToElement(new{command})));
        Check("explicit preparation has no owner state",Act("prepare controls toxic").GetProperty("state").ValueKind==JsonValueKind.Null);
        Check("begin creates original control practice",Act("begin").GetProperty("state").GetProperty("breakbar").GetProperty("value").GetInt32()==5);
        Check("retreat remains explicit not boss-world escape",Act("retreat").GetProperty("state").GetProperty("outcome").GetString()=="withdrawn");
        Check("read stable",JsonSerializer.Serialize(r.Snapshot())==JsonSerializer.Serialize(r.Snapshot()));
        var report=new{checks=checks.Count,controls=checks,trace=S(t)};
        string json=JsonSerializer.Serialize(report,new JsonSerializerOptions{WriteIndented=true})+"\n";
        if(args.Length==1)File.WriteAllText(args[0],json);Console.Write(json);return 0;
    }
}
