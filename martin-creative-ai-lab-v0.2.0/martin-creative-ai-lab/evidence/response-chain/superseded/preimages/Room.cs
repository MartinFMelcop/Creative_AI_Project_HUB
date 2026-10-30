using System;
using System.Linq;
using System.Text.Json;
using NorthStar.Combat;
namespace NorthStar.CombatStudy;
public sealed class Room
{
    private Trial game=new();
    private readonly PassiveSlot preparation=new();
    private string profile="toxic";
    private bool preparing;
    private long sequence;
    private object observation;
    public Room(){observation=Observe("initial",true);}
    private object Observe(string command,bool accepted)=>new {
        sequence,command,accepted,phase=preparing?"preparation":game.Active?"active":"ended",
        preparation=new{profile,passive=PassiveIds.Name(preparation.Selection),armor=PassiveIds.Name(preparation.Armor)},
        state=preparing?null:game.Snapshot()
    };
    public object Snapshot()=>observation;
    public object Execute(JsonElement document)
    {
        if(document.ValueKind!=JsonValueKind.Object)throw new ArgumentException("Object required");
        var fields=document.EnumerateObject().ToArray();
        if(fields.Length!=1||fields[0].Name!="command"||fields[0].Value.ValueKind!=JsonValueKind.String)throw new ArgumentException("Exactly one command required");
        string command=fields[0].Value.GetString()!;
        bool prepare=command is "prepare toxic" or "prepare heated";
        bool restart=command is "restart toxic" or "restart heated";
        bool equip=command.StartsWith("equip ",StringComparison.Ordinal);
        Passive selected=Passive.None;Armor armor=Armor.Light;
        if(equip)
        {
            var words=command.Split(' ');
            if(words.Length!=3)throw new ArgumentException("Exact passive and armor required");
            selected=PassiveIds.Parse(words[1]);armor=PassiveIds.ParseArmor(words[2]);
        }
        else if(!prepare&&!restart&&command is not ("begin" or "strike" or "bash" or "guard" or "treat" or "cleanse" or "retreat"))throw new ArgumentException("Unknown command");
        long next=checked(sequence+1);bool accepted;
        if(prepare)
        {
            // Explicit new practice discards the prior ephemeral trial; it is not a live swap.
            profile=command[8..];preparation.Equip(Passive.None,Armor.Light,PassiveContext.Preparation);preparing=true;accepted=true;
        }
        else if(restart)
        {
            // Retained default consumer semantics: restart starts an active None trial immediately.
            profile=command[8..];preparation.Equip(Passive.None,Armor.Light,PassiveContext.Preparation);game=new Trial(profile);preparing=false;accepted=true;
        }
        else if(equip)
            accepted=preparation.Equip(selected,armor,preparing?PassiveContext.Preparation:game.Active?PassiveContext.Combat:PassiveContext.Ended);
        else if(command=="begin")
        {
            accepted=preparing;
            if(accepted){game=new Trial(profile,preparation.Selection,preparation.Armor);preparing=false;}
        }
        else accepted=!preparing&&game.Execute(command);
        sequence=next;observation=Observe(command,accepted);return observation;
    }
}
