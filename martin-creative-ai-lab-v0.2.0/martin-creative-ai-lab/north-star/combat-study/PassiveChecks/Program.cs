using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using NorthStar.Combat;
using NorthStar.CombatStudy;

static class Program
{
    static readonly List<string> checks=new();
    static void Check(string id,bool condition){if(!condition)throw new Exception(id);if(checks.Contains(id))throw new Exception("Unique checks required");checks.Add(id);}
    static JsonElement V(Room r)=>JsonSerializer.SerializeToElement(r.Snapshot());
    static JsonElement S(Room r)=>V(r).GetProperty("state");
    static JsonElement Act(Room r,string command)=>JsonSerializer.SerializeToElement(r.Execute(JsonSerializer.SerializeToElement(new{command})));
    static bool Flag(JsonElement e,string k)=>e.GetProperty(k).GetBoolean();
    static int N(JsonElement e,string k)=>e.GetProperty(k).GetInt32();
    static Room Practice(string profile,string passive,string armor)
    {var r=new Room();Act(r,"prepare "+profile);Act(r,"equip "+passive+" "+armor);Act(r,"begin");return r;}
    static void Main(string[] args)
    {
        if(args.Length!=1)throw new ArgumentException("External output JSON required");
        var slot=new PassiveSlot();Check("One slot begins None",slot.Selection==Passive.None);
        Check("Explicit preparation selects lining",slot.Equip(Passive.Lining,Armor.Heavy,PassiveContext.Preparation));
        foreach(var context in new[]{PassiveContext.Combat,PassiveContext.Cutscene,PassiveContext.Ended})Check("Non-preparation context refuses "+context,!slot.Equip(Passive.LastThread,Armor.Light,context)&&slot.Selection==Passive.Lining&&slot.Armor==Armor.Heavy);
        slot.Equip(Passive.LastThread,Armor.Heavy,PassiveContext.Preparation);var replaced=slot.CreateEncounter();var notStacked=replaced.Resolve(100,20,DamageKind.PhysicalDirect);Check("Replacement removes lining rather than stacking",notStacked.EffectiveDamage==20&&replaced.Selection==Passive.LastThread);
        var lining=new PassiveEncounter(Passive.Lining,Armor.Heavy);var hit=lining.Resolve(100,20,DamageKind.PhysicalDirect);Check("Heavy physical direct contact20 becomes18",hit.EffectiveDamage==18&&hit.HpAfter==82&&hit.DamageReduced==2&&hit.ActualHpLost==18&&hit.AvoidedHpLoss==2);
        var guard=lining.Resolve(100,10,DamageKind.PhysicalDirect);Check("Guard-first10 becomes9",guard.EffectiveDamage==9&&guard.HpAfter==91);
        Check("Declared away-from-zero rounding at odd contact",lining.Resolve(100,15,DamageKind.PhysicalDirect).EffectiveDamage==14&&lining.Resolve(100,19,DamageKind.PhysicalDirect).EffectiveDamage==17);
        Check("Light armor supplies no lining mitigation",new PassiveEncounter(Passive.Lining,Armor.Light).Resolve(100,20,DamageKind.PhysicalDirect).HpAfter==80);
        Check("Other direct contact is not physical context",lining.Resolve(100,20,DamageKind.OtherDirect).HpAfter==80);
        Check("DOT is separate and not mitigated",lining.Resolve(100,6,DamageKind.Dot).HpAfter==94);
        var over=lining.Resolve(5,20,DamageKind.PhysicalDirect);Check("Raw reduction is not overkill HP saved",over.DamageReduced==2&&over.ActualHpLost==5&&over.AvoidedHpLoss==0);
        var thread=new PassiveEncounter(Passive.LastThread,Armor.Light);Check("Zero hit cannot spend rescue at1HP",!thread.Resolve(1,0,DamageKind.PhysicalDirect).Rescued&&!thread.RescueSpent);
        Check("Nonfatal hit cannot spend rescue",!thread.Resolve(100,20,DamageKind.PhysicalDirect).Rescued&&!thread.RescueSpent);
        var fatal=thread.Resolve(10,20,DamageKind.PhysicalDirect);Check("Actual fatal hit leaves1HP once without inventing raw mitigation",fatal.Rescued&&fatal.HpAfter==1&&fatal.EffectiveDamage==20&&fatal.DamageReduced==0&&fatal.ActualHpLost==9&&fatal.AvoidedHpLoss==1&&thread.RescueSpent);
        Check("Second fatal direct hit defeats",thread.Resolve(1,20,DamageKind.PhysicalDirect).HpAfter==0);
        Check("Dead target never resurrects",new PassiveEncounter(Passive.LastThread,Armor.Light).Resolve(0,20,DamageKind.PhysicalDirect).HpAfter==0);
        var dotThread=new PassiveEncounter(Passive.LastThread,Armor.Heavy);Check("Fatal DOT does not activate direct-hit rescue",dotThread.Resolve(4,6,DamageKind.Dot).HpAfter==0&&!dotThread.RescueSpent);
        var other=new PassiveEncounter(Passive.LastThread,Armor.Light);Check("Declared other direct hit remains eligible",other.Resolve(10,10,DamageKind.OtherDirect).Rescued);
        bool invalid=false;try{thread.Resolve(-1,20,DamageKind.PhysicalDirect);}catch(ArgumentException){invalid=true;}Check("Invalid typed hit leaves usage state exact",invalid&&thread.RescueSpent);
        var active=new Room();var initial=S(active).GetRawText();var denied=Act(active,"equip lining heavy");Check("Initial active round0 is not out-of-combat",!Flag(denied,"accepted")&&S(active).GetRawText()==initial);
        Act(active,"prepare toxic");Check("Explicit fresh preparation has no active encounter",V(active).GetProperty("phase").GetString()=="preparation"&&S(active).ValueKind==JsonValueKind.Null);
        var pre=Act(active,"strike");Check("Preparation cannot execute combat actions",!Flag(pre,"accepted")&&S(active).ValueKind==JsonValueKind.Null);
        Act(active,"equip lining heavy");Act(active,"equip last-thread light");Act(active,"begin");Check("Actual Begin owns only the selected effect",S(active).GetProperty("passive").GetString()=="last-thread"&&!Flag(S(active),"rescueSpent"));
        var before=S(active).GetRawText();var refused=Act(active,"equip lining heavy");Check("Active equip cannot recreate heal or reset the encounter",!Flag(refused,"accepted")&&S(active).GetRawText()==before);
        var win=Practice("toxic","last-thread","light");foreach(var command in new[]{"strike","strike","strike","cleanse","strike"})Act(win,command);
        Check("Actual Last thread policy secures at1HP",S(win).GetProperty("outcome").GetString()=="secured"&&N(S(win),"hp")==1&&N(S(win),"enemyHp")==0&&Flag(S(win),"rescueSpent"));
        var baseline=Practice("toxic","none","light");foreach(var command in new[]{"strike","strike","strike","cleanse"})Act(baseline,command);
        Check("Same None policy dies before its final attack",S(baseline).GetProperty("outcome").GetString()=="defeated"&&N(S(baseline),"hp")==0&&N(S(baseline),"enemyHp")==24);
        var losing=Practice("toxic","last-thread","light");foreach(var command in new[]{"strike","strike","strike","bash"})Act(losing,command);
        Check("Actual rescue then DOT still defeats in same round",S(losing).GetProperty("outcome").GetString()=="defeated"&&N(S(losing),"hp")==0&&N(S(losing),"round")==4&&Flag(S(losing),"rescueSpent")&&Flag(S(losing).GetProperty("lastHit"),"rescued")&&N(S(losing).GetProperty("lastHit"),"hpAfter")==1);
        var liningGame=Practice("toxic","lining","heavy");Act(liningGame,"guard");Check("Actual lining guard still pays full poison and bleed",N(S(liningGame),"hp")==82&&N(S(liningGame).GetProperty("lastHit"),"effectiveDamage")==9);
        var observe=V(win).GetRawText();for(int i=0;i<10;i++)V(win);Check("Reads cannot rearm or change completed trial",V(win).GetRawText()==observe);
        var terminal=Act(win,"equip none heavy");Check("Terminal equip is not an implicit new encounter",!Flag(terminal,"accepted")&&Flag(S(win),"rescueSpent")&&N(S(win),"hp")==1);
        Act(win,"prepare heated");Act(win,"equip last-thread light");Act(win,"begin");Check("Only explicit new practice begins a fresh encounter",N(S(win),"hp")==100&&!Flag(S(win),"rescueSpent")&&N(S(win),"round")==0);
        File.WriteAllText(args[0],JsonSerializer.Serialize(new{schema_version=1,kind="actual_passive_native",checks=new{passed=checks.Count,failed=0},controls=checks,none_defeat=V(baseline),same_round_dot_defeat=V(losing),lining_guard=V(liningGame),limits="Source prose subset and declared destination policy, not Ruby/RGSS/learning/class eligibility, full passives, human balance or Unity/Windows/Steam."},new JsonSerializerOptions{WriteIndented=true})+"\n");Console.WriteLine($"PASS: {checks.Count} passive native controls");
    }
}
