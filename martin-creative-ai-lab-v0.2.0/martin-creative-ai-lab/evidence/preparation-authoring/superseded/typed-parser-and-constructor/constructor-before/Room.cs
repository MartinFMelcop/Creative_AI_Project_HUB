using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using IntakeRoom=NorthStar.Intake.Room;
using MemoryRoom=NorthStar.MemoryStudy.Room;
using NorthStar.FieldPresentation;
using NorthStar.Preparation;
using SampleCase=NorthStar.FieldSampling.SampleCase;
using SampleFacts=NorthStar.FieldSampling.Facts;

namespace NorthStar.FieldJourney;

// One outer owner coordinates actual unchanged child owners and finite fitting use.
public sealed class Room
{
    private readonly IntakeRoom intake;
    private readonly Book preparationBook;
    private string? draftCardId,confirmedCardId;
    private readonly SampleCase sampleCase=new();
    private readonly MemoryRoom memory;
    public Room(string servicePolicy="independent",Book? book=null)
    {preparationBook=book??PackLoader.Default();memory=new MemoryRoom(servicePolicy);intake=new IntakeRoom();}
    private readonly Dictionary<string,string> assembled=new(StringComparer.Ordinal);
    private int sequence;
    private Response response=Projector.Initial();
    private bool workshopClosed;
    private string command="initial";
    private bool accepted=true;
    private string text="Propose, review and confirm one person before paid preparation. Acquired fittings and field materials are separate finite supplies.";
    private static JsonElement Json(object value)=>JsonSerializer.SerializeToElement(value);
    private JsonElement Intake()=>Json(intake.Snapshot());
    private JsonElement Memory()=>Json(memory.Snapshot());
    private static bool Flag(JsonElement element,string name)=>element.GetProperty(name).GetBoolean();
    private bool Acquired(string bench)=>Memory().GetProperty("benches").EnumerateArray().Single(b=>b.GetProperty("id").GetString()==bench).GetProperty("delivered").GetBoolean();
    private object Observe(string cmd,bool ok,string message)=>new {
        sequence,command=cmd,accepted=ok,text=message,workshop_closed=workshopClosed,
        sample_case=sampleCase.Snapshot(SamplingFacts(Intake())),
        preparation_book=PreparationBook(),
        intake=intake.Snapshot(),memory=memory.Snapshot(),encounter_view=Projector.Observe(Facts(Intake()),response),
        fittings=new[]{"west","east"}.Select(bench=>new {bench,acquired=Acquired(bench),spent=assembled.ContainsKey(bench),available=Acquired(bench)&&!assembled.ContainsKey(bench),rig=assembled.TryGetValue(bench,out var rig)?rig:null}).ToArray(),
        assembly_receipts=assembled.Select(pair=>new {bench=pair.Key,rig=pair.Value,request_id="fitting_"+pair.Key}).ToArray()
    };
    private object PreparationBook()
    {
        var card=Intake();var state=card.GetProperty("state");bool editable=!Flag(state,"active")&&!Flag(state,"complete");int level=state.GetProperty("level").GetInt32();
        return new {sha256=preparationBook.Sha256,draft_card_id=draftCardId,confirmed_card_id=confirmedCardId,cards=preparationBook.Cards.Select(c=>new {id=c.Id,title=c.Title,description=c.Description,class_id=c.Proposal.ClassId,background_id=c.Proposal.BackgroundId,slots=c.Proposal.Slots,minimum_level=c.MinimumLevel,recommended_rig=c.RecommendedRig,eligible=editable&&preparationBook.Eligible(c,level)}).ToArray()};
    }
    private static SampleFacts SamplingFacts(JsonElement card)
    {
        var e=card.GetProperty("state");
        return new SampleFacts(Flag(card,"confirmed"),e.GetProperty("attempts").GetInt32(),e.GetProperty("stage").GetInt32(),e.GetProperty("position").GetInt32(),e.GetProperty("beat").GetInt32(),e.GetProperty("health").GetInt32(),Flag(e,"active"),Flag(e,"won"),Flag(e,"complete"));
    }
    private static Facts Facts(JsonElement card)
    {
        var state=card.GetProperty("state");var id=card.GetProperty("identity");bool confirmed=Flag(card,"confirmed");
        return new Facts(confirmed,confirmed?id.GetProperty("handle").GetString():null,confirmed?id.GetProperty("accent").GetString():null,confirmed?id.GetProperty("class_id").GetString():null,
            state.GetProperty("rig").GetString()!.ToLowerInvariant(),state.GetProperty("attempts").GetInt32(),state.GetProperty("stage").GetInt32(),Flag(state,"active"),Flag(state,"won"),Flag(state,"complete"),state.GetProperty("beat").GetInt32(),state.GetProperty("position").GetInt32(),state.GetProperty("health").GetInt32(),state.GetProperty("resolve").GetInt32(),card.GetProperty("threat").GetString()!);
    }
    private static string ActionKind(string cmd,JsonElement root,JsonElement before)
    {
        if(cmd=="sample")return "wait";
        if(cmd!="slot")return cmd;
        int slot=Number(root,"slot")-1;var slots=before.GetProperty("state").GetProperty("slots");
        return slot>=0&&slot<slots.GetArrayLength()&&slots[slot].ValueKind==JsonValueKind.String&&slots[slot].GetString()=="dash"?"dash":"skill";
    }
    public object Snapshot()=>Observe(command,accepted,text);
    private static string Text(JsonElement root,string key)=>root.GetProperty(key).ValueKind==JsonValueKind.String?root.GetProperty(key).GetString()!:throw new ArgumentException("Exact string required.");
    private static int Number(JsonElement root,string key)=>root.GetProperty(key).TryGetInt32(out int result)?result:throw new ArgumentException("Exact integer required.");
    private static string Bench(JsonElement root){string result=Text(root,"bench");return result is "west" or "east"?result:throw new ArgumentException("Actual named bench required.");}
    private static string Rig(JsonElement root,bool allowUnprepared){string result=Text(root,"rig");return result is "plate" or "trail"||allowUnprepared&&result=="unprepared"?result:throw new ArgumentException("Exact rig required.");}
    private static void Fields(JsonElement root,string[] extra)
    {
        if(root.ValueKind!=JsonValueKind.Object)throw new ArgumentException("Object required.");
        var properties=root.EnumerateObject().ToArray();var expected=new[]{"command","revision"}.Concat(extra).ToArray();
        if(properties.Length!=expected.Length||properties.Select(p=>p.Name).Distinct(StringComparer.Ordinal).Count()!=properties.Length||properties.Any(p=>!expected.Contains(p.Name,StringComparer.Ordinal)))throw new ArgumentException("Exact unique command fields required.");
    }
    private JsonElement Child(JsonElement input,string childCommand,bool useMemory,params string[] forwarded)
    {
        var values=new Dictionary<string,object?>{{"command",childCommand},{"revision",(useMemory?Memory():Intake()).GetProperty("sequence")}};
        foreach(string name in forwarded)values.Add(name,input.GetProperty(name));
        return Json(useMemory?memory.Execute(Json(values)):intake.Execute(Json(values)));
    }
    public object Execute(JsonElement root)
    {
        if(root.ValueKind!=JsonValueKind.Object||!root.TryGetProperty("command",out _))throw new ArgumentException("Command required.");
        string cmd=Text(root,"command");
        string[] extras=cmd switch {
            "draft"=>new[]{"handle","accent","class_id","background_id","slots"},
            "confirm"=>new[]{"draft_revision"},"allocate"=>new[]{"axis","points"},"slot"=>new[]{"slot"},
            "help" or "demonstrate" or "serve" or "decline"=>new[]{"bench"},"craft"=>new[]{"bench","rig"},"begin"=>new[]{"rig"},
            "sample"=>new[]{"site"},"propose-card"=>new[]{"card_id"},
            "review" or "walk" or "wait" or "wait-window"=>Array.Empty<string>(),_=>throw new ArgumentException("Unknown command.")};
        Fields(root,extras);
        // Parse every adapter-owned field before any child can change state.
        int revision=Number(root,"revision");
        string? bench=cmd is "help" or "demonstrate" or "serve" or "decline" or "craft"?Bench(root):null;
        string? rig=cmd is "craft" or "begin"?Rig(root,cmd=="begin"):null;
        string? site=cmd=="sample"?Text(root,"site"):null;
        if(site!=null)SampleCase.ValidateSite(site);
        Card? proposed=cmd=="propose-card"?preparationBook.Find(Text(root,"card_id")):null;
        if(revision!=sequence)return Observe(cmd,false,"Old outer intent refused. Read current facts before deliberately acting again.");
        int next=checked(sequence+1);bool ok=false;string message;
        var current=Intake();bool confirmed=Flag(current,"confirmed"),ready=confirmed&&!Flag(current,"pending");
        if(cmd=="propose-card")
        {
            var e=current.GetProperty("state");
            if(Flag(e,"active")||Flag(e,"complete")||!preparationBook.Eligible(proposed!,e.GetProperty("level").GetInt32()))message="That exact card is unavailable at the actual earned level or current encounter. No proposal, permission or resource was granted.";
            else
            {
                var draft=current.GetProperty("draft");
                var request=Json(new {command="draft",revision=current.GetProperty("sequence"),handle=draft.GetProperty("handle"),accent=draft.GetProperty("accent"),class_id=proposed!.Proposal.ClassId,background_id=proposed.Proposal.BackgroundId,slots=proposed.Proposal.Slots});
                var result=Json(intake.Execute(request));ok=Flag(result,"accepted");message=result.GetProperty("text").GetString()!;
                if(ok){draftCardId=proposed.Id;message="Authored card proposed as a draft only. Review and confirm separately; its rig is guidance, not equipment or a grant.";}
            }
        }
        else if(cmd is "help" or "demonstrate" or "serve" or "decline" or "wait-window")
        {
            if(workshopClosed)message="Departure closed preparation. The workshop observation is historical; no remote work, fitting or return was observed.";
            else if(!(cmd=="decline"?confirmed:ready))message="Confirm the current whole identity before paid workshop preparation. A draft supplies no work, witness or goods.";
            else {var result=Child(root,cmd=="wait-window"?"wait":cmd,true,extras);ok=Flag(result,"accepted");message=result.GetProperty("text").GetString()!;}
        }
        else if(cmd=="craft")
        {
            if(workshopClosed)message="Departure closed assembly. Existing acquired fittings and supplies are not refunded or converted remotely.";
            else if(!ready)message="Confirm the current whole identity before assembly; pending proposals cannot spend materials or fittings.";
            else if(!Acquired(bench!))message="That exact fitting has not been acquired. Current witness eligibility or a promise is not a crafting component.";
            else if(assembled.ContainsKey(bench!))message="That acquired fitting was already assembled. It cannot fund a second rig.";
            else
            {
                // Only a newly applied real craft consumes the separate acquired fitting.
                // Both children and this ledger are private; there is no await/publication between them.
                var request=Json(new {command="craft",revision=current.GetProperty("sequence"),request_id="fitting_"+bench,recipe_id=rig+"_rig"});
                var result=Json(intake.Execute(request));ok=Flag(result,"accepted");
                if(ok){assembled.Add(bench!,rig!);message="Actual "+rig+" assembly spent 2 fiber, 1 binder and the acquired "+bench+" fitting. Its service receipt remains historical acquisition, not another available component.";}
                else message=result.GetProperty("text").GetString()!;
            }
        }
        else if(cmd=="sample")
        {
            if(!sampleCase.CanCollect(site!,SamplingFacts(current)))message="Sampling requires the one unused case and your actual active position at that exact site. Nothing was collected or spent.";
            else
            {
                var result=Child(root,"wait",false);ok=Flag(result,"accepted");
                if(ok)
                {
                    sampleCase.Collect(site!,SamplingFacts(current),SamplingFacts(Intake()));
                    message="The actual Wait resolved its threat and beat before collection. The one case is now spent; "+(Json(sampleCase.Snapshot(SamplingFacts(Intake()))).GetProperty("acquired").GetBoolean()?"surviving acquisition is carried, not returned or delivered.":"the paid encounter failed before acquisition; no sample was obtained.");
                }
                else message=result.GetProperty("text").GetString()!;
            }
        }
        else
        {
            var result=Child(root,cmd,false,extras);ok=Flag(result,"accepted");message=result.GetProperty("text").GetString()!;
            if(cmd=="begin"&&ok){workshopClosed=true;message+=" Preparation is now closed; later encounter beats do not advance the separate historical workshop clock.";}
        }
        if(ok&&cmd=="draft")draftCardId=null;
        if(ok&&cmd=="confirm")confirmedCardId=draftCardId;
        if(ok)sampleCase.ObserveAcceptedTransition(SamplingFacts(current),SamplingFacts(Intake()));
        // The projector describes the actual delegated draft; the outer receipt retains propose-card.
        response=Projector.Transition(Facts(current),Facts(Intake()),cmd=="propose-card"?"draft":cmd,ok,ActionKind(cmd,root,current),response.event_sequence);
        sequence=next;command=cmd;accepted=ok;text=message;
        return Snapshot();
    }
}
