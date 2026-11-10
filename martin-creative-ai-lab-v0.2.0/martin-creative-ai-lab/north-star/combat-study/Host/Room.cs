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
    private bool preparing,responses,controls,initiative;
    private string tempo="heavy";
    private long sequence;
    private object observation;
    private bool earnedStarted,earnedMode,unlocked;
    private long attempt;
    private object? receipt;
    public Room(){observation=Observe("initial",true);}
    private object Observe(string command,bool accepted)
    {
        if(earnedStarted)return new {
            sequence,command,accepted,phase=preparing?"preparation":game.Active?"active":"ended",
            preparation=new{profile,responses,controls,initiative,tempo,passive=PassiveIds.Name(preparation.Selection),armor=PassiveIds.Name(preparation.Armor)},
            state=preparing?null:game.Snapshot(),earned=new {mode=earnedMode,unlocked,attempt,receipt}
        };
        return new {
            sequence,command,accepted,phase=preparing?"preparation":game.Active?"active":"ended",
            preparation=new{profile,responses,controls,initiative,tempo,passive=PassiveIds.Name(preparation.Selection),armor=PassiveIds.Name(preparation.Armor)},
            state=preparing?null:game.Snapshot()
        };
    }
    public object Snapshot()=>observation;
    private static bool Action(string command)=>command is "strike" or "bash" or "guard" or "treat" or "cleanse" or "retreat" or "commit" or "release" or "break-ward" or "light-control" or "hard-control";
    private static string Parse(JsonElement document,bool allowReview,out long? review)
    {
        review=null;
        if(document.ValueKind!=JsonValueKind.Object)throw new ArgumentException("Object required");
        var fields=document.EnumerateObject().ToArray();
        if(fields.Length!=1&&(!allowReview||fields.Length!=2))throw new ArgumentException("Exact command envelope required");
        var commands=fields.Where(p=>p.Name=="command").ToArray();
        if(commands.Length!=1||commands[0].Value.ValueKind!=JsonValueKind.String)throw new ArgumentException("Exactly one command string required");
        if(fields.Length==2)
        {
            var revisions=fields.Where(p=>p.Name=="reviewed_sequence").ToArray();
            if(revisions.Length!=1||revisions[0].Value.ValueKind!=JsonValueKind.Number||!revisions[0].Value.TryGetInt64(out long number)||number<0)throw new ArgumentException("Exact nonnegative reviewed sequence required");
            review=number;
        }
        return commands[0].Value.GetString()!;
    }
    public object Forecast(JsonElement document)
    {
        string command=Parse(document,false,out _);
        if(preparing||!Action(command))throw new ArgumentException("Inspect one encounter action after Begin.");
        return new {sequence,forecast=game.Forecast(command)};
    }
    public object Execute(JsonElement document)
    {
        string command=Parse(document,true,out long? review);
        // A review binds context, not permission. Existing direct commands retain their contract.
        if(review.HasValue&&(review.Value!=sequence||preparing||!game.Active||!Action(command)))
            throw new ArgumentException("Inspected context changed. Read and inspect again before confirming.");
        bool earnedPrepare=command is "prepare earned toxic" or "prepare earned heated";
        bool responsePrepare=command is "prepare responses toxic" or "prepare responses heated";
        bool controlPrepare=command is "prepare controls toxic" or "prepare controls heated";
        bool initiativePrepare=command is "prepare initiative toxic" or "prepare initiative heated";
        bool tempoSelect=command is "tempo heavy" or "tempo quick";
        bool prepare=earnedPrepare||initiativePrepare||controlPrepare||responsePrepare||command is "prepare toxic" or "prepare heated";
        bool restart=command is "restart toxic" or "restart heated";
        bool equip=command.StartsWith("equip ",StringComparison.Ordinal);
        Passive selected=Passive.None;Armor armor=Armor.Light;
        if(equip)
        {
            var words=command.Split(' ');
            if(words.Length!=3)throw new ArgumentException("Exact passive and armor required");
            selected=PassiveIds.Parse(words[1]);armor=PassiveIds.ParseArmor(words[2]);
        }
        else if(!tempoSelect&&!prepare&&!restart&&command is not ("begin" or "strike" or "bash" or "guard" or "treat" or "cleanse" or "retreat" or "commit" or "release" or "break-ward" or "light-control" or "hard-control"))throw new ArgumentException("Unknown command");
        // A paid earned encounter cannot be replaced; preparation drafts are not active encounters.
        if((prepare||restart)&&!preparing&&game.Active&&
            (earnedMode||earnedPrepare&&sequence!=0))
            throw new ArgumentException("Finish or withdraw from the actual encounter before preparing another practice.");
        if(equip&&earnedMode&&!unlocked&&selected!=Passive.None)
            throw new ArgumentException("Clear an actual earned practice with None before selecting a passive.");
        long next=checked(sequence+1);bool accepted;
        bool activeBefore=!preparing&&game.Active;
        if(prepare)
        {
            // Explicit new practice discards the prior ephemeral trial; it is not a live swap.
            earnedMode=earnedPrepare;if(earnedPrepare)earnedStarted=true;
            initiative=initiativePrepare;tempo="heavy";responses=responsePrepare;controls=controlPrepare;profile=earnedPrepare?command[15..]:initiativePrepare?command[19..]:controlPrepare?command[17..]:responsePrepare?command[18..]:command[8..];preparation.Equip(Passive.None,Armor.Light,PassiveContext.Preparation);preparing=true;accepted=true;
        }
        else if(restart)
        {
            // Retained default consumer semantics: restart starts an active None trial immediately.
            earnedMode=false;initiative=false;tempo="heavy";responses=false;controls=false;profile=command[8..];preparation.Equip(Passive.None,Armor.Light,PassiveContext.Preparation);game=new Trial(profile);preparing=false;accepted=true;
        }
        else if(tempoSelect)
        {
            accepted=preparing&&initiative;if(accepted)tempo=command[6..];
        }
        else if(equip)
            accepted=preparation.Equip(selected,armor,preparing?PassiveContext.Preparation:game.Active?PassiveContext.Combat:PassiveContext.Ended);
        else if(command=="begin")
        {
            accepted=preparing;
            if(accepted){long nextAttempt=earnedMode?checked(attempt+1):attempt;game=new Trial(profile,preparation.Selection,preparation.Armor,responses,controls,initiative,tempo);preparing=false;attempt=nextAttempt;}
        }
        else accepted=!preparing&&game.Execute(command);
        // Only the live accepted transition may award; forecasts reconstruct Trial without this ledger.
        if(accepted&&Action(command)&&activeBefore&&earnedMode&&!unlocked&&game.Secured&&preparation.Selection==Passive.None)
        {unlocked=true;receipt=new {kind="earned-practice-clear",sequence=next,attempt,profile};}
        sequence=next;observation=Observe(command,accepted);return observation;
    }
}
