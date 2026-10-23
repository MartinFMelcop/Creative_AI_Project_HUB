using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using NorthStar.AuthoredScene;

namespace NorthStar.AuthoredSceneChecks;

public static class Program
{
    private static readonly List<string> Controls=new();
    private static void Check(string name,bool condition)
    { if(!condition || Controls.Contains(name))throw new InvalidOperationException("FAIL: "+name); Controls.Add(name); }
    private static JsonElement State(Room room)=>JsonSerializer.SerializeToElement(room.Snapshot().state);
    private static Observation Command(Room room,string command)
    { using var json=JsonDocument.Parse(JsonSerializer.Serialize(new{command})); return room.Execute(json.RootElement); }
    private static void Run(Room room,params string[] commands)
    { foreach(string command in commands)if(!Command(room,command).accepted)throw new InvalidOperationException("Fixture refused: "+command); }
    private static Room Surveyed()
    { var room=new Room(); Run(room,"survey","skill","skill","walk","skill"); return room; }
    private static Room Committed()
    { var room=Surveyed(); Run(room,"open","hear","offer","terms dusk","confirm"); return room; }
    private static void Invalid(Room room,string name,string raw)
    {
        string before=JsonSerializer.Serialize(room.Snapshot());
        using var document=JsonDocument.Parse(raw);
        bool rejected=false;
        try { room.Execute(document.RootElement); } catch(ArgumentException) { rejected=true; }
        Check(name+"_rejected",rejected);
        Check(name+"_observation_unchanged",JsonSerializer.Serialize(room.Snapshot())==before);
    }
    public static int Main(string[] args)
    {
        try
        {
            if(args.Length!=1)throw new ArgumentException("Usage: NorthStar.AuthoredSceneChecks REPORT");
            var room=new Room();
            Check("initial_envelope",room.Snapshot().sequence==0 && room.Snapshot().command=="initial" && room.Snapshot().accepted);
            Check("initial_text_actual_owner",room.Snapshot().text.Contains("Edda") && room.Snapshot().text.Contains("Rill"));
            string snapshot=JsonSerializer.Serialize(room.Snapshot());
            for(int i=0;i<25;i++)room.Snapshot();
            Check("observational_reads_do_not_advance",snapshot==JsonSerializer.Serialize(room.Snapshot()));
            var invalid=new Dictionary<string,string>{["nonobject"]="[]",["missing"]="{}",["extra"]="{\"command\":\"work\",\"complete\":true}",["duplicate"]="{\"command\":\"work\",\"command\":\"work\"}",["nonstring"]="{\"command\":1}",["null"]="{\"command\":null}",["fabricated_completion"]="{\"command\":\"complete\"}",["whitespace"]="{\"command\":\" work\"}",["case"]="{\"command\":\"Work\"}",["unknown_terms"]="{\"command\":\"terms forever\"}"};
            foreach(var pair in invalid)Invalid(room,pair.Key,pair.Value);
            string state=State(room).GetRawText();
            var refused=Command(room,"confirm");
            Check("valid_refusal_is_observed",!refused.accepted && refused.sequence==1 && refused.command=="confirm" && refused.text.Contains("refused"));
            Check("valid_refusal_preserves_gameplay",State(room).GetRawText()==state);
            Run(room,"decline","work","work","work");
            Check("refusal_can_finish_local_work",State(room).GetProperty("crates").GetInt32()==5 && !State(room).GetProperty("delivered").GetBoolean());
            Check("local_path_no_fabricated_return",!State(room).GetProperty("returned").GetBoolean() && State(room).GetProperty("guide_location").GetString()=="local");
            long sequence=room.Snapshot().sequence;
            Run(room,"restart");
            Check("restart_retains_observation_order",room.Snapshot().sequence==sequence+1);
            Check("restart_fresh_ephemeral_owner",State(room).GetProperty("crates").GetInt32()==0 && State(room).GetProperty("remaining").GetInt32()==4 && State(room).GetProperty("receipts").GetArrayLength()==0);
            room=Surveyed();
            Check("survey_is_actual_encounter",State(room).GetProperty("surveyed").GetBoolean() && State(room).GetProperty("encounter").GetProperty("xp").GetInt32()==10);
            Run(room,"open","hear","offer","terms dusk");
            Check("tentative_guide_stays_local",State(room).GetProperty("guide_available").GetBoolean() && State(room).GetProperty("guide_location").GetString()=="local");
            Run(room,"work"); var stale=Command(room,"confirm");
            Check("stale_terms_refused",!stale.accepted && State(room).GetProperty("guide_available").GetBoolean());
            room=Committed();
            Check("confirmed_is_preparing_not_departed",State(room).GetProperty("guide_location").GetString()=="local-preparing" && !State(room).GetProperty("delivery_started").GetBoolean() && State(room).GetProperty("capacity").GetInt32()==1);
            Run(room,"withdraw");
            Check("withdraw_restores_local_capacity",State(room).GetProperty("capacity").GetInt32()==2 && State(room).GetProperty("guide_location").GetString()=="local");
            Check("withdraw_keeps_both_receipts",State(room).GetProperty("receipts").GetArrayLength()==2);
            room=Committed(); Run(room,"depart guided");
            Check("departure_not_handoff",State(room).GetProperty("guide_location").GetString()=="travelling" && !State(room).GetProperty("delivered").GetBoolean() && !State(room).GetProperty("returned").GetBoolean());
            Check("guided_cost_observed",State(room).GetProperty("remaining").GetInt32()==1);
            Run(room,"skill","skill","walk","skill","walk","skill","work");
            Check("guided_actual_delivery_and_return",State(room).GetProperty("delivered").GetBoolean() && State(room).GetProperty("returned").GetBoolean() && State(room).GetProperty("guide_location").GetString()=="local");
            Check("unfinished_work_not_erased",State(room).GetProperty("crates").GetInt32()==2 && State(room).GetProperty("remaining").GetInt32()==0);
            Check("actual_reward_owned_once",State(room).GetProperty("encounter").GetProperty("xp").GetInt32()==25);
            state=State(room).GetRawText(); Check("no_postdelivery_reward_farm",!Command(room,"skill").accepted && State(room).GetRawText()==state);
            room=Surveyed(); Run(room,"decline","depart solo","skill","skill","walk","skill","walk","skill");
            Check("solo_delivery_keeps_rill_local",State(room).GetProperty("delivered").GetBoolean() && State(room).GetProperty("guide_location").GetString()=="local" && State(room).GetProperty("crates").GetInt32()==0 && State(room).GetProperty("remaining").GetInt32()==0);
            room=Committed(); Run(room,"depart guided","wait","wait");
            Check("failed_guided_is_unaccounted",State(room).GetProperty("status").GetString()=="failed" && State(room).GetProperty("guide_location").GetString()=="unaccounted" && !State(room).GetProperty("delivered").GetBoolean() && !State(room).GetProperty("returned").GetBoolean());
            Check("failure_text_no_confirmed_death",room.Snapshot().text.Contains("not a confirmed death or return"));
            room=Committed(); Run(room,"work","work","work");
            Check("deadline_is_not_return",State(room).GetProperty("due_elapsed").GetBoolean() && !State(room).GetProperty("returned").GetBoolean() && !State(room).GetProperty("delivered").GetBoolean() && State(room).GetProperty("guide_location").GetString()=="local-preparing");
            var report=new{schema_version=1,checks=new{passed=Controls.Count,failed=0},controls=Controls,scope="Actual Room and unchanged RequestExpedition; not HTTP/browser, Unity/Windows, human comprehension or persistence"};
            File.WriteAllText(args[0],JsonSerializer.Serialize(report,new JsonSerializerOptions{WriteIndented=true})+"\n");
            Console.WriteLine("PASS: "+Controls.Count+" authored scene native controls."); return 0;
        }
        catch(Exception error) { Console.Error.WriteLine(error.Message); return 1; }
    }
}
