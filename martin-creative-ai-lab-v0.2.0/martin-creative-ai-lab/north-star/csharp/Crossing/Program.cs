using System;
using System.IO;
using System.Text.Json;
using NorthStar.Domain;
using NorthStar.Crossing;
using CrossingAction = NorthStar.Crossing.Action;

internal static class Program
{
    private static object Describe(Session s) => new {
        stage=s.Stage,active=s.Active,won=s.Won,complete=s.Complete,beat=s.Beat,position=s.Position,
        health=s.Health,resolve=s.Resolve,max_health=s.MaximumHealth,max_resolve=s.MaximumResolve,
        level=s.Progression.Level,xp=s.Progression.TotalXp,unspent=s.Progression.UnspentMain,
        vitality=s.Progression.Vitality,focus=s.Progression.Focus,spent_resolve=s.SpentResolve,rejected=s.Rejected };
    private static int Main(string[] args)
    {
        if (args.Length == 2 && args[0] == "--demo")
        {
            var s = new Session(); s.Prepare(Approach.Lure,Outfit.Trail); s.Begin();
            foreach (var action in new[] {CrossingAction.Walk,CrossingAction.Skill,CrossingAction.Walk,CrossingAction.Skill}) s.Act(action);
            var first=Describe(s); s.Allocate(Allocation.Focus,2); s.Begin();
            foreach (var action in new[] {CrossingAction.Skill,CrossingAction.Skill,CrossingAction.Dash,CrossingAction.Skill,CrossingAction.Dash,CrossingAction.Skill}) s.Act(action);
            if (!s.Complete || s.Progression.Level!=3) throw new InvalidOperationException("Destination demo failed.");
            File.WriteAllText(args[1],JsonSerializer.Serialize(new {schema_version=1,kind="north_star_csharp_journey",survey=first,crossing=Describe(s)},new JsonSerializerOptions {WriteIndented=true})+"\n");
            Console.WriteLine("PASS: prepared survey -> earned points -> Focus allocation -> distinct Lure crossing -> level3 reward");return 0;
        }
        if (args.Length != 0) { Console.Error.WriteLine("Usage: dotnet NorthStar.Crossing.dll [--demo output.json]");return 2; }
        var session=new Session();
        Console.WriteLine("NORTH STAR / ORIGINAL C# PROGRESSION EXPERIMENT — terminal consumer, not Unity or final class canon.");
        while (!session.Complete)
        {
            if (!session.Active)
            {
                Console.WriteLine("PREPARATION: Anchor blocks in place for2; Lure advances1 while drawing a bolt for3. Both are exposed to pulse. Plate HP14/resolve6; Trail HP10/resolve10.");
                Console.WriteLine("Commands: anchor | lure | plate | trail | vitality N | focus N | enter | quit");
            }
            else Console.WriteLine((session.Stage==0?"SURVEY":"CROSSING")+" / beat "+session.Beat+"/"+session.MaximumBeats+" / position "+session.Position+" (need "+session.RequiredPosition+" by deadline) / HP "+session.Health+" / resolve "+session.Resolve+"\n"+session.Threat+"\nwalk | dash (1 resolve,2distance) | skill | wait | quit");
            Console.WriteLine("Level "+session.Progression.Level+" / XP "+session.Progression.TotalXp+" / earned points "+session.Progression.UnspentMain+". "+session.Last);
            string? line=Console.ReadLine();if(line==null || line=="quit")return 0;
            if(session.Active)
            {
                CrossingAction action;
                if(Enum.TryParse(line,true,out action))session.Act(action);else Console.WriteLine("Unknown action; state unchanged.");
            }
            else
            {
                var words=line.Split(' ',StringSplitOptions.RemoveEmptyEntries);
                if(words.Length==2 && long.TryParse(words[1],out long points) && (words[0]=="vitality" || words[0]=="focus"))
                    Console.WriteLine(session.Allocate(words[0]=="vitality"?Allocation.Vitality:Allocation.Focus,points)?"Allocation committed.":"Unavailable allocation; state unchanged.");
                else if(line=="enter")session.Begin();
                else if(line=="anchor" || line=="lure")session.Prepare(line=="anchor"?Approach.Anchor:Approach.Lure,session.Outfit);
                else if(line=="plate" || line=="trail")session.Prepare(session.Approach,line=="plate"?Outfit.Plate:Outfit.Trail);
                else Console.WriteLine("Unknown preparation command; state unchanged.");
            }
        }
        Console.WriteLine("Connected crossing complete. "+session.Last);return 0;
    }
}
