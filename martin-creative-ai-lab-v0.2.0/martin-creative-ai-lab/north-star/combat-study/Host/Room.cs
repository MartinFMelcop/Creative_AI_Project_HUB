using System;
using System.Linq;
using System.Text.Json;
namespace NorthStar.CombatStudy;
public sealed class Room
{
    private Trial game=new();
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
        if(command is not ("strike" or "bash" or "guard" or "treat" or "cleanse" or "retreat" or "restart toxic" or "restart heated"))throw new ArgumentException("Unknown command");
        long next=checked(sequence+1);
        bool accepted;
        if(command.StartsWith("restart ",StringComparison.Ordinal)){game=new Trial(command[8..]);accepted=true;}
        else accepted=game.Execute(command);
        sequence=next;observation=Observe(command,accepted);return observation;
    }
}
