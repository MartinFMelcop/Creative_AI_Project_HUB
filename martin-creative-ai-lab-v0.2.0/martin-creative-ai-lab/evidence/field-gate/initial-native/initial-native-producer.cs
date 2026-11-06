using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using NorthStar.FieldJourney;
using Gate=NorthStar.FieldGate.Gate;

static class Program
{
    static readonly List<string> controls=new();
    static void Check(string id,bool ok){if(!ok)throw new Exception(id);if(controls.Contains(id))throw new Exception("Unique controls required");controls.Add(id);}
    static JsonElement Json(object v)=>JsonSerializer.SerializeToElement(v);
    static JsonElement View(Room r)=>Json(r.Snapshot());
    static JsonElement State(Room r)=>View(r).GetProperty("intake").GetProperty("state");
    static JsonElement G(Gate g)=>Json(g.Snapshot());
    static bool B(JsonElement e,string k)=>e.GetProperty(k).GetBoolean();
    static int N(JsonElement e,string k)=>e.GetProperty(k).GetInt32();
    static JsonElement Send(Room r,string cmd,object? extra=null)
    {var d=new Dictionary<string,object?>{{"command",cmd},{"revision",N(View(r),"sequence")}};if(extra!=null)foreach(var p in Json(extra).EnumerateObject())d.Add(p.Name,p.Value);return Json(r.Execute(Json(d)));}
    static void Do(Room r,string cmd,object? extra=null){if(!B(Send(r,cmd,extra),"accepted"))throw new Exception("Actual action refused: "+cmd);}
    static void Act(Gate g,string cmd,string? target=null){if(!g.Execute(cmd,target,out _))throw new Exception("Gate action refused: "+cmd);}
    static string History(Room r){var v=View(r);return Json(new{intake=v.GetProperty("intake"),memory=v.GetProperty("memory"),fittings=v.GetProperty("fittings"),assembly=v.GetProperty("assembly_receipts"),sample=v.GetProperty("sample_case"),book=v.GetProperty("preparation_book"),encounter=v.GetProperty("encounter_view")}).GetRawText();}
    static Room Prepare()
    {
        var r=new Room();Do(r,"draft",new{handle="Neri",accent="teal",class_id="lure",background_id="trailborn",slots=new string?[]{"draw",null,null,null}});Do(r,"review");Do(r,"confirm",new{draft_revision=N(View(r).GetProperty("intake"),"draft_revision")});
        foreach(string bench in new[]{"west","east"}){Do(r,"help",new{bench});Do(r,"serve",new{bench});Do(r,"craft",new{bench,rig="trail"});}
        Do(r,"begin",new{rig="trail"});return r;
    }
    static void Survey(Room r){foreach(string c in new[]{"slot","slot","walk","slot"})Do(r,c,c=="slot"?new{slot=1}:null);}
    static Room Complete()
    {
        var r=Prepare();Survey(r);Do(r,"allocate",new{axis="focus",points=2});Do(r,"begin",new{rig="trail"});foreach(string c in new[]{"slot","slot","walk","slot","walk","slot"})Do(r,c,c=="slot"?new{slot=1}:null);return r;
    }
    static readonly (string cmd,string? target)[] Direct={ ("gate-move","left"),("gate-work",null),("gate-work",null),("gate-move","right"),("gate-work",null),("gate-work",null),("gate-work",null),("gate-move","exit"),("gate-exit",null)};
    static readonly (string cmd,string? target)[] Grounded={ ("gate-ground",null),("gate-move","left"),("gate-work",null),("gate-work",null),("gate-move","right"),("gate-work",null),("gate-work",null),("gate-move","exit"),("gate-exit",null)};
    static void Route(Gate g,IEnumerable<(string cmd,string? target)> actions){foreach(var a in actions)Act(g,a.cmd,a.target);}
    static void Reject(Action a,string label){bool caught=false;try{a();}catch(ArgumentException){caught=true;}Check(label,caught);}
    static void Main(string[] args)
    {
        if(args.Length!=1)throw new ArgumentException("Output JSON required");
        var early=new Room();string before=History(early);Check("Unconfirmed gate entry refuses without child mutation",!B(Send(early,"gate-enter"),"accepted")&&History(early)==before);
        var survey=Prepare();Survey(survey);before=History(survey);Check("Actual survey victory is not final gate eligibility",!B(Send(survey,"gate-enter"),"accepted")&&History(survey)==before&&!B(State(survey),"complete"));
        var withdrawn=Prepare();Do(withdrawn,"withdraw");before=History(withdrawn);Check("Actual withdrawn journey cannot enter gate",!B(Send(withdrawn,"gate-enter"),"accepted")&&History(withdrawn)==before);
        var lost=Prepare();for(int i=0;i<4&&B(State(lost),"active");i++)Do(lost,"wait");before=History(lost);Check("Actual failed journey cannot enter gate",!B(Send(lost,"gate-enter"),"accepted")&&History(lost)==before);
        var r=Complete();Check("Actual final road supplies original costs and earned progress",B(State(r),"complete")&&N(State(r),"xp")==25&&N(State(r),"health")==11&&N(State(r),"resolve")==7&&N(State(r),"consumed_rigs")==2);
        before=View(r).GetRawText();Reject(()=>r.Execute(Json(new{command="gate-enter",revision=N(View(r),"sequence"),health=100})),"Forged gate HP field rejected before entry");Check("Malformed entry preserves entire current snapshot",View(r).GetRawText()==before);
        string frozen=History(r);Do(r,"gate-enter");Check("Explicit entry transfers actual remaining health resolve and identity",N(View(r).GetProperty("gate"),"health")==11&&N(View(r).GetProperty("gate"),"resolve")==7&&View(r).GetProperty("gate").GetProperty("entry").GetProperty("handle").GetString()=="Neri"&&History(r)==frozen);
        foreach(string cmd in new[]{"allocate","propose-card","begin","walk","withdraw"}){object? extra=cmd=="allocate"?new{axis="focus",points=1}:cmd=="propose-card"?new{card_id="lure-dash"}:cmd=="begin"?new{rig="trail"}:null;Check("Post-entry child mutation refused: "+cmd,!B(Send(r,cmd,extra),"accepted")&&History(r)==frozen);}
        var state=View(r);int old=N(state,"sequence")-1;string gateBefore=state.GetProperty("gate").GetRawText();Check("Old outer intent cannot pay a gate beat",!B(Json(r.Execute(Json(new{command="gate-wait",revision=old}))),"accepted")&&View(r).GetProperty("gate").GetRawText()==gateBefore&&History(r)==frozen);
        foreach(var a in Direct){Do(r,a.cmd,a.target==null?null:new{target=a.target});Check("Historical children exact after paid gate action "+N(View(r).GetProperty("gate"),"beat"),History(r)==frozen);}
        var direct=View(r).GetProperty("gate");Check("Actual integrated direct policy opens only after living exit",B(direct,"completed")&&!B(direct,"failed")&&N(direct,"health")==5&&N(direct,"resolve")==7&&N(direct,"integrity")==1&&N(direct,"beat")==9);
        gateBefore=direct.GetRawText();Check("Completed gate refuses another beat or retry",!B(Send(r,"gate-wait"),"accepted")&&!B(Send(r,"gate-enter"),"accepted")&&View(r).GetProperty("gate").GetRawText()==gateBefore&&History(r)==frozen);
        var groundedRoom=Complete();string groundedHistory=History(groundedRoom);Do(groundedRoom,"gate-enter");foreach(var a in Grounded)Do(groundedRoom,a.cmd,a.target==null?null:new{target=a.target});var grounded=View(groundedRoom).GetProperty("gate");Check("Actual integrated grounding trades resolve and integrity for less health loss",B(grounded,"completed")&&N(grounded,"health")==9&&N(grounded,"resolve")==5&&N(grounded,"integrity")==2&&History(groundedRoom)==groundedHistory);
        var unit=new Gate(11,7,"Neri","teal","lure","trail");Act(unit,"gate-ground");Check("Grounding pays before quiet future without supplying catches or exit",B(G(unit),"grounded")&&!B(G(unit),"completed")&&!B(G(unit),"left_raised")&&N(G(unit),"health")==9&&N(G(unit),"integrity")==2);
        Act(unit,"gate-move","left");Act(unit,"gate-work");Check("One work beat is not catch completion",N(G(unit),"progress")==1&&!B(G(unit),"left_raised"));Act(unit,"gate-wait");Check("Release resets partial paid work",N(G(unit),"progress")==0);Act(unit,"gate-work");Act(unit,"gate-move","right");Check("Movement resets partial paid work",N(G(unit),"progress")==0&&!B(G(unit),"left_raised"));
        var directUnit=new Gate(11,7,"Neri","teal","lure","trail");Route(directUnit,Direct.Take(4));Act(directUnit,"gate-work");Check("Announced player contact interrupts catch before progress",N(G(directUnit),"progress")==0&&N(G(directUnit),"health")==7&&!B(G(directUnit),"right_raised"));
        var closed=new Gate(11,0,"Neri","teal","lure","trail");gateBefore=G(closed).GetRawText();Check("Closed exit and insufficient resolve refuse atomically",!closed.Execute("gate-move","exit",out _)&&!closed.Execute("gate-brace",null,out _)&&!closed.Execute("gate-ground",null,out _)&&G(closed).GetRawText()==gateBefore);Reject(()=>closed.Execute("gate-move","LEFT",out _),"Unknown location is not normalized");
        var brace=new Gate(11,1,"Neri","teal","lure","trail");Act(brace,"gate-brace");Check("Brace pays one resolve for current threat only",N(G(brace),"health")==11&&N(G(brace),"resolve")==0&&N(G(brace),"beat")==1);
        var lowHealth=new Gate(1,2,"Fixture","teal","lure","trail");Act(lowHealth,"gate-ground");Check("Declared low-health grounding fixture fails before shutdown application",B(G(lowHealth),"failed")&&!B(G(lowHealth),"grounded")&&N(G(lowHealth),"resolve")==0&&N(G(lowHealth),"integrity")==2);
        var lowExit=new Gate(7,7,"Fixture","teal","lure","trail");Route(lowExit,Direct);Check("Declared low-health exit fixture loses before passage completion",B(G(lowExit),"failed")&&!B(G(lowExit),"completed")&&G(lowExit).GetProperty("position").GetString()=="exit");
        var brokenWork=new Gate(100,0,"Fixture","teal","anchor","plate");for(int i=0;i<8;i++)Act(brokenWork,"gate-wait");Act(brokenWork,"gate-move","left");Act(brokenWork,"gate-work");Act(brokenWork,"gate-work");Check("Declared mechanism fixture breaks before second work can raise catch",B(G(brokenWork),"failed")&&!B(G(brokenWork),"left_raised")&&N(G(brokenWork),"progress")==0);
        var brokenGround=new Gate(100,2,"Fixture","teal","anchor","plate");for(int i=0;i<6;i++)Act(brokenGround,"gate-wait");Act(brokenGround,"gate-ground");Check("Declared mechanism fixture pays grounding but breaks before shutdown",B(G(brokenGround),"failed")&&!B(G(brokenGround),"grounded")&&N(G(brokenGround),"resolve")==0);
        var idle=new Gate(11,7,"Neri","teal","lure","trail");for(int i=0;i<20&&idle.Active;i++)Act(idle,"gate-wait");Check("Actual bounded inaction policy loses without invented passage",B(G(idle),"failed")&&!B(G(idle),"completed"));
        var replay=new Gate(11,7,"Neri","teal","lure","trail");Route(replay,Direct);Check("Accepted direct transitions replay deterministically",G(replay).GetRawText()==direct.GetRawText());before=G(replay).GetRawText();for(int i=0;i<100;i++)G(replay);Check("Reads and elapsed observation cannot advance terminal gate",G(replay).GetRawText()==before);
        File.WriteAllText(args[0],JsonSerializer.Serialize(new{schema_version=1,checks=controls,actual_direct=View(r),actual_grounded=View(groundedRoom),inaction=G(idle),fixtures=new{ground_death=G(lowHealth),exit_death=G(lowExit),work_break=G(brokenWork),ground_break=G(brokenGround)},limits="Actual software controls overlap outcomes, not participants, balance or Unity/Windows/Steam validation. Low-health/mechanism units are declared synthetic fixtures, separate from actual complete Field entry routes. Continuous source timing and retry are not reproduced."},new JsonSerializerOptions{WriteIndented=true})+"\n");Console.WriteLine("PASS: "+controls.Count+" actual gate native controls");
    }
}
