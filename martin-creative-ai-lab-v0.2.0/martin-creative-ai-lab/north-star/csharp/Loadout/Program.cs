using System;
using System.IO;
using System.Text.Json;
using NorthStar.Domain;
using NorthStar.Forge;
using NorthStar.Loadout;

internal static class Program
{
    private static void Survey(PreparedExpedition e)
    {if(!e.Walk()||!e.UseSlot(0)||!e.Walk()||!e.UseSlot(0)||!e.Won)throw new InvalidOperationException("Prepared survey failed.");}
    private static object Demo()
    {
        var anchor=new PreparedExpedition();anchor.Craft("first","trail_rig");anchor.Craft("second","trail_rig");anchor.Begin(Rig.Trail);Survey(anchor);
        var earned=anchor.Snapshot();anchor.Allocate(Allocation.Focus,2);
        if(!anchor.Replace("anchor","trailborn",new string?[]{"brace","dash",null,null})||!anchor.Begin(Rig.Trail))throw new InvalidOperationException("Earned Dash preparation failed.");
        foreach(int slot in new[]{0,0,1,0,1,0})if(!anchor.UseSlot(slot))throw new InvalidOperationException("Anchor action rejected.");
        if(!anchor.Complete)throw new InvalidOperationException("Anchor/Trail crossing failed.");
        var lure=new PreparedExpedition();lure.Replace("lure","trailborn",new string?[]{"draw",null,null,null});lure.Craft("first","plate_rig");lure.Craft("second","plate_rig");lure.Begin(Rig.Plate);Survey(lure);
        lure.Allocate(Allocation.Vitality,2);lure.Begin(Rig.Plate);
        lure.Walk();lure.UseSlot(0);lure.Walk();lure.Walk();lure.Walk();lure.UseSlot(0);
        if(!lure.Complete)throw new InvalidOperationException("Lure/Plate crossing failed.");
        var bare=new PreparedExpedition();bare.Replace("anchor","workshop",new string?[]{null,null,null,null});bare.Begin(Rig.Unprepared);while(bare.Active)bare.Walk();
        var bareSurvey=bare.Snapshot();bare.Allocate(Allocation.Vitality,2);bare.Begin(Rig.Unprepared);while(bare.Active)bare.Walk();
        if(bare.Won||bare.Health!=0)throw new InvalidOperationException("Retained empty-loadout walking policy unexpectedly won.");
        var rejected=new PreparedExpedition();string before=JsonSerializer.Serialize(rejected.Snapshot());bool denial=!rejected.Replace("lure","workshop",new string?[]{"brace","dash",null,null});
        bool unchanged=before==JsonSerializer.Serialize(rejected.Snapshot());if(!denial||!unchanged)throw new InvalidOperationException("Incompatible proposal changed identity.");
        return new {schema_version=1,kind="north_star_loadout_journeys",earned_level2=earned,anchor_trail_complete=anchor.Snapshot(),lure_plate_complete=lure.Snapshot(),empty_survey_success=bareSurvey,empty_crossing_failure=bare.Snapshot(),invalid_proposal_rejected=denial,invalid_proposal_unchanged=unchanged,limits="Two original experimental disciplines, three implemented action definitions and four-slot capacity. Fixed policies, not final classes/backgrounds, historical skills, optimality, Unity, Windows, Steam or player validation."};
    }
    private static int Main(string[] args)
    {
        if(args.Length==2&&args[0]=="--demo")
        {File.WriteAllText(args[1],JsonSerializer.Serialize(Demo(),new JsonSerializerOptions{WriteIndented=true})+"\n");Console.WriteLine("PASS: earned Dash, independent Anchor/Trail and Lure/Plate journeys; empty-loadout and atomic-rejection controls retained.");return 0;}
        if(args.Length!=0){Console.Error.WriteLine("Usage: NorthStar.Loadout [--demo output.json]");return 2;}
        var e=new PreparedExpedition();int request=0;
        Console.WriteLine("NORTH STAR / EXPLICIT PREPARATION — original terminal experiment, not Unity or approved class canon.");
        Console.WriteLine("Disciplines: anchor uses brace (2resolve, stationary protection); lure uses draw (3resolve, advances against bolt). Both exposed to pulse. Outfits remain independent: plateHP14/resolve6 or trailHP10/resolve10 before earned bonuses.");
        Console.WriteLine("Background compatibility: anchor/workshop, anchor/trailborn, lure/trailborn. Backgrounds are compatibility-only experimental metadata, no supply/stat bonus. Four slots capacity; brace/draw level1, shared dash level2 costs1resolve, advances2. Walk/Wait always available.");
        Console.WriteLine("Rig crafting costs2fiber+1binder; starting4fiber+2binder. Enter consumes one rig, no failure refund. Unprepared entry disables skill. No saves.");
        while(!e.Complete)
        {
            Console.WriteLine(JsonSerializer.Serialize(e.Snapshot()));Console.WriteLine(e.Last);
            if(e.Active)Console.WriteLine(e.Threat+" Need position"+e.RequiredPosition+" by beat"+e.MaximumBeats+". walk | wait | slot 1..4 | quit");
            else Console.WriteLine("loadout CLASS BACKGROUND SLOT1 SLOT2 SLOT3 SLOT4 (- empty) | craft plate/trail | enter plate/trail/unprepared | vitality N | focus N | quit");
            string? line=Console.ReadLine();if(line==null||line=="quit")return 0;var words=line.Split(' ',StringSplitOptions.RemoveEmptyEntries);
            if(words.Length==7&&words[0]=="loadout")e.Replace(words[1],words[2],new string?[]{words[3]=="-"?null:words[3],words[4]=="-"?null:words[4],words[5]=="-"?null:words[5],words[6]=="-"?null:words[6]});
            else if(words.Length==2&&words[0]=="craft"&&(words[1]=="plate"||words[1]=="trail"))e.Craft("cli_"+request++,words[1]+"_rig");
            else if(words.Length==2&&words[0]=="enter"&&Enum.TryParse<Rig>(words[1],true,out var rig))e.Begin(rig);
            else if(words.Length==2&&words[0]=="slot"&&int.TryParse(words[1],out int slot))e.UseSlot(slot-1);
            else if(words.Length==2&&long.TryParse(words[1],out long points)&&(words[0]=="vitality"||words[0]=="focus"))e.Allocate(words[0]=="vitality"?Allocation.Vitality:Allocation.Focus,points);
            else if(line=="walk")e.Walk();else if(line=="wait")e.Wait();else Console.WriteLine("Unknown command; state unchanged.");
        }
        Console.WriteLine(JsonSerializer.Serialize(e.Snapshot()));Console.WriteLine("Connected expedition complete.");return 0;
    }
}
