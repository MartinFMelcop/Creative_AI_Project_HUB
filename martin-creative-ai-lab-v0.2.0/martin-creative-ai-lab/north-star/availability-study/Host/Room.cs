using System;
using System.Linq;
using System.Text.Json;
using NorthStar.Availability;
namespace NorthStar.AvailabilityHost;
public sealed class Room
{
    private Session game=new();
    private long sequence;
    private object observation;
    public Room(){observation=Observe("initial",true);}
    private object Observe(string command,bool accepted)=>new {sequence,command,accepted,state=game.Snapshot()};
    public object Snapshot()=>observation;
    public object Execute(JsonElement document)
    {
        if(document.ValueKind!=JsonValueKind.Object)throw new ArgumentException("Object required");
        var fields=document.EnumerateObject().ToArray();
        if(fields.Length!=1||fields[0].Name!="command"||fields[0].Value.ValueKind!=JsonValueKind.String)throw new ArgumentException("Exactly one command required");
        string command=fields[0].Value.GetString()!;
        if(command is not ("promise" or "reserve" or "shape" or "collect" or "leave" or "wait" or "alone" or "withdraw" or "restart"))throw new ArgumentException("Unknown command");
        long next=checked(sequence+1);bool accepted;
        if(command=="restart"){game=new Session();accepted=true;}else accepted=game.Execute(command);
        sequence=next;observation=Observe(command,accepted);return observation;
    }
}
