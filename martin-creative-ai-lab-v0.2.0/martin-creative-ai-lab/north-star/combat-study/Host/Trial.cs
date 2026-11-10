using System;
using System.Collections.Generic;
using System.Linq;
using NorthStar.Combat;
namespace NorthStar.CombatStudy
{

// An original deterministic practice encounter. Its global rounds are separate
// from Crossing beats; no historical characters, regions or battle loop imported.
public sealed class Trial
{
    readonly EffectSet effects = new EffectSet();
    readonly List<string> events = new List<string>();
    readonly string profile;
    readonly uint initialSeed;
    readonly List<string> acceptedCommands = new List<string>();
    readonly PassiveEncounter passive;
    HitResult? lastHit;
    readonly bool responses;
    readonly Initiative? initiative;
    readonly Breakbar? breakbar;
    ControlResult? lastControl;
    bool wardAvailable=true;
    ResponseChain? pending;
    string[] resolution=Array.Empty<string>();
    public bool Active=>outcome=="active";
    public bool Secured=>outcome=="secured";
    int round, hp=100, enemyHp=96, charges=2;
    string outcome="active";
    public string Last {get; private set;}="Choose an action. Reads and elapsed time do not advance the round.";
    public Trial(string profile="toxic",Passive passive=Passive.None,Armor armor=Armor.Light,bool responses=false,bool controls=false,bool initiativeMode=false,string tempo="heavy",uint initiativeSeed=Initiative.DefaultSeed)
    {
        if(profile!="toxic" && profile!="heated") throw new ArgumentException("Unknown practice profile.");
        if((responses?1:0)+(controls?1:0)+(initiativeMode?1:0)>1)throw new ArgumentException("Practice modes are exclusive.");
        initiative=initiativeMode?new Initiative(tempo,initiativeSeed):null;
        initialSeed=initiativeSeed;
        this.profile=profile;this.responses=responses;breakbar=controls?new Breakbar(5):null;
        this.passive=new PassiveEncounter(passive,armor);
        if(profile=="toxic") { effects.Apply(Effect.Poison,3);effects.Apply(Effect.Bleed,3); }
        else { effects.Apply(Effect.Burn,3);effects.Apply(Effect.Disarm,2); }
        events.Add(profile=="toxic"?"Practice begins with poison and bleed, each lasting three global rounds.":"Practice begins with burn for three rounds and disarm for two rounds.");
    }
    string Threat => round%3==1 ? "Pressure: 20 direct damage, then extends poison (toxic) or burn (heated) by two rounds." : "Contact: 20 direct damage.";
    // Reuse this same owner for a bounded conditional branch, never a second rule engine.
    public object Forecast(string command)
    {
        if(!Active)throw new ArgumentException("An active encounter is required for inspection.");
        var branch=new Trial(profile,passive.Selection,passive.Armor,responses,breakbar!=null,
            initiative!=null,initiative==null?"heavy":initiative.Style,initialSeed);
        foreach(string accepted in acceptedCommands)
            if(!branch.Execute(accepted))throw new InvalidOperationException("Accepted history failed to reconstruct its owner.");
        branch.Last=Last;
        if(!branch.Execute(command))throw new ArgumentException("Inspect a currently legal action. "+branch.Last);
        return new {command,boundary=branch.pending!=null?"response":branch.Active?"action":"ended",state=branch.Snapshot()};
    }
    public bool Execute(string command)
    {
        bool accepted=ExecuteCore(command);
        if(accepted)acceptedCommands.Add(command);
        return accepted;
    }
    bool ExecuteCore(string command)
    {
        if(outcome!="active") return Refuse("Encounter ended. Restart explicitly to practice again.");
        if(pending!=null)
        {
            if(command!="release"&&command!="break-ward")return Refuse("Resolve the committed response first. No action, contact or round was spent.");
            if(command=="break-ward"&&(!pending.HasWard||charges==0))return Refuse("Breaking requires the actual pending ward and one remaining charge. No cost or resolution occurred.");
            bool broken=command=="break-ward";
            if(broken)charges--;
            var result=pending.Resolve(broken);pending=null;
            resolution=result.Entries.Select(e=>e.Kind+":"+(e.Applied?"applied":"cancelled")).ToArray();
            events.Clear();lastHit=null;
            if(broken)events.Add("Break ward committed: one shared treatment charge spent before resolution.");
            foreach(var entry in resolution)events.Add("Resolution: "+entry);
            enemyHp=Math.Max(0,enemyHp-result.Damage);
            events.Add("Committed strike resolved: "+result.Damage+" direct damage. Its cast charge is never refunded, including when countered.");
            return FinishRound(false);
        }
        if(command=="commit")
        {
            if(!responses)return Refuse("Response practice was not prepared. No cost or round spent.");
            if(!effects.WeaponEnabled)return Refuse("Disarmed: committed strike unavailable. No charge or round spent.");
            if(charges==0)return Refuse("No shared treatment charge remains to commit. No round spent.");
            int damage=(int)Math.Round(48*effects.AttackMultiplier,MidpointRounding.AwayFromZero);
            var chain=new ResponseChain(damage,wardAvailable);
            charges--;pending=chain;wardAvailable=false;resolution=Array.Empty<string>();events.Clear();lastHit=null;
            Last="Committed strike costs one shared treatment charge now. "+(chain.HasWard?"The target committed its one ward. Break it for one remaining charge, or Release without refund.":"The target has no ward reserve left. Release resolves the pending strike.");
            events.Add(Last);return true;
        }
        if(command=="release"||command=="break-ward")return Refuse("No response chain is pending. No charge or round spent.");
        if(command=="light-control"||command=="hard-control")
        {
            if(breakbar==null)return Refuse("Control practice was not prepared. No cost or round spent.");
            bool hard=command=="hard-control";
            if(hard&&charges==0)return Refuse("Hard control needs one shared treatment charge. No round spent.");
            if(hard)charges--;
            events.Clear();lastHit=null;lastControl=breakbar.Apply(hard?ControlWeight.Hard:ControlWeight.Light);
            events.Add($"Control paid: one actual round{(hard?" and one shared charge":"")}; drained {lastControl.Drained}, refilled {lastControl.Refilled}, applied {lastControl.Applied}. No target HP damage.");
            return FinishRound(false,lastControl.Applied);
        }
        if(!new[]{"strike","bash","guard","treat","cleanse","retreat"}.Contains(command)) return Refuse("Unknown action.");
        if(command=="strike"&&!effects.WeaponEnabled) return Refuse("Disarmed: strike unavailable. Bash remains available; no round spent.");
        if((command=="treat"||command=="cleanse")&&charges==0) return Refuse("No treatment charges remain; no round spent.");
        if(command=="cleanse"&&effects.Snapshot().Length==0) return Refuse("No effects to cleanse; no charge or round spent.");
        if(initiative!=null)return InitiativeRound(command);
        events.Clear();lastHit=null;lastControl=null;
        if(command=="retreat") { outcome="withdrawn";Last="You withdraw. No victory or death is inferred.";events.Add(Last);return true; }
        bool guard=command=="guard";
        if(command=="strike"||command=="bash")
        {
            int damage=(int)Math.Round((command=="strike"?24:14)*effects.AttackMultiplier,MidpointRounding.AwayFromZero);
            enemyHp=Math.Max(0,enemyHp-damage);events.Add($"{command}: {damage} direct damage to target. Burn multiplier {effects.AttackMultiplier:0.0}.");
        }
        if(command=="treat") { charges--;int amount=(int)Math.Round(32*effects.HealingMultiplier,MidpointRounding.AwayFromZero);int healed=Math.Min(100-hp,amount);hp+=healed;events.Add($"Treatment spent: healed {healed} (eligible {amount}; bleed multiplier {effects.HealingMultiplier:0.0})."); }
        if(command=="cleanse") { charges--;events.Add($"Treatment spent: removed {effects.Cleanse()} effects."); }
        if(guard) events.Add("Guard halves this round's direct contact; it cannot reduce DOT.");
        return FinishRound(guard);
    }
    bool InitiativeRound(string command)
    {
        events.Clear();lastHit=null;lastControl=null;bool guard=false;
        var queue=initiative!.Current;
        events.Add($"Initiative round {queue.Round}: {string.Join(" then ",queue.Order)}; scores {queue.PlayerScore}/{queue.TargetScore}.");
        foreach(string actor in queue.Order)
        {
            if(hp==0||enemyHp==0||outcome!="active")break;
            if(actor=="target")Contact(guard);
            else
            {
                if(command=="retreat"){outcome="withdrawn";events.Add("You withdraw in your actual slot; no victory or return is inferred.");break;}
                if(command=="strike"||command=="bash")
                {
                    int damage=(int)Math.Round((command=="strike"?initiative.StrikeDamage:initiative.BashDamage)*effects.AttackMultiplier,MidpointRounding.AwayFromZero);
                    enemyHp=Math.Max(0,enemyHp-damage);events.Add($"{command}: {damage} direct damage to target. Burn multiplier {effects.AttackMultiplier:0.0}.");
                }
                if(command=="treat"){charges--;int amount=(int)Math.Round(32*effects.HealingMultiplier,MidpointRounding.AwayFromZero);int healed=Math.Min(100-hp,amount);hp+=healed;events.Add($"Treatment spent in player slot: healed {healed} (eligible {amount}).");}
                if(command=="cleanse"){charges--;events.Add($"Treatment spent in player slot: removed {effects.Cleanse()} effects.");}
                if(command=="guard"){guard=true;events.Add("Guard raised in player slot; only later contact is halved. DOT is unchanged.");}
            }
            if(hp==0)outcome="defeated";
            else if(enemyHp==0)outcome="secured";
        }
        if(outcome!="withdrawn")CloseRound();
        else {Last=$"Round {queue.Round}: withdrawn in player slot.";events.Add(Last);}
        if(outcome=="active")initiative.Advance();
        return true;
    }
    void Contact(bool guard)
    {
        int direct=guard?10:20;lastHit=passive.Resolve(hp,direct,DamageKind.PhysicalDirect);int directLoss=hp-lastHit.HpAfter;hp=lastHit.HpAfter;
        events.Add($"Target contact: {direct} incoming direct damage; {directLoss} actual HP lost.");
        if(passive.Selection!=Passive.None)events.Add($"Passive {PassiveIds.Name(passive.Selection)} / {PassiveIds.Name(passive.Armor)}: physical contact {direct} → {lastHit.EffectiveDamage}; damage reduced {lastHit.DamageReduced}; actual HP lost {lastHit.ActualHpLost}; HP loss avoided {lastHit.AvoidedHpLoss}; fatal-hit rescue {(lastHit.Rescued?"used now":"not used now")}; once-per-encounter rescue {(passive.Selection!=Passive.LastThread?"not equipped":passive.RescueSpent?"spent":"unspent")}. DOT is separate and remains payable.");
        if(hp>0&&round%3==1){var effect=profile=="toxic"?Effect.Poison:Effect.Burn;effects.Apply(effect,2);events.Add($"Announced pressure reapplied {effect}: remaining {effects.Remaining(effect)} before tick.");}
    }
    void CloseRound()
    {
        round++;
        var tick=effects.EndRound(round,100);
        foreach(var entry in tick.Entries)
        {
            int loss=Math.Min(hp,entry.Damage);hp-=loss;
            events.Add($"End round {round}: {entry.Effect} incoming DOT {entry.Damage}; actual HP lost {loss}; {entry.Remaining} rounds remain. Guard does not reduce this tick.");
        }
        outcome=hp==0?"defeated":enemyHp==0?"secured":"active";
        Last=$"Round {round} resolved: {outcome}.";events.Add(Last);
    }
    bool FinishRound(bool guard,bool controlled=false)
    {
        if(controlled)events.Add("Applied control suppresses this contact and pressure only. End-round DOT remains payable.");
        if(enemyHp>0&&!controlled)
        {
            int direct=guard?10:20;lastHit=passive.Resolve(hp,direct,DamageKind.PhysicalDirect);int directLoss=hp-lastHit.HpAfter;hp=lastHit.HpAfter;
            events.Add($"Target contact: {direct} incoming direct damage; {directLoss} actual HP lost.");
            if(passive.Selection!=Passive.None)events.Add($"Passive {PassiveIds.Name(passive.Selection)} / {PassiveIds.Name(passive.Armor)}: physical contact {direct} → {lastHit.EffectiveDamage}; damage reduced {lastHit.DamageReduced}; actual HP lost {lastHit.ActualHpLost}; HP loss avoided {lastHit.AvoidedHpLoss}; fatal-hit rescue {(lastHit.Rescued?"used now":"not used now")}; once-per-encounter rescue {(passive.Selection!=Passive.LastThread?"not equipped":passive.RescueSpent?"spent":"unspent")}. DOT is separate and remains payable.");
            if(round%3==1) { var effect=profile=="toxic"?Effect.Poison:Effect.Burn;effects.Apply(effect,2);events.Add($"Announced pressure reapplied {effect}: remaining {effects.Remaining(effect)} before tick."); }
        }
        round++;
        var tick=effects.EndRound(round,100);
        foreach(var entry in tick.Entries)
        {
            int loss=Math.Min(hp,entry.Damage);hp-=loss;
            events.Add($"End round {round}: {entry.Effect} incoming DOT {entry.Damage}; actual HP lost {loss}; {entry.Remaining} rounds remain. Guard does not reduce this tick.");
        }
        outcome=hp==0?"defeated":enemyHp==0?"secured":"active";
        Last=$"Round {round} resolved: {outcome}.";events.Add(Last);return true;
    }
    bool Refuse(string reason) { Last=reason;return false; }
    object? HitObservation()=>lastHit==null?null:new {kind=lastHit.Kind.ToString(),incoming=lastHit.Incoming,effectiveDamage=lastHit.EffectiveDamage,hpBefore=lastHit.HpBefore,hpAfter=lastHit.HpAfter,damageReduced=lastHit.DamageReduced,actualHpLost=lastHit.ActualHpLost,avoidedHpLoss=lastHit.AvoidedHpLoss,rescued=lastHit.Rescued};
    public object Snapshot()=>new { profile,initiative=initiative==null?null:new {style=initiative.Style,playerAgility=initiative.PlayerAgility,enemyAgility=initiative.TargetAgility,round=initiative.Current.Round,order=initiative.Current.Order,playerScore=initiative.Current.PlayerScore,targetScore=initiative.Current.TargetScore,seedState=initiative.Current.SeedState},breakbar=breakbar==null?null:new {phase=breakbar.Protected?"protected":"exposed",value=breakbar.Value,capacity=breakbar.Capacity,lastApplied=lastControl?.Applied??false,lastDrain=lastControl?.Drained??0,lastRefill=lastControl?.Refilled??0},responsePractice=responses,wardAvailable=responses&&wardAvailable,pending=pending==null?null:new {ward=pending.HasWard,items=pending.PendingCount},resolution=resolution.ToArray(),round,hp,maxHp=100,enemyHp,charges,effects=effects.Snapshot().Select(e=>new {effect=e.Effect.ToString(),remaining=e.Remaining}).ToArray(),threat=outcome=="active"?Threat:"No further threat; encounter ended.",events=events.ToArray(),outcome,last=Last,weaponEnabled=effects.WeaponEnabled,attackMultiplier=effects.AttackMultiplier,healingMultiplier=effects.HealingMultiplier,passive=PassiveIds.Name(passive.Selection),armor=PassiveIds.Name(passive.Armor),rescueSpent=passive.RescueSpent,lastHit=HitObservation() };
}
}
