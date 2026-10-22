using System;
using System.IO;
using System.Text.Json;
using NorthStar.Domain;
using NorthStar.Forge;
using CrossingAction=NorthStar.Crossing.Action;

internal static class Program
{
    private static object Describe(Expedition e)=>new {stage=e.Stage,active=e.Active,complete=e.Complete,won=e.Won,beat=e.Beat,position=e.Position,health=e.Health,resolve=e.Resolve,max_health=e.MaximumHealth,max_resolve=e.MaximumResolve,rig=e.CurrentRig.ToString(),attempts=e.Attempts,consumed_rigs=e.ConsumedRigs,transactions=e.Transactions,inventory=e.Inventory,xp=e.Progression.TotalXp,level=e.Progression.Level,unspent=e.Progression.UnspentMain};
    private static void Survey(Expedition e)
    {foreach(var a in new[]{CrossingAction.Walk,CrossingAction.Skill,CrossingAction.Walk,CrossingAction.Skill})if(!e.Act(a))throw new InvalidOperationException("Survey policy rejected.");}
    private static object Demo()
    {
        var trail=new Expedition();trail.Craft("trail_1","trail_rig");trail.Craft("trail_2","trail_rig");trail.Begin(Rig.Trail);Survey(trail);
        var survey=Describe(trail);trail.Allocate(Allocation.Focus,2);trail.Begin(Rig.Trail);
        foreach(var a in new[]{CrossingAction.Skill,CrossingAction.Skill,CrossingAction.Dash,CrossingAction.Skill,CrossingAction.Dash,CrossingAction.Skill})trail.Act(a);
        if(!trail.Complete || trail.ConsumedRigs!=2)throw new InvalidOperationException("Trail destination failed.");
        var plate=new Expedition();plate.Craft("plate_1","plate_rig");plate.Craft("plate_2","plate_rig");plate.Begin(Rig.Plate);Survey(plate);plate.Allocate(Allocation.Vitality,2);plate.Begin(Rig.Plate);
        foreach(var a in new[]{CrossingAction.Walk,CrossingAction.Skill,CrossingAction.Walk,CrossingAction.Walk,CrossingAction.Walk,CrossingAction.Skill})plate.Act(a);
        if(!plate.Complete)throw new InvalidOperationException("Plate walking destination failed.");
        var bare=new Expedition();bare.Begin(Rig.Unprepared);
        foreach(var a in new[]{CrossingAction.Walk,CrossingAction.Walk,CrossingAction.Walk,CrossingAction.Walk})bare.Act(a);
        if(!bare.Won)throw new InvalidOperationException("Unprepared survey should remain feasible.");
        var bareSurvey=Describe(bare);bare.Allocate(Allocation.Vitality,2);bare.Begin(Rig.Unprepared);while(bare.Active)bare.Act(CrossingAction.Walk);
        if(bare.Won)throw new InvalidOperationException("Unprepared hard crossing negative unexpectedly won.");
        var mixed=new Expedition();mixed.Begin(Rig.Unprepared);while(mixed.Active)mixed.Act(CrossingAction.Walk);
        mixed.Allocate(Allocation.Focus,2);mixed.Craft("one_trail","trail_rig");mixed.Begin(Rig.Trail);
        foreach(var a in new[]{CrossingAction.Skill,CrossingAction.Skill,CrossingAction.Dash,CrossingAction.Skill,CrossingAction.Dash,CrossingAction.Skill})mixed.Act(a);
        if(!mixed.Complete || mixed.Inventory["fiber"]!=2 || mixed.Inventory["binder"]!=1)throw new InvalidOperationException("Mixed conservation journey failed.");
        var retry=new Expedition();retry.Craft("one","trail_rig");retry.Begin(Rig.Trail);
        while(retry.Active)retry.Act(CrossingAction.Wait);
        bool missingRigRejected=!retry.Begin(Rig.Trail);var afterFailure=Describe(retry);
        if(!missingRigRejected || retry.ConsumedRigs!=1 || !retry.Begin(Rig.Unprepared))throw new InvalidOperationException("Failure conservation failed.");
        return new {schema_version=1,kind="north_star_crafting_journeys",trail_survey=survey,trail_complete=Describe(trail),plate_complete=Describe(plate),mixed_complete=Describe(mixed),unprepared_survey_success=bareSurvey,unprepared_walking_failure=Describe(bare),failed_trail_no_refund=afterFailure,missing_rig_rejected=missingRigRejected,unprepared_retry=Describe(retry),limits="Fixed scripted policies; no optimality, player preference, Unity, Windows, Steam or durable inventory claim."};
    }
    private static int Main(string[] args)
    {
        if(args.Length==2 && args[0]=="--demo")
        {File.WriteAllText(args[1],JsonSerializer.Serialize(Demo(),new JsonSerializerOptions{WriteIndented=true})+"\n");Console.WriteLine("PASS: two crafted and one mixed connected journeys, unprepared walking loss, failed-rig no-refund and unprepared retry.");return 0;}
        if(args.Length!=0){Console.Error.WriteLine("Usage: NorthStar.Forge [--demo output.json]");return 2;}
        var e=new Expedition();Console.WriteLine("NORTH STAR / FORGE — separate original expedition-supplies experiment, not Unity or final canon.");
        Console.WriteLine("4fiber +2binder can craft two rigs total. Each costs2fiber+1binder and is consumed for ONE encounter, even on failure.");
        Console.WriteLine("Plate rig: HP14/resolve6, Anchor skill blocks bolt for2. Trail rig: HP10/resolve10, Lure skill advances1 against bolt for3. Both take pulse damage unless moving.");
        Console.WriteLine("Unprepared: Plate/Anchor resources, walk/dash/wait only. Preparation is locked during encounters. No saves.");
        int request=0;
        while(!e.Complete)
        {
            Console.WriteLine(JsonSerializer.Serialize(Describe(e)));
            Console.WriteLine(e.Last);
            if(e.Active)Console.WriteLine(e.Threat+" Position needs "+e.RequiredPosition+" by beat"+e.MaximumBeats+". walk | dash | skill | wait | quit");
            else Console.WriteLine("craft plate | craft trail | enter plate | enter trail | enter unprepared | vitality N | focus N | quit");
            string? line=Console.ReadLine();if(line==null || line=="quit")return 0;
            var words=line.Split(' ',StringSplitOptions.RemoveEmptyEntries);
            if(words.Length==2 && words[0]=="craft" && (words[1]=="plate"||words[1]=="trail"))e.Craft("cli_"+request++,words[1]+"_rig");
            else if(words.Length==2 && words[0]=="enter" && Enum.TryParse<Rig>(words[1],true,out var rig))e.Begin(rig);
            else if(words.Length==2 && long.TryParse(words[1],out long points) && (words[0]=="vitality"||words[0]=="focus"))e.Allocate(words[0]=="vitality"?Allocation.Vitality:Allocation.Focus,points);
            else if(Enum.TryParse<CrossingAction>(line,true,out var action))e.Act(action);
            else Console.WriteLine("Unknown command; state unchanged.");
        }
        Console.WriteLine(JsonSerializer.Serialize(Describe(e)));Console.WriteLine("Two-stage expedition complete. "+e.Last);return 0;
    }
}
