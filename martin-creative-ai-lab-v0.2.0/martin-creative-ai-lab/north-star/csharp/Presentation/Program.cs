using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Net;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using NorthStar.Crossing;
using CrossingAction = NorthStar.Crossing.Action;
namespace NorthStar.Presentation;

// Presentation observes the unchanged Crossing owner. No animation clock owns gameplay.
public sealed class Room
{
    private Session session=new();
    private long sequence;
    private Dictionary<string,object> observation;
    public Room(){observation=Observe("initial",true,"ready",State(),State(),0,0,0,"none");}
    private Dictionary<string,object> State()=>new(){["approach"]=session.Approach.ToString().ToLowerInvariant(),["outfit"]=session.Outfit.ToString().ToLowerInvariant(),["stage"]=session.Stage,["beat"]=session.Beat,["position"]=session.Position,["health"]=session.Health,["resolve"]=session.Resolve,["max_health"]=session.MaximumHealth,["max_resolve"]=session.MaximumResolve,["spent_resolve"]=session.SpentResolve,["rejected"]=session.Rejected,["active"]=session.Active,["won"]=session.Won,["complete"]=session.Complete,["required_position"]=session.RequiredPosition,["max_beats"]=session.MaximumBeats,["pulse"]=session.Pulse,["threat"]=session.Threat,["last"]=session.Last,["level"]=session.Progression.Level,["xp"]=session.Progression.TotalXp};
    private Dictionary<string,object> Observe(string command,bool accepted,string pose,Dictionary<string,object> before,Dictionary<string,object> after,int damage,int cost,int moved,string contact)
    {
        var result=new Dictionary<string,object>(after){["sequence"]=sequence,["accepted"]=accepted,["command"]=command,["pose"]=pose,["before"]=before,["after"]=after,["damage"]=damage,["cost"]=cost,["moved"]=moved,["contact"]=contact};return result;
    }
    public Dictionary<string,object> Snapshot()=>observation;
    public Dictionary<string,object> Execute(JsonElement d)
    {
        if(d.ValueKind!=JsonValueKind.Object)throw new ArgumentException("Object required.");
        var properties=d.EnumerateObject().ToArray();
        if(properties.Select(x=>x.Name).Distinct().Count()!=properties.Length)throw new ArgumentException("Repeated field.");
        string op=d.GetProperty("op").GetString()??"";
        string[] fields=op switch{"prepare"=>new[]{"op","approach","outfit"},"action"=>new[]{"op","action"},"begin" or "restart"=>new[]{"op"},_=>throw new ArgumentException("Unknown command.")};
        if(properties.Length!=fields.Length||properties.Any(x=>!fields.Contains(x.Name)))throw new ArgumentException("Exact command fields required.");
        // All syntax is validated before invoking the owner or changing observation identity.
        Approach approach=Approach.Anchor;Outfit outfit=Outfit.Plate;CrossingAction action=CrossingAction.Wait;
        if(op=="prepare")
        {
            approach=d.GetProperty("approach").GetString() switch{"anchor"=>Approach.Anchor,"lure"=>Approach.Lure,_=>throw new ArgumentException("Unknown approach.")};
            outfit=d.GetProperty("outfit").GetString() switch{"plate"=>Outfit.Plate,"trail"=>Outfit.Trail,_=>throw new ArgumentException("Unknown outfit.")};
        }
        if(op=="action")action=d.GetProperty("action").GetString() switch{"walk"=>CrossingAction.Walk,"dash"=>CrossingAction.Dash,"skill"=>CrossingAction.Skill,"wait"=>CrossingAction.Wait,_=>throw new ArgumentException("Unknown action.")};
        var before=State();bool pulse=session.Pulse;int health=session.Health,spent=session.SpentResolve,position=session.Position;
        bool accepted=op switch{"prepare"=>session.Prepare(approach,outfit),"begin"=>session.Begin(),"action"=>session.Act(action),"restart"=>Restart(),_=>false};
        sequence++;
        int damage=accepted&&op=="action"?health-session.Health:0,cost=accepted&&op=="action"?session.SpentResolve-spent:0,moved=accepted&&op=="action"?session.Position-position:0;
        string contact="none",pose=accepted?"ready":"rejected";
        if(accepted&&op=="action")
        {
            contact=damage>0?"hurt":pulse&&moved>0?"evaded":!pulse&&action==CrossingAction.Skill?"protected":"none";
            pose=action==CrossingAction.Skill?session.Approach.ToString().ToLowerInvariant():action.ToString().ToLowerInvariant();
            if(!session.Active)pose=session.Won?"won":"lost";
        }
        observation=Observe(op=="action"?action.ToString().ToLowerInvariant():op,accepted,pose,before,State(),damage,cost,moved,contact);return observation;
    }
    private bool Restart(){session=new Session();return true;}
}

public static class Program
{
    public static readonly JsonSerializerOptions Json=new(){WriteIndented=true};
    public static async Task<int> Main(string[] args)
    {
        try
        {
            if(args.Length!=5||args[0]!="--serve"||args[3]!="--seconds")throw new ArgumentException("Usage: --serve PORT WEBROOT --seconds 1..600");
            int port=int.Parse(args[1]),seconds=int.Parse(args[4]);if(port<1024||port>65535||seconds<1||seconds>600)throw new ArgumentException("Bound loopback port/lifetime required.");
            string web=Path.GetFullPath(args[2]);var room=new Room();var clock=Stopwatch.StartNew();
            using var listener=new HttpListener();listener.Prefixes.Add($"http://127.0.0.1:{port}/");listener.Start();Console.WriteLine($"READY http://127.0.0.1:{port}/");
            while(clock.Elapsed.TotalSeconds<seconds)
            {
                var pending=listener.GetContextAsync();if(await Task.WhenAny(pending,Task.Delay(Math.Max(1,(int)((seconds-clock.Elapsed.TotalSeconds)*1000))))!=pending)break;
                var c=await pending;byte[] body;string type="application/json";int status=200;
                try
                {
                    string path=c.Request.Url!.AbsolutePath;
                    if(c.Request.HttpMethod=="GET"&&new[]{"/","/index.html","/style.css","/app.js"}.Contains(path))
                    {string file=path=="/"?"index.html":path[1..];body=File.ReadAllBytes(Path.Combine(web,file));type=file.EndsWith(".css")?"text/css":file.EndsWith(".js")?"text/javascript":"text/html";}
                    else if(c.Request.HttpMethod=="POST"&&path=="/command")
                    {
                        if(c.Request.ContentLength64<0||c.Request.ContentLength64>1024)throw new ArgumentException("Bounded request required.");
                        if(c.Request.ContentType?.StartsWith("application/json",StringComparison.OrdinalIgnoreCase)!=true||c.Request.Headers["Origin"] is string origin&&origin!=$"http://127.0.0.1:{port}")throw new ArgumentException("Same-origin JSON required.");
                        using var doc=await JsonDocument.ParseAsync(c.Request.InputStream);body=Encoding.UTF8.GetBytes(JsonSerializer.Serialize(room.Execute(doc.RootElement),Json));
                    }
                    else if(c.Request.HttpMethod=="GET"&&path=="/state")body=Encoding.UTF8.GetBytes(JsonSerializer.Serialize(room.Snapshot(),Json));
                    else{status=404;body=Encoding.UTF8.GetBytes("{}");}
                }
                catch(Exception e)when(e is ArgumentException or JsonException or KeyNotFoundException or InvalidOperationException){status=400;body=Encoding.UTF8.GetBytes("{\"error\":\"Invalid command; state unchanged\"}");}
                c.Response.StatusCode=status;c.Response.ContentType=type;c.Response.Headers["Cache-Control"]="no-store";c.Response.ContentLength64=body.Length;await c.Response.OutputStream.WriteAsync(body);c.Response.Close();
            }
            listener.Stop();return 0;
        }
        catch(Exception e){Console.Error.WriteLine(e.Message);return 1;}
    }
}
