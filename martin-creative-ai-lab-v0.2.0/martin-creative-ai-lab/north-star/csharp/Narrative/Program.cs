using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;

namespace NorthStar.Narrative
{
    public static class Program
    {
        private static readonly JsonSerializerOptions Json=new JsonSerializerOptions{WriteIndented=true};
        public static readonly string[] SurveyPath={"survey","skill","skill","walk","skill"};
        public static readonly string[] DeliveryPath={"skill","skill","walk","skill","walk","skill"};
        public static object Journey(string name,IEnumerable<string> commands)
        {
            var game=new RequestExpedition();var observations=new List<object>();
            foreach(string command in commands){bool accepted=game.Command(command);observations.Add(new {command,accepted,text=game.Last,after=game.Snapshot()});}
            return new {name,observations,final=game.Snapshot()};
        }
        private static string[] Join(params string[][] sections){var result=new List<string>();foreach(var section in sections)result.AddRange(section);return result.ToArray();}
        public static object Demo()=>new {schema_version=1,scope="Actual original in-session request consumer and unchanged Crossing model; synthetic deterministic journeys, not human choices, Unity, persistent campaign or NPC AI",journeys=new []{
            Journey("local_refusal",new[]{"open","hear","decline","work","work","work"}),
            Journey("guided_dusk",Join(SurveyPath,new[]{"open","hear","offer","terms dusk","confirm","depart guided"},DeliveryPath,new[]{"work"})),
            Journey("solo_delivery",Join(SurveyPath,new[]{"decline","depart solo"},DeliveryPath)),
            Journey("defer_fresh",Join(SurveyPath,new[]{"open","hear","offer","terms dusk","defer","work","confirm","open","hear","offer","terms open","confirm","depart guided"},DeliveryPath)),
            Journey("withdraw_before_departure",Join(SurveyPath,new[]{"open","hear","offer","terms dusk","confirm","withdraw","work"})),
            Journey("failed_delivery",Join(SurveyPath,new[]{"open","hear","offer","terms dusk","confirm","depart guided","wait","wait"})),
            Journey("deadline_not_return",Join(SurveyPath,new[]{"open","hear","offer","terms dusk","confirm","work","work","work","depart guided"})),
            Journey("stale_proposal",Join(SurveyPath,new[]{"open","hear","offer","terms dusk","work","confirm","open","offer"}))}};
        public static int Main(string[] args)
        {
            try
            {
                if(args.Length==2&&args[0]=="--demo"){File.WriteAllText(args[1],JsonSerializer.Serialize(Demo(),Json)+"\n");Console.WriteLine("PASS: eight actual request journeys, including retained refusal, stale-consent, failed-delivery and deadline negatives.");return 0;}
                if(args.Length!=0){Console.Error.WriteLine("Usage: NorthStar.Narrative [--demo REPORT]");return 2;}
                var game=new RequestExpedition();Console.WriteLine("The shutter list — original experimental request scene\n"+game.Last);
                Console.WriteLine("Commands: open, hear, offer, terms dusk|open, confirm, defer, decline, withdraw, work, survey, depart guided|solo, skill, walk, dash, wait, show, quit. No save is created.");
                while(true)
                {
                    Console.WriteLine($"\nLight {game.Remaining}/4; shutters {game.Crates}/5; local capacity {game.Capacity}; Rill {game.GuideLocation}; coil {(game.Delivered?"delivered":"not delivered")}; request {game.Status}.");
                    if(game.Active)Console.WriteLine(JsonSerializer.Serialize(game.Snapshot(),Json));
                    Console.Write("> ");string? line=Console.ReadLine();if(line==null||line=="quit")break;
                    if(line=="show"){Console.WriteLine(JsonSerializer.Serialize(game.Snapshot(),Json));continue;}
                    bool accepted=game.Command(line);Console.WriteLine((accepted?"":"REFUSED: ")+game.Last);
                }
                Console.WriteLine("Session ended. In-session facts follow; no persistent quest or future return is inferred.\n"+JsonSerializer.Serialize(game.Snapshot(),Json));return 0;
            }
            catch(Exception error)when(error is IOException||error is UnauthorizedAccessException||error is ArgumentException){Console.Error.WriteLine(error.Message);return 2;}
        }
    }
}
