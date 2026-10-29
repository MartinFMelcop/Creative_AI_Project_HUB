using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using NorthStar.FieldJourney;
using NorthStar.FieldSampling;

static class Program
{
    static readonly List<string> controls=new();
    static void Check(string name,bool ok){if(!ok)throw new Exception(name);if(controls.Contains(name))throw new Exception("Repeated check identity");controls.Add(name);}
    static JsonElement View(Room r)=>JsonSerializer.SerializeToElement(r.Snapshot());
    static JsonElement E(Room r)=>View(r).GetProperty("intake").GetProperty("state");
    static JsonElement C(Room r)=>View(r).GetProperty("sample_case");
    static bool Flag(JsonElement e,string key)=>e.GetProperty(key).GetBoolean();
    static string Status(Room r)=>C(r).GetProperty("status").GetString()!;
    static JsonElement Send(Room r,string command,object? fields=null)
    {
        var d=new Dictionary<string,object?>{{"command",command},{"revision",View(r).GetProperty("sequence").GetInt32()}};
        if(fields!=null)foreach(var p in JsonSerializer.SerializeToElement(fields).EnumerateObject())d.Add(p.Name,p.Value);
        return JsonSerializer.SerializeToElement(r.Execute(JsonSerializer.SerializeToElement(d)));
    }
    static bool Ok(JsonElement v)=>Flag(v,"accepted");
    static void Do(Room r,string cmd,object? fields=null){if(!Ok(Send(r,cmd,fields)))throw new Exception("Setup refused "+cmd);}
    static string Facts(Room r)=>JsonSerializer.Serialize(new{state=E(r),memory=View(r).GetProperty("memory"),sample=C(r)});
    static void Refuse(Room r,string cmd,object? fields,string name){string b=Facts(r);Check(name,!Ok(Send(r,cmd,fields))&&Facts(r)==b);}
    static Room Prepared()
    {
        var r=new Room();Do(r,"draft",new{handle="Iona",accent="teal",class_id="lure",background_id="trailborn",slots=new string?[]{"draw",null,null,null}});Do(r,"review");Do(r,"confirm",new{draft_revision=View(r).GetProperty("intake").GetProperty("draft_revision").GetInt32()});
        foreach(string bench in new[]{"west","east"}){Do(r,"help",new{bench});Do(r,"serve",new{bench});Do(r,"craft",new{bench,rig="trail"});}
        return r;
    }
    static void Draw(Room r)=>Do(r,"slot",new{slot=1});
    static void Survey(Room r){Draw(r);Draw(r);Do(r,"walk");Draw(r);}
    static void Final(Room r){Draw(r);Draw(r);Do(r,"walk");Draw(r);Do(r,"walk");Draw(r);}
    static void Focus(Room r)=>Do(r,"allocate",new{axis="focus",points=2});
    static void Main(string[] args)
    {
        if(args.Length!=1)throw new ArgumentException("Output required");
        var initial=new Room();Check("One issued empty case is disclosed, not acquired cargo",Status(initial)=="empty"&&!Flag(C(initial),"case_spent")&&!Flag(C(initial),"acquired"));
        Refuse(initial,"sample",new{site="ridge"},"Unconfirmed nonactive person cannot sample");
        var r=Prepared();Refuse(r,"sample",new{site="ridge"},"Confirmed preparation is not actual site arrival");
        Do(r,"begin",new{rig="trail"});Refuse(r,"sample",new{site="ridge"},"Actual entry at position zero does not acquire site evidence");
        Draw(r);Check("Actual draw reaches ridge without collection",E(r).GetProperty("position").GetInt32()==1&&Status(r)=="empty"&&!Flag(C(r),"acquired"));
        Check("Exact site eligibility separates current and later encounters",C(r).GetProperty("sites")[0].GetProperty("eligible").GetBoolean()&&!C(r).GetProperty("sites")[1].GetProperty("eligible").GetBoolean());
        Refuse(r,"sample",new{site="channel"},"Wrong known site refuses without spending case or beat");
        string before=View(r).GetRawText();string unknown=JsonSerializer.Serialize(new{command="sample",revision=View(r).GetProperty("sequence").GetInt32(),site="forged"});
        try{r.Execute(JsonDocument.Parse(unknown).RootElement);throw new Exception("Unknown site accepted");}catch(ArgumentException){}
        Check("Unknown exact site throws before owner or receipt mutation",View(r).GetRawText()==before);
        int rev=View(r).GetProperty("sequence").GetInt32();string duplicate="{\"command\":\"sample\",\"revision\":"+rev+",\"site\":\"ridge\",\"site\":\"ridge\"}";
        try{r.Execute(JsonDocument.Parse(duplicate).RootElement);throw new Exception("Duplicate fields accepted");}catch(ArgumentException){}
        Check("Duplicate sampling fields cannot cause a partial child transition",View(r).GetRawText()==before);
        Check("Stale sampling intent leaves exact owner snapshot unchanged",!Ok(JsonSerializer.SerializeToElement(r.Execute(JsonSerializer.SerializeToElement(new{command="sample",revision=0,site="ridge"}))))&&View(r).GetRawText()==before);
        int hp=E(r).GetProperty("health").GetInt32(),beat=E(r).GetProperty("beat").GetInt32();string memory=View(r).GetProperty("memory").GetRawText();
        Do(r,"sample",new{site="ridge"});Check("Sampling pays actual Wait bolt contact before acquiring",Status(r)=="carried"&&Flag(C(r),"case_spent")&&Flag(C(r),"acquired")&&E(r).GetProperty("beat").GetInt32()==beat+1&&E(r).GetProperty("health").GetInt32()==hp-4&&E(r).GetProperty("position").GetInt32()==1);
        Check("Receipt records actual before/after damage and the current attempt",C(r).GetProperty("receipt").GetProperty("health_lost").GetInt32()==4&&C(r).GetProperty("receipt").GetProperty("attempt").GetInt32()==1&&C(r).GetProperty("receipt").GetProperty("before_beat").GetInt32()==1);
        Check("Accepted sampling projects actual wait contact, not a fabricated skill",View(r).GetProperty("encounter_view").GetProperty("action").GetProperty("kind").GetString()=="wait");
        Check("Actual encounter sampling never advances historical workshop time",View(r).GetProperty("memory").GetRawText()==memory);
        Refuse(r,"sample",new{site="ridge"},"One spent case cannot collect the same site again");
        Do(r,"walk");Draw(r);Check("Survey victory carries sample but cannot secure final route",Status(r)=="carried"&&Flag(E(r),"won")&&!Flag(E(r),"complete")&&E(r).GetProperty("xp").GetInt32()==10);
        string receipt=C(r).GetProperty("receipt").GetRawText();Focus(r);Check("Earned allocation cannot resupply or secure cargo",Status(r)=="carried"&&Flag(C(r),"case_spent")&&C(r).GetProperty("receipt").GetRawText()==receipt);
        Do(r,"begin",new{rig="trail"});Refuse(r,"sample",new{site="channel"},"Later site cannot replace the already carried sample");Final(r);
        Check("Only actual final Crossing secures the carried ridge sample",Status(r)=="secured"&&Flag(E(r),"complete")&&E(r).GetProperty("xp").GetInt32()==25&&E(r).GetProperty("consumed_rigs").GetInt32()==2);
        Check("Final security preserves original acquisition receipt",C(r).GetProperty("receipt").GetRawText()==receipt&&Flag(C(r),"acquired"));
        var channel=Prepared();Do(channel,"begin",new{rig="trail"});Survey(channel);Check("Deferring site keeps the same unused case after survey",Status(channel)=="empty"&&!Flag(C(channel),"case_spent"));Focus(channel);Do(channel,"begin",new{rig="trail"});Draw(channel);Draw(channel);
        Check("Actual second encounter position two opens channel only",C(channel).GetProperty("sites")[1].GetProperty("eligible").GetBoolean()&&!C(channel).GetProperty("sites")[0].GetProperty("eligible").GetBoolean());
        hp=E(channel).GetProperty("health").GetInt32();Do(channel,"sample",new{site="channel"});Check("Channel sampling pays actual stationary pulse",Status(channel)=="carried"&&E(channel).GetProperty("health").GetInt32()==hp-6&&E(channel).GetProperty("beat").GetInt32()==3&&C(channel).GetProperty("site").GetString()=="channel");Draw(channel);Do(channel,"walk");Draw(channel);
        Check("Channel route can actually secure the exclusive later sample",Status(channel)=="secured"&&Flag(E(channel),"complete")&&E(channel).GetProperty("health").GetInt32()==5&&C(channel).GetProperty("collection_attempt").GetInt32()==2);
        var death=Prepared();Do(death,"begin",new{rig="trail"});Do(death,"walk");Do(death,"wait");Check("Low actual HP ridge eligibility does not promise survival",E(death).GetProperty("health").GetInt32()==2&&C(death).GetProperty("sites")[0].GetProperty("eligible").GetBoolean());
        Do(death,"sample",new{site="ridge"});Check("Lethal collection wait spends case without acquiring",Status(death)=="lost"&&Flag(C(death),"case_spent")&&!Flag(C(death),"acquired")&&!Flag(E(death),"won")&&E(death).GetProperty("health").GetInt32()==0&&C(death).GetProperty("receipt").GetProperty("health_lost").GetInt32()==2);
        Do(death,"begin",new{rig="trail"});Draw(death);Refuse(death,"sample",new{site="ridge"},"Retry cannot replace case broken before acquisition");
        var losing=Prepared();Do(losing,"begin",new{rig="trail"});Draw(losing);Do(losing,"sample",new{site="ridge"});receipt=C(losing).GetProperty("receipt").GetRawText();Do(losing,"wait");Check("Later actual failed encounter loses previously acquired cargo",Status(losing)=="lost"&&Flag(C(losing),"acquired")&&!Flag(E(losing),"won")&&C(losing).GetProperty("receipt").GetRawText()==receipt);
        Do(losing,"begin",new{rig="trail"});Draw(losing);Refuse(losing,"sample",new{site="ridge"},"Retry cannot resupply a lost previously acquired case");
        var unused=Prepared();Do(unused,"begin",new{rig="trail"});for(int i=0;i<4&&Flag(E(unused),"active");i++)Do(unused,"wait");Check("Ordinary failure does not consume an unused case",Status(unused)=="empty"&&!Flag(C(unused),"case_spent"));Do(unused,"begin",new{rig="trail"});Draw(unused);Do(unused,"sample",new{site="ridge"});Check("Same originally unused case remains usable on real retry",Flag(C(unused),"acquired")&&C(unused).GetProperty("collection_attempt").GetInt32()==2);
        var none=Prepared();Do(none,"begin",new{rig="trail"});Survey(none);Focus(none);Do(none,"begin",new{rig="trail"});Final(none);Check("Skipping sampling preserves actual old full-route outcomes",Flag(E(none),"complete")&&E(none).GetProperty("health").GetInt32()==11&&E(none).GetProperty("xp").GetInt32()==25&&Status(none)=="empty"&&!Flag(C(none),"case_spent"));
        before=View(channel).GetRawText();for(int i=0;i<100;i++)View(channel);Check("Repeated reads retain cargo receipt and event identity",View(channel).GetRawText()==before);
        File.WriteAllText(args[0],JsonSerializer.Serialize(new{schema_version=1,kind="field_sampling_native",checks=new{passed=controls.Count,failed=0},controls,ridge=View(r),channel=View(channel),lethal_collection=View(death),later_loss=View(losing),unused_retry=View(unused),no_sampling=View(none),limits="Overlapping software controls, not participants, source balance, approved canon, return/delivery, Unity/Windows/Steam or human assessment."},new JsonSerializerOptions{WriteIndented=true})+"\n");Console.WriteLine("PASS: "+controls.Count+" field sampling native controls");
    }
}
