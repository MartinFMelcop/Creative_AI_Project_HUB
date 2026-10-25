using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using NorthStar.Domain;
using NorthStar.Tooling;
using NorthStar.Crossing;
using CrossingAction=NorthStar.Crossing.Action;

namespace NorthStar.ToolingStudy;

// A narrow original consumer. Actual inventory and Crossing retain their private owners.
public sealed class Room
{
    private static readonly HashSet<string> Commands=new(StringComparer.Ordinal){"craft","enter","walk","dash","skill","wait","restart equipped","restart missing"};
    private ToolWorkshop workshop;
    private Session encounter=new();
    private int sequence,attempts,consumedRigs;
    private bool started,accepted=true;
    private string mode="equipped",lastCommand="initial",last="Four fiber, two binder and one owned gauge. Two rigs are possible; the same gauge must remain. Crafting is not an expedition result.";
    private static ToolWorkshop Create(bool hasGauge)
    {
        var catalog=new ItemCatalog(new[]{"fiber","binder","gauge","trail_rig"});
        var recipe=new CraftRecipe("trail_rig","bench","bench_permission",new[]{new MaterialAmount("fiber",2),new MaterialAmount("binder",1)},new[]{new MaterialAmount("trail_rig",1)});
        return new ToolWorkshop(catalog,new[]{new MaterialAmount("fiber",4),new MaterialAmount("binder",2),new MaterialAmount("gauge",hasGauge?1:0),new MaterialAmount("trail_rig",0)},new[]{new ToolRecipe(recipe,new[]{"gauge"})},new[]{"bench_permission"});
    }
    public Room(){workshop=Create(true);}
    public object Snapshot()=>new {sequence,accepted,command=lastCommand,text=last,state=new {
        mode,inventory=workshop.Snapshot,transactions=workshop.CommittedCount,consumed_rigs=consumedRigs,attempts,
        encounter=started?new {active=encounter.Active,complete=encounter.Complete,won=encounter.Won,stage=encounter.Stage,beat=encounter.Beat,position=encounter.Position,health=encounter.Health,resolve=encounter.Resolve,threat=encounter.Threat,required_position=encounter.RequiredPosition,maximum_beats=encounter.MaximumBeats}:null,
        scope="Original finite ephemeral tooling consumer of unchanged inventory/Crossing. No source item effects/quests, persistent world, approved canon, Unity/Windows/Steam or human validation."}};
    public object Execute(JsonElement document)
    {
        if(document.ValueKind!=JsonValueKind.Object)throw new ArgumentException("Object required.");
        var fields=document.EnumerateObject().ToArray();
        if(fields.Length!=1 || fields[0].Name!="command" || fields[0].Value.ValueKind!=JsonValueKind.String)throw new ArgumentException("Exact command object required.");
        string command=fields[0].Value.GetString()!;
        if(!Commands.Contains(command))throw new ArgumentException("Unknown exact command.");
        sequence++;lastCommand=command;accepted=false;
        if(command.StartsWith("restart ",StringComparison.Ordinal))
        {
            mode=command[8..];workshop=Create(mode=="equipped");encounter=new Session();started=false;attempts=0;consumedRigs=0;accepted=true;
            last="A fresh "+mode+" trial replaces this ephemeral study. Initial materials are assay setup, not refunded world resources or an acquired tool.";return Snapshot();
        }
        if(command=="craft")
        {
            if(encounter.Active || encounter.Complete){last="The bench is unavailable during or after this expedition. No inventory changes.";return Snapshot();}
            var result=workshop.Craft("craft_"+sequence,"trail_rig","bench");accepted=result.Applied;
            last=result.Applied?"Two fiber and one binder were actually consumed. One Trail rig was made; the required gauge remains owned and unconsumed.":result.Reason;
            return Snapshot();
        }
        if(command=="enter")
        {
            if(encounter.Active || encounter.Complete){last="An active or completed expedition cannot start another entry.";return Snapshot();}
            if(workshop.Quantity("trail_rig")<1){last="No crafted rig exists. Entry cannot spend material promises or the retained gauge.";return Snapshot();}
            var result=workshop.Consume("entry_"+attempts,"trail_rig",1);
            if(!result.Applied){last=result.Reason;return Snapshot();}
            if(!encounter.Prepare(Approach.Lure,Outfit.Trail) || !encounter.Begin())throw new InvalidOperationException("Private Crossing violated validated entry preconditions.");
            attempts++;consumedRigs++;started=true;accepted=true;
            last="One actual crafted rig was consumed for this fixed Lure/Trail encounter. The gauge remains at the bench. Failure gives no rig or material refund.";return Snapshot();
        }
        if(!encounter.Active){last="No encounter is active. Observation or an action name cannot enter a journey.";return Snapshot();}
        var action=command switch {"walk"=>CrossingAction.Walk,"dash"=>CrossingAction.Dash,"skill"=>CrossingAction.Skill,_=>CrossingAction.Wait};
        accepted=encounter.Act(action);last=encounter.Last;
        if(!encounter.Active && encounter.Won && !encounter.Complete)last+=" Survey won; final expedition is still incomplete. A second actual rig and explicit entry are required.";
        return Snapshot();
    }
}
