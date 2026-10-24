using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using NorthStar.Reputation;

namespace NorthStar.ReputationStudy;

// Original finite laboratory policy. No legacy defaults, factions or effect catalog imported.
public sealed class Room
{
    private sealed class Region
    {
        internal readonly string Id;
        internal int Standing=-1, Work;
        internal bool Custody, Returned, Service;
        internal Region(string id){Id=id;}
        internal object Snapshot()=>new {id=Id,standing=Standing,custody=Custody,returned=Returned,work=Work,service=Service};
    }
    private sealed record Receipt(string kind,string region,int sequence,int standing_before,int standing_after,int time_cost,int coin_cost);
    private static readonly HashSet<string> Commands=new(StringComparer.Ordinal){"visit quay","visit orchard","borrow","return","help","service","restart"};
    private Region[] regions={new("quay"),new("orchard")};
    private readonly List<Receipt> receipts=new();
    private string selected="quay",lastCommand="initial";
    private string last="Two independent counters begin at the experimental -1 setting. It describes this assay, not your character's worth. No tool has been borrowed or service supplied.";
    private int time=4,coins=3,sequence;
    private bool accepted=true;
    public object Snapshot()=>new {sequence,accepted,command=lastCommand,text=last,state=new {
        time,coins,region=selected,regions=regions.Select(r=>r.Snapshot()).ToArray(),receipts=receipts.ToArray(),
        scope="Original finite ephemeral laboratory consumer; no imported background/default policy, full legacy effects, persistent world, human validation or approved North Star canon."}};
    public object Execute(JsonElement document)
    {
        if(document.ValueKind!=JsonValueKind.Object)throw new ArgumentException("Object required.");
        var fields=document.EnumerateObject().ToArray();
        if(fields.Length!=1 || fields[0].Name!="command" || fields[0].Value.ValueKind!=JsonValueKind.String)throw new ArgumentException("Exact command object required.");
        string command=fields[0].Value.GetString()!;
        if(!Commands.Contains(command))throw new ArgumentException("Unknown exact command.");
        sequence++;lastCommand=command;accepted=false;
        if(command=="restart")
        {
            regions=new[]{new Region("quay"),new Region("orchard")};selected="quay";time=4;coins=3;receipts.Clear();accepted=true;
            last="A separate ephemeral trial begins. Earlier trial state is discarded; this is not a saved campaign.";
            return Snapshot();
        }
        if(command.StartsWith("visit ",StringComparison.Ordinal))
        {selected=command[6..];accepted=true;last="You inspect the "+selected+" counter. Looking spends no time and changes no standing, custody or service.";return Snapshot();}
        var region=regions.Single(r=>r.Id==selected);
        int before=region.Standing;
        switch(command)
        {
            case "borrow":
                if(region.Custody || region.Returned){last="This counter's one loan is already held or returned. No second tool is created.";break;}
                region.Custody=true;accepted=true;last="The counter hands over its one measuring tool. Custody is observed; borrowing itself earns no standing.";
                receipts.Add(new("borrow",selected,sequence,before,before,0,0));break;
            case "return":
                if(!region.Custody){last="No tool from this counter is in your custody. A promise or another counter's tool cannot be returned here.";break;}
                if(time<2){last="Two work periods are needed to inspect and return this held tool. Time is insufficient; the loan remains outstanding.";break;}
                int after=Standing.Add(before,2);
                time-=2;region.Custody=false;region.Returned=true;region.Standing=after;accepted=true;
                last="Actual inspection and return cost two periods. This counter's standing changes from "+before+" to "+after+". The other counter receives no event.";
                receipts.Add(new("return",selected,sequence,before,after,2,0));break;
            case "help":
                if(time<1){last="No work period remains. No help event or standing change occurs.";break;}
                int helped=Standing.Add(before,1);time--;region.Work++;region.Standing=helped;accepted=true;
                last="One minor task costs one period. Standing changes from "+before+" to "+helped+". At -1, repeated +1 tasks cannot cross the source threshold; time is still spent.";
                receipts.Add(new("help",selected,sequence,before,helped,1,0));break;
            case "service":
                if(region.Service){last="This counter's service was already supplied. No repeat receipt or debit occurs.";break;}
                if(region.Standing<1){last="This experimental counter requires positive standing for its service. Coins alone do not unlock it; no debit occurs.";break;}
                if(time<1 || coins<2){last="The service requires one period and two coins. Insufficient resources; no debit or service occurs.";break;}
                time--;coins-=2;region.Service=true;accepted=true;
                last="The counter actually calibrates your measure: one period and two coins paid. Its service is now supplied; the other counter remains independent.";
                receipts.Add(new("service",selected,sequence,before,before,1,2));break;
        }
        return Snapshot();
    }
}
