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
    static Room Prepare(string finalRig="trail")
    {
        var r=new Room();Do(r,"draft",new{handle="Neri",accent="teal",class_id="lure",background_id="trailborn",slots=new string?[]{"draw",null,null,null}});Do(r,"review");Do(r,"confirm",new{draft_revision=N(View(r).GetProperty("intake"),"draft_revision")});
        foreach(string bench in new[]{"west","east"}){Do(r,"help",new{bench});Do(r,"serve",new{bench});Do(r,"craft",new{bench,rig=bench=="east"?finalRig:"trail"});}
        Do(r,"begin",new{rig="trail"});return r;
    }
    static void Survey(Room r){foreach(string c in new[]{"slot","slot","walk","slot"})Do(r,c,c=="slot"?new{slot=1}:null);}
    static Room Complete(string finalRig="trail")
    {
        var r=Prepare(finalRig);Survey(r);Do(r,"allocate",new{axis="focus",points=2});Do(r,"begin",new{rig=finalRig});foreach(string c in new[]{"slot","slot","walk","slot","walk","slot"})Do(r,c,c=="slot"?new{slot=1}:null);return r;
    }
    static readonly (string cmd,string? target)[] Direct={ ("gate-move","left"),("gate-work",null),("gate-work",null),("gate-move","right"),("gate-work",null),("gate-work",null),("gate-work",null),("gate-move","exit"),("gate-exit",null)};
    static readonly (string cmd,string? target)[] Grounded={ ("gate-ground",null),("gate-move","left"),("gate-work",null),("gate-work",null),("gate-move","right"),("gate-work",null),("gate-work",null),("gate-move","exit"),("gate-exit",null)};
    static void Route(Gate g,IEnumerable<(string cmd,string? target)> actions){foreach(var a in actions)Act(g,a.cmd,a.target);}
    static void Reject(Action a,string label){bool caught=false;try{a();}catch(ArgumentException){caught=true;}Check(label,caught);}
    static JsonElement Assist(JsonElement gate)=>gate.GetProperty("assist");
    static JsonElement GateView(Room room)=>View(room).GetProperty("gate");
    static void RoomRoute(Room room,IEnumerable<(string cmd,string? target)> actions)
    {foreach(var a in actions)Do(room,a.cmd,a.target==null?null:new{target=a.target});}
    static object EquipmentControls()
    {
        var early=new Room();string history=History(early);
        Check("Assist before actual gate entry refuses without touching earlier children",!B(Send(early,"gate-assist"),"accepted")&&History(early)==history);
        var plate=Complete("plate");var plateControl=Complete("plate");
        Check("Actual crafted final Plate enters from earned journey at HP15 resolve3",N(State(plate),"health")==15&&N(State(plate),"resolve")==3&&State(plate).GetProperty("rig").GetString()=="Plate"&&N(State(plate),"consumed_rigs")==2);
        Do(plate,"gate-enter");Do(plateControl,"gate-enter");string plateHistory=History(plate);RoomRoute(plate,Direct.Take(4));RoomRoute(plateControl,Direct.Take(4));
        var plateBefore=GateView(plate);Check("Matched real Plate policies have identical facts before the chosen work beat",plateBefore.GetRawText()==GateView(plateControl).GetRawText()&&B(Assist(plateBefore),"eligible")&&Assist(plateBefore).GetProperty("protects").GetString()=="player");
        string full=View(plate).GetRawText();
        Reject(()=>plate.Execute(Json(new{command="gate-assist",revision=N(View(plate),"sequence"),rig="trail"})),"Client cannot forge the worn rig through an assist field");
        Check("Forged assist rig preserves the complete current observation",View(plate).GetRawText()==full);
        Reject(()=>plate.Execute(Json(new{command="gate-assist",revision=N(View(plate),"sequence"),used=false})),"Client cannot rearm assist with a used field");
        Check("Forged assist use flag preserves the complete current observation",View(plate).GetRawText()==full);
        Check("Stale assist cannot pay or consume the actual one-use owner",!B(Json(plate.Execute(Json(new{command="gate-assist",revision=N(View(plate),"sequence")-1}))),"accepted")&&GateView(plate).GetRawText()==plateBefore.GetRawText()&&History(plate)==plateHistory);
        Do(plate,"gate-assist");Do(plateControl,"gate-work");var plateAfter=GateView(plate);var controlAfter=GateView(plateControl);
        Check("Actual Plate assist pays one resolve and beat while blocking only player contact",N(plateAfter,"resolve")==N(plateBefore,"resolve")-1&&N(plateAfter,"beat")==N(plateBefore,"beat")+1&&N(plateAfter,"health")==N(plateBefore,"health")&&N(plateAfter,"integrity")==N(plateBefore,"integrity")&&B(Assist(plateAfter),"used")&&!B(Assist(plateAfter),"eligible")&&Assist(plateAfter).GetProperty("last_blocked").GetString()=="player"&&History(plate)==plateHistory);
        Check("Matched ordinary work takes actual contact and loses progress",N(controlAfter,"health")==N(plateBefore,"health")-2&&N(controlAfter,"progress")==0&&N(plateAfter,"progress")==1&&!B(plateAfter,"right_raised"));
        Do(plate,"gate-work");Do(plateControl,"gate-work");Check("Protected work changes a real later catch and exit permission",B(GateView(plate),"right_raised")&&!B(GateView(plateControl),"right_raised"));
        string controlBeforeExit=GateView(plateControl).GetRawText();Check("Matched unassisted policy cannot leave with its unfinished catch",!B(Send(plateControl,"gate-move",new{target="exit"}),"accepted")&&GateView(plateControl).GetRawText()==controlBeforeExit);
        Do(plate,"gate-move",new{target="exit"});Do(plate,"gate-exit");var plateFinal=GateView(plate);
        Check("Actual assisted Plate route exits alive without healing or another item",B(plateFinal,"completed")&&!B(plateFinal,"failed")&&N(plateFinal,"health")==13&&N(plateFinal,"resolve")==2&&N(plateFinal,"integrity")==1&&N(plateFinal,"beat")==8&&History(plate)==plateHistory);
        Do(plateControl,"gate-work");Do(plateControl,"gate-move",new{target="exit"});Do(plateControl,"gate-exit");
        Check("Actual unassisted Plate policy remains a distinct paid survivor",B(GateView(plateControl),"completed")&&N(GateView(plateControl),"health")==9&&N(GateView(plateControl),"resolve")==3&&N(GateView(plateControl),"beat")==9);
        string terminal=GateView(plate).GetRawText();Check("Completed real assist cannot be rearmed by replay or reentry",!B(Send(plate,"gate-assist"),"accepted")&&!B(Send(plate,"gate-enter"),"accepted")&&GateView(plate).GetRawText()==terminal&&History(plate)==plateHistory);

        var trail=Complete();var trailControl=Complete();Do(trail,"gate-enter");Do(trailControl,"gate-enter");string trailHistory=History(trail);RoomRoute(trail,Direct.Take(2));RoomRoute(trailControl,Direct.Take(2));var trailBefore=GateView(trail);
        Check("Matched actual Trail policies expose the same winch threat and paid partial work",trailBefore.GetRawText()==GateView(trailControl).GetRawText()&&N(trailBefore,"progress")==1&&trailBefore.GetProperty("next_threat").GetString()=="winch"&&Assist(trailBefore).GetProperty("protects").GetString()=="winch");
        Do(trail,"gate-assist");Do(trailControl,"gate-work");var trailAfter=GateView(trail);
        Check("Actual Trail assist preserves partial work and pays to prevent one winch loss",N(trailAfter,"integrity")==3&&N(GateView(trailControl),"integrity")==2&&N(trailAfter,"resolve")==6&&N(trailAfter,"beat")==3&&B(trailAfter,"left_raised")&&N(trailAfter,"health")==9&&Assist(trailAfter).GetProperty("last_blocked").GetString()=="winch"&&History(trail)==trailHistory);
        string spent=trailAfter.GetRawText();Check("Actual spent assist refuses another use without another beat or child mutation",!B(Send(trail,"gate-assist"),"accepted")&&GateView(trail).GetRawText()==spent&&History(trail)==trailHistory);
        RoomRoute(trail,Direct.Skip(3));RoomRoute(trailControl,Direct.Skip(3));var trailFinal=GateView(trail);
        Check("Actual Trail route retains one integrity at one resolve cost with unchanged exit timing",B(trailFinal,"completed")&&B(GateView(trailControl),"completed")&&N(trailFinal,"health")==5&&N(trailFinal,"resolve")==6&&N(trailFinal,"integrity")==2&&N(trailFinal,"beat")==9&&N(GateView(trailControl),"integrity")==1&&History(trail)==trailHistory);

        var quiet=new Gate(11,2,"Fixture","teal","anchor","plate");Act(quiet,"gate-move","left");Act(quiet,"gate-assist");
        Check("Quiet use deliberately wastes the finite opportunity but still performs one paid work beat",N(G(quiet),"resolve")==1&&N(G(quiet),"beat")==2&&N(G(quiet),"progress")==1&&B(Assist(G(quiet)),"used")&&Assist(G(quiet)).GetProperty("last_blocked").GetString()=="none");
        string quietBefore=G(quiet).GetRawText();Check("Used assist refuses atomically even with resolve and an unraised catch",!quiet.Execute("gate-assist",null,out _)&&G(quiet).GetRawText()==quietBefore);
        var wrongPlate=new Gate(11,2,"Fixture","teal","anchor","plate");Act(wrongPlate,"gate-move","left");Act(wrongPlate,"gate-work");Act(wrongPlate,"gate-assist");
        Check("Plate on a winch beat spends the use and cannot protect mechanism integrity",N(G(wrongPlate),"integrity")==2&&N(G(wrongPlate),"resolve")==1&&B(G(wrongPlate),"left_raised")&&B(Assist(G(wrongPlate)),"used")&&Assist(G(wrongPlate)).GetProperty("last_blocked").GetString()=="none");
        var wrongTrail=new Gate(11,2,"Fixture","teal","lure","trail");Route(wrongTrail,Direct.Take(4));Act(wrongTrail,"gate-assist");
        Check("Trail on a player beat spends the use and contact still interrupts work",N(G(wrongTrail),"health")==7&&N(G(wrongTrail),"resolve")==1&&N(G(wrongTrail),"progress")==0&&B(Assist(G(wrongTrail)),"used")&&Assist(G(wrongTrail)).GetProperty("last_blocked").GetString()=="none");
        var noRig=new Gate(11,2,"Fixture","teal","anchor","unprepared");Act(noRig,"gate-move","left");string noRigBefore=G(noRig).GetRawText();
        Check("Unprepared outfit cannot invent equipment assistance",!noRig.Execute("gate-assist",null,out _)&&G(noRig).GetRawText()==noRigBefore&&Assist(G(noRig)).GetProperty("protects").GetString()=="none");
        var noResolve=new Gate(11,0,"Fixture","teal","anchor","plate");Act(noResolve,"gate-move","left");string noResolveBefore=G(noResolve).GetRawText();Check("Empty resolve cannot pay an equipment assist",!noResolve.Execute("gate-assist",null,out _)&&G(noResolve).GetRawText()==noResolveBefore);
        var wrongPosition=new Gate(11,1,"Fixture","teal","anchor","plate");string positionBefore=G(wrongPosition).GetRawText();Check("Ground is not an eligible catch for equipment work",!wrongPosition.Execute("gate-assist",null,out _)&&G(wrongPosition).GetRawText()==positionBefore);
        var raised=new Gate(11,2,"Fixture","teal","anchor","plate");Route(raised,Direct.Take(3));string raisedBefore=G(raised).GetRawText();Check("A raised catch cannot consume an unused assist",!raised.Execute("gate-assist",null,out _)&&G(raised).GetRawText()==raisedBefore&&!B(Assist(G(raised)),"used"));
        Reject(()=>wrongPosition.Execute("gate-assist","left",out _),"Direct assist cannot smuggle a movement target");Check("Malformed direct assist preserves the owner",G(wrongPosition).GetRawText()==positionBefore);
        var lethal=new Gate(3,1,"Fixture","teal","lure","trail");Act(lethal,"gate-move","left");for(int i=0;i<3;i++)Act(lethal,"gate-wait");Act(lethal,"gate-assist");
        Check("Wrong player defense pays use and resolve then death prevents catch work",B(G(lethal),"failed")&&N(G(lethal),"health")==0&&N(G(lethal),"resolve")==0&&N(G(lethal),"progress")==0&&!B(G(lethal),"left_raised")&&B(Assist(G(lethal)),"used"));
        var breakage=new Gate(100,1,"Fixture","teal","anchor","plate");for(int i=0;i<8;i++)Act(breakage,"gate-wait");Act(breakage,"gate-move","left");Act(breakage,"gate-work");Act(breakage,"gate-assist");
        Check("Wrong winch defense pays use then mechanism failure prevents second work completion",B(G(breakage),"failed")&&N(G(breakage),"integrity")==0&&N(G(breakage),"resolve")==0&&!B(G(breakage),"left_raised")&&N(G(breakage),"progress")==0&&B(Assist(G(breakage)),"used"));
        return new {plate_before=plateBefore,plate_assisted_work=plateAfter,plate_ordinary_work=controlAfter,plate_assisted=View(plate),plate_unassisted=View(plateControl),trail_before=trailBefore,trail_assisted_work=trailAfter,trail_assisted=View(trail),trail_unassisted=View(trailControl),fixtures=new{quiet=G(quiet),wrong_plate=G(wrongPlate),wrong_trail=G(wrongTrail),no_rig=G(noRig),no_resolve=G(noResolve),wrong_position=G(wrongPosition),raised=G(raised),lethal=G(lethal),mechanism_failure=G(breakage)}};
    }
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
        var openOnly=new Gate(11,7,"Neri","teal","lure","trail");Route(openOnly,Direct.Take(7));Check("Two raised catches are not a completed passage",B(G(openOnly),"left_raised")&&B(G(openOnly),"right_raised")&&!B(G(openOnly),"completed"));Act(openOnly,"gate-move","exit");Check("Exit position still needs the explicit paid living exit",!B(G(openOnly),"completed")&&G(openOnly).GetProperty("position").GetString()=="exit");
        var closed=new Gate(11,0,"Neri","teal","lure","trail");gateBefore=G(closed).GetRawText();Check("Closed exit and insufficient resolve refuse atomically",!closed.Execute("gate-move","exit",out _)&&!closed.Execute("gate-brace",null,out _)&&!closed.Execute("gate-ground",null,out _)&&G(closed).GetRawText()==gateBefore);Reject(()=>closed.Execute("gate-move","LEFT",out _),"Unknown location is not normalized");
        var brace=new Gate(11,1,"Neri","teal","lure","trail");Act(brace,"gate-brace");Check("Brace pays one resolve for current threat only",N(G(brace),"health")==11&&N(G(brace),"resolve")==0&&N(G(brace),"beat")==1);
        var lowHealth=new Gate(1,2,"Fixture","teal","lure","trail");Act(lowHealth,"gate-ground");Check("Declared low-health grounding fixture fails before shutdown application",B(G(lowHealth),"failed")&&!B(G(lowHealth),"grounded")&&N(G(lowHealth),"resolve")==0&&N(G(lowHealth),"integrity")==2);
        var lowExit=new Gate(5,7,"Fixture","teal","lure","trail");Route(lowExit,Direct);Check("Declared low-health exit fixture loses before passage completion",B(G(lowExit),"failed")&&!B(G(lowExit),"completed")&&G(lowExit).GetProperty("position").GetString()=="exit");
        var brokenWork=new Gate(100,0,"Fixture","teal","anchor","plate");for(int i=0;i<8;i++)Act(brokenWork,"gate-wait");Act(brokenWork,"gate-move","left");Act(brokenWork,"gate-work");Act(brokenWork,"gate-work");Check("Declared mechanism fixture breaks before second work can raise catch",B(G(brokenWork),"failed")&&!B(G(brokenWork),"left_raised")&&N(G(brokenWork),"progress")==0);
        var brokenGround=new Gate(100,2,"Fixture","teal","anchor","plate");for(int i=0;i<6;i++)Act(brokenGround,"gate-wait");Act(brokenGround,"gate-ground");Check("Declared mechanism fixture pays grounding but breaks before shutdown",B(G(brokenGround),"failed")&&!B(G(brokenGround),"grounded")&&N(G(brokenGround),"resolve")==0);
        var idle=new Gate(11,7,"Neri","teal","lure","trail");for(int i=0;i<20&&idle.Active;i++)Act(idle,"gate-wait");Check("Actual bounded inaction policy loses without invented passage",B(G(idle),"failed")&&!B(G(idle),"completed"));
        var replay=new Gate(11,7,"Neri","teal","lure","trail");Route(replay,Direct);Check("Accepted direct transitions replay deterministically",G(replay).GetRawText()==direct.GetRawText());before=G(replay).GetRawText();for(int i=0;i<100;i++)G(replay);Check("Reads and elapsed observation cannot advance terminal gate",G(replay).GetRawText()==before);
        var equipmentAssist=EquipmentControls();
        File.WriteAllText(args[0],JsonSerializer.Serialize(new{schema_version=1,checks=controls,equipment_assist=equipmentAssist,actual_direct=View(r),actual_grounded=View(groundedRoom),inaction=G(idle),fixtures=new{ground_death=G(lowHealth),exit_death=G(lowExit),work_break=G(brokenWork),ground_break=G(brokenGround)},limits="Actual software controls overlap outcomes, not participants, balance or Unity/Windows/Steam validation. Low-health/mechanism units are declared synthetic fixtures, separate from actual complete Field entry routes. Continuous source timing and retry are not reproduced."},new JsonSerializerOptions{WriteIndented=true})+"\n");Console.WriteLine("PASS: "+controls.Count+" actual gate native controls");
    }
}
