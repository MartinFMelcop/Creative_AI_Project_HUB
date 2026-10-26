using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using NorthStar.Domain;
using NorthStar.Forge;
using NorthStar.Loadout;

namespace NorthStar.Intake;

public sealed class Identity
{
    public string handle {get;}
    public string accent {get;}
    public string class_id {get;}
    public string background_id {get;}
    public IReadOnlyList<string?> slots {get;}
    public Identity(string handle,string accent,string classId,string backgroundId,IEnumerable<string?> slots)
    {this.handle=handle;this.accent=accent;class_id=classId;background_id=backgroundId;this.slots=Array.AsReadOnly(slots.ToArray());}
}

// The draft has no gameplay authority. Only explicit confirmation reaches the private owner.
public sealed class Room
{
    private readonly PreparedExpedition owner=new();
    private Identity draft=new("Wayfarer","copper","anchor","workshop",new string?[]{"brace",null,null,null});
    private Identity? identity;
    private long sequence;
    private int draftRevision=1;
    private int? reviewed;
    private bool pending=true;
    private string command="initial",text="Draft only. Review exact preparation and explicitly confirm before spending supplies.";
    private bool accepted=true;
    public object Snapshot()=>Observe(command,accepted,text);
    private object Observe(string cmd,bool ok,string message)=>new {
        sequence,command=cmd,accepted=ok,text=message,confirmed=identity!=null,pending,
        draft_revision=draftRevision,reviewed_revision=reviewed,draft,identity,
        state=owner.Snapshot(),threat=owner.Threat,required_position=owner.RequiredPosition,maximum_beats=owner.MaximumBeats
    };
    private static void Fields(JsonElement root,params string[] extra)
    {
        if(root.ValueKind!=JsonValueKind.Object)throw new ArgumentException("Object required.");
        string[] names=new[]{"command","revision"}.Concat(extra).ToArray();
        var fields=root.EnumerateObject().ToArray();
        if(fields.Length!=names.Length||fields.Select(x=>x.Name).Distinct(StringComparer.Ordinal).Count()!=fields.Length||fields.Any(x=>!names.Contains(x.Name,StringComparer.Ordinal)))throw new ArgumentException("Exact command fields required.");
    }
    private static string Text(JsonElement root,string key)=>root.GetProperty(key).ValueKind==JsonValueKind.String?root.GetProperty(key).GetString()!:throw new ArgumentException("String required.");
    private static int Number(JsonElement root,string key)=>root.GetProperty(key).TryGetInt32(out int value)?value:throw new ArgumentException("Integer required.");
    private bool Editable=>!owner.Active&&!owner.Complete;
    private bool Ready=>identity!=null&&!pending;
    public object Execute(JsonElement root)
    {
        if(root.ValueKind!=JsonValueKind.Object||!root.TryGetProperty("command",out _))throw new ArgumentException("Command required.");
        string cmd=Text(root,"command");
        string[] extras=cmd switch {
            "draft"=>new[]{"handle","accent","class_id","background_id","slots"},
            "confirm"=>new[]{"draft_revision"},"craft"=>new[]{"request_id","recipe_id"},
            "begin"=>new[]{"rig"},"slot"=>new[]{"slot"},"allocate"=>new[]{"axis","points"},
            "review" or "walk" or "wait"=>Array.Empty<string>(),_=>throw new ArgumentException("Unknown command.")};
        Fields(root,extras);
        if(Number(root,"revision")!=sequence)return Observe(cmd,false,"Stale intent refused. Read current facts before a fresh deliberate action.");
        bool ok=false;string message="Action unavailable; gameplay state unchanged.";
        if(cmd=="draft")
        {
            string handle=Text(root,"handle"),accent=Text(root,"accent"),classId=Text(root,"class_id"),background=Text(root,"background_id");
            if(handle.Length<1||handle.Length>24||handle.Any(c=>!(c>='A'&&c<='Z'||c>='a'&&c<='z'||c>='0'&&c<='9'||c=='_'||c=='-'))||accent is not ("copper" or "teal" or "violet"))throw new ArgumentException("Bounded original handle/accent required.");
            JsonElement values=root.GetProperty("slots");
            if(values.ValueKind!=JsonValueKind.Array||values.GetArrayLength()!=4)throw new ArgumentException("Exactly four slots required.");
            string?[] slots=values.EnumerateArray().Select(x=>x.ValueKind==JsonValueKind.Null?null:x.ValueKind==JsonValueKind.String?x.GetString():throw new ArgumentException("String/null slots required.")).ToArray();
            // Validate the complete candidate before replacing any draft or owner field.
            var candidate=new PreparedLoadout(classId,background,slots);
            PreparedExpedition.Catalog().Validate(candidate,owner.Progression.Level);
            if(Editable&&(identity==null||handle==identity.handle))
            {draft=new Identity(handle,accent,classId,background,slots);draftRevision=checked(draftRevision+1);reviewed=null;pending=true;ok=true;message="Draft changed only. Previous review expired; committed identity, supplies and progress remain unchanged.";}
            else message="Identity handle is fixed after confirmation; preparation edits are unavailable during/after an encounter.";
        }
        else if(cmd=="review")
        {
            if(Editable){reviewed=draftRevision;ok=true;message="Exact draft reviewed. Confirmation is separate; no owner, supplies or progress changed.";}
        }
        else if(cmd=="confirm")
        {
            int revision=Number(root,"draft_revision");
            if(Editable&&pending&&reviewed==draftRevision&&revision==draftRevision&&owner.Replace(draft.class_id,draft.background_id,draft.slots))
            {identity=new Identity(draft.handle,draft.accent,draft.class_id,draft.background_id,draft.slots);pending=false;ok=true;message="Reviewed identity and complete preparation confirmed atomically. No supply, health or reward grant.";}
            else message="Confirmation requires the current exact reviewed draft and an editable journey.";
        }
        else if(cmd=="craft")
        {
            string request=Text(root,"request_id"),recipe=Text(root,"recipe_id");
            if(Ready){var result=owner.Craft(request,recipe);ok=result.Applied;message=result.Reason;}
            else message="Confirm the pending preparation before spending materials.";
        }
        else if(cmd=="begin")
        {
            string rig=Text(root,"rig");
            Rig selected=rig switch {"plate"=>Rig.Plate,"trail"=>Rig.Trail,"unprepared"=>Rig.Unprepared,_=>throw new ArgumentException("Exact rig required.")};
            if(Ready){ok=owner.Begin(selected);message=owner.Last;}else message="Confirm the pending preparation before entry.";
        }
        else if(cmd=="allocate")
        {
            string axis=Text(root,"axis");int points=Number(root,"points");
            Allocation allocation=axis switch {"focus"=>Allocation.Focus,"vitality"=>Allocation.Vitality,_=>throw new ArgumentException("Exact allocation axis required.")};
            if(identity!=null){ok=owner.Allocate(allocation,points);message=owner.Last;}
        }
        else if(cmd=="slot")
        {int slot=Number(root,"slot");if(identity!=null){ok=owner.UseSlot(slot-1);message=owner.Last;}}
        else if(identity!=null)
        {ok=cmd=="walk"?owner.Walk():owner.Wait();message=owner.Last;}
        sequence=checked(sequence+1);command=cmd;accepted=ok;text=message;
        return Snapshot();
    }
}
