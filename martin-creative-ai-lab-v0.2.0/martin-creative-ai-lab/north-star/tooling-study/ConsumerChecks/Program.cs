using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using NorthStar.ToolingStudy;

static class Checks
{
    static readonly List<string> Controls=new();
    static void Check(bool ok,string id){if(!ok)throw new InvalidOperationException(id);Controls.Add(id);}
    static JsonElement Read(Room r)=>JsonSerializer.SerializeToElement(r.Snapshot());
    static JsonElement State(Room r)=>Read(r).GetProperty("state");
    static int Stock(Room r,string item)=>State(r).GetProperty("inventory").GetProperty(item).GetInt32();
    static JsonElement Encounter(Room r)=>State(r).GetProperty("encounter");
    static bool B(JsonElement value,string key)=>value.GetProperty(key).GetBoolean();
    static int I(JsonElement value,string key)=>value.GetProperty(key).GetInt32();
    static bool Act(Room r,string command)
    {using var d=JsonDocument.Parse(JsonSerializer.Serialize(new{command}));return B(JsonSerializer.SerializeToElement(r.Execute(d.RootElement)),"accepted");}
    static void Refuse(Room r,string command,string id){string before=State(r).GetRawText();Check(!Act(r,command)&&State(r).GetRawText()==before,id);}
    static void Policy(Room r,params string[] commands){foreach(var c in commands)if(!Act(r,c))throw new InvalidOperationException("Actual policy refused:"+c);}
    static int Main(string[] args)
    {
        try
        {
            if(args.Length!=1)throw new ArgumentException("Usage: ConsumerChecks FRESH_OUTPUT_JSON");
            var r=new Room();
            Check(Stock(r,"fiber")==4&&Stock(r,"binder")==2&&Stock(r,"gauge")==1&&Stock(r,"trail_rig")==0,"explicit-finite-stock-with-actual-owned-gauge");
            Check(Encounter(r).ValueKind==JsonValueKind.Null,"no-child-encounter-before-actual-entry");
            Refuse(r,"enter","uncrafted-materials-and-tool-cannot-enter");Refuse(r,"skill","action-name-does-not-start-an-encounter");
            Check(Act(r,"craft")&&Stock(r,"fiber")==2&&Stock(r,"binder")==1&&Stock(r,"trail_rig")==1&&Stock(r,"gauge")==1,"first-atomic-production-spends-only-ingredients");
            Check(Act(r,"craft")&&Stock(r,"fiber")==0&&Stock(r,"binder")==0&&Stock(r,"trail_rig")==2&&Stock(r,"gauge")==1,"second-production-retains-the-same-single-tool");
            Refuse(r,"craft","retained-tool-alone-cannot-manufacture-more-material");
            Check(I(State(r),"transactions")==2,"only-two-crafts-committed");
            string idle=State(r).GetRawText();Check(Enumerable.Range(0,5).All(_=>State(r).GetRawText()==idle),"observation-cannot-craft-consume-or-enter");
            Check(Act(r,"enter")&&Stock(r,"trail_rig")==1&&Stock(r,"gauge")==1&&I(State(r),"consumed_rigs")==1&&B(Encounter(r),"active"),"real-first-entry-consumes-output-not-tool");
            Refuse(r,"enter","repeat-active-entry-cannot-double-consume");Refuse(r,"craft","active-encounter-cannot-use-the-bench");
            Policy(r,"skill","skill","walk","skill");
            Check(!B(Encounter(r),"active")&&B(Encounter(r),"won")&&!B(Encounter(r),"complete"),"actual-survey-victory-is-not-final-completion");
            Refuse(r,"walk","finished-survey-does-not-accept-next-encounter-action");
            Check(Act(r,"enter")&&Stock(r,"trail_rig")==0&&Stock(r,"gauge")==1&&I(State(r),"attempts")==2,"explicit-second-entry-consumes-second-produced-rig");
            Policy(r,"skill","skill","walk","skill","walk","skill");
            Check(B(Encounter(r),"complete")&&B(Encounter(r),"won")&&!B(Encounter(r),"active")&&Stock(r,"gauge")==1,"actual-final-crossing-completes-with-retained-gauge");
            Check(I(State(r),"transactions")==4&&I(State(r),"consumed_rigs")==2,"two-productions-and-two-actual-output-consumptions");
            Refuse(r,"enter","completed-journey-cannot-enter-or-consume-again");Refuse(r,"craft","completed-journey-cannot-refund-by-crafting");
            var missing=new Room();Act(missing,"restart missing");
            Check(Stock(missing,"gauge")==0&&Stock(missing,"fiber")==4&&Encounter(missing).ValueKind==JsonValueKind.Null,"missing-tool-preset-is-an-explicit-fresh-trial");
            Refuse(missing,"craft","missing-tool-refuses-without-spending-materials");
            Check(I(State(missing),"transactions")==0&&Stock(missing,"trail_rig")==0,"missing-tool-refusal-does-not-commit-or-grant-output");
            var losing=new Room();Policy(losing,"craft","enter","wait","wait","wait");
            Check(!B(Encounter(losing),"active")&&!B(Encounter(losing),"won")&&!B(Encounter(losing),"complete")&&Stock(losing,"trail_rig")==0&&Stock(losing,"fiber")==2&&Stock(losing,"binder")==1&&Stock(losing,"gauge")==1,"actual-loss-retains-tool-but-never-refunds-used-rig-or-ingredients");
            Refuse(losing,"enter","loss-cannot-reenter-with-promised-rig");
            Check(Act(losing,"craft")&&Stock(losing,"fiber")==0&&Stock(losing,"binder")==0&&Stock(losing,"gauge")==1,"remaining-finite-materials-allow-only-one-real-replacement");
            Policy(losing,"enter","skill","skill","walk","skill");
            Check(B(Encounter(losing),"won")&&!B(Encounter(losing),"complete")&&Stock(losing,"trail_rig")==0,"replacement-can-win-survey-with-final-stage-still-unfunded");
            Refuse(losing,"enter","spent-supplies-cannot-supply-final-journey");Refuse(losing,"craft","finite-loss-remains-consequential-with-tool-still-owned");
            string snapshot=Read(r).GetRawText();
            foreach(string text in new[]{"{}","[]","{\"command\":\"craft\",\"gauge\":1}","{\"command\":\"craft\",\"command\":\"enter\"}","{\"command\":\"grant gauge\"}"})
            {bool rejected=false;try{using var d=JsonDocument.Parse(text);r.Execute(d.RootElement);}catch(ArgumentException){rejected=true;}Check(rejected&&Read(r).GetRawText()==snapshot,"invalid-or-fabricated-input-refuses-"+Controls.Count);}
            int before=I(Read(r),"sequence");Act(r,"restart equipped");Check(I(Read(r),"sequence")>before&&Stock(r,"fiber")==4&&I(State(r),"transactions")==0&&Encounter(r).ValueKind==JsonValueKind.Null,"explicit-restart-is-separate-trial-not-world-refund");
            using(var f=new FileStream(args[0],FileMode.CreateNew,FileAccess.Write))JsonSerializer.Serialize(f,new{schema_version=1,passed=Controls.Count,failed=0,controls=Controls,scope="Actual new tool wrapper and unchanged inventory/Crossing composition. No old source matrix, historical item effects, Unity/Windows/Steam, save or human validation."},new JsonSerializerOptions{WriteIndented=true});
            Console.WriteLine("PASS:"+Controls.Count+" actual tooling consumer controls");return 0;
        }
        catch(Exception e)when(e is ArgumentException or IOException or InvalidOperationException){Console.Error.WriteLine(e.Message);return 1;}
    }
}
