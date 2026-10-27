using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using NorthStar.FieldJourney;

static class Program
{
    static readonly List<string> controls=new();
    static void Check(string id,bool ok){if(!ok)throw new Exception(id);if(controls.Contains(id))throw new Exception("Unique controls required");controls.Add(id);}
    static JsonElement View(Room r)=>JsonSerializer.SerializeToElement(r.Snapshot());
    static JsonElement I(Room r)=>View(r).GetProperty("intake");
    static JsonElement E(Room r)=>I(r).GetProperty("state");
    static JsonElement M(Room r)=>View(r).GetProperty("memory");
    static JsonElement F(Room r,string b)=>View(r).GetProperty("fittings").EnumerateArray().Single(x=>x.GetProperty("bench").GetString()==b);
    static bool Flag(JsonElement v,string k)=>v.GetProperty(k).GetBoolean();
    static JsonElement Send(Room r,string command,object? extra=null)
    {var d=new Dictionary<string,object?>{{"command",command},{"revision",View(r).GetProperty("sequence").GetInt32()}};if(extra!=null)foreach(var p in JsonSerializer.SerializeToElement(extra).EnumerateObject())d.Add(p.Name,p.Value);return JsonSerializer.SerializeToElement(r.Execute(JsonSerializer.SerializeToElement(d)));}
    static bool Ok(JsonElement v)=>Flag(v,"accepted");
    static string Facts(Room r)=>JsonSerializer.Serialize(new{intake=I(r),memory=M(r),fittings=View(r).GetProperty("fittings"),closed=View(r).GetProperty("workshop_closed"),receipts=View(r).GetProperty("assembly_receipts")});
    static void Refusal(Room r,string cmd,object? extra,string label){string before=Facts(r);Check(label,!Ok(Send(r,cmd,extra))&&Facts(r)==before);}
    static void Confirm(Room r){Send(r,"review");if(!Ok(Send(r,"confirm",new{draft_revision=I(r).GetProperty("draft_revision").GetInt32()})))throw new Exception("Explicit confirmation failed");}
    static Room Person(){var r=new Room();Send(r,"draft",new{handle="Neri",accent="teal",class_id="anchor",background_id="workshop",slots=new string?[]{"brace",null,null,null}});Confirm(r);return r;}
    static void Acquire(Room r,string bench){if(!Ok(Send(r,"help",new{bench}))||!Ok(Send(r,"serve",new{bench})))throw new Exception("Actual component service failed");}
    static void Craft(Room r,string bench,string rig="trail"){if(!Ok(Send(r,"craft",new{bench,rig})))throw new Exception("Actual component assembly failed");}
    static void Survey(Room r){foreach(string cmd in new[]{"walk","slot","walk","slot"})if(!Ok(Send(r,cmd,cmd=="slot"?new{slot=1}:null)))throw new Exception("Actual survey action failed");}
    static void Main(string[] args)
    {
        if(args.Length!=1)throw new ArgumentException("Output JSON required");
        var r=new Room();Refusal(r,"help",new{bench="west"},"Unconfirmed person cannot perform paid local work");Refusal(r,"craft",new{bench="west",rig="trail"},"Unconfirmed card cannot assemble a rig");Refusal(r,"begin",new{rig="trail"},"Unconfirmed refusal cannot close preparation");
        r=Person();Check("Confirmed original identity belongs to the actual private intake",I(r).GetProperty("identity").GetProperty("handle").GetString()=="Neri");
        Refusal(r,"craft",new{bench="west",rig="trail"},"Otherwise stocked crafting refuses without an actually acquired component");
        Send(r,"help",new{bench="west"});Check("Actual help pays only workshop resources",M(r).GetProperty("parts").GetInt32()==3&&M(r).GetProperty("turn").GetInt32()==1&&E(r).GetProperty("inventory").GetProperty("fiber").GetInt32()==4);
        Refusal(r,"craft",new{bench="west",rig="trail"},"Current witness eligibility is not acquired fitting");
        Send(r,"serve",new{bench="west"});Check("Actual service creates one acquired unused fitting",Flag(F(r,"west"),"acquired")&&Flag(F(r,"west"),"available")&&!Flag(F(r,"west"),"spent")&&!Flag(E(r),"complete"));
        Refusal(r,"craft",new{bench="east",rig="trail"},"West component cannot silently fund east provenance");
        for(int n=0;n<3;n++)Send(r,"wait-window");Send(r,"decline",new{bench="west"});Check("Expiry and withdrawal cannot revoke acquired physical component",Flag(F(r,"west"),"available")&&M(r).GetProperty("turn").GetInt32()==5);
        Send(r,"draft",new{handle="Neri",accent="violet",class_id="anchor",background_id="workshop",slots=new string?[]{"brace",null,null,null}});
        Refusal(r,"craft",new{bench="west",rig="trail"},"Pending identity amendment cannot consume fitting or field materials");Confirm(r);
        string oldMemory=M(r).GetRawText();Craft(r,"west");Check("Real assembly consumes exact field inputs and marks the acquired component spent",Flag(F(r,"west"),"acquired")&&Flag(F(r,"west"),"spent")&&!Flag(F(r,"west"),"available")&&E(r).GetProperty("inventory").GetProperty("fiber").GetInt32()==2&&E(r).GetProperty("inventory").GetProperty("binder").GetInt32()==1&&E(r).GetProperty("inventory").GetProperty("trail_rig").GetInt32()==1&&M(r).GetRawText()==oldMemory);
        Refusal(r,"craft",new{bench="west",rig="plate"},"A spent fitting cannot be replayed into a second rig");
        Acquire(r,"east");Check("Two fitting receipts do not imply expedition completion",Flag(M(r),"complete")&&!Flag(E(r),"complete")&&Flag(F(r,"east"),"available"));Craft(r,"east");
        oldMemory=M(r).GetRawText();Send(r,"begin",new{rig="trail"});Check("Actual prepared entry consumes rig and closes workshop",Flag(View(r),"workshop_closed")&&Flag(E(r),"active")&&E(r).GetProperty("consumed_rigs").GetInt32()==1&&E(r).GetProperty("inventory").GetProperty("trail_rig").GetInt32()==1);
        Refusal(r,"wait-window",null,"Departure prevents remote workshop clock advancement");Refusal(r,"demonstrate",new{bench="west"},"Departure prevents remotely observed work or acquired output");
        Survey(r);Check("Survey progress is actual earned level and not final completion",Flag(E(r),"won")&&!Flag(E(r),"complete")&&E(r).GetProperty("level").GetInt32()==2&&M(r).GetRawText()==oldMemory);
        Send(r,"allocate",new{axis="focus",points=2});Send(r,"draft",new{handle="Neri",accent="violet",class_id="anchor",background_id="trailborn",slots=new string?[]{"brace","dash",null,null}});Confirm(r);
        Check("Earned amendment preserves person and spent provenance",I(r).GetProperty("identity").GetProperty("handle").GetString()=="Neri"&&E(r).GetProperty("attempts").GetInt32()==1&&Flag(F(r,"west"),"spent")&&Flag(F(r,"east"),"spent"));
        Send(r,"begin",new{rig="trail"});foreach(int slot in new[]{1,1,2,1,2,1})Send(r,"slot",new{slot});
        Check("Actual full route retains the same confirmed person and two spent rigs",Flag(E(r),"complete")&&Flag(E(r),"won")&&E(r).GetProperty("xp").GetInt32()==25&&E(r).GetProperty("consumed_rigs").GetInt32()==2&&I(r).GetProperty("identity").GetProperty("handle").GetString()=="Neri");
        Check("Encounter beats never advanced or manufactured workshop observations",M(r).GetRawText()==oldMemory);
        var early=Person();Acquire(early,"west");Craft(early,"west");Acquire(early,"east");Send(early,"begin",new{rig="trail"});Survey(early);
        Check("Premature departure can retain an acquired but unused east fitting",Flag(F(early,"east"),"available")&&Flag(View(early),"workshop_closed")&&E(early).GetProperty("inventory").GetProperty("trail_rig").GetInt32()==0);
        Refusal(early,"craft",new{bench="east",rig="trail"},"Unused fitting does not imply remote assembly or return to workshop");Refusal(early,"begin",new{rig="trail"},"Prepared harder entry can remain unfunded after premature departure");
        var losing=Person();Acquire(losing,"west");Craft(losing,"west");Send(losing,"begin",new{rig="trail"});for(int n=0;n<10&&Flag(E(losing),"active");n++)Send(losing,"wait");
        Check("Actual loss cannot refund allocated fitting or consumed rig",!Flag(E(losing),"won")&&!Flag(E(losing),"complete")&&Flag(F(losing,"west"),"acquired")&&Flag(F(losing,"west"),"spent")&&!Flag(F(losing,"west"),"available")&&E(losing).GetProperty("consumed_rigs").GetInt32()==1&&E(losing).GetProperty("inventory").GetProperty("trail_rig").GetInt32()==0);
        var bare=Person();Send(bare,"begin",new{rig="unprepared"});Check("Explicit unchanged unprepared entry is not falsely component-gated",Flag(E(bare),"active")&&E(bare).GetProperty("consumed_rigs").GetInt32()==0&&Flag(View(bare),"workshop_closed")&&!Flag(F(bare,"west"),"acquired"));Send(bare,"slot",new{slot=1});Check("Unprepared entry does not gain discipline skill",E(bare).GetProperty("beat").GetInt32()==0);
        var before=View(losing).GetRawText();var stale=JsonSerializer.SerializeToElement(new{command="wait",revision=0});Check("Old outer intent refuses without owner or stored observation mutation",!Ok(JsonSerializer.SerializeToElement(losing.Execute(stale)))&&View(losing).GetRawText()==before);
        try{losing.Execute(JsonSerializer.SerializeToElement(new{command="craft",revision=View(losing).GetProperty("sequence").GetInt32(),bench="forged",rig="trail"}));throw new Exception("Forged provenance accepted");}catch(ArgumentException){}
        Check("Malformed provenance is rejected before any child mutation",View(losing).GetRawText()==before);
        File.WriteAllText(args[0],JsonSerializer.Serialize(new{schema_version=1,kind="field_journey_native",checks=new{passed=controls.Count,failed=0},controls,complete=View(r),premature=View(early),losing=View(losing),unprepared=View(bare),limits="Synthetic overlapping controls, not people, source balance, Unity/Windows/Steam, account persistence or production authority."},new JsonSerializerOptions{WriteIndented=true})+"\n");Console.WriteLine($"PASS: {controls.Count} field journey native controls");
    }
}
