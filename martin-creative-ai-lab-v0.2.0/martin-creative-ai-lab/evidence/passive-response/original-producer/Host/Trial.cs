using System;
using System.Collections.Generic;
using System.Linq;
using NorthStar.Combat;
namespace NorthStar.CombatStudy;

// An original deterministic practice encounter. Its global rounds are separate
// from Crossing beats; no historical characters, regions or battle loop imported.
public sealed class Trial
{
    readonly EffectSet effects = new();
    readonly List<string> events = new();
    readonly string profile;
    int round, hp=100, enemyHp=96, charges=2;
    string outcome="active";
    public string Last {get; private set;}="Choose an action. Reads and elapsed time do not advance the round.";
    public Trial(string profile="toxic")
    {
        if(profile!="toxic" && profile!="heated") throw new ArgumentException("Unknown practice profile.");
        this.profile=profile;
        if(profile=="toxic") { effects.Apply(Effect.Poison,3);effects.Apply(Effect.Bleed,3); }
        else { effects.Apply(Effect.Burn,3);effects.Apply(Effect.Disarm,2); }
        events.Add(profile=="toxic"?"Practice begins with poison and bleed, each lasting three global rounds.":"Practice begins with burn for three rounds and disarm for two rounds.");
    }
    string Threat => round%3==1 ? "Pressure: 20 direct damage, then extends poison (toxic) or burn (heated) by two rounds." : "Contact: 20 direct damage.";
    public bool Execute(string command)
    {
        if(outcome!="active") return Refuse("Encounter ended. Restart explicitly to practice again.");
        if(!new[]{"strike","bash","guard","treat","cleanse","retreat"}.Contains(command)) return Refuse("Unknown action.");
        if(command=="strike"&&!effects.WeaponEnabled) return Refuse("Disarmed: strike unavailable. Bash remains available; no round spent.");
        if((command=="treat"||command=="cleanse")&&charges==0) return Refuse("No treatment charges remain; no round spent.");
        if(command=="cleanse"&&effects.Snapshot().Length==0) return Refuse("No effects to cleanse; no charge or round spent.");
        events.Clear();
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
        if(enemyHp>0)
        {
            int direct=guard?10:20;int directLoss=Math.Min(hp,direct);hp-=directLoss;events.Add($"Target contact: {direct} incoming direct damage; {directLoss} actual HP lost.");
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
    public object Snapshot()=>new { profile,round,hp,maxHp=100,enemyHp,charges,effects=effects.Snapshot().Select(e=>new {effect=e.Effect.ToString(),remaining=e.Remaining}).ToArray(),threat=outcome=="active"?Threat:"No further threat; encounter ended.",events=events.ToArray(),outcome,last=Last,weaponEnabled=effects.WeaponEnabled,attackMultiplier=effects.AttackMultiplier,healingMultiplier=effects.HealingMultiplier };
}
