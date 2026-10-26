using System;
using System.IO;
using System.Net;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;

namespace NorthStar.Intake;

public static class Program
{
    public static readonly JsonSerializerOptions Json=new(){WriteIndented=true};
    public static async Task<int> Main(string[] args)
    {
        try
        {
            if(args.Length!=5 || args[0]!="--serve" || args[3]!="--seconds")
                throw new ArgumentException("Usage: --serve PORT WEBROOT --seconds 1..600");
            int port=int.Parse(args[1]),seconds=int.Parse(args[4]);
            if(port<1024 || port>65535 || seconds<1 || seconds>600)
                throw new ArgumentException("Bound loopback port/lifetime required.");
            string web=Path.GetFullPath(args[2]);
            if(!Directory.Exists(web))throw new ArgumentException("Web root must exist.");
            var room=new Room();
            using var lifetime=new CancellationTokenSource(TimeSpan.FromSeconds(seconds));
            using var listener=new HttpListener();
            listener.Prefixes.Add($"http://127.0.0.1:{port}/");
            listener.Start();
            Console.WriteLine($"READY http://127.0.0.1:{port}/");
            try
            {
                while(!lifetime.IsCancellationRequested)
                {
                    var context=await listener.GetContextAsync().WaitAsync(lifetime.Token);
                    await Respond(context,room,web,port,lifetime.Token);
                }
            }
            catch(OperationCanceledException) when(lifetime.IsCancellationRequested) { }
            finally { listener.Stop(); }
            return 0;
        }
        catch(Exception error) when(error is ArgumentException or FormatException or OverflowException
                                   or IOException or UnauthorizedAccessException or JsonException or HttpListenerException)
        { Console.Error.WriteLine(error.Message); return 1; }
    }

    private static async Task Respond(HttpListenerContext context,Room room,string web,int port,CancellationToken lifetime)
    {
        byte[] body; string type="application/json"; int status=200;
        using var request=CancellationTokenSource.CreateLinkedTokenSource(lifetime);
        request.CancelAfter(TimeSpan.FromSeconds(3));
        try
        {
            string path=context.Request.Url!.AbsolutePath;
            if(context.Request.HttpMethod=="GET" && path=="/state")
                body=Encoding.UTF8.GetBytes(JsonSerializer.Serialize(room.Snapshot(),Json));
            else if(context.Request.HttpMethod=="GET" && path is "/" or "/index.html" or "/style.css" or "/app.js")
            {
                string file=path=="/"?"index.html":path[1..];
                body=await File.ReadAllBytesAsync(Path.Combine(web,file),request.Token);
                type=file.EndsWith(".css",StringComparison.Ordinal)?"text/css":file.EndsWith(".js",StringComparison.Ordinal)?"text/javascript":"text/html";
            }
            else if(context.Request.HttpMethod=="POST" && path=="/command")
            {
                if(context.Request.ContentLength64<0 || context.Request.ContentLength64>4096)
                    throw new ArgumentException("Bounded JSON required.");
                string media=(context.Request.ContentType??"").Split(';',2)[0].Trim();
                if(!media.Equals("application/json",StringComparison.OrdinalIgnoreCase)
                   || context.Request.Headers["Origin"] is string origin && origin!=$"http://127.0.0.1:{port}")
                    throw new ArgumentException("Same-origin JSON required.");
                using var document=await JsonDocument.ParseAsync(context.Request.InputStream,cancellationToken:request.Token);
                body=Encoding.UTF8.GetBytes(JsonSerializer.Serialize(room.Execute(document.RootElement),Json));
            }
            else { status=404; body=Encoding.UTF8.GetBytes("{}"); }
        }
        catch(Exception error) when(error is ArgumentException or JsonException or InvalidOperationException or OverflowException)
        { status=400; body=Encoding.UTF8.GetBytes("{\"error\":\"Invalid command; state unchanged\"}"); }
        catch(OperationCanceledException) when(!lifetime.IsCancellationRequested)
        { status=408; body=Encoding.UTF8.GetBytes("{\"error\":\"Request deadline; command not applied\"}"); }
        catch(FileNotFoundException)
        { status=404; body=Encoding.UTF8.GetBytes("{}"); }
        try
        {
            context.Response.StatusCode=status; context.Response.ContentType=type;
            context.Response.Headers["Cache-Control"]="no-store";
            context.Response.ContentLength64=body.Length;
            await context.Response.OutputStream.WriteAsync(body,lifetime);
        }
        catch(Exception error) when(error is IOException or HttpListenerException or ObjectDisposedException) { }
        finally { context.Response.Close(); }
    }
}
