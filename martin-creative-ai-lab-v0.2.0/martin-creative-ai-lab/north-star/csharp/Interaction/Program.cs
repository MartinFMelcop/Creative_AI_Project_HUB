using System.Collections.Generic;
using System;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using System.Diagnostics;
using System.Net;
using System.Text;
using System.Text.Json;
using NorthStar.InputTiming;
namespace NorthStar.Interaction;
public static class Program
{
    public static readonly JsonSerializerOptions Json=new(){WriteIndented=true};
    public static object Demo()
    {
        static void Hold(WorkRoom r,long duration){r.Input(false);r.Advance(r.Now,false,true);r.Input(true);long end=r.Now+duration;while(r.Now<end)r.Advance(Math.Min(end,r.Now+100),false,true);r.Input(false);}
        var completed=new WorkRoom();completed.Select("ground");Hold(completed,1500);object afterGround=completed.Snapshot();completed.Select("catch-a");Hold(completed,1000);completed.Select("catch-b");Hold(completed,1000);completed.Exit();
        var cancelled=new WorkRoom();cancelled.Select("ground");cancelled.Input(true);cancelled.Advance(500,false,true);cancelled.Input(false);
        var hit=new WorkRoom();hit.Select("ground");hit.Input(true);hit.Advance(500,false,true);hit.Advance(1000,false,true);hit.Advance(1500,true,true);
        var timeout=new WorkRoom();timeout.Select("ground");timeout.Input(true);timeout.Advance(2000);
        var paused=new WorkRoom();paused.Input(true);paused.Advance(400,false,true);paused.Pause();paused.Advance(9000,false,true);paused.Resume();paused.Advance(9500,false,true);
        var optional=new WorkRoom();Hold(optional,1000);optional.Select("catch-b");Hold(optional,1000);optional.Exit();
        return new {schema_version=1,kind="actual_csharp_timed_work",grounded_not_goal=afterGround,completed=completed.Snapshot(),release=cancelled.Snapshot(),same_boundary_hit=hit.Snapshot(),missing_input=timeout.Snapshot(),held_resume=paused.Snapshot(),optional_grounding=optional.Snapshot()};
    }
    public static async Task<int> Main(string[] args)
    {
        try
        {
            if(args.Length==2&&args[0]=="--demo"){File.WriteAllText(args[1],JsonSerializer.Serialize(Demo(),Json)+"\n");return 0;}
            if(args.Length!=5||args[0]!="--serve"||args[3]!="--seconds")throw new ArgumentException("Usage: --demo REPORT | --serve PORT WEBROOT --seconds 1..600");
            int port=int.Parse(args[1]),seconds=int.Parse(args[4]);if(port<1024||port>65535||seconds<1||seconds>600)throw new ArgumentException("Bound loopback port/lifetime required.");
            string web=Path.GetFullPath(args[2]);var room=new WorkRoom();var clock=Stopwatch.StartNew();
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
                        using var doc=await JsonDocument.ParseAsync(c.Request.InputStream);var d=doc.RootElement;string op=d.GetProperty("op").GetString()??"";
                        if(d.EnumerateObject().Select(x=>x.Name).Distinct().Count()!=d.EnumerateObject().Count()||d.EnumerateObject().Any(x=>!new[]{"op","held","target"}.Contains(x.Name)))throw new ArgumentException("Unknown/repeated input field.");
                        if(!new[]{"heartbeat","pause","resume","select","hit","exit","restart"}.Contains(op))throw new ArgumentException("Unknown command.");
                        bool held=op=="heartbeat"&&d.GetProperty("held").GetBoolean();string target=op=="select"?d.GetProperty("target").GetString()??"":"";
                        if(op=="select"&&!new[]{"catch-a","ground","catch-b"}.Contains(target))throw new ArgumentException("Unknown station.");
                        long now=clock.ElapsedMilliseconds;room.Advance(now,op=="hit",op=="heartbeat");
                        switch(op){case "heartbeat":room.Input(held);break;case "pause":room.Pause("focus/pause");break;case "resume":room.Resume();break;case "select":room.Select(target);break;case "exit":room.Exit();break;case "restart":room=new WorkRoom();room.Advance(now,false,true);break;}
                        body=Encoding.UTF8.GetBytes(JsonSerializer.Serialize(room.Snapshot(),Json));
                    }
                    else if(c.Request.HttpMethod=="GET"&&path=="/state"){room.Advance(clock.ElapsedMilliseconds);body=Encoding.UTF8.GetBytes(JsonSerializer.Serialize(room.Snapshot(),Json));}
                    else {status=404;body=Encoding.UTF8.GetBytes("{}");}
                }
                catch(Exception e)when(e is ArgumentException or JsonException or KeyNotFoundException or InvalidOperationException){status=400;body=Encoding.UTF8.GetBytes("{\"error\":\"Invalid command; no success claim\"}");}
                c.Response.StatusCode=status;c.Response.ContentType=type;c.Response.Headers["Cache-Control"]="no-store";c.Response.ContentLength64=body.Length;await c.Response.OutputStream.WriteAsync(body);c.Response.Close();
            }
            listener.Stop();return 0;
        }
        catch(Exception e){Console.Error.WriteLine(e.Message);return 1;}
    }
}
