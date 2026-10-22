using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using NorthStar.Domain;
using NorthStar.Forge;
using NorthStar.Crossing;
using NorthStar.Loadout;
using A=NorthStar.Crossing.Action;
internal static class Program
{
 static readonly List<string> controls=new List<string>();
 static void Check(bool v,string n){if(!v)throw new InvalidOperationException("FAIL: "+n);controls.Add(n);}
 static void Reject(System.Action a,string n){bool rejected=false;try{a();}catch(ArgumentException){rejected=true;}Check(rejected,n);}
 static string Frozen(PreparedExpedition e)=>JsonSerializer.Serialize(e.Snapshot());
 static PreparedLoadout P(string c="anchor",string b="workshop",params string?[] slots)=>new PreparedLoadout(c,b,slots.Length==0?new string?[]{"brace",null,null,null}:slots);
 static void Native(string output)
 {
  var cat=PreparedExpedition.Catalog();var p=P();cat.Validate(p,1);Check(cat.ActionFor(p,0,1)==PreparedAction.Skill,"class skill resolves actual action");
  foreach(var bad in new[]{P("lure","workshop","draw",null,null,null),P("missing","workshop"),P("anchor","missing"),P("anchor","workshop","draw",null,null,null),P("anchor","workshop","brace","brace",null,null),P("anchor","workshop","unknown",null,null,null)})Reject(()=>cat.Validate(bad,1),"unknown/incompatible/duplicate proposal rejects "+controls.Count);
  var dash=P("anchor","workshop","brace","dash",null,null);Reject(()=>cat.Validate(dash,1),"Dash below prerequisite rejects");cat.Validate(dash,2);Check(cat.ActionFor(dash,1,2)==PreparedAction.Dash,"Dash exact boundary accepts");
  Reject(()=>cat.Validate(p,0),"level zero rejects");Reject(()=>cat.Validate(p,4097),"overbound level rejects");
  foreach(int i in new[]{-1,1,4})Reject(()=>cat.ActionFor(p,i,1),"empty/invalid slot rejects "+i);
  cat.Validate(P("anchor","workshop",null,null,null,null),1);Check(true,"explicit empty slots permitted");
  Reject(()=>new PreparedLoadout("anchor","workshop",new string?[3]),"short slot vector rejects");Reject(()=>new PreparedLoadout("anchor","workshop",new string?[5]),"long slot vector rejects");Reject(()=>P("bad:id"),"invalid identifier rejects");
  var input=new string?[]{"brace",null,null,null};var copy=new PreparedLoadout("anchor","workshop",input);input[0]="draw";Check(copy.Slots[0]=="brace","incoming slots detached");
  bool immutable=false;try{((IList<string?>)copy.Slots)[0]="draw";}catch(NotSupportedException){immutable=true;}Check(immutable,"public slots immutable");
  Reject(()=>new LoadoutCatalog(new[]{"a","a"},new[]{"b"},Array.Empty<BackgroundPermission>(),Array.Empty<SkillDefinition>()),"duplicate class rejects");
  Reject(()=>new LoadoutCatalog(new[]{"a"},new[]{"b","b"},Array.Empty<BackgroundPermission>(),Array.Empty<SkillDefinition>()),"duplicate background rejects");
  Reject(()=>new LoadoutCatalog(new[]{"a"},new[]{"b"},new[]{new BackgroundPermission("a","x")},Array.Empty<SkillDefinition>()),"dangling relation rejects");
  Reject(()=>new LoadoutCatalog(new[]{"a"},new[]{"b"},new[]{new BackgroundPermission("a","b"),new BackgroundPermission("a","b")},Array.Empty<SkillDefinition>()),"duplicate relation rejects");
  Reject(()=>new LoadoutCatalog(new[]{"a"},new[]{"b"},Array.Empty<BackgroundPermission>(),new[]{new SkillDefinition("s","x",1,PreparedAction.Skill)}),"dangling skill class rejects");
  Reject(()=>new SkillDefinition("s","a",0,PreparedAction.Skill),"invalid skill level rejects");Reject(()=>new SkillDefinition("s","a",1,(PreparedAction)99),"unknown action rejects");
  var closed=new LoadoutCatalog(new[]{"a"},new[]{"b"},Array.Empty<BackgroundPermission>(),Array.Empty<SkillDefinition>());Reject(()=>closed.Validate(new PreparedLoadout("a","b",new string?[4]),1),"missing relation fails closed");
  var e=new PreparedExpedition();string before=Frozen(e);
  Check(!e.Replace("lure","trailborn",new string?[]{"brace",null,null,null})&&Frozen(e)==before,"class change never silently deletes slots");Check(!e.Replace("anchor","workshop",new string?[]{"brace","dash",null,null})&&Frozen(e)==before,"locked proposal all-state rejection");
  Check(e.Replace("lure","trailborn",new string?[]{"draw",null,null,null})&&e.Replace("anchor","workshop",new string?[]{"brace",null,null,null}),"explicit class replacements revalidate without stale cache");
  Check(e.Craft("one","trail_rig").Applied&&e.Craft("two","trail_rig").Applied,"actual supplies crafted");before=Frozen(e);Check(!e.Begin((Rig)99)&&Frozen(e)==before,"invalid rig entry cannot consume supply");Check(e.Begin(Rig.Trail)&&e.Health==10&&e.Resolve==10,"Anchor independently uses Trail resources");before=Frozen(e);
  Check(!e.Replace("lure","trailborn",new string?[]{"draw",null,null,null})&&Frozen(e)==before,"active replacement atomic");Check(!e.UseSlot(1)&&!e.UseSlot(-1)&&Frozen(e)==before,"active empty/invalid slot preserves entire state");
  Check(!e.Begin(Rig.Plate)&&!e.Craft("active","plate_rig").Applied&&!e.Allocate(Allocation.Focus,1)&&Frozen(e)==before,"active entry crafting allocation locked");
  Check(e.UseSlot(0)&&e.Position==0&&e.Resolve==8,"Anchor stationary protection costs2 with Trail");e.Walk();e.Walk();e.UseSlot(0);Check(e.Won&&e.Progression.Level==2&&e.Progression.TotalXp==10,"actual encounter earns prerequisite");
  Check(e.Allocate(Allocation.Focus,2)&&e.Replace("anchor","trailborn",new string?[]{"brace","dash",null,null})&&e.Begin(Rig.Trail),"earned Dash commits before harder crossing");foreach(int slot in new[]{0,0,1,0,1,0})Check(e.UseSlot(slot),"actual slot action "+controls.Count);
  Check(e.Complete&&e.Position==4&&e.Health==11&&e.Resolve==5&&e.ConsumedRigs==2&&e.Progression.TotalXp==25,"Anchor Trail connected journey exact consequences");before=Frozen(e);Check(!e.Replace("lure","trailborn",new string?[]{"draw",null,null,null})&&!e.Begin(Rig.Unprepared)&&!e.UseSlot(0)&&Frozen(e)==before,"completed session cannot reset or repay");
  var lure=new PreparedExpedition();lure.Replace("lure","trailborn",new string?[]{"draw",null,null,null});lure.Craft("one","plate_rig");lure.Craft("two","plate_rig");lure.Begin(Rig.Plate);Check(lure.UseSlot(0)&&lure.Position==1&&lure.Resolve==3,"Lure advances with Plate at actual cost3");lure.Walk();lure.Walk();lure.UseSlot(0);Check(lure.Won,"Lure Plate survey wins");lure.Allocate(Allocation.Vitality,2);lure.Begin(Rig.Plate);lure.Walk();lure.UseSlot(0);lure.Walk();lure.Walk();lure.Walk();lure.UseSlot(0);Check(lure.Complete&&lure.Health==7&&lure.Position==6,"Lure Plate connected policy wins");
  var bare=new PreparedExpedition();bare.Replace("anchor","workshop",new string?[4]);bare.Begin(Rig.Unprepared);while(bare.Active)bare.Walk();Check(bare.Won&&bare.Health==2&&bare.ConsumedRigs==0,"empty loadout survey feasible");bare.Allocate(Allocation.Vitality,2);bare.Begin(Rig.Unprepared);while(bare.Active)bare.Walk();Check(!bare.Won&&bare.Health==0&&bare.Progression.TotalXp==10,"empty harder walking failure retained");
  var failed=new PreparedExpedition();failed.Craft("one","trail_rig");failed.Begin(Rig.Trail);while(failed.Active)failed.Wait();before=Frozen(failed);Check(!failed.Begin(Rig.Trail)&&Frozen(failed)==before&&failed.Inventory["trail_rig"]==0,"failed rig not restored on retry");Check(failed.Craft("one","trail_rig").Replay&&Frozen(failed)==before,"replay cannot refill failed supply");
  var direct=new Expedition();direct.Craft("one","plate_rig");string stock=JsonSerializer.Serialize(new{direct.Inventory,direct.Attempts,direct.Transactions});Check(!direct.Begin(Rig.Plate,(Approach)99)&&stock==JsonSerializer.Serialize(new{direct.Inventory,direct.Attempts,direct.Transactions}),"invalid explicit approach rejects before consumption");
  File.WriteAllText(output,JsonSerializer.Serialize(new{schema_version=1,kind="north_star_loadout_native",passed=controls.Count,failed=0,controls},new JsonSerializerOptions{WriteIndented=true})+"\n");Console.WriteLine("PASS: "+controls.Count+" native preparation/consumer controls.");
 }
 static void Fields(JsonElement e,params string[] names)
 {if(e.ValueKind!=JsonValueKind.Object)throw new FormatException("Expected object.");var seen=new HashSet<string>(StringComparer.Ordinal);foreach(var p in e.EnumerateObject())if(!names.Contains(p.Name)||!seen.Add(p.Name))throw new FormatException("Unknown/duplicate field.");if(seen.Count!=names.Length)throw new FormatException("Missing field.");}
 static string Text(JsonElement e){if(e.ValueKind!=JsonValueKind.String)throw new FormatException("Expected string.");return e.GetString()!;}
 static int Integer(JsonElement e){if(e.ValueKind!=JsonValueKind.Number||!e.TryGetInt32(out int v))throw new FormatException("Expected integer.");return v;}
 static JsonElement[] ArrayOf(JsonElement e,int max){if(e.ValueKind!=JsonValueKind.Array||e.GetArrayLength()>max)throw new FormatException("Invalid bounded array.");return e.EnumerateArray().ToArray();}
 static int Study(string input,string output)
 {
  if(new FileInfo(input).Length>8*1024*1024)throw new FormatException("Study exceeds8MiB.");using var doc=JsonDocument.Parse(File.ReadAllText(input),new JsonDocumentOptions{MaxDepth=16});var root=doc.RootElement;
  Fields(root,"schema_version","classes","backgrounds","relations","skills","cases");if(Integer(root.GetProperty("schema_version"))!=1)throw new FormatException("Unsupported schema.");
  var classes=ArrayOf(root.GetProperty("classes"),64).Select(Text).ToArray();var backgrounds=ArrayOf(root.GetProperty("backgrounds"),128).Select(Text).ToArray();
  var relations=new List<BackgroundPermission>();foreach(var r in ArrayOf(root.GetProperty("relations"),8192)){Fields(r,"class_id","background_id");relations.Add(new BackgroundPermission(Text(r.GetProperty("class_id")),Text(r.GetProperty("background_id"))));}
  var skills=new List<SkillDefinition>();foreach(var r in ArrayOf(root.GetProperty("skills"),1024))
  {Fields(r,"id","class_id","min_level","action");string a=Text(r.GetProperty("action"));if(a!="skill"&&a!="dash")throw new FormatException("Unknown action.");var c=r.GetProperty("class_id");skills.Add(new SkillDefinition(Text(r.GetProperty("id")),c.ValueKind==JsonValueKind.Null?null:Text(c),Integer(r.GetProperty("min_level")),a=="skill"?PreparedAction.Skill:PreparedAction.Dash));}
  var catalog=new LoadoutCatalog(classes,backgrounds,relations,skills);var rows=new List<object>();var ids=new HashSet<string>(StringComparer.Ordinal);var cases=ArrayOf(root.GetProperty("cases"),10000);if(cases.Length==0)throw new FormatException("Study requires cases.");
  foreach(var r in cases)
  {
   Fields(r,"id","class_id","background_id","level","slots");string id=Text(r.GetProperty("id"));if(id.Length<1||id.Length>64||!ids.Add(id))throw new FormatException("Invalid/duplicate case ID.");string c=Text(r.GetProperty("class_id")),b=Text(r.GetProperty("background_id"));int level=Integer(r.GetProperty("level"));var slots=ArrayOf(r.GetProperty("slots"),4).Select(x=>x.ValueKind==JsonValueKind.Null?null:Text(x)).ToArray();
   bool accepted=true;try{catalog.Validate(new PreparedLoadout(c,b,slots),level);}catch(ArgumentException){accepted=false;}rows.Add(new{id,accepted});
  }
  File.WriteAllText(output,JsonSerializer.Serialize(new{schema_version=1,kind="loadout_compatibility_results",rows},new JsonSerializerOptions{WriteIndented=true})+"\n");Console.WriteLine("PASS: "+rows.Count+" actual C# eligibility observations.");return 0;
 }
 static int Main(string[] args)
 {
  if(args.Length==2&&args[0]=="native"){Native(args[1]);return 0;}
  if(args.Length==3&&args[0]=="study")return Study(args[1],args[2]);Console.Error.WriteLine("Usage: NorthStar.LoadoutChecks native output.json | study input.json output.json");return 2;
 }
}
