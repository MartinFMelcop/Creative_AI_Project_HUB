using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using NorthStar.Intake;

static class Program
{
    static readonly List<string> controls=new();
    static JsonElement View(Room r)=>JsonSerializer.SerializeToElement(r.Snapshot());
    static string Facts(Room r){var v=View(r);return JsonSerializer.Serialize(new{identity=v.GetProperty("identity"),state=v.GetProperty("state")});}
    static JsonElement Send(Room r,string command,object? extra=null)
    {
        var values=new Dictionary<string,object?>{{"command",command},{"revision",View(r).GetProperty("sequence").GetInt64()}};
        if(extra!=null)foreach(var p in JsonSerializer.SerializeToElement(extra).EnumerateObject())values.Add(p.Name,p.Value);
        return JsonSerializer.SerializeToElement(r.Execute(JsonSerializer.SerializeToElement(values)));
    }
    static void Check(string id,bool condition){if(!condition)throw new Exception(id);controls.Add(id);}
    static bool Ok(JsonElement v)=>v.GetProperty("accepted").GetBoolean();
    static JsonElement S(Room r)=>View(r).GetProperty("state");
    static void Confirm(Room r){Send(r,"review");Check("Explicit current review confirms at native step "+controls.Count,Ok(Send(r,"confirm",new{draft_revision=View(r).GetProperty("draft_revision").GetInt32()})));}
    static void Main(string[] args)
    {
        if(args.Length!=1)throw new ArgumentException("Output JSON required.");
        var r=new Room();var initial=Facts(r);
        Check("Initial card is unconfirmed",!View(r).GetProperty("confirmed").GetBoolean());
        Check("Unconfirmed craft cannot grant or spend",!Ok(Send(r,"craft",new{request_id="early",recipe_id="trail_rig"}))&&Facts(r)==initial);
        Check("Unconfirmed entry cannot create encounter",!Ok(Send(r,"begin",new{rig="trail"}))&&Facts(r)==initial);
        Check("Confirmation without review fails",!Ok(Send(r,"confirm",new{draft_revision=1}))&&Facts(r)==initial);
        Send(r,"review");int old=View(r).GetProperty("draft_revision").GetInt32();
        Check("Draft can stage independent cosmetic identity",Ok(Send(r,"draft",new{handle="Kestrel",accent="teal",class_id="anchor",background_id="workshop",slots=new string?[]{"brace",null,null,null}}))&&Facts(r)==initial);
        Check("Edit invalidates previous review",!Ok(Send(r,"confirm",new{draft_revision=old}))&&!View(r).GetProperty("confirmed").GetBoolean());
        var before=View(r).GetRawText();
        try{Send(r,"draft",new{handle="Kestrel",accent="teal",class_id="lure",background_id="workshop",slots=new string?[]{"draw",null,null,null}});throw new Exception("Invalid proposal accepted");}catch(ArgumentException){}
        Check("Invalid whole proposal leaves all observation fields exact",View(r).GetRawText()==before);
        Confirm(r);Check("Confirmed card has exact original name and accent",View(r).GetProperty("identity").GetProperty("handle").GetString()=="Kestrel"&&View(r).GetProperty("identity").GetProperty("accent").GetString()=="teal");
        var stale=JsonSerializer.SerializeToElement(new{command="wait",revision=0});before=View(r).GetRawText();
        Check("Stale response refuses",!Ok(JsonSerializer.SerializeToElement(r.Execute(stale))));
        Check("Stale intent leaves stored receipt and owner exact",View(r).GetRawText()==before);
        Send(r,"craft",new{request_id="rig-a",recipe_id="trail_rig"});Send(r,"craft",new{request_id="rig-b",recipe_id="trail_rig"});
        Check("Confirmed identity uses actual finite crafting",S(r).GetProperty("inventory").GetProperty("fiber").GetInt32()==0&&S(r).GetProperty("inventory").GetProperty("trail_rig").GetInt32()==2);
        Send(r,"begin",new{rig="trail"});var active=Facts(r);
        Check("Active cosmetic edit cannot reset owner",!Ok(Send(r,"draft",new{handle="Kestrel",accent="violet",class_id="anchor",background_id="workshop",slots=new string?[]{"brace",null,null,null}}))&&Facts(r)==active);
        foreach(string c in new[]{"walk","slot","walk","slot"})Send(r,c,c=="slot"?new{slot=1}:null);
        Check("Actual survey earns stage without final completion",S(r).GetProperty("won").GetBoolean()&&!S(r).GetProperty("complete").GetBoolean()&&S(r).GetProperty("level").GetInt32()==2);
        Send(r,"allocate",new{axis="focus",points=2});var earned=Facts(r);
        Check("Different handle refuses without losing earned facts",!Ok(Send(r,"draft",new{handle="Other",accent="violet",class_id="anchor",background_id="trailborn",slots=new string?[]{"brace","dash",null,null}}))&&Facts(r)==earned);
        Send(r,"draft",new{handle="Kestrel",accent="violet",class_id="anchor",background_id="trailborn",slots=new string?[]{"brace","dash",null,null}});
        Check("Earned amendment preserves live identity and resources",Facts(r)==earned);
        Check("Pending amendment blocks entry before rig spend",!Ok(Send(r,"begin",new{rig="trail"}))&&Facts(r)==earned);
        Confirm(r);Check("Confirmation preserves earned owner facts",JsonSerializer.Serialize(S(r).GetProperty("inventory"))==JsonSerializer.Serialize(JsonDocument.Parse(earned).RootElement.GetProperty("state").GetProperty("inventory"))&&S(r).GetProperty("attempts").GetInt32()==1&&S(r).GetProperty("xp").GetInt32()==10);
        Send(r,"begin",new{rig="trail"});foreach(int slot in new[]{1,1,2,1,2,1})Send(r,"slot",new{slot});
        Check("Same named owner completes actual earned-action journey",S(r).GetProperty("complete").GetBoolean()&&S(r).GetProperty("consumed_rigs").GetInt32()==2&&View(r).GetProperty("identity").GetProperty("handle").GetString()=="Kestrel");
        var complete=Facts(r);Check("Completed edit cannot erase completion",!Ok(Send(r,"draft",new{handle="Kestrel",accent="teal",class_id="lure",background_id="trailborn",slots=new string?[]{"draw",null,null,null}}))&&Facts(r)==complete);
        var losing=new Room();Confirm(losing);Send(losing,"craft",new{request_id="loss",recipe_id="trail_rig"});Send(losing,"begin",new{rig="trail"});
        for(int n=0;n<20&&S(losing).GetProperty("active").GetBoolean();n++)Send(losing,"wait");
        Check("Actual failure retains spent rig without completion",!S(losing).GetProperty("won").GetBoolean()&&!S(losing).GetProperty("complete").GetBoolean()&&S(losing).GetProperty("consumed_rigs").GetInt32()==1&&S(losing).GetProperty("inventory").GetProperty("trail_rig").GetInt32()==0);
        var loss=Facts(losing);Send(losing,"draft",new{handle="Wayfarer",accent="violet",class_id="anchor",background_id="workshop",slots=new string?[]{"brace",null,null,null}});Confirm(losing);
        Check("Post-loss confirmation never refunds or heals",S(losing).GetProperty("health").GetInt32()==0&&S(losing).GetProperty("consumed_rigs").GetInt32()==1&&S(losing).GetProperty("inventory").GetProperty("trail_rig").GetInt32()==0);
        File.WriteAllText(args[0],JsonSerializer.Serialize(new{schema_version=1,kind="intake_native_consumer",checks=new{passed=controls.Count,failed=0},controls,complete=View(r),failed=View(losing),limits="Software controls, not people, legacy creation parsing, Unity, Windows or Steam."},new JsonSerializerOptions{WriteIndented=true})+"\n");
        Console.WriteLine($"PASS: {controls.Count} intake native consumer controls");
    }
}
