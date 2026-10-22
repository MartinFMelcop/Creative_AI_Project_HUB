using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text.Json;
using NorthStar.Recovery;

public static class RecoveryProgram
{
 public static (int Exit,string Output) Child(params string[] args)
 {
  string process=Environment.ProcessPath!;
  string host=Path.GetFileNameWithoutExtension(process).Equals("dotnet",StringComparison.OrdinalIgnoreCase)?process:Environment.GetEnvironmentVariable("DOTNET_HOST_PATH")??"";
  if(!File.Exists(host))
  {
   var runtime=new DirectoryInfo(System.Runtime.InteropServices.RuntimeEnvironment.GetRuntimeDirectory());
   host=Path.Combine(runtime.Parent!.Parent!.Parent!.FullName,OperatingSystem.IsWindows()?"dotnet.exe":"dotnet");
  }
  if(!File.Exists(host))throw new IOException("Cannot locate the active .NET runtime host.");
  var info=new ProcessStartInfo(host){RedirectStandardOutput=true,RedirectStandardError=true,UseShellExecute=false};
  info.ArgumentList.Add(typeof(RecoverySession).Assembly.Location);foreach(string a in args)info.ArgumentList.Add(a);
  using var p=Process.Start(info)!;var output=p.StandardOutput.ReadToEndAsync();var errors=p.StandardError.ReadToEndAsync();
  if(!p.WaitForExit(15000)){p.Kill(true);p.WaitForExit();throw new IOException("Child deadline exceeded.");}
  string text=output.GetAwaiter().GetResult();errors.GetAwaiter().GetResult();return(p.ExitCode,text);
 }
 static JsonElement Json(string s)=>JsonDocument.Parse(s).RootElement.Clone();
 static void Require(bool b,string s){if(!b)throw new InvalidOperationException(s);}
 static JsonElement Ok(params string[] args){var r=Child(args);Require(r.Exit==0,"Child failed: "+string.Join(" ",args.Take(2)));return Json(r.Output);}
 static JsonElement Show(string p)=>Ok("show",p);
 static JsonElement Submit(string p,string id,string c)=>Ok("submit",p,id,c);
 const string Craft="{\"op\":\"craft\",\"recipe\":\"trail_rig\"}";
 public static object Demo()
 {
  string folder=Path.Combine(Path.GetTempPath(),"northstar-recovery-"+Guid.NewGuid().ToString("N"));Directory.CreateDirectory(folder);
  try
  {
   string p=Path.Combine(folder,"run.json");Ok("new",p);Submit(p,"craft_1",Craft);Submit(p,"craft_2",Craft);Submit(p,"enter_1","{\"op\":\"begin\",\"rig\":\"trail\"}");Submit(p,"walk_1","{\"op\":\"walk\"}");
   var mid=Show(p);var reopened=Show(p);Require(mid.GetRawText()==reopened.GetRawText(),"Mid-encounter replay changed state.");
   var replay=Submit(p,"craft_1",Craft);bool unchanged=mid.GetRawText()==Show(p).GetRawText();Require(replay.GetProperty("Duplicate").GetBoolean()&&unchanged,"Retry duplicated effect.");
   var conflict=Submit(p,"craft_1","{\"op\":\"craft\",\"recipe\":\"plate_rig\"}");bool conflictRejected=!conflict.GetProperty("Accepted").GetBoolean()&&mid.GetRawText()==Show(p).GetRawText();Require(conflictRejected,"Conflict mutated run.");
   Submit(p,"skill_1","{\"op\":\"slot\",\"slot\":0}");Submit(p,"walk_2","{\"op\":\"walk\"}");Submit(p,"skill_2","{\"op\":\"slot\",\"slot\":0}");Submit(p,"focus","{\"op\":\"allocate\",\"axis\":\"focus\",\"points\":2}");
   Submit(p,"loadout","{\"op\":\"replace\",\"class_id\":\"anchor\",\"background_id\":\"trailborn\",\"slots\":[\"brace\",\"dash\",null,null]}");Submit(p,"enter_2","{\"op\":\"begin\",\"rig\":\"trail\"}");
   int index=0;foreach(int slot in new[]{0,0,1,0,1,0})Submit(p,"hard_"+index++,"{\"op\":\"slot\",\"slot\":"+slot+"}");
   var completed=Show(p);Require(completed.GetProperty("state").GetProperty("complete").GetBoolean()&&completed.GetProperty("state").GetProperty("xp").GetInt64()==25,"Persistent journey failed.");
   var boundaries=new List<object>();
   foreach(string point in new[]{"before_write","before_replace","after_replace"})
   {
    string file=Path.Combine(folder,point+".json");Ok("new",file);var before=Show(file);var crash=Child("crash",file,"attempt",Craft,point);Require(crash.Exit==79,"Declared fault boundary not reached.");
    var recovered=Show(file);bool after=point=="after_replace";JsonElement expected;
    if(after){string reference=Path.Combine(folder,point+"-reference.json");Ok("new",reference);Submit(reference,"attempt",Craft);expected=Show(reference);}else expected=before;
    Require(recovered.GetRawText()==expected.GetRawText(),"Crash recovered partial/unexpected state.");var retry=Submit(file,"attempt",Craft);Require(retry.GetProperty("Duplicate").GetBoolean()==after,"Receipt disagrees with durable boundary.");
    boundaries.Add(new{point,child_exit=crash.Exit,expected_revision=expected.GetProperty("revision").GetInt32(),recovered_revision=recovered.GetProperty("revision").GetInt32(),expected=expected.GetProperty("state"),recovered=recovered.GetProperty("state"),state_preserved=true,retry_request_id="attempt",retry_command=new{op="craft",recipe="trail_rig"},retry_duplicate=retry.GetProperty("Duplicate").GetBoolean(),retry_accepted=retry.GetProperty("Accepted").GetBoolean()});
   }
   string failure=Path.Combine(folder,"failure.json");Ok("new",failure);Submit(failure,"craft",Craft);Submit(failure,"enter","{\"op\":\"begin\",\"rig\":\"trail\"}");for(int n=0;n<3;n++)Submit(failure,"wait_"+n,"{\"op\":\"wait\"}");
   var lost=Show(failure);var denied=Submit(failure,"retry","{\"op\":\"begin\",\"rig\":\"trail\"}");Require(!denied.GetProperty("Accepted").GetBoolean()&&lost.GetRawText()==Show(failure).GetRawText(),"Failed rig refunded or retry mutated state.");
   string invalid=Path.Combine(folder,"invalid.json");File.WriteAllText(invalid,"{broken");byte[] corrupt=File.ReadAllBytes(invalid);bool invalidRejected=Child("show",invalid).Exit!=0&&File.ReadAllBytes(invalid).SequenceEqual(corrupt);Require(invalidRejected,"Corrupt run overwritten/reset.");
   bool newDenied=Child("new",p).Exit!=0;Require(newDenied,"New overwrote existing run.");bool second;
   using(var held=new RecoverySession(p,false)){second=Child("show",p).Exit!=0;Require(second,"Second process bypassed local ownership.");}
   bool ownerDeathRecovered=false;
   var ownerInfo=new ProcessStartInfo(Environment.ProcessPath!){RedirectStandardOutput=true,RedirectStandardError=true,UseShellExecute=false};
   // Reuse Child's host resolution for a bounded blocking owner through a special child command.
   string ready=Path.Combine(folder,"owner.ready");
   string runtimeHost=Path.Combine(new DirectoryInfo(System.Runtime.InteropServices.RuntimeEnvironment.GetRuntimeDirectory()).Parent!.Parent!.Parent!.FullName,OperatingSystem.IsWindows()?"dotnet.exe":"dotnet");
   ownerInfo.FileName=runtimeHost;ownerInfo.ArgumentList.Add(typeof(RecoverySession).Assembly.Location);ownerInfo.ArgumentList.Add("hold");ownerInfo.ArgumentList.Add(p);ownerInfo.ArgumentList.Add(ready);
   using(var owner=Process.Start(ownerInfo)!)
   {
    try
    {
     var watch=Stopwatch.StartNew();while(!File.Exists(ready)&&!owner.HasExited&&watch.ElapsedMilliseconds<5000)System.Threading.Thread.Sleep(10);
     Require(File.Exists(ready)&&!owner.HasExited,"Owner process did not acquire lease.");Require(Child("show",p).Exit!=0,"Live owner did not exclude another process.");
     owner.Kill(true);Require(owner.WaitForExit(5000),"Owner process did not terminate.");ownerDeathRecovered=Show(p).GetRawText()==completed.GetRawText();Require(ownerDeathRecovered,"OS process death did not release ownership or preserved journal.");
    }
    finally{if(!owner.HasExited){owner.Kill(true);owner.WaitForExit(5000);}}
   }
   return new{schema_version=1,kind="north_star_recovery_journeys",mid_encounter_before_restart=mid.GetProperty("state"),mid_encounter_after_restart=reopened.GetProperty("state"),completed=completed.GetProperty("state"),completed_revision=completed.GetProperty("revision").GetInt32(),replay_after_restart=new{duplicate=replay.GetProperty("Duplicate").GetBoolean(),unchanged,request_id="craft_1",command=new{op="craft",recipe="trail_rig"}},conflict_rejected=conflictRejected,invalid_file_rejected=invalidRejected,existing_new_rejected=newDenied,second_writer_rejected=second,owner_death_recovered=ownerDeathRecovered,failure_boundaries=boundaries,no_refund=lost.GetProperty("state"),no_refund_retry_rejected=!denied.GetProperty("Accepted").GetBoolean(),limits="Actual local Linux processes and trusted regular paths; no power-loss/directory-fsync, network/account authority, tamper resistance, Unity, Windows, Steam or human validation."};
  }
  finally{Directory.Delete(folder,true);}
 }
 static int Play(string path)
 {
  using var run=new RecoverySession(path,false);Console.WriteLine("NORTH STAR / RECOVERABLE EXPEDITION — local journal experiment. Accepted commands save before receipt; EOF/quit closes the run.");
  Console.WriteLine("craft trail|plate; enter trail|plate|unprepared; walk; wait; slot 1..4; focus N; vitality N; loadout CLASS BACKGROUND SLOT1 SLOT2 SLOT3 SLOT4 (- empty); quit");
  while(true)
  {
   Console.WriteLine(run.StateJson);Console.WriteLine(run.Advice);string? line=Console.ReadLine();if(line==null||line=="quit")return 0;string[] w=line.Split(' ',StringSplitOptions.RemoveEmptyEntries);RecoveryCommand? command=null;
   if(w.Length==1&&(w[0]=="walk"||w[0]=="wait"))command=new(w[0]);else if(w.Length==2&&w[0]=="craft")command=new("craft",w[1]+"_rig");else if(w.Length==2&&w[0]=="enter")command=new("begin",w[1]);
   else if(w.Length==2&&w[0]=="slot"&&long.TryParse(w[1],out long slot))command=new("slot",Number:slot-1);else if(w.Length==2&&(w[0]=="focus"||w[0]=="vitality")&&long.TryParse(w[1],out long points))command=new("allocate",w[0],Number:points);
   else if(w.Length==7&&w[0]=="loadout")command=new("replace",w[1],w[2],Slots:w.Skip(3).Select(x=>x=="-"?null:x).ToArray());
   if(command==null){Console.WriteLine("Unknown command; state unchanged.");continue;}Console.WriteLine(run.Submit("play_"+Guid.NewGuid().ToString("N"),command).Reason);
  }
 }
 public static int Main(string[] args)
 {
  try
  {
   if(args.Length==2&&args[0]=="--demo"){File.WriteAllText(args[1],JsonSerializer.Serialize(Demo(),new JsonSerializerOptions{WriteIndented=true})+"\n");Console.WriteLine("PASS: real restart/retry, three crash boundaries, corrupt-file and competing-writer controls.");return 0;}
   if(args.Length==2&&args[0]=="play")return Play(args[1]);
   if(args.Length==3&&args[0]=="hold"){using var held=new RecoverySession(args[1],false);File.WriteAllText(args[2],"owned");System.Threading.Thread.Sleep(System.Threading.Timeout.Infinite);return 0;}
   if(args.Length==2&&(args[0]=="new"||args[0]=="show")){using var run=new RecoverySession(args[1],args[0]=="new");Console.WriteLine(JsonSerializer.Serialize(new{revision=run.Revision,state=run.State}));return 0;}
   if((args.Length==4&&args[0]=="submit")||(args.Length==5&&args[0]=="crash"))
   {using var run=new RecoverySession(args[1],false);string? point=args.Length==5?args[4]:null;if(point!=null&&!new[]{"before_write","before_replace","after_replace"}.Contains(point))throw new ArgumentException("Invalid failure boundary.");using var doc=JsonDocument.Parse(args[3]);var receipt=run.Submit(args[2],RecoveryCommand.Parse(doc.RootElement),point==null?null:stage=>{if(stage==point)Environment.Exit(79);});Console.WriteLine(JsonSerializer.Serialize(receipt));return 0;}
   Console.Error.WriteLine("Usage: NorthStar.Recovery new|show|play PATH; submit PATH ID COMMAND_JSON; --demo REPORT. Developer crash mode: crash PATH ID COMMAND_JSON POINT.");return 2;
  }
  catch(Exception e)when(e is IOException||e is UnauthorizedAccessException||e is JsonException||e is FormatException||e is ArgumentException||e is InvalidDataException){Console.Error.WriteLine("REFUSED: "+e.Message);return 3;}
 }
}
