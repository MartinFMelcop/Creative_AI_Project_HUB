using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using NorthStar.FieldJourney;
using NorthStar.FieldPresentation;
static class Program
{
 static readonly List<string> checks=new();
 static void Check(string id,bool value){if(!value)throw new Exception(id);checks.Add(id);}
 static JsonElement View(Room r)=>JsonSerializer.SerializeToElement(r.Snapshot());
 static JsonElement P(Room r)=>View(r).GetProperty("encounter_view");
 static JsonElement E(Room r)=>P(r).GetProperty("encounter");
 static JsonElement A(Room r)=>P(r).GetProperty("action");
 static JsonElement S(Room r)=>View(r).GetProperty("intake").GetProperty("state");
 static int N(JsonElement e,string n)=>e.GetProperty(n).GetInt32();
 static bool F(JsonElement e,string n)=>e.GetProperty(n).GetBoolean();
 static string? T(JsonElement e,string n)=>e.GetProperty(n).GetString();
 static JsonElement Send(Room r,string command,object? fields=null){var d=new Dictionary<string,object?>{{"command",command},{"revision",N(View(r),"sequence")}};if(fields!=null)foreach(var p in JsonSerializer.SerializeToElement(fields).EnumerateObject())d.Add(p.Name,p.Value);return JsonSerializer.SerializeToElement(r.Execute(JsonSerializer.SerializeToElement(d)));}
 static void Confirm(Room r){Send(r,"review");Send(r,"confirm",new{draft_revision=N(View(r).GetProperty("intake"),"draft_revision")});}
 static Room Person(string name="Neri",string discipline="lure"){var r=new Room();Send(r,"draft",new{handle=name,accent="teal",class_id=discipline,background_id="trailborn",slots=new string?[]{discipline=="lure"?"draw":"brace",null,null,null}});Confirm(r);return r;}
 static void Prepare(Room r){foreach(string bench in new[]{"west","east"}){Send(r,"help",new{bench});Send(r,"serve",new{bench});Send(r,"craft",new{bench,rig="trail"});}}
 static void Slot(Room r,int slot=1)=>Send(r,"slot",new{slot});
 static void Main(string[] args)
 {
  if(args.Length!=1)throw new ArgumentException("Output JSON required");
  var r=new Room();Check("Initial unconfirmed projection creates no person or active threat",!F(P(r).GetProperty("person"),"confirmed")&&T(E(r),"threat_kind")=="none");
  r=Person();Check("Actual confirmed identity and cosmetic accent reach projection",T(P(r).GetProperty("person"),"handle")=="Neri"&&T(P(r).GetProperty("person"),"accent")=="teal");
  Check("Preparation does not depict a rig merely selected in a form",T(P(r).GetProperty("person"),"rig")=="none");Prepare(r);Send(r,"begin",new{rig="trail"});
  Check("Actual entry projects the actual used rig",T(P(r).GetProperty("person"),"rig")=="trail"&&F(E(r),"active"));
  Check("Entry recovery is not narrated as healing or paid action",T(A(r),"kind")=="entry"&&N(A(r),"health_lost")==0&&N(A(r),"resolve_gained")==0&&N(A(r),"event_sequence")==0);
  Check("Actual initial announced bolt is projected",T(E(r),"threat_kind")=="bolt");
  string before=S(r).GetRawText();Slot(r,4);Check("Empty slot refusal leaves owner facts exact",!F(View(r),"accepted")&&S(r).GetRawText()==before);
  Check("Refusal creates no accepted paid response",T(A(r),"kind")=="refused"&&N(A(r),"event_sequence")==0&&N(A(r),"health_lost")==0);
  Slot(r);Check("Actual Lure bolt response protects and moves",T(A(r),"contact")=="protected"&&N(A(r),"from_position")==0&&N(A(r),"to_position")==1&&N(A(r),"resolve_spent")==3);
  Slot(r);Check("Threshold reached with active beats is not completion",F(E(r),"threshold_reached")&&F(E(r),"active")&&!F(E(r),"complete")&&N(E(r),"beat")==2&&N(E(r),"max_beats")==4);
  Check("Display bound is independent of position threshold",N(E(r),"world_end")==8&&N(E(r),"required_position")==2);
  Check("Next actual pulse is not the prior bolt",T(E(r),"threat_kind")=="pulse");
  Send(r,"walk");Check("Actual pulse movement evades and gains resolve",T(A(r),"contact")=="evaded"&&N(A(r),"resolve_gained")==2&&N(A(r),"health_lost")==0);
  Slot(r);Check("Survey retains resolved objective while owner advances",T(E(r),"phase")=="survey-won"&&N(E(r),"stage")==0&&N(E(r),"owner_stage")==1&&N(E(r),"max_beats")==4&&!F(E(r),"complete"));
  string facts=P(r).GetRawText();Check("Reads retain event and projection exactly",P(r).GetRawText()==facts);
  int hp=N(S(r),"health");Send(r,"allocate",new{axis="focus",points=1});Send(r,"draft",new{handle="Neri",accent="violet",class_id="lure",background_id="trailborn",slots=new string?[]{"draw","dash",null,null}});Confirm(r);
  Check("Earned amendment retains same person and does not heal",T(P(r).GetProperty("person"),"handle")=="Neri"&&T(P(r).GetProperty("person"),"accent")=="violet"&&N(S(r),"health")==hp);
  Send(r,"begin",new{rig="trail"});Check("Actual second entry has its own required objective",N(E(r),"stage")==1&&N(E(r),"required_position")==4&&N(E(r),"max_beats")==6);
  Slot(r);Slot(r);Slot(r,2);Check("Earned actual Dash is depicted as Dash",T(A(r),"kind")=="dash"&&N(A(r),"to_position")-N(A(r),"from_position")==2&&N(A(r),"resolve_spent")==1);
  Slot(r);Check("Harder threshold with beats pending stays active",F(E(r),"threshold_reached")&&F(E(r),"active")&&!F(E(r),"complete"));Slot(r,2);Slot(r);
  Check("Actual final Crossing supplies completion",F(E(r),"complete")&&F(E(r),"won")&&!F(E(r),"active")&&N(S(r),"consumed_rigs")==2);
  Check("Terminal projection cannot announce a future attack",T(E(r),"threat_kind")=="none");
  before=S(r).GetRawText();Slot(r);Check("Terminal refusal cannot rearm or alter completed owner",S(r).GetRawText()==before&&T(A(r),"kind")=="refused");
  var loss=Person("Sela");Prepare(loss);Send(loss,"begin",new{rig="trail"});Send(loss,"wait");Check("Actual damaging wait depicts actual harm",N(A(loss),"health_lost")==4&&T(A(loss),"contact")=="hurt");while(F(S(loss),"active"))Send(loss,"wait");
  Check("Actual defeat never becomes victory or refund",T(E(loss),"phase")=="failed"&&!F(E(loss),"won")&&!F(E(loss),"complete")&&N(S(loss),"consumed_rigs")==1&&N(S(loss),"xp")==0);
  var anchor=Person("Ivo","anchor");Prepare(anchor);Send(anchor,"begin",new{rig="trail"});Slot(anchor);Check("Anchor protection is stationary and uses actual discipline",T(P(anchor).GetProperty("person"),"class_id")=="anchor"&&T(A(anchor),"contact")=="protected"&&!F(A(anchor),"moved"));
  before=View(anchor).GetRawText();try{anchor.Execute(JsonSerializer.SerializeToElement(new{command="wait",revision=N(View(anchor),"sequence"),encounter_view=new{complete=true}}));throw new Exception("Forged projection accepted");}catch(ArgumentException){}Check("Client projection field is rejected before owner mutation",View(anchor).GetRawText()==before);
  File.WriteAllText(args[0],JsonSerializer.Serialize(new{schema_version=1,checks=new{passed=checks.Count,failed=0},controls=checks,final=View(r),loss=View(loss),limits="Overlapping actual software controls, not participant or source/Unity/Windows validation."},new JsonSerializerOptions{WriteIndented=true})+"\n");Console.WriteLine($"PASS: {checks.Count} actual field projection native controls");
 }
}
