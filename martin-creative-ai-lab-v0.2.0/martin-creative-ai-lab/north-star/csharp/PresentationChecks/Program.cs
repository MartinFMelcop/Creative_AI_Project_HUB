using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using NorthStar.Presentation;
public static class Checks
{
    private static readonly List<object> observations=new();private static readonly List<object> negativePolicies=new();private static int count;
    private static Dictionary<string,object> Do(Room r,string json){using var d=JsonDocument.Parse(json);return r.Execute(d.RootElement);}
    private static void Check(bool ok,string name){count++;observations.Add(new{name,passed=ok});if(!ok)throw new Exception(name);}
    private static int I(Dictionary<string,object> s,string key)=>(int)s[key];
    public static int Main(string[] args)
    {
        try
        {
            if(args.Length!=1)throw new ArgumentException("Usage: NorthStar.PresentationChecks OUTPUT");
            foreach(string approach in new[]{"anchor","lure"})foreach(string outfit in new[]{"plate","trail"})
            {
                var r=new Room();Do(r,$"{{\"op\":\"prepare\",\"approach\":\"{approach}\",\"outfit\":\"{outfit}\"}}");var begun=Do(r,"{\"op\":\"begin\"}");
                Check((string)begun["approach"]==approach&&(string)begun["outfit"]==outfit,"Independent approach/outfit "+approach+"/"+outfit);
                var skill=Do(r,"{\"op\":\"action\",\"action\":\"skill\"}");
                Check((bool)skill["accepted"]&&(string)skill["pose"]==approach&&(string)skill["contact"]=="protected"&&I(skill,"damage")==0,"Actual bolt protection "+approach+"/"+outfit);
                Check(I(skill,"moved")== (approach=="lure"?1:0)&&I(skill,"cost")== (approach=="lure"?3:2),"Real differentiated movement/cost "+approach+"/"+outfit);
                string frozen=JsonSerializer.Serialize(r.Snapshot());Check(frozen==JsonSerializer.Serialize(r.Snapshot()),"Reads cannot advance presentation "+approach+"/"+outfit);
            }
            var room=new Room();var first=Do(room,"{\"op\":\"action\",\"action\":\"skill\"}");
            Check(!(bool)first["accepted"]&&(string)first["pose"]=="rejected"&&(string)first["contact"]=="none"&&I(first,"damage")==0,"Inactive rejected skill cannot fabricate contact");
            string unchanged=JsonSerializer.Serialize(room.Snapshot());
            foreach(string bad in new[]{"{\"op\":\"begin\",\"extra\":1}","{\"op\":\"begin\",\"op\":\"restart\"}","{\"op\":\"action\",\"action\":\"Skill\"}","{\"op\":\"prepare\",\"approach\":\"anchor\",\"outfit\":\"missing\"}","[]"})
            {bool rejected=false;try{Do(room,bad);}catch(Exception e)when(e is ArgumentException or InvalidOperationException){rejected=true;}Check(rejected&&unchanged==JsonSerializer.Serialize(room.Snapshot()),"Malformed request atomic "+bad);}
            Do(room,"{\"op\":\"begin\"}");var walk=Do(room,"{\"op\":\"action\",\"action\":\"walk\"}");Check((string)walk["contact"]=="hurt"&&I(walk,"damage")==4&&I(walk,"moved")==1,"Walk shows actual bolt damage");
            Do(room,"{\"op\":\"action\",\"action\":\"skill\"}");var dash=Do(room,"{\"op\":\"action\",\"action\":\"dash\"}");Check((string)dash["contact"]=="evaded"&&I(dash,"damage")==0&&I(dash,"moved")==2,"Actual pulse evasion");
            var win=Do(room,"{\"op\":\"action\",\"action\":\"skill\"}");Check((bool)win["won"]&&(string)win["pose"]=="won"&&(long)win["xp"]==10,"Survey reward follows actual completion");
            var refused=Do(room,"{\"op\":\"action\",\"action\":\"skill\"}");Check(!(bool)refused["accepted"]&&(string)refused["contact"]=="none"&&(long)refused["xp"]==10,"Post-encounter refusal cannot repeat reward/contact");
            long sequence=(long)refused["sequence"];var reset=Do(room,"{\"op\":\"restart\"}");Check((long)reset["sequence"]==sequence+1&&(long)reset["xp"]==0&&(string)reset["pose"]=="ready","Restart clears owner but not observation ordering");
            var scarce=new Room();Do(scarce,"{\"op\":\"begin\"}");for(int n=0;n<3;n++)Do(scarce,"{\"op\":\"action\",\"action\":\"skill\"}");var rejectedSkill=Do(scarce,"{\"op\":\"action\",\"action\":\"skill\"}");
            Check(!(bool)rejectedSkill["accepted"]&&I(rejectedSkill,"beat")==3&&(string)rejectedSkill["contact"]=="none"&&I(rejectedSkill,"cost")==0,"Scarce resolve rejects without ghost contact or beat");
            foreach(string approach in new[]{"anchor","lure"})foreach(string outfit in new[]{"plate","trail"})
            {
                var journey=new Room();Do(journey,$"{{\"op\":\"prepare\",\"approach\":\"{approach}\",\"outfit\":\"{outfit}\"}}");Do(journey,"{\"op\":\"begin\"}");
                var locked=Do(journey,"{\"op\":\"prepare\",\"approach\":\"anchor\",\"outfit\":\"plate\"}");Check(!(bool)locked["accepted"]&&(string)locked["approach"]==approach&&(string)locked["outfit"]==outfit,"Active identity preparation locked "+approach+"/"+outfit);
                string[] survey=approach=="lure"&&outfit=="plate"?new[]{"walk","skill","dash","walk"}:new[]{"walk","skill","dash","skill"};
                foreach(string action in survey)Do(journey,$"{{\"op\":\"action\",\"action\":\"{action}\"}}");
                Check((bool)journey.Snapshot()["won"]&&(long)journey.Snapshot()["xp"]==10,"Actual survey journey "+approach+"/"+outfit);
                Do(journey,"{\"op\":\"begin\"}");
                // Distinct actual budgets need distinct routes; walking recovers resolve but accepts bolt damage.
                string[] route=outfit=="plate"?new[]{"walk","skill","dash","walk","dash","skill"}:approach=="lure"?new[]{"skill","walk","dash","skill","dash","skill"}:new[]{"skill","skill","dash","skill","dash","skill"};
                foreach(string action in route)Do(journey,$"{{\"op\":\"action\",\"action\":\"{action}\"}}");
                Check((bool)journey.Snapshot()["complete"]&&(long)journey.Snapshot()["xp"]==25&&(string)journey.Snapshot()["pose"]=="won","Actual complete crossing journey "+approach+"/"+outfit);
            }
            var loss=new Room();Do(loss,"{\"op\":\"begin\"}");for(int n=0;n<4;n++)Do(loss,"{\"op\":\"action\",\"action\":\"wait\"}");
            Check(!(bool)loss.Snapshot()["won"]&&(string)loss.Snapshot()["pose"]=="lost"&&(long)loss.Snapshot()["xp"]==0,"Waiting failure cannot fabricate progress or reward");
            foreach(string phase in new[]{"survey","delivery"})
            {
                string outfit=phase=="survey"?"plate":"trail";
                string[] naive=phase=="survey"?new[]{"walk","skill","dash","skill"}:new[]{"skill","skill","dash","skill","dash","skill"};
                string[] distinct=phase=="survey"?new[]{"walk","skill","dash","walk"}:new[]{"skill","walk","dash","skill","dash","skill"};
                var trials=new List<object>();Dictionary<string,object>? negative=null,positive=null;
                foreach(bool alternative in new[]{false,true})
                {
                    var trial=new Room();Do(trial,$"{{\"op\":\"prepare\",\"approach\":\"lure\",\"outfit\":\"{outfit}\"}}");Do(trial,"{\"op\":\"begin\"}");
                    // Delivery begins only after the same actual successful survey in both rival trials.
                    if(phase=="delivery")
                    {
                        foreach(string action in new[]{"walk","skill","dash","skill"})Do(trial,$"{{\"op\":\"action\",\"action\":\"{action}\"}}");
                        Check((bool)trial.Snapshot()["won"]&&(long)trial.Snapshot()["xp"]==10,"Negative delivery trial actual survey prerequisite "+alternative);
                        Do(trial,"{\"op\":\"begin\"}");
                    }
                    var baseline=trial.Snapshot();var steps=new List<object>();string[] policy=alternative?distinct:naive;
                    foreach(string action in policy)steps.Add(Do(trial,$"{{\"op\":\"action\",\"action\":\"{action}\"}}"));
                    var final=trial.Snapshot();if(alternative)positive=final;else negative=final;
                    trials.Add(new{policy_kind=alternative?"distinct_budget_route":"naive_universal_route",policy,baseline,steps,final});
                }
                Check(negative!=null&&!(bool)negative["accepted"]&&(string)negative["pose"]=="rejected"&&(string)negative["contact"]=="none"&&I(negative,"cost")==0&&I(negative,"beat")== (phase=="survey"?3:5)&&!(bool)negative["complete"]&&(long)negative["xp"]== (phase=="survey"?0L:10L),"Retained naive "+phase+" policy exhausts actual resolve without ghost completion");
                Check(positive!=null&&(bool)positive["won"]&&(long)positive["xp"]== (phase=="survey"?10L:25L)&&(phase=="survey"|| (bool)positive["complete"]),"Distinct "+phase+" policy succeeds under identical owner rules");
                negativePolicies.Add(new{phase,approach="lure",outfit,reason="A universal protection policy exceeds this actual resolve budget; the different route accepts a real bolt hit while recovering resolve.",trials});
            }
            File.WriteAllText(args[0],JsonSerializer.Serialize(new{schema_version=1,kind="actual_csharp_crossing_presentation_checks",checks=count,observations,negative_policies=negativePolicies},Program.Json)+"\n");Console.WriteLine($"PRESENTATION_CHECKS {count} passed");return 0;
        }
        catch(Exception e){Console.Error.WriteLine(e.Message);return 1;}
    }
}
