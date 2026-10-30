using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using NorthStar.Memory;
using NorthStar.Conditions;

namespace NorthStar.MemoryStudy;

// Original finite witness service; memory queries observe work, never execute it.
public sealed class Room
{
    private readonly FlagMemory flags=new(new[]{new FlagDefinition("helped",FlagScope.Npc,null),new FlagDefinition("support",FlagScope.Relation,null),new FlagDefinition("offer-closed",FlagScope.Relation,null)});
    private readonly RecentMemory events=new(new[]{new EventDefinition("demonstrated",3)});
    private readonly HashSet<string> delivered=new(StringComparer.Ordinal);
    private readonly List<object> history=new();
    private int sequence,parts=4,coins=2;
    private string text="Two independent benches, four parts and two coins. No help has been observed and no fitting exists.";
    private string command="initial";
    private bool accepted=true;
    private readonly string policy;
    private readonly CompiledCondition westRule,eastRule;
    private const string BaseExpression="Helped=true & Support=true & Recent=true";
    private const string QueryExpression="HasTag(local-request)=true & HasFlag(helped)=true & HasFlag(support)=true & HasRecentEvent(demonstrated)=true";
    private static readonly QueryReference[] QueryDeclarations={new(QueryKind.Tag,"local-request"),new(QueryKind.Flag,"helped"),new(QueryKind.Flag,"support"),new(QueryKind.Flag,"offer-closed"),new(QueryKind.RecentEvent,"demonstrated")};
    private string Expression(string bench)=>(policy=="single-offer"?QueryExpression:BaseExpression)+(policy=="ordered"&&bench=="east"?" & OtherDelivered=true":"")+(policy=="single-offer"?" & HasFlag(offer-closed)=false":"");
    public Room(string policy="independent")
    {
        if(policy is not ("independent" or "ordered" or "single-offer"))throw new ArgumentException("Exact service policy required.");
        this.policy=policy;
        if(policy=="ordered")text="Two named benches, four parts and two coins. The east commission also requires actual west delivery; a condition never supplies a fitting.";
        if(policy=="single-offer")text="Each named bench has one offer. An accepted withdrawal permanently closes only that bench. Paid demonstration can renew support, not reopen its offer.";
        var symbols=new Dictionary<string,ConditionType>(StringComparer.Ordinal){{"Helped",ConditionType.Boolean},{"Support",ConditionType.Boolean},{"Recent",ConditionType.Boolean},{"OtherDelivered",ConditionType.Boolean},{"Coins",ConditionType.Integer}};
        westRule=policy=="single-offer"?ConditionCompiler.Compile(Expression("west"),symbols,"west",QueryDeclarations):ConditionCompiler.Compile(Expression("west"),symbols);eastRule=policy=="single-offer"?ConditionCompiler.Compile(Expression("east"),symbols,"east",QueryDeclarations):ConditionCompiler.Compile(Expression("east"),symbols);
    }
    private ConditionResult Condition(string bench)=>(bench=="west"?westRule:eastRule).Evaluate(new Dictionary<string,ConditionValue>(StringComparer.Ordinal){
        {"Helped",ConditionValue.Boolean(Helped(bench))},{"Support",ConditionValue.Boolean(Supported(bench))},{"Recent",ConditionValue.Boolean(Recent(bench))},
        {"OtherDelivered",ConditionValue.Boolean(delivered.Contains(bench=="west"?"east":"west"))},{"Coins",ConditionValue.Integer(coins)}},QueryFacts(bench));
    private QuerySnapshot QueryFacts(string bench)=>new(bench,new[]{
        new QueryObservation(new QueryReference(QueryKind.Tag,"local-request"),bench is "west" or "east"),
        new QueryObservation(new QueryReference(QueryKind.Flag,"helped"),Helped(bench)),
        new QueryObservation(new QueryReference(QueryKind.Flag,"support"),Supported(bench)),
        new QueryObservation(new QueryReference(QueryKind.Flag,"offer-closed"),OfferClosed(bench)),
        new QueryObservation(new QueryReference(QueryKind.RecentEvent,"demonstrated"),Recent(bench))});
    private bool OfferClosed(string bench)=>policy=="single-offer"&&flags.Exact("offer-closed",FlagScope.Relation,bench);
    private bool Helped(string bench)=>flags.Exact("helped",FlagScope.Npc,bench);
    private bool Supported(string bench)=>flags.Exact("support",FlagScope.Relation,bench);
    private bool Recent(string bench)=>events.Exact("demonstrated",bench);
    private bool Eligible(string bench)=>Helped(bench)&&Supported(bench)&&Recent(bench)&&coins>0&&!delivered.Contains(bench)&&Condition(bench).Satisfied;
    private void Tick(){flags.Tick();events.Tick();if(flags.Turn!=events.Turn)throw new InvalidOperationException("Private clocks diverged.");}
    private object Observe(string cmd,bool ok,string message)=>new {
        sequence,command=cmd,accepted=ok,text=message,turn=flags.Turn,parts,coins,policy,
        complete=delivered.Count==2,
        benches=new[]{"west","east"}.Select(id=>new{id,helped=Helped(id),support=Supported(id),recent=Recent(id),offer_closed=OfferClosed(id),expires=events.ExactExpiry("demonstrated",id),eligible=Eligible(id),delivered=delivered.Contains(id),condition_expression=Expression(id),condition_satisfied=Condition(id).Satisfied,condition_complete=Condition(id).Complete}).ToArray(),
        history=history.ToArray()
    };
    public object Snapshot()=>Observe(command,accepted,text);
    public object Execute(JsonElement root)
    {
        if(root.ValueKind!=JsonValueKind.Object)throw new ArgumentException("Object required.");
        var properties=root.EnumerateObject().ToArray();
        if(properties.Select(p=>p.Name).Distinct(StringComparer.Ordinal).Count()!=properties.Length||!root.TryGetProperty("command",out var cmdValue)||cmdValue.ValueKind!=JsonValueKind.String)throw new ArgumentException("Exact unique command fields required.");
        string cmd=cmdValue.GetString()!;
        if(cmd is not ("help" or "demonstrate" or "serve" or "decline" or "wait"))throw new ArgumentException("Unknown command.");
        string[] names=cmd=="wait"?new[]{"command","revision"}:new[]{"command","revision","bench"};
        if(properties.Length!=names.Length||properties.Any(p=>!names.Contains(p.Name,StringComparer.Ordinal)))throw new ArgumentException("Exact fields required.");
        if(!root.GetProperty("revision").TryGetInt32(out int revision))throw new ArgumentException("Integer revision required.");
        string? bench=null;
        if(cmd!="wait")
        {var b=root.GetProperty("bench");if(b.ValueKind!=JsonValueKind.String||b.GetString() is not ("west" or "east"))throw new ArgumentException("Actual named bench required.");bench=b.GetString()!;}
        if(revision!=sequence)return Observe(cmd,false,"Old intent refused. Read current facts before deliberately acting again.");
        int next=checked(sequence+1);bool ok=false;string message="No action occurred.";
        if(history.Count>=1024)return Observe(cmd,false,"Bounded session capacity reached; no action occurred.");
        if(cmd=="help"||cmd=="demonstrate")
        {
            if(delivered.Contains(bench!))message="That bench already supplied its one fitting. No new service is available.";
            else if(cmd=="help"&&Helped(bench!))message="Past help remains observed. A new paid demonstration is separate from repeating that work.";
            else if(cmd=="demonstrate"&&!Helped(bench!))message="No past help exists at that bench; a demonstration cannot invent it.";
            else if(parts<1)message="No spare part remains; a promise cannot supply a demonstration.";
            else
            {
                // Gate first, then pay one actual action, then write the newly observed fact.
                Tick();parts--;flags.Set("helped",true,bench,FlagScope.Npc);flags.Set("support",true,bench,FlagScope.Relation);events.Push("demonstrated",bench);
                ok=true;message=cmd=="help"?"One part and one action spent on actual local help. This bench observed the demonstration; its current window expires at turn "+(flags.Turn+3)+".":"One part and one action spent on a fresh local demonstration. Current support explicitly renewed; past help was not replayed.";
            }
        }
        else if(cmd=="serve")
        {
            if(delivered.Contains(bench!))message="That fitting already exists. A repeat cannot mint another.";
            else if(!Eligible(bench!))message="No current service: this exact bench requires observed help, current support, its recent demonstration, one actual coin and the displayed authored condition. No cost paid.";
            else {Tick();coins--;delivered.Add(bench!);ok=true;message="One coin and one action spent. The "+bench+" bench actually supplied its one fitting. Later expiry cannot erase this output.";}
        }
        else if(cmd=="decline")
        {
            if(OfferClosed(bench!))message="That named offer is already closed. No new withdrawal, work or output occurred.";
            else if(!Supported(bench!)&&!Recent(bench!))message="No current support or demonstration to withdraw; past facts remain unchanged.";
            else {flags.Clear("support",bench,FlagScope.Relation);events.Clear("demonstrated",bench);if(policy=="single-offer")flags.Set("offer-closed",true,bench,FlagScope.Relation);ok=true;message="Current local support withdrawn without a turn. Past observed help and any actual fitting remain true; a fresh paid demonstration is required to reopen an unfinished opportunity.";if(policy=="single-offer")message="This named offer permanently closed without a turn. Past help and actual fitting remain true. A fresh paid demonstration may renew support, but cannot reopen the offer.";}
        }
        else {Tick();ok=true;message="One deliberately chosen wait action elapsed. No work, fitting, recognition or return was created.";}
        sequence=next;command=cmd;accepted=ok;text=message;
        if(ok)history.Add(new{sequence,command=cmd,bench,turn=flags.Turn,parts,coins,fittings=delivered.Count});
        return Snapshot();
    }
}
