using System;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Nodes;
namespace NorthStar.AvailabilityHost;
public sealed class Room
{
    private JourneyOwner game=new();
    private long sequence;
    private object observation;
    public Room(){observation=Observe("initial",true);}
    private object Observe(string command,bool accepted)
    {
        // Preserve the workshop observation; composition adds its own actual journey facts.
        JsonObject state=JsonSerializer.SerializeToNode(game.WorkshopSnapshot(),Program.Json)!.AsObject();
        state["commands"]=JsonSerializer.SerializeToNode(game.Commands,Program.Json);
        state["journey"]=JsonSerializer.SerializeToNode(game.Snapshot(),Program.Json);
        return new {sequence,command,accepted,state};
    }
    public object Snapshot()=>observation;
    public object Execute(JsonElement document)
    {
        if(document.ValueKind!=JsonValueKind.Object)throw new ArgumentException("Object required");
        var fields=document.EnumerateObject().ToArray();
        if(fields.Length!=1||fields[0].Name!="command"||fields[0].Value.ValueKind!=JsonValueKind.String)throw new ArgumentException("Exactly one command required");
        string command=fields[0].Value.GetString()!;
        if(command is not ("promise" or "reserve" or "shape" or "collect" or "leave" or "wait" or "alone" or "withdraw" or "restart" or "route fast" or "route sheltered" or "walk" or "dash" or "skill" or "continue" or "deliver"))throw new ArgumentException("Unknown command");
        long next=checked(sequence+1);bool accepted;
        if(command=="restart"){game=new JourneyOwner();accepted=true;}else accepted=game.Execute(command);
        sequence=next;observation=Observe(command,accepted);return observation;
    }
}
