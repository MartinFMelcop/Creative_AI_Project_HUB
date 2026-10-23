using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using NorthStar.Narrative;

namespace NorthStar.AuthoredScene;

// An observation has no methods capable of completing or advancing the scene.
public sealed class Observation
{
    public long sequence { get; }
    public string command { get; }
    public bool accepted { get; }
    public string text { get; }
    public object state { get; }
    public Observation(long sequence, string command, bool accepted, RequestExpedition owner)
    {
        this.sequence=sequence; this.command=command; this.accepted=accepted;
        text=owner.Last; state=owner.Snapshot();
    }
}

public sealed class Room
{
    private static readonly HashSet<string> Commands=new(StringComparer.Ordinal)
    {
        "open", "hear", "offer", "terms dusk", "terms open", "confirm", "defer",
        "decline", "withdraw", "work", "survey", "depart guided", "depart solo",
        "skill", "walk", "dash", "wait", "restart"
    };
    private RequestExpedition game=new();
    private long sequence;
    private Observation observation;
    public Room() { observation=new Observation(0,"initial",true,game); }
    public Observation Snapshot()=>observation;
    public Observation Execute(JsonElement document)
    {
        if(document.ValueKind!=JsonValueKind.Object)throw new ArgumentException("Object required.");
        var fields=document.EnumerateObject().ToArray();
        if(fields.Length!=1 || fields[0].Name!="command" || fields[0].Value.ValueKind!=JsonValueKind.String)
            throw new ArgumentException("Exactly one string command required.");
        string command=fields[0].Value.GetString()!;
        if(!Commands.Contains(command))throw new ArgumentException("Unknown exact command.");
        long next=checked(sequence+1);
        bool accepted;
        if(command=="restart") { game=new RequestExpedition(); accepted=true; }
        else accepted=game.Command(command);
        sequence=next;
        observation=new Observation(sequence,command,accepted,game);
        return observation;
    }
}
