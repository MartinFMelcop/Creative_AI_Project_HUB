using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using NorthStar.Combat;
using NorthStar.CombatStudy;

static class ForecastChecks
{
    static readonly List<string> controls=new();
    static readonly List<object> traces=new();
    static JsonElement J(object value)=>JsonSerializer.SerializeToElement(value);
    static void Check(string label,bool yes){if(!yes)throw new Exception(label);controls.Add(label);}
    static void Refuse(string label,Action action){try{action();}catch(Exception e)when(e is ArgumentException or InvalidOperationException){Check(label,true);return;}throw new Exception("Not refused: "+label);}
    static void Pair(string label,Trial live,string command)
    {
        string before=J(live.Snapshot()).GetRawText();
        var projected=J(live.Forecast(command));
        for(int n=0;n<3;n++)Check(label+" repeat "+n,J(live.Forecast(command)).GetRawText()==projected.GetRawText()&&J(live.Snapshot()).GetRawText()==before);
        Check(label+" actual action accepts",live.Execute(command));
        Check(label+" complete projection equals actual state",projected.GetProperty("state").GetRawText()==J(live.Snapshot()).GetRawText());
        traces.Add(new{label,command,before=JsonDocument.Parse(before).RootElement.Clone(),projected,actual=live.Snapshot()});
    }
    public static void Run(string? path)
    {
        bool complete=false;string? failure=null;
        try
        {
            Pair("classic cleanse",new Trial(),"cleanse");
            var refused=new Trial("heated");string before=J(refused.Snapshot()).GetRawText();
            Refuse("Disarmed forecast refuses without touching live Last",()=>refused.Forecast("strike"));
            Check("Illegal forecast leaves full live state exact",J(refused.Snapshot()).GetRawText()==before);
            refused.Execute("unknown");Pair("Prior refusal text does not corrupt reconstruction",refused,"guard");
            var response=new Trial(responses:true);var cast=J(response.Forecast("commit"));
            Check("Commit stops at pending response without assuming release",cast.GetProperty("boundary").GetString()=="response"&&cast.GetProperty("state").GetProperty("round").GetInt32()==0&&cast.GetProperty("state").GetProperty("charges").GetInt32()==1&&cast.GetProperty("state").GetProperty("enemyHp").GetInt32()==96);
            Pair("paid commit",response,"commit");before=J(response.Snapshot()).GetRawText();
            Refuse("Pending response rejects unrelated preview",()=>response.Forecast("guard"));
            Check("Pending refusal changes no live state",J(response.Snapshot()).GetRawText()==before);
            var release=J(response.Forecast("release"));var broken=J(response.Forecast("break-ward"));
            Check("Alternative responses keep distinct actual costs and effects",release.GetProperty("state").GetProperty("charges").GetInt32()==1&&broken.GetProperty("state").GetProperty("charges").GetInt32()==0&&release.GetProperty("state").GetProperty("enemyHp").GetInt32()==96&&broken.GetProperty("state").GetProperty("enemyHp").GetInt32()==48);
            Pair("actual pending break",response,"break-ward");
            var control=new Trial(controls:true);control.Execute("hard-control");control.Execute("hard-control");Pair("already exposed breakbar",control,"light-control");
            var rescued=new Trial("toxic",Passive.LastThread);
            foreach(string command in new[]{"strike","strike","strike","cleanse"})rescued.Execute(command);
            Check("Fixture reaches actual spent rescue while alive",rescued.Active&&J(rescued.Snapshot()).GetProperty("rescueSpent").GetBoolean());
            Pair("spent rescue cannot rearm",rescued,"guard");
            Check("Forecasted terminal loss is actual loss",!rescued.Active&&J(rescued.Snapshot()).GetProperty("outcome").GetString()=="defeated");
            Refuse("Ended owner cannot be forecast as fresh",()=>rescued.Forecast("guard"));
            var initiative=new Trial(initiativeMode:true,tempo:"quick",initiativeSeed:123u);initiative.Execute("guard");Pair("live seeded initiative",initiative,"strike");
            Pair("withdraw stops without another round",new Trial(),"retreat");
            var room=new Room();before=J(room.Snapshot()).GetRawText();var proposal=J(room.Forecast(J(new{command="guard"})));
            Check("Room preview preserves observation and sequence",J(room.Snapshot()).GetRawText()==before&&proposal.GetProperty("sequence").GetInt64()==0);
            var actual=J(room.Execute(J(new{command="guard",reviewed_sequence=0})));
            Check("Guarded confirmation executes exact reviewed action once",actual.GetProperty("accepted").GetBoolean()&&actual.GetProperty("sequence").GetInt64()==1&&actual.GetProperty("state").GetRawText()==proposal.GetProperty("forecast").GetProperty("state").GetRawText());
            before=J(room.Snapshot()).GetRawText();Refuse("Stale confirmation cannot replay",()=>room.Execute(J(new{command="guard",reviewed_sequence=0})));
            Check("Stale confirmation preserves entire observation",J(room.Snapshot()).GetRawText()==before);
            foreach(string invalid in new[]{"{\"command\":\"guard\",\"reviewed_sequence\":-1}","{\"command\":\"guard\",\"reviewed_sequence\":\"1\"}","{\"command\":\"guard\",\"reviewed_sequence\":1,\"extra\":0}","{\"command\":\"guard\",\"reviewed_sequence\":1,\"reviewed_sequence\":1}","{\"command\":\"restart toxic\",\"reviewed_sequence\":1}"})
            {Refuse("Malformed or lifecycle review refused "+controls.Count,()=>room.Execute(JsonDocument.Parse(invalid).RootElement));Check("Malformed review atomic "+controls.Count,J(room.Snapshot()).GetRawText()==before);}
            Refuse("Forecast rejects supplied projection field",()=>room.Forecast(J(new{command="guard",state=new{hp=100}})));
            room.Execute(J(new{command="prepare toxic"}));before=J(room.Snapshot()).GetRawText();
            Refuse("Draft preparation cannot forecast an encounter",()=>room.Forecast(J(new{command="guard"})));
            Refuse("Draft preparation cannot confirm an encounter",()=>room.Execute(J(new{command="guard",reviewed_sequence=2})));
            Check("Draft refusals preserve preparation",J(room.Snapshot()).GetRawText()==before);
            complete=true;
        }
        catch(Exception e){failure=e.Message;throw;}
        finally
        {
            if(path!=null)File.WriteAllText(Path.Combine(Path.GetDirectoryName(path)!,"forecast-native.json"),JsonSerializer.Serialize(new{complete,failure,checks=new{passed=controls.Count,failed=complete?0:1},controls,traces,scope="Actual same-owner conditional action branches; overlapping software controls, not human comprehension or balance."},new JsonSerializerOptions{WriteIndented=true})+"\n");
            Console.WriteLine("Forecast controls: "+controls.Count+"; complete: "+complete);
        }
    }
}
