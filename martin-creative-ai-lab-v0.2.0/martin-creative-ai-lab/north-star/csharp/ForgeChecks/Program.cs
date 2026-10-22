using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using NorthStar.Domain;
using NorthStar.Forge;
using A=NorthStar.Crossing.Action;
internal static class Program
{
 static readonly List<string> passed=new List<string>();
 static void Check(bool ok,string name){if(!ok)throw new InvalidOperationException("FAIL: "+name);passed.Add(name);}
 static void Reject(System.Action a,string name){bool ok=false;try{a();}catch(ArgumentException){ok=true;}Check(ok,name);}
 static string State(CraftInventory i)=>JsonSerializer.Serialize(new {stock=i.Snapshot,ledger=i.CommittedCount});
 static string State(Expedition e)=>JsonSerializer.Serialize(new {stock=e.Inventory,e.Transactions,e.Attempts,e.ConsumedRigs,e.Active,e.Complete,e.Won,e.Stage,e.Beat,e.Position,e.Health,e.Resolve,e.MaximumHealth,e.MaximumResolve,rig=e.CurrentRig,xp=e.Progression.TotalXp,main=e.Progression.UnspentMain});
 static CraftRecipe Recipe(string id="rig",string unlock="permit",IEnumerable<MaterialAmount>? inputs=null,IEnumerable<MaterialAmount>? outputs=null)=>new CraftRecipe(id,"bench",unlock,inputs??new[]{new MaterialAmount("fiber",2),new MaterialAmount("binder",1)},outputs??new[]{new MaterialAmount("rig",1)});
 static CraftInventory Stock(int fiber=4,int binder=2,int rig=0,CraftRecipe? recipe=null,string[]? unlocks=null)=>new CraftInventory(new[]{new MaterialAmount("fiber",fiber),new MaterialAmount("binder",binder),new MaterialAmount("rig",rig)},new[]{recipe??Recipe()},unlocks??new[]{"permit"});
 static void Survey(Expedition e){foreach(var a in new[]{A.Walk,A.Skill,A.Walk,A.Skill})Check(e.Act(a),"survey action "+passed.Count);}
 static void Native()
 {
  var i=Stock();Check(i.Craft("r1","rig","bench").Applied,"craft applies");Check(i.Quantity("fiber")==2&&i.Quantity("binder")==1&&i.Quantity("rig")==1,"exact conservation");
  var before=State(i);var result=i.Craft("r1","rig","bench");Check(!result.Applied&&result.Replay&&State(i)==before,"same request no-op");
  Check(i.Consume("use","rig",1).Applied,"output actually consumed");before=State(i);Check(i.Craft("r1","rig","bench").Replay&&State(i)==before&&i.Quantity("rig")==0,"replay after consumption never refills");
  Check(!i.Craft("r1","other","bench").Applied&&State(i)==before,"recipe substitution rejects atomically");Check(!i.Craft("r1","rig","elsewhere").Applied&&State(i)==before,"station substitution rejects atomically");
  Check(!i.Consume("r1","fiber",1).Applied&&State(i)==before,"cross-operation identity conflict");Check(i.Consume("use","rig",1).Replay&&State(i)==before,"consumption replay no-op");Check(!i.Consume("use","fiber",1).Applied&&State(i)==before,"consume substitution rejects");
  foreach(var station in new[]{"wrong","bench"}){var n=Stock(binder:0);before=State(n);Check(!n.Craft("failed","rig",station).Applied&&State(n)==before,"station or mixed shortage atomic "+station);}
  var locked=Stock(unlocks:Array.Empty<string>());before=State(locked);Check(!locked.Craft("locked","rig","bench").Applied&&State(locked)==before,"missing unlock atomic");
  var full=Stock(rig:CraftInventory.MaximumQuantity);before=State(full);Check(!full.Craft("overflow","rig","bench").Applied&&State(full)==before,"output overflow leaves all inputs intact");
  var unknown=Stock();before=State(unknown);Check(!unknown.Craft("retry","missing","bench").Applied&&State(unknown)==before,"unknown recipe atomic");Check(unknown.Craft("retry","rig","bench").Applied,"failed ID reusable");
  var aggregate=Stock(fiber:3,recipe:Recipe(inputs:new[]{new MaterialAmount("fiber",2),new MaterialAmount("fiber",2)}));before=State(aggregate);Check(!aggregate.Craft("duplicate","rig","bench").Applied&&State(aggregate)==before,"duplicate inputs aggregate before availability");
  var enough=Stock(recipe:Recipe(inputs:new[]{new MaterialAmount("fiber",2),new MaterialAmount("fiber",2)}));Check(enough.Craft("aggregate","rig","bench").Applied&&enough.Quantity("fiber")==0,"aggregate exact spend");
  var overlap=Stock(fiber:2,recipe:Recipe(inputs:new[]{new MaterialAmount("fiber",2)},outputs:new[]{new MaterialAmount("fiber",1)}));Check(overlap.Craft("net","rig","bench").Applied&&overlap.Quantity("fiber")==1,"input output overlap conserves");
  var self=Stock(fiber:1,recipe:Recipe(inputs:new[]{new MaterialAmount("fiber",2)},outputs:new[]{new MaterialAmount("fiber",3)}));before=State(self);Check(!self.Craft("bad","rig","bench").Applied&&State(self)==before,"output cannot prefinance input");
  var snapshot=i.Snapshot;Check(i.Craft("r2","rig","bench").Applied&&snapshot["fiber"]==2&&i.Quantity("fiber")==0,"snapshot detached");
  bool immutable=false;try{((IDictionary<string,int>)i.Snapshot)["fiber"]=99;}catch(NotSupportedException){immutable=true;}Check(immutable,"inventory projection immutable");
  immutable=false;try{((IDictionary<string,int>)Recipe().Inputs)["fiber"]=0;}catch(NotSupportedException){immutable=true;}Check(immutable,"recipe projection immutable");
  Reject(()=>Stock(fiber:-1),"negative inventory rejects");Reject(()=>Stock(fiber:CraftInventory.MaximumQuantity+1),"oversized inventory rejects");
  Reject(()=>new CraftInventory(new[]{new MaterialAmount("x",1),new MaterialAmount("x",1)},Array.Empty<CraftRecipe>(),Array.Empty<string>()),"duplicate stock rejects");
  Reject(()=>new CraftInventory(Array.Empty<MaterialAmount>(),new[]{Recipe(),Recipe()},Array.Empty<string>()),"duplicate recipes reject");Reject(()=>new CraftInventory(Array.Empty<MaterialAmount>(),Array.Empty<CraftRecipe>(),new[]{"x","x"}),"duplicate unlocks reject");
  Reject(()=>Recipe(inputs:Array.Empty<MaterialAmount>()),"empty inputs reject");Reject(()=>Recipe(outputs:Array.Empty<MaterialAmount>()),"empty outputs reject");Reject(()=>Recipe(inputs:new[]{new MaterialAmount("fiber",0)}),"zero inputs reject");Reject(()=>Recipe(outputs:new[]{new MaterialAmount("rig",-1)}),"negative output rejects");
  Reject(()=>Recipe(inputs:new[]{new MaterialAmount("fiber",CraftInventory.MaximumQuantity),new MaterialAmount("fiber",1)}),"aggregate overflow rejects");Reject(()=>Recipe(id:"bad:id"),"delimiter ID rejects");Reject(()=>i.Craft("bad id","rig","bench"),"invalid request rejects");
  before=State(i);Reject(()=>i.Consume("zero","rig",0),"zero consumption rejects");Check(State(i)==before,"invalid consume all-state invariant");
  var bounded=new CraftInventory(new[]{new MaterialAmount("fiber",1)},new[]{Recipe(inputs:new[]{new MaterialAmount("fiber",1)},outputs:new[]{new MaterialAmount("fiber",1)})},new[]{"permit"});
  for(int n=0;n<10000;n++)if(!bounded.Craft("id_"+n,"rig","bench").Applied)throw new InvalidOperationException("Early ledger cap");before=State(bounded);Check(!bounded.Craft("overflow","rig","bench").Applied&&State(bounded)==before,"ledger cap10000 atomic");Check(bounded.Craft("id_0","rig","bench").Replay&&State(bounded)==before,"full ledger replay retained");
  var e=new Expedition();before=State(e);Check(!e.Begin(Rig.Trail)&&State(e)==before,"missing rig entry atomic");Check(!e.Begin((Rig)99)&&State(e)==before,"unknown rig atomic");Check(!e.Craft("entry_0","trail_rig").Applied&&State(e)==before,"internal entry namespace protected");
  Check(e.Craft("t1","trail_rig").Applied&&e.Craft("t2","trail_rig").Applied,"two scarce rigs craft");before=State(e);Check(!e.Craft("t3","plate_rig").Applied&&State(e)==before,"third rig impossible");
  Check(e.Begin(Rig.Trail)&&e.ConsumedRigs==1&&e.Inventory["trail_rig"]==1,"one rig consumed on entry");Check(e.MaximumHealth==10&&e.MaximumResolve==10,"Trail drives actual resources");before=State(e);
  Check(!e.Craft("active","plate_rig").Applied&&State(e)==before,"active crafting atomic");Check(!e.Begin(Rig.Plate)&&State(e)==before,"active entry atomic");Check(!e.Allocate(Allocation.Focus,1)&&State(e)==before,"active allocation atomic");Survey(e);Check(e.Won&&e.Progression.TotalXp==10,"survey earned reward");Check(e.Allocate(Allocation.Focus,2),"earned Focus allocation");Check(e.Begin(Rig.Trail)&&e.ConsumedRigs==2,"second rig consumed");
  foreach(var a in new[]{A.Skill,A.Skill,A.Dash,A.Skill,A.Dash,A.Skill})Check(e.Act(a),"Trail crossing action "+passed.Count);
  Check(e.Complete&&e.Progression.TotalXp==25&&e.Inventory["trail_rig"]==0,"Trail connected completion conserved");before=State(e);Check(!e.Begin(Rig.Unprepared)&&!e.Craft("after","plate_rig").Applied&&State(e)==before,"completed state cannot restart or craft");
  var p=new Expedition();p.Craft("p1","plate_rig");p.Craft("p2","plate_rig");p.Begin(Rig.Plate);Check(p.MaximumHealth==14&&p.MaximumResolve==6,"Plate actual distinct resources");Survey(p);p.Allocate(Allocation.Vitality,2);p.Begin(Rig.Plate);foreach(var a in new[]{A.Walk,A.Skill,A.Walk,A.Walk,A.Walk,A.Skill})p.Act(a);Check(p.Complete&&p.Health==7,"Plate Vitality distinct exposed policy survives");
  var mixed=new Expedition();mixed.Begin(Rig.Unprepared);while(mixed.Active)mixed.Act(A.Walk);Check(mixed.Won,"mixed journey unprepared survey feasible");mixed.Allocate(Allocation.Focus,2);mixed.Craft("one_trail","trail_rig");mixed.Begin(Rig.Trail);foreach(var a in new[]{A.Skill,A.Skill,A.Dash,A.Skill,A.Dash,A.Skill})mixed.Act(a);Check(mixed.Complete&&mixed.ConsumedRigs==1&&mixed.Inventory["fiber"]==2&&mixed.Inventory["binder"]==1,"mixed connected journey conserves one rig worth of resources");
  var failure=new Expedition();failure.Craft("f1","trail_rig");failure.Begin(Rig.Trail);while(failure.Active)failure.Act(A.Wait);Check(!failure.Won&&failure.Inventory["trail_rig"]==0&&failure.ConsumedRigs==1,"failure never refunds rig");before=State(failure);Check(!failure.Begin(Rig.Trail)&&State(failure)==before,"retry missing rig atomic");Check(failure.Craft("f1","trail_rig").Replay&&State(failure)==before,"replay after failure cannot mint rig");Check(failure.Progression.TotalXp==0,"failed encounter no XP");Check(failure.Begin(Rig.Unprepared),"unprepared retry available");
  var bare=new Expedition();bare.Begin(Rig.Unprepared);before=State(bare);Check(!bare.Act(A.Skill)&&State(bare)==before,"unprepared skill rejection all-state invariant");while(bare.Active)bare.Act(A.Walk);Check(bare.Won&&bare.Health==2&&bare.ConsumedRigs==0,"unprepared walking survey succeeds");bare.Allocate(Allocation.Vitality,2);bare.Begin(Rig.Unprepared);while(bare.Active)bare.Act(A.Walk);Check(!bare.Won&&bare.Health==0&&bare.ConsumedRigs==0,"unprepared hard crossing walking failure retained");
 }
 static int Main(string[] args)
 {
  if(args.Length!=2||args[0]!="native"){Console.Error.WriteLine("Usage: NorthStar.ForgeChecks native output.json");return 2;}
  Native();File.WriteAllText(args[1],JsonSerializer.Serialize(new {schema_version=1,kind="north_star_crafting_native",passed=passed.Count,failed=0,controls=passed},new JsonSerializerOptions{WriteIndented=true})+"\n");Console.WriteLine("PASS: "+passed.Count+" native crafting and connected consumer controls.");return 0;
 }
}
