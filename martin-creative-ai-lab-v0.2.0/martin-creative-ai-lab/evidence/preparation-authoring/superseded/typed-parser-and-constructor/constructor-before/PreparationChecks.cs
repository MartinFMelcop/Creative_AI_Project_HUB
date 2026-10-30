using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using NorthStar.FieldJourney;
using NorthStar.Preparation;

static class Program
{
    static readonly List<string> controls=new();
    static void Check(string id,bool value){if(!value)throw new Exception(id);if(controls.Contains(id))throw new Exception("Duplicate native control");controls.Add(id);}
    static JsonElement View(Room r)=>JsonSerializer.SerializeToElement(r.Snapshot());
    static JsonElement E(Room r)=>View(r).GetProperty("intake").GetProperty("state");
    static JsonElement B(Room r)=>View(r).GetProperty("preparation_book");
    static string Game(Room r)=>JsonSerializer.Serialize(new{state=E(r),memory=View(r).GetProperty("memory"),sample=View(r).GetProperty("sample_case"),fittings=View(r).GetProperty("fittings")});
    static bool Flag(JsonElement v,string name)=>v.GetProperty(name).GetBoolean();
    static bool Ok(JsonElement v)=>Flag(v,"accepted");
    static JsonElement Send(Room r,string command,object? fields=null)
    {
        var d=new Dictionary<string,object?>{{"command",command},{"revision",View(r).GetProperty("sequence").GetInt32()}};
        if(fields!=null)foreach(var p in JsonSerializer.SerializeToElement(fields).EnumerateObject())d.Add(p.Name,p.Value);
        return JsonSerializer.SerializeToElement(r.Execute(JsonSerializer.SerializeToElement(d)));
    }
    static void Do(Room r,string command,object? fields=null){if(!Ok(Send(r,command,fields)))throw new Exception("Setup refused "+command);}
    static void Confirm(Room r){Do(r,"review");Do(r,"confirm",new{draft_revision=View(r).GetProperty("intake").GetProperty("draft_revision").GetInt32()});}
    static void Reject(Action action,string name){bool refused=false;try{action();}catch(Exception e)when(e is ArgumentException or JsonException or IOException){refused=true;}Check(name,refused);}
    static void Draft(Room r,Card c)=>Do(r,"draft",new{handle="Wayfarer",accent="copper",class_id=c.Proposal.ClassId,background_id=c.Proposal.BackgroundId,slots=c.Proposal.Slots});
    static void Gear(Room r,string rig){foreach(string bench in new[]{"west","east"}){Do(r,"help",new{bench});Do(r,"serve",new{bench});Do(r,"craft",new{bench,rig});}}
    static void Draw(Room r)=>Do(r,"slot",new{slot=1});
    static void LureSurvey(Room r){Draw(r);Draw(r);Do(r,"walk");Draw(r);}
    static JsonNode Parse(byte[] bytes)=>JsonNode.Parse(bytes)!;
    static Book Changed(byte[] raw,Action<JsonNode> mutate){var n=Parse(raw);mutate(n);return PackLoader.Parse(Encoding.UTF8.GetBytes(n.ToJsonString()));}
    static void Main(string[] args)
    {
        if(args.Length!=1)throw new ArgumentException("OUTPUT required");
        byte[] raw=File.ReadAllBytes(Path.Combine(AppContext.BaseDirectory,"preparations.json"));var book=PackLoader.Default();
        Check("Actual authored pack copied into consumer output and hashed",book.Sha256==Convert.ToHexString(SHA256.HashData(raw)).ToLowerInvariant()&&book.Cards.Count==4);
        var r=new Room();Check("Initial book grants no proposal or confirmation provenance",B(r).GetProperty("draft_card_id").ValueKind==JsonValueKind.Null&&B(r).GetProperty("confirmed_card_id").ValueKind==JsonValueKind.Null);
        var sourceSlots=new string?[]{"draw",null,null,null};var immutable=new Card("immutable","Original","Immutable authored proposal.","lure","trailborn",sourceSlots,1,"trail");sourceSlots[0]="dash";Check("Authored card clones mutable slot inputs",immutable.Proposal.Slots[0]=="draw");
        string game=Game(r);Check("Early earned card refuses without gameplay or provenance grants",!Ok(Send(r,"propose-card",new{card_id="lure-dash"}))&&Game(r)==game&&B(r).GetProperty("draft_card_id").ValueKind==JsonValueKind.Null);
        string before=View(r).GetRawText();Reject(()=>r.Execute(JsonSerializer.SerializeToElement(new{command="propose-card",revision=View(r).GetProperty("sequence").GetInt32(),card_id="LURE-START"})),"Unknown card case is not normalized");Check("Unknown card leaves complete receipt and source facts exact",View(r).GetRawText()==before);
        Reject(()=>r.Execute(JsonDocument.Parse("{\"command\":\"propose-card\",\"revision\":1,\"card_id\":\"lure-start\",\"card_id\":\"anchor-start\"}").RootElement),"Duplicate command fields cannot create a partial draft");
        Do(r,"propose-card",new{card_id="lure-start"});Check("Proposing actual card affects draft only",Game(r)==game&&B(r).GetProperty("draft_card_id").GetString()=="lure-start"&&!Flag(View(r).GetProperty("intake"),"confirmed")&&B(r).GetProperty("confirmed_card_id").ValueKind==JsonValueKind.Null);
        Check("Card proposal has preparation observation and no encounter event",View(r).GetProperty("encounter_view").GetProperty("action").GetProperty("kind").GetString()=="preparation"&&View(r).GetProperty("encounter_view").GetProperty("action").GetProperty("event_sequence").GetInt64()==0);
        Check("Confirmation cannot replace explicit review",!Ok(Send(r,"confirm",new{draft_revision=View(r).GetProperty("intake").GetProperty("draft_revision").GetInt32()})));
        Confirm(r);Check("Separate review and confirmation bind actual whole preparation",B(r).GetProperty("confirmed_card_id").GetString()=="lure-start"&&E(r).GetProperty("class_id").GetString()=="lure"&&E(r).GetProperty("slots")[0].GetString()=="draw");
        Check("Rig recommendation is not acquired or equipped inventory",E(r).GetProperty("attempts").GetInt32()==0&&!E(r).GetProperty("inventory").TryGetProperty("trail_rig",out _)&&E(r).GetProperty("xp").GetInt32()==0);
        var manual=new Room();Draft(manual,book.Find("lure-start"));Confirm(manual);Check("Actual manual and card preparation have equal gameplay facts",Game(manual)==Game(r));
        Do(r,"propose-card",new{card_id="anchor-start"});Do(r,"review");int reviewed=View(r).GetProperty("intake").GetProperty("draft_revision").GetInt32();Draft(r,book.Find("lure-start"));
        Check("Successful manual edit clears draft provenance and expires review",B(r).GetProperty("draft_card_id").ValueKind==JsonValueKind.Null&&View(r).GetProperty("intake").GetProperty("reviewed_revision").ValueKind==JsonValueKind.Null);
        Check("Old reviewed card cannot confirm after manual edit",!Ok(Send(r,"confirm",new{draft_revision=reviewed}))&&B(r).GetProperty("confirmed_card_id").GetString()=="lure-start");Confirm(r);Check("Manual confirmation clears current card provenance",B(r).GetProperty("confirmed_card_id").ValueKind==JsonValueKind.Null);
        var variant=Changed(raw,n=>n["cards"]![1]!["slots"]=new JsonArray((string?)null,"draw",null,null));var authored=new Room("independent",variant);Do(authored,"propose-card",new{card_id="lure-start"});Confirm(authored);Gear(authored,"trail");Do(authored,"begin",new{rig="trail"});
        before=E(authored).GetRawText();Check("Custom authored pack really changes usable slot, not display alone",!Ok(Send(authored,"slot",new{slot=1}))&&E(authored).GetRawText()==before&&Ok(Send(authored,"slot",new{slot=2}))&&E(authored).GetProperty("position").GetInt32()==1);
        Check("Custom source identity remains distinct and stable",B(authored).GetProperty("sha256").GetString()==variant.Sha256&&variant.Sha256!=book.Sha256);
        var lure=new Room();Do(lure,"propose-card",new{card_id="lure-start"});Confirm(lure);Gear(lure,"trail");Do(lure,"begin",new{rig="trail"});game=Game(lure);Check("Active encounter refuses new card without reset",!Ok(Send(lure,"propose-card",new{card_id="anchor-start"}))&&Game(lure)==game);
        LureSurvey(lure);Check("Actual survey earns permission without auto-amendment",E(lure).GetProperty("level").GetInt32()==2&&E(lure).GetProperty("xp").GetInt32()==10&&E(lure).GetProperty("slots")[1].ValueKind==JsonValueKind.Null);
        Do(lure,"allocate",new{axis="focus",points=2});game=Game(lure);Do(lure,"propose-card",new{card_id="lure-dash"});Check("Earned card proposes without healing XP or inventory change",Game(lure)==game&&B(lure).GetProperty("confirmed_card_id").GetString()=="lure-start");Confirm(lure);Check("Earned amendment requires explicit confirmation before slot use",E(lure).GetProperty("slots")[1].GetString()=="dash"&&B(lure).GetProperty("confirmed_card_id").GetString()=="lure-dash");
        Do(lure,"begin",new{rig="trail"});Draw(lure);Draw(lure);Do(lure,"slot",new{slot=2});Draw(lure);Do(lure,"walk");Draw(lure);Check("Authored Lure preparation and earned Dash complete real encounters",Flag(E(lure),"complete")&&E(lure).GetProperty("xp").GetInt32()==25&&E(lure).GetProperty("consumed_rigs").GetInt32()==2);
        var anchor=new Room();Do(anchor,"propose-card",new{card_id="anchor-start"});Confirm(anchor);Gear(anchor,"plate");Do(anchor,"begin",new{rig="plate"});Draw(anchor);Do(anchor,"walk");Do(anchor,"walk");Draw(anchor);Do(anchor,"allocate",new{axis="focus",points=2});Do(anchor,"propose-card",new{card_id="anchor-dash"});Confirm(anchor);Do(anchor,"begin",new{rig="plate"});Do(anchor,"walk");Draw(anchor);Do(anchor,"slot",new{slot=2});Draw(anchor);Do(anchor,"walk");Draw(anchor);
        Check("Authored Anchor identity also enacts actual costly full route",Flag(E(anchor),"complete")&&E(anchor).GetProperty("class_id").GetString()=="anchor"&&E(anchor).GetProperty("consumed_rigs").GetInt32()==2);
        before=View(lure).GetRawText();for(int i=0;i<100;i++)View(lure);Check("Reads cannot reload pack or change actual provenance",View(lure).GetRawText()==before);
        Reject(()=>Changed(raw,n=>n["schema_version"]=2),"Unsupported schema rejected");
        Reject(()=>Changed(raw,n=>n["coins"]=100),"Unknown grant field rejected");
        Reject(()=>Changed(raw,n=>n["cards"]![0]!["class_id"]="unknown"),"Unknown class cannot fall through to Lure");
        Reject(()=>Changed(raw,n=>n["cards"]![1]!["background_id"]="workshop"),"Known incompatible background rejected");
        Reject(()=>Changed(raw,n=>n["cards"]![0]!["slots"]=new JsonArray("draw",null,null,null)),"Wrong discipline skill rejected");
        Reject(()=>Changed(raw,n=>n["cards"]![2]!["minimum_level"]=1),"Declared early Dash rejected at pack intake");
        Reject(()=>Changed(raw,n=>n["cards"]![0]!["id"]="lure-start"),"Duplicate card identity rejects entire pack");
        Reject(()=>Changed(raw,n=>n["cards"]![0]!["slots"]=new JsonArray("brace","brace",null,null)),"Duplicate skill rejected");
        Reject(()=>Changed(raw,n=>n["cards"]![0]!["recommended_rig"]="unprepared"),"Unsupported rig recommendation rejected");
        Reject(()=>Changed(raw,n=>n["cards"]![0]!["slots"]=new JsonArray("brace")),"Wrong slot count rejected");
        Reject(()=>Changed(raw,n=>n["cards"]![0]!["minimum_level"]="1"),"String numeric coercion rejected");
        Reject(()=>PackLoader.Parse(Encoding.UTF8.GetBytes("{\"schema_version\":1,\"schema_version\":1,\"cards\":[]}")),"Duplicate root fields rejected");
        Reject(()=>PackLoader.Parse(new byte[65537]),"Oversized source pack rejected");
        Reject(()=>PackLoader.Parse(Encoding.UTF8.GetBytes("{}")),"Missing required structure rejected");
        Reject(()=>PackLoader.Load(Path.Combine(Path.GetTempPath(),Guid.NewGuid()+".json")),"Missing pack cannot silently use fallback");
        File.WriteAllText(args[0],JsonSerializer.Serialize(new{schema_version=1,checks=new{passed=controls.Count,failed=0},controls,source_book_sha256=book.Sha256,lure=View(lure),anchor=View(anchor),custom=View(authored),limits="Actual software controls overlap outcomes, not independent people, full historical creation parsing, final class canon or Unity/Windows/Steam validation."},new JsonSerializerOptions{WriteIndented=true})+"\n");Console.WriteLine("PASS: "+controls.Count+" authored preparation native controls");
    }
}
