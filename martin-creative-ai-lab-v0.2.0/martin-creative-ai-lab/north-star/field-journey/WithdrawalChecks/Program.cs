using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using NorthStar.FieldJourney;

static class Program
{
    static readonly List<string> controls=new();
    static void Check(string id,bool ok){if(!ok)throw new Exception(id);if(controls.Contains(id))throw new Exception("Unique control required");controls.Add(id);}
    static JsonElement View(Room r)=>JsonSerializer.SerializeToElement(r.Snapshot());
    static JsonElement I(Room r)=>View(r).GetProperty("intake");
    static JsonElement E(Room r)=>I(r).GetProperty("state");
    static JsonElement C(Room r)=>View(r).GetProperty("sample_case");
    static bool Flag(JsonElement e,string n)=>e.GetProperty(n).GetBoolean();
    static bool Ok(JsonElement e)=>Flag(e,"accepted");
    static JsonElement Send(Room r,string cmd,object? fields=null)
    {var d=new Dictionary<string,object?>{{"command",cmd},{"revision",View(r).GetProperty("sequence").GetInt32()}};if(fields!=null)foreach(var p in JsonSerializer.SerializeToElement(fields).EnumerateObject())d.Add(p.Name,p.Value);return JsonSerializer.SerializeToElement(r.Execute(JsonSerializer.SerializeToElement(d)));}
    static void Do(Room r,string cmd,object? fields=null){if(!Ok(Send(r,cmd,fields)))throw new Exception("Actual setup refused "+cmd);}
    static string Owned(Room r)=>JsonSerializer.Serialize(new{intake=I(r),memory=View(r).GetProperty("memory"),fittings=View(r).GetProperty("fittings"),assembly=View(r).GetProperty("assembly_receipts")});
    static string ClosedFacts(Room r)=>JsonSerializer.Serialize(new{owned=Owned(r),encounter=View(r).GetProperty("encounter_view"),sample=C(r),withdrawn=View(r).GetProperty("withdrawn"),receipt=View(r).GetProperty("withdrawal_receipt")});
    static Room Prepared()
    {
        var r=new Room();Do(r,"draft",new{handle="Iona",accent="teal",class_id="lure",background_id="trailborn",slots=new string?[]{"draw",null,null,null}});Do(r,"review");Do(r,"confirm",new{draft_revision=I(r).GetProperty("draft_revision").GetInt32()});
        foreach(string bench in new[]{"west","east"}){Do(r,"help",new{bench});Do(r,"serve",new{bench});Do(r,"craft",new{bench,rig="trail"});}return r;
    }
    static void Draw(Room r)=>Do(r,"slot",new{slot=1});
    static void Survey(Room r){Draw(r);Draw(r);Do(r,"walk");Draw(r);}
    static void Main(string[] args)
    {
        if(args.Length!=1)throw new ArgumentException("External output JSON required");
        var initial=new Room();string before=Owned(initial);Check("Unconfirmed initial person cannot withdraw a never-departed journey",!Ok(Send(initial,"withdraw"))&&!Flag(View(initial),"withdrawn")&&Owned(initial)==before);
        var r=Prepared();before=Owned(r);Check("Confirmed stocked preparation is not an actual departure",!Ok(Send(r,"withdraw"))&&!Flag(View(r),"withdrawn")&&Owned(r)==before&&!Flag(C(r),"case_spent"));
        Do(r,"begin",new{rig="trail"});before=View(r).GetRawText();
        Check("Stale withdrawal cannot overwrite owner or stored observation",!Ok(JsonSerializer.SerializeToElement(r.Execute(JsonSerializer.SerializeToElement(new{command="withdraw",revision=0}))))&&View(r).GetRawText()==before);
        string duplicate="{\"command\":\"withdraw\",\"revision\":"+View(r).GetProperty("sequence")+",\"revision\":"+View(r).GetProperty("sequence")+"}";
        foreach(string bad in new[]{duplicate,JsonSerializer.Serialize(new{command="withdraw",revision=View(r).GetProperty("sequence").GetInt32(),complete=true}),"{\"command\":\"withdraw\",\"revision\":1.5}"})
        {bool rejected=false;try{r.Execute(JsonDocument.Parse(bad).RootElement);}catch(ArgumentException){rejected=true;}Check("Malformed withdrawal cannot partly settle custody "+controls.Count,rejected&&View(r).GetRawText()==before);}
        string priorEncounter=View(r).GetProperty("encounter_view").GetRawText();string owned=Owned(r);int revision=View(r).GetProperty("sequence").GetInt32();Do(r,"withdraw");var active=View(r);
        Check("Actual departure allows one explicit outer withdrawal",Flag(active,"withdrawn")&&Flag(active,"encounter_historical")&&active.GetProperty("sequence").GetInt32()==revision+1);
        Check("Child active state remains exact history without another contact",Owned(r)==owned&&View(r).GetProperty("encounter_view").GetRawText()==priorEncounter&&Flag(E(r),"active")&&!Flag(E(r),"won")&&!Flag(E(r),"complete"));
        Check("Unused original case is not broken or spent by withdrawal",C(r).GetProperty("status").GetString()=="empty"&&!Flag(C(r),"case_spent")&&!Flag(C(r),"acquired")&&!Flag(C(r),"collection_open")&&C(r).GetProperty("sites").EnumerateArray().All(s=>!Flag(s,"eligible")));
        var receipt=active.GetProperty("withdrawal_receipt");Check("Withdrawal receipt names actual costs and rejects inferred completion or home return",receipt.GetProperty("attempt").GetInt32()==1&&receipt.GetProperty("consumed_rigs").GetInt32()==1&&Flag(receipt,"child_active")&&!Flag(receipt,"complete")&&!Flag(receipt,"returned")&&receipt.GetProperty("health").GetInt32()==E(r).GetProperty("health").GetInt32());
        Check("Withdrawn preparation cannot advertise an eligible authored card",View(r).GetProperty("preparation_book").GetProperty("cards").EnumerateArray().All(c=>!Flag(c,"eligible")));
        string closed=ClosedFacts(r);var commands=new (string command,object? extra)[]{("walk",null),("wait",null),("slot",new{slot=1}),("begin",new{rig="trail"}),("sample",new{site="ridge"}),("help",new{bench="west"}),("demonstrate",new{bench="west"}),("serve",new{bench="west"}),("decline",new{bench="west"}),("wait-window",null),("craft",new{bench="west",rig="trail"}),("allocate",new{axis="focus",points=1}),("draft",new{handle="Iona",accent="violet",class_id="lure",background_id="trailborn",slots=new string?[]{"draw",null,null,null}}),("review",null),("confirm",new{draft_revision=I(r).GetProperty("draft_revision").GetInt32()}),("propose-card",new{card_id=View(r).GetProperty("preparation_book").GetProperty("cards")[0].GetProperty("id").GetString()}),("withdraw",null)};
        foreach(var cmd in commands)Check("Closed expedition refuses later "+cmd.command,!Ok(Send(r,cmd.command,cmd.extra))&&ClosedFacts(r)==closed);
        before=View(r).GetRawText();for(int n=0;n<50;n++)View(r);Check("Reads retain exact withdrawal receipt and observation identity",View(r).GetRawText()==before);
        Check("Withdrawal cannot refund consumed rig or create another purchase",E(r).GetProperty("consumed_rigs").GetInt32()==1&&E(r).GetProperty("inventory").GetProperty("trail_rig").GetInt32()==1&&E(r).GetProperty("inventory").GetProperty("fiber").GetInt32()==0);
        var cargo=Prepared();Do(cargo,"begin",new{rig="trail"});Draw(cargo);Do(cargo,"sample",new{site="ridge"});string sampleReceipt=C(cargo).GetProperty("receipt").GetRawText();owned=Owned(cargo);Do(cargo,"withdraw");
        Check("Explicit withdrawal relinquishes carried custody while keeping acquisition",C(cargo).GetProperty("status").GetString()=="lost"&&C(cargo).GetProperty("loss_reason").GetString()=="withdrawn"&&Flag(C(cargo),"acquired")&&Flag(C(cargo),"case_spent"));
        Check("Relinquished receipt preserves actual paid sampling contact",C(cargo).GetProperty("receipt").GetRawText()==sampleReceipt&&Owned(cargo)==owned&&E(cargo).GetProperty("health").GetInt32()==6&&E(cargo).GetProperty("beat").GetInt32()==2);
        var between=Prepared();Do(between,"begin",new{rig="trail"});Survey(between);Do(between,"draft",new{handle="Iona",accent="violet",class_id="lure",background_id="trailborn",slots=new string?[]{"draw",null,null,null}});owned=Owned(between);Do(between,"withdraw");
        Check("Confirmed person can withdraw between encounters with amendment pending",Flag(View(between),"withdrawn")&&Flag(I(between),"pending")&&Owned(between)==owned&&Flag(E(between),"won")&&!Flag(E(between),"active")&&!Flag(E(between),"complete"));
        Check("Survey withdrawal retains only actual earned XP and remaining rig",E(between).GetProperty("xp").GetInt32()==10&&E(between).GetProperty("consumed_rigs").GetInt32()==1&&E(between).GetProperty("inventory").GetProperty("trail_rig").GetInt32()==1);
        var complete=Prepared();Do(complete,"begin",new{rig="trail"});Survey(complete);Do(complete,"allocate",new{axis="focus",points=2});Do(complete,"begin",new{rig="trail"});Draw(complete);Draw(complete);Do(complete,"walk");Draw(complete);Do(complete,"walk");Draw(complete);owned=Owned(complete);
        Check("Actual final completion cannot be retroactively withdrawn",Flag(E(complete),"complete")&&!Ok(Send(complete,"withdraw"))&&!Flag(View(complete),"withdrawn")&&Owned(complete)==owned&&E(complete).GetProperty("xp").GetInt32()==25);
        var failed=Prepared();Do(failed,"begin",new{rig="trail"});for(int n=0;n<4&&Flag(E(failed),"active");n++)Do(failed,"wait");owned=Owned(failed);Do(failed,"withdraw");Check("After real failure withdrawal closes retry without inventing another defeat",Flag(View(failed),"withdrawn")&&Owned(failed)==owned&&!Flag(E(failed),"won")&&!Flag(E(failed),"active"));
        File.WriteAllText(args[0],JsonSerializer.Serialize(new{schema_version=1,kind="field_explicit_withdrawal_native",checks=new{passed=controls.Count,failed=0},controls,active,cargo=View(cargo),between=View(between),complete=View(complete),failed=View(failed),limits="Original outer lifecycle policy; unchanged child observations remain historical. No escape/home return, new reward/refund, participants, balance, persistence, Unity/Windows/Steam or author approval."},new JsonSerializerOptions{WriteIndented=true})+"\n");Console.WriteLine("PASS: "+controls.Count+" explicit withdrawal native controls");
    }
}
