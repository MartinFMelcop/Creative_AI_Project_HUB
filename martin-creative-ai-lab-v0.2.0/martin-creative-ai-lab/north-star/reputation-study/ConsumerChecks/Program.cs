using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using NorthStar.ReputationStudy;

static class Checks
{
    static readonly List<string> Passed=new();
    static void Check(bool condition,string label){if(!condition)throw new InvalidOperationException(label);Passed.Add(label);}
    static JsonElement Read(Room r)=>JsonSerializer.SerializeToElement(r.Snapshot());
    static JsonElement Act(Room r,string command)
    {using var d=JsonDocument.Parse(JsonSerializer.Serialize(new {command}));return JsonSerializer.SerializeToElement(r.Execute(d.RootElement));}
    static JsonElement State(Room r)=>Read(r).GetProperty("state");
    static JsonElement Region(Room r,string id)=>State(r).GetProperty("regions").EnumerateArray().Single(x=>x.GetProperty("id").GetString()==id);
    static int I(JsonElement e,string key)=>e.GetProperty(key).GetInt32();
    static bool B(JsonElement e,string key)=>e.GetProperty(key).GetBoolean();
    static bool Apply(Room r,string command)=>B(Act(r,command),"accepted");
    static void UnchangedRefusal(Room r,string command,string label)
    {string before=State(r).GetRawText();Check(!Apply(r,command)&&State(r).GetRawText()==before,label);}
    static int Main(string[] args)
    {
        try
        {
            if(args.Length!=1)throw new ArgumentException("Usage: ConsumerChecks FRESH_OUTPUT_JSON");
            var r=new Room();
            Check(I(State(r),"time")==4&&I(State(r),"coins")==3,"finite-original-starting-resources");
            Check(I(Region(r,"quay"),"standing")==-1&&I(Region(r,"orchard"),"standing")==-1,"explicit-original-seeds-not-source-defaults");
            UnchangedRefusal(r,"service","coins-cannot-buy-through-standing-refusal");
            UnchangedRefusal(r,"return","promise-cannot-return-unheld-tool");
            Check(Apply(r,"borrow")&&B(Region(r,"quay"),"custody")&&I(Region(r,"quay"),"standing")==-1&&I(State(r),"time")==4,"actual-loan-is-not-return-or-standing-event");
            UnchangedRefusal(r,"borrow","one-loan-cannot-duplicate-tool");
            Apply(r,"visit orchard");UnchangedRefusal(r,"return","other-region-tool-cannot-be-returned-here");
            Check(!B(Region(r,"orchard"),"custody")&&B(Region(r,"quay"),"custody"),"custody-remains-region-specific");
            Apply(r,"visit quay");Check(Apply(r,"return"),"actual-inspected-return-accepted");
            Check(I(State(r),"time")==2&&I(State(r),"coins")==3&&!B(Region(r,"quay"),"custody")&&B(Region(r,"quay"),"returned"),"return-consumes-time-and-held-tool-without-spending-coins");
            Check(I(Region(r,"quay"),"standing")==1&&I(Region(r,"orchard"),"standing")==-1,"accepted-return-crosses-only-its-region");
            UnchangedRefusal(r,"return","returned-tool-cannot-award-event-twice");
            Check(Apply(r,"service")&&B(Region(r,"quay"),"service")&&I(State(r),"time")==1&&I(State(r),"coins")==1,"real-service-consumes-one-period-and-two-coins");
            UnchangedRefusal(r,"service","repeat-service-cannot-debit-or-receipt-twice");
            var receipts=State(r).GetProperty("receipts").EnumerateArray().ToArray();
            Check(receipts.Length==3&&receipts.Select(x=>x.GetProperty("kind").GetString()).SequenceEqual(new[]{"borrow","return","service"}),"actual-receipt-order-separates-custody-return-and-service");
            Apply(r,"visit orchard");Apply(r,"borrow");UnchangedRefusal(r,"return","insufficient-time-keeps-outstanding-other-loan");
            Check(B(Region(r,"orchard"),"custody")&&!B(Region(r,"orchard"),"returned")&&!B(Region(r,"orchard"),"service"),"elapsed-budget-does-not-return-outstanding-loan");
            var losing=new Room();bool allHelp=true;for(int n=0;n<4;n++)allHelp&=Apply(losing,"help");Check(allHelp,"four-actual-minor-help-events-accepted");
            Check(I(State(losing),"time")==0&&I(Region(losing,"quay"),"standing")==-1&&I(Region(losing,"quay"),"work")==4,"retained-source-counterexample-repeated-minor-help-stalls");
            UnchangedRefusal(losing,"help","exhausted-time-cannot-create-extra-help");UnchangedRefusal(losing,"service","losing-help-policy-never-supplies-service");
            var alternate=new Room();Apply(alternate,"borrow");Apply(alternate,"return");Apply(alternate,"help");
            Check(I(Region(alternate,"quay"),"standing")==2&&Apply(alternate,"service")&&I(State(alternate),"time")==0,"minor-help-after-actual-crossing-can-improve-standing-at-real-cost");
            string snapshot=Read(alternate).GetRawText();Check(Enumerable.Range(0,5).All(_=>Read(alternate).GetRawText()==snapshot),"repeated-observation-never-advances-outcomes");
            foreach(string malformed in new[]{"{}","{\"command\":\"service\",\"state\":{\"service\":true}}","{\"command\":\"service\",\"command\":\"restart\"}","{\"command\":\" SERVICE \"}","[]"})
            {bool rejected=false;try{using var d=JsonDocument.Parse(malformed);alternate.Execute(d.RootElement);}catch(ArgumentException){rejected=true;}Check(rejected&&Read(alternate).GetRawText()==snapshot,"invalid-envelope-refuses-without-mutation-"+Passed.Count);}
            int old=I(Read(alternate),"sequence");Apply(alternate,"restart");
            Check(I(Read(alternate),"sequence")>old&&I(State(alternate),"time")==4&&I(State(alternate),"coins")==3&&State(alternate).GetProperty("receipts").GetArrayLength()==0,"explicit-ephemeral-restart-is-separate-trial-not-persistence");
            var result=new{schema_version=1,passed=Passed.Count,failed=0,controls=Passed,scope="Original finite service policy consuming selected source arithmetic. No source effect catalog/defaults, human fairness, Ruby/RMXP, Unity/Windows or persistent-world execution."};
            using(var stream=new FileStream(args[0],FileMode.CreateNew,FileAccess.Write))JsonSerializer.Serialize(stream,result,new JsonSerializerOptions{WriteIndented=true});
            Console.WriteLine("PASS: "+Passed.Count+" actual consumer controls");return 0;
        }
        catch(Exception e)when(e is ArgumentException or IOException or InvalidOperationException){Console.Error.WriteLine(e.Message);return 1;}
    }
}
