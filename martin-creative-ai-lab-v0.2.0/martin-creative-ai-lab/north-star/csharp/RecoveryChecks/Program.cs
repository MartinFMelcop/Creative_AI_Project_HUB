using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Nodes;
using NorthStar.Recovery;
internal static class Program
{
 static readonly List<string> labels=new();
 static void Check(bool value,string label){if(!value)throw new InvalidOperationException("FAIL: "+label);labels.Add(label);}
 static void Reject(System.Action action,string label)
 {try{action();}catch(Exception e)when(e is IOException||e is JsonException||e is FormatException||e is ArgumentException||e is InvalidDataException||e is ObjectDisposedException){Check(true,label);return;}throw new InvalidOperationException("FAIL not rejected: "+label);}
 static string Bytes(string p)=>File.ReadAllText(p);
 static RecoveryCommand Craft()=>new("craft","trail_rig");
 static string Rechecksum(JsonObject obj)
 {
  string payload=new JsonObject{["schema_version"]=obj["schema_version"]!.DeepClone(),["rules_id"]=obj["rules_id"]!.DeepClone(),["entries"]=obj["entries"]!.DeepClone()}.ToJsonString(new JsonSerializerOptions{WriteIndented=false});
  obj["checksum"]=Protocol.Hash(payload);return obj.ToJsonString(new JsonSerializerOptions{WriteIndented=false});
 }
 static void Native()
 {
  string dir=Path.Combine(Path.GetTempPath(),"recovery-native-"+Guid.NewGuid().ToString("N"));Directory.CreateDirectory(dir);
  try
  {
   string p=Path.Combine(dir,"run.json");string initial;
   using(var run=new RecoverySession(p,true))
   {
    initial=run.StateJson;Check(run.Revision==0&&File.Exists(p),"new persists explicit empty run");string prior=Bytes(p);
    var denied=run.Submit("missing",new("begin","trail"));Check(!denied.Accepted&&run.Revision==0&&run.StateJson==initial&&Bytes(p)==prior,"invalid command leaves memory file and receipt ledger unchanged");
    Reject(()=>run.Submit("bad id",Craft()),"bad request identifier rejects");Check(Bytes(p)==prior,"invalid request preserves bytes");
    Check(run.Submit("one",Craft()).Accepted&&run.Revision==1,"craft commits before receipt");prior=Bytes(p);string state=run.StateJson;
    var retry=run.Submit("one",Craft());Check(retry.Accepted&&retry.Duplicate&&retry.OriginalRevision==1&&retry.CurrentRevision==1&&state==run.StateJson&&Bytes(p)==prior,"same request replay no mutation");
    var conflict=run.Submit("one",new("craft","plate_rig"));Check(!conflict.Accepted&&!conflict.Duplicate&&run.StateJson==state&&Bytes(p)==prior,"request substitution rejects without state or file mutation");
    Check(run.Submit("two",Craft()).Accepted,"second finite supply craft accepted");
    Check(run.Submit("begin",new("begin","trail")).Accepted,"entry actually spends crafted rig");
    prior=Bytes(p);state=run.StateJson;
    Check(!run.Submit("replace",new("replace","lure","trailborn",Slots:new string?[]{"draw",null,null,null})).Accepted&&state==run.StateJson&&Bytes(p)==prior,"active identity replacement refuses without persistence");
    Check(!run.Submit("early_dash",new("slot",Number:1)).Accepted&&state==run.StateJson&&Bytes(p)==prior,"empty slot refuses without time resource or file changes");
    Reject(()=>new RecoverySession(p,false).Dispose(),"same-process competing owner rejected");
    Check(run.Advice.Contains("BOLT")&&run.Advice.Contains("position 2")&&run.Advice.Contains("beat 4"),"active restored consumer exposes actual threat and objective");
    Check(run.Submit("first_walk",new("walk")).Accepted,"accepted encounter action persisted");
   }
   string disposedPath=Path.Combine(dir,"disposed.json");var stale=new RecoverySession(disposedPath,true);stale.Dispose();
   using(var fresh=new RecoverySession(disposedPath,false)){string bytes=Bytes(disposedPath);Reject(()=>stale.Submit("late",Craft()),"disposed owner cannot submit after lease transfer");Check(fresh.Revision==0&&Bytes(disposedPath)==bytes,"disposed refusal preserves fresh owner and file");}
   string parallelPath=Path.Combine(dir,"parallel.json");using(var owner=new RecoverySession(parallelPath,true))
   {var first=System.Threading.Tasks.Task.Run(()=>owner.Submit("parallel_1",Craft()));var second=System.Threading.Tasks.Task.Run(()=>owner.Submit("parallel_2",Craft()));System.Threading.Tasks.Task.WaitAll(first,second);Check(first.Result.Accepted&&second.Result.Accepted&&owner.Revision==2&&owner.State.GetProperty("inventory").GetProperty("trail_rig").GetInt32()==2,"same-owner concurrent submissions serialize without lost commands");}
   string canonical;
   using(var recovered=new RecoverySession(p,false))
   {
    canonical=recovered.StateJson;Check(recovered.Revision==4&&recovered.State.GetProperty("active").GetBoolean()&&recovered.State.GetProperty("beat").GetInt32()==1,"mid-encounter replay restores exact next beat");
    Check(recovered.State.GetProperty("inventory").GetProperty("fiber").GetInt32()==0&&recovered.State.GetProperty("consumed_rigs").GetInt32()==1,"replay preserves materials and consumed output together");
    string before=Bytes(p);var oldReceipt=recovered.Submit("one",Craft());Check(oldReceipt.Duplicate&&oldReceipt.OriginalRevision==1&&oldReceipt.CurrentRevision==4&&recovered.StateJson==canonical&&Bytes(p)==before,"recovered old receipt labels original and current revision without minting resources");
    Check(recovered.Submit("skill",new("slot",Number:0)).Accepted&&recovered.Submit("walk",new("walk")).Accepted&&recovered.Submit("skill2",new("slot",Number:0)).Accepted,"survey continues from recovered beat");
    Check(recovered.State.GetProperty("level").GetInt32()==2&&recovered.State.GetProperty("xp").GetInt64()==10,"recovered encounter awards actual progression");
    Check(recovered.Submit("allocate",new("allocate","focus",Number:2)).Accepted,"earned allocation persisted");
    Check(recovered.Submit("loadout",new("replace","anchor","trailborn",Slots:new string?[]{"brace","dash",null,null})).Accepted,"earned equipped action persisted");
    Check(recovered.Submit("entry2",new("begin","trail")).Accepted,"second rig consumption persisted");int n=0;foreach(int slot in new[]{0,0,1,0,1,0})Check(recovered.Submit("action_"+n++,new("slot",Number:slot)).Accepted,"hard action persist "+n);
    Check(recovered.State.GetProperty("complete").GetBoolean()&&recovered.State.GetProperty("xp").GetInt64()==25&&recovered.State.GetProperty("health").GetInt32()==11,"persistent completion exact rewards and health");
    canonical=recovered.StateJson;
   }
   using(var complete=new RecoverySession(p,false)){Check(complete.StateJson==canonical,"completed run recovers exact full state");string before=Bytes(p);Check(!complete.Submit("again",new("begin","trail")).Accepted&&Bytes(p)==before,"completed recovery cannot restart or repay");}
   Reject(()=>new RecoverySession(p,true).Dispose(),"new never overwrites existing run");
   string saved=Bytes(p);
   foreach(string kind in new[]{"schema","rules","checksum","sequence","semantic","state_hash","duplicate_request","unknown_field","boolean_level"})
   {
    var obj=JsonNode.Parse(saved)!.AsObject();
    switch(kind)
    {
     case "schema":obj["schema_version"]=2;break;case "rules":obj["rules_id"]=new string('0',64);break;case "checksum":obj["checksum"]=new string('0',64);break;
     case "sequence":obj["entries"]![0]!["sequence"]=2;break;
     case "semantic":obj["entries"]![0]!["command"]!["recipe"]="missing_rig";break;
     case "state_hash":obj["entries"]![0]!["state_hash"]=new string('0',64);break;
     case "duplicate_request":obj["entries"]![1]!["request_id"]=obj["entries"]![0]!["request_id"]!.DeepClone();break;
     case "unknown_field":obj["unknown"]=1;break;
     case "boolean_level":obj["schema_version"]=true;break;
    }
    string mutant=Path.Combine(dir,kind+".json");File.WriteAllText(mutant,kind=="checksum"?obj.ToJsonString():Rechecksum(obj));string before=Bytes(mutant);
    Reject(()=>new RecoverySession(mutant,false).Dispose(),"malformed or semantically invalid run rejected "+kind);Check(Bytes(mutant)==before,"refusal preserves original bytes "+kind);
   }
   foreach(string text in new[]{"{broken",saved.Replace("\"schema_version\":1","\"schema_version\":1,\"schema_version\":1"),saved.Replace("\"schema_version\":1,","")})
   {string bad=Path.Combine(dir,"broken.json");File.WriteAllText(bad,text);Reject(()=>new RecoverySession(bad,false).Dispose(),"truncated duplicate or missing fields refused "+labels.Count);Check(Bytes(bad)==text,"bad format preserved "+labels.Count);}
   var excess=JsonNode.Parse(saved)!.AsObject();var many=new JsonArray();for(int n=0;n<=RecoverySession.MaximumEntries;n++)many.Add(excess["entries"]![0]!.DeepClone());excess["entries"]=many;string excessPath=Path.Combine(dir,"excess.json");File.WriteAllText(excessPath,excess.ToJsonString());Reject(()=>new RecoverySession(excessPath,false).Dispose(),"overbound entry count rejected before replay");
   string huge=Path.Combine(dir,"huge.json");File.WriteAllText(huge,new string(' ',RecoverySession.MaximumBytes+1));Reject(()=>new RecoverySession(huge,false).Dispose(),"overbound journal refused before parse");
   string missing=Path.Combine(dir,"missing.json");Reject(()=>new RecoverySession(missing,false).Dispose(),"missing open cannot create new run");Check(!File.Exists(missing),"missing recovery does not create save");
   foreach(string point in new[]{"before_write","before_replace","after_replace"})
   {
    string f=Path.Combine(dir,"fault_"+point+".json");string before;
    using(var run=new RecoverySession(f,true))
    {
     before=run.StateJson;Reject(()=>run.Submit("request",Craft(),p=>{if(p==point)throw new IOException("Injected write fault.");}),"injected exception observed "+point);
     Check(run.Blocked&&run.StateJson==before&&run.Revision==0,"uncertain write never publishes memory or receipt "+point);Reject(()=>run.Submit("next",Craft()),"uncertain writer remains blocked "+point);
    }
    using var open=new RecoverySession(f,false);Check(open.Revision==(point=="after_replace"?1:0),"recovery selects complete old/new journal "+point);var retry=open.Submit("request",Craft());Check(retry.Accepted&&retry.Duplicate==(point=="after_replace"),"retry after write uncertainty owns one effect "+point);
   }
   string alias=Path.Combine(dir,"alias.json");File.CreateSymbolicLink(alias,p);Reject(()=>new RecoverySession(alias,false).Dispose(),"save symlink rejected");File.Delete(alias);
   string leaseAlias=Path.Combine(dir,"lease-alias.json");File.WriteAllText(leaseAlias,saved);File.CreateSymbolicLink(leaseAlias+".lock",p+".lock");Reject(()=>new RecoverySession(leaseAlias,false).Dispose(),"lease symlink rejected");File.Delete(leaseAlias+".lock");
   using var commandDoc=JsonDocument.Parse("{\"op\":\"walk\",\"unexpected\":true}");Reject(()=>RecoveryCommand.Parse(commandDoc.RootElement),"unknown command field rejected");
   Check(RecoverySession.RulesIdentity.Length==64&&RecoverySession.RulesIdentity.Any(c=>c!='0'),"source-embedded rules identity is nonempty SHA256");
  }
  finally{Directory.Delete(dir,true);}
 }
 static int Main(string[] args)
 {
  if(args.Length!=2||args[0]!="native"){Console.Error.WriteLine("Usage: NorthStar.RecoveryChecks native OUTPUT");return 2;}
  Native();File.WriteAllText(args[1],JsonSerializer.Serialize(new{schema_version=1,kind="north_star_recovery_native",passed=labels.Count,failed=0,controls=labels},new JsonSerializerOptions{WriteIndented=true})+"\n");Console.WriteLine("PASS: "+labels.Count+" native joint recovery controls.");return 0;
 }
}
