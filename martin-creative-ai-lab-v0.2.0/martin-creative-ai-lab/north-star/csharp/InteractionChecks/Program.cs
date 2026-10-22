using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using NorthStar.InputTiming;
using P=NorthStar.Interaction.Program;
var controls=new List<string>();
void Check(string name,bool value){if(!value)throw new Exception(name);controls.Add(name);}
string State(WorkRoom r)=>JsonSerializer.Serialize(r.Snapshot());
void Advance(WorkRoom r,long end,int step){while(r.Now<end)r.Advance(Math.Min(end,r.Now+step),false,true);}
WorkRoom Start(string target="ground"){var r=new WorkRoom();r.Select(target);r.Input(true);return r;}
foreach(int step in new[]{1,17,50,250,500}){var r=Start();Advance(r,1499,step);Check("no early grounding "+step,!r.Grounded&&r.Paid==0);r.Advance(1500,false,true);Check("exact deadline "+step,r.Grounded&&r.Paid==1&&r.Integrity==2&&!r.Won);Advance(r,3000,step);Check("held completion once "+step,r.Paid==1&&r.Completions==1);}
foreach(int boundary in new[]{0,500,1499,1500}){var r=Start();Advance(r,boundary,500);if(boundary==1500){Check("completed before later release",r.Paid==1);continue;}r.Input(false);Advance(r,2000,500);Check("release discards "+boundary,r.Paid==0&&r.Progress==0);}
foreach(string reason in new[]{"movement","pause","focus"}){var r=Start();Advance(r,500,100);if(reason=="movement")r.Select("catch-b");else r.Pause(reason);Advance(r,10000,500);r.Resume();Check(reason+" no held resume",!r.Working&&r.NeedNeutral&&r.Paid==0);r.Input(false);r.Input(true);Check(reason+" fresh starts zero",r.Working&&r.Progress==0);}
var timeout=Start();timeout.Advance(5000);Check("missing heartbeat cancels at lease",timeout.Paused&&timeout.Progress==0&&timeout.LastProgress==600&&timeout.Paid==0);
var hit=Start();Advance(hit,1000,100);hit.Advance(1500,true,true);Check("harm owns exact completion boundary",!hit.Grounded&&hit.Paid==0&&hit.Integrity==2&&hit.Health==2&&hit.LastCause=="hit");
var repeat=Start();Advance(repeat,500,100);repeat.Input(true);Check("repeat does not restart",repeat.Progress==500);Advance(repeat,1500,100);repeat.Input(true);Check("repeat cannot repay",repeat.Paid==1);
var bad=Start();Advance(bad,500,100);string before=State(bad);try{bad.Advance(499);throw new Exception("backward accepted");}catch(ArgumentOutOfRangeException){}Check("backward clock preserves whole state",before==State(bad));try{bad.Advance(86400001);throw new Exception("overflow accepted");}catch(ArgumentOutOfRangeException){}Check("clock bound preserves state",before==State(bad));try{bad.Select("fake");throw new Exception("unknown accepted");}catch(ArgumentException){}Check("unknown station preserves state",before==State(bad));
var dead=Start();dead.Advance(0,true,true);dead.Advance(0,true,true);dead.Advance(0,true,true);Check("resource loss owns failure",dead.Lost&&!dead.Exit());
var demo=JsonSerializer.SerializeToElement(P.Demo());Check("actual living full route",demo.GetProperty("completed").GetProperty("won").GetBoolean());Check("grounding optional actual route",demo.GetProperty("optional_grounding").GetProperty("won").GetBoolean()&&!demo.GetProperty("optional_grounding").GetProperty("grounded").GetBoolean());
if(args.Length!=1)throw new ArgumentException("Usage: REPORT");File.WriteAllText(args[0],JsonSerializer.Serialize(new{schema_version=1,passed=controls.Count,failed=0,controls},P.Json)+"\n");Console.WriteLine("PASS: "+controls.Count+" actual timed-work controls");
