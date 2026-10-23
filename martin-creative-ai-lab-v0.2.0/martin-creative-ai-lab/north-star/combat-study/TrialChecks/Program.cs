using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using NorthStar.CombatStudy;

static class TrialChecks
{
    static readonly List<object> controls=new();
    static readonly List<object> journeys=new();
    static void Check(string id,bool passed,object? evidence=null){controls.Add(new {id,passed,evidence});if(!passed)throw new Exception("FAILED "+id);Console.WriteLine("PASS "+id);}
    static JsonElement View(Room room)=>JsonSerializer.SerializeToElement(room.Snapshot());
    static JsonElement Act(Room room,string command){using var d=JsonDocument.Parse(JsonSerializer.Serialize(new {command}));return JsonSerializer.SerializeToElement(room.Execute(d.RootElement));}
    static void Schema()
    {
        var room=new Room();string before=View(room).GetRawText();
        for(int i=0;i<10;i++)View(room);
        Check("observation-is-not-action",View(room).GetRawText()==before);
        string[] invalid={"null","[]","{}","{\"command\":1}","{\"command\":\"unknown\"}","{\"command\":\"strike\",\"extra\":1}","{\"command\":\"strike\",\"command\":\"guard\"}"};
        for(int i=0;i<invalid.Length;i++){bool rejected=false;try{using var d=JsonDocument.Parse(invalid[i]);room.Execute(d.RootElement);}catch(ArgumentException){rejected=true;}Check("schema-reject-atomic-"+i,rejected&&View(room).GetRawText()==before,new {input=invalid[i]});}
    }
    static int Main(string[] args)
    {
        string? path=args.Length==1?args[0]:null;bool passed=false;string? failure=null;
        try{if(args.Length>1)throw new ArgumentException("Optional output JSON path only");Schema();Journeys();passed=true;return 0;}
        catch(Exception e){failure=e.Message;Console.Error.WriteLine(failure);return 1;}
        finally{if(path!=null)File.WriteAllText(path,JsonSerializer.Serialize(new {passed,failure,controls,journeys},new JsonSerializerOptions{WriteIndented=true}));Console.WriteLine($"{controls.Count} consumer controls; passed: {passed}");}
    }
    static JsonElement S(JsonElement o)=>o.GetProperty("state");
    static int N(JsonElement s,string k)=>s.GetProperty(k).GetInt32();
    static string T(JsonElement s,string k)=>s.GetProperty(k).GetString()!;
    static string Game(JsonElement s)=>JsonSerializer.Serialize(new {round=N(s,"round"),hp=N(s,"hp"),enemy=N(s,"enemyHp"),charges=N(s,"charges"),effects=s.GetProperty("effects"),outcome=T(s,"outcome")});
    static JsonElement Journey(string id,string profile,params string[] commands){var room=new Room();var views=new List<JsonElement>{Act(room,"restart "+profile)};foreach(string command in commands){var view=Act(room,command);Check(id+"-accepted-"+views.Count,view.GetProperty("accepted").GetBoolean());views.Add(view);}journeys.Add(new {id,profile,commands,observations=views});return S(views[^1]);}
    static void Journeys(){
      var toxic=Journey("toxic-win","toxic","strike","strike","strike","strike");Check("toxic-real-victory",T(toxic,"outcome")=="secured"&&N(toxic,"hp")==7&&N(toxic,"enemyHp")==0,toxic);
      var heated=Journey("heated-win","heated","cleanse","strike","guard","strike","strike","treat","strike");Check("heated-real-victory",T(heated,"outcome")=="secured"&&N(heated,"hp")==10&&N(heated,"enemyHp")==0&&N(heated,"charges")==0,heated);
      var mistimed=Journey("heated-mistimed-treatment-negative","heated","cleanse","strike","treat","strike","strike","strike");Check("mistimed-treatment-does-not-secure",T(mistimed,"outcome")=="defeated"&&N(mistimed,"hp")==0&&N(mistimed,"enemyHp")==7,mistimed);
      foreach(string profile in new[]{"toxic","heated"}){var room=new Room();Act(room,"restart "+profile);var views=new List<JsonElement>();for(int i=0;i<12&&T(S(View(room)),"outcome")=="active";i++)views.Add(Act(room,"guard"));var end=S(View(room));Check(profile+"-constant-guard-defeated",T(end,"outcome")=="defeated"&&N(end,"hp")==0,end);journeys.Add(new {id=profile+"-guard-loss",observations=views});}
      var guard=Journey("guard-observation","toxic","guard");var attack=Journey("strike-observation","toxic","strike");Check("guard-halves-contact-leaves-full-dot",N(guard,"hp")==81&&N(attack,"hp")==71&&guard.GetProperty("events").GetRawText().Contains("Poison incoming DOT 6; actual HP lost 6")&&guard.GetProperty("events").GetRawText().Contains("Bleed incoming DOT 3; actual HP lost 3"),new {guard,attack});
      var clean=Journey("cleanse-cost","toxic","cleanse");Check("cleanse-charge-and-opportunity",N(clean,"charges")==1&&N(clean,"enemyHp")==96&&N(clean,"hp")==80&&clean.GetProperty("effects").GetArrayLength()==0,clean);
      var heal=Journey("bleed-treatment","toxic","strike","treat");Check("bleed-real-healing",N(heal,"hp")==64&&N(heal,"charges")==1&&heal.GetProperty("events").GetRawText().Contains("eligible 22"),heal);
      var hot=new Room();Act(hot,"restart heated");var initial=S(View(hot));var refused=Act(hot,"strike");Check("disarm-refusal-atomic",!refused.GetProperty("accepted").GetBoolean()&&Game(S(refused))==Game(initial),refused);var bash=S(Act(hot,"bash"));Check("disarm-bash-and-burn",N(bash,"enemyHp")==86&&N(bash,"hp")==77&&N(bash,"round")==1,bash);var second=S(Act(hot,"guard"));Check("disarm-global-expiry",second.GetProperty("weaponEnabled").GetBoolean()&&N(second,"round")==2,second);var burn=S(Act(hot,"strike"));Check("burn-real-strike",N(burn,"enemyHp")==69&&burn.GetProperty("events").GetRawText().Contains("strike: 17 direct"),burn);
      var withdrawal=new Room();var ret=Act(withdrawal,"retreat");Check("withdrawal-no-fabricated-win",T(S(ret),"outcome")=="withdrawn"&&N(S(ret),"round")==0&&N(S(ret),"hp")==100,ret);var post=Act(withdrawal,"strike");Check("terminal-refusal-atomic",!post.GetProperty("accepted").GetBoolean()&&Game(S(ret))==Game(S(post)),post);var restart=Act(withdrawal,"restart heated");Check("explicit-restart",T(S(restart),"profile")=="heated"&&N(S(restart),"round")==0&&N(S(restart),"hp")==100&&N(S(restart),"charges")==2,restart);
      var depleted=new Room();Act(depleted,"strike");Act(depleted,"treat");Act(depleted,"treat");var old=S(View(depleted));var no=Act(depleted,"treat");Check("exhausted-treatment-atomic",!no.GetProperty("accepted").GetBoolean()&&Game(S(no))==Game(old),no);
    }
}
