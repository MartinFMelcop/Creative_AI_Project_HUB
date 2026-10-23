using System;
using System.Collections.Generic;

namespace NorthStar.Combat
{
    // Finite nonnegative inputs (maximum 1,000,000) and levels 0..1000 are the
    // destination boundary. Ruby coercion/negative-denominator recovery is rejected.
    // Rounding is Ruby-compatible for this nonnegative domain, never ties-to-even.
    public static class Formula
    {
        internal static double Number(double n) { if(double.IsNaN(n)||double.IsInfinity(n)||n<0||n>1000000) throw new ArgumentOutOfRangeException(nameof(n)); return n; }
        static int Level(int n) { if(n<0||n>1000) throw new ArgumentOutOfRangeException(nameof(n)); return n; }
        static double Clamp(double n,double lo,double hi)=>Math.Max(lo,Math.Min(hi,n));
        static double Ratio(double a,double b)=>a/(b<=0?0.000001:b);
        internal static int Round(double n) { if(double.IsNaN(n)||double.IsInfinity(n)||n<0||n>int.MaxValue-0.5) throw new ArgumentOutOfRangeException(nameof(n)); return checked((int)Math.Round(n,MidpointRounding.AwayFromZero)); }
        public static double Hit(double acc,double eva,int atkLvl,int defLvl,double? baseHit=null) { Number(acc);Number(eva);Level(atkLvl);Level(defLvl);return Clamp(Number(baseHit??0.9)*Ratio(acc,acc+eva)*Clamp(1+0.02*(atkLvl-defLvl),0.85,1.15),0.05,0.95); }
        public static double Crit(double percent,double? critBase=null)=>Clamp(Number(percent)/100*Number(critBase??1),0,0.5);
        public static double Raw(double attack,double scale,double lethality) { var n=Number(attack)*Number(scale)*(1+Number(lethality)); if(double.IsInfinity(n)) throw new ArgumentOutOfRangeException(); return n; }
        public static int Mitigate(double raw,double defense,int level) { Number(raw);Number(defense);Level(level);double k=100+10*level;return Round(raw*k/(k+defense)); }
        public static double ApplyChance(double eff,double res,double? baseApply=null) { Number(eff);Number(res);return Clamp(Number(baseApply??1)*Ratio(eff,eff+res),0.05,0.95); }
        public static int Duration(double baseDur,double applyPercent,double tenPercent) { Number(baseDur);Number(applyPercent);Number(tenPercent);return Math.Max(1,Round(Math.Max(0,baseDur*(1+applyPercent/100-tenPercent/100)))); }
        // Source adapter: case-insensitive, whitespace significant; unknown status is zero.
        public static int Dot(string status,int maxHP) { if(status==null)throw new ArgumentNullException(nameof(status));Number(maxHP);switch(status.ToUpperInvariant()){case "POISON":return Round(maxHP*0.06);case "BLEED":case "BURN":return Round(maxHP*0.03);default:return 0;} }
        public static int Reapply(int remaining,int add) { if(remaining<0||add<0)throw new ArgumentOutOfRangeException();return Math.Max(1,checked(remaining+add)); }
    }
    public enum Effect { Poison, Bleed, Burn, Disarm }
    public sealed class EffectView { public Effect Effect {get;} public int Remaining {get;} internal EffectView(Effect effect,int remaining){Effect=effect;Remaining=remaining;} }
    public sealed class TickEntry { public Effect Effect {get;} public int Damage {get;} public int Remaining {get;} internal TickEntry(Effect effect,int damage,int remaining){Effect=effect;Damage=damage;Remaining=remaining;} }
    public sealed class Tick { public int Round {get;} public int Damage {get;} public TickEntry[] Entries=> (TickEntry[])entries.Clone(); readonly TickEntry[] entries; internal Tick(int round,int damage,TickEntry[] entries){Round=round;Damage=damage;this.entries=entries;} }
    public sealed class EffectSet
    {
        readonly SortedDictionary<Effect,int> active=new SortedDictionary<Effect,int>();int lastRound;
        static void Valid(Effect e){if(!Enum.IsDefined(typeof(Effect),e))throw new ArgumentOutOfRangeException(nameof(e));}
        public void Apply(Effect effect,int duration){Valid(effect);if(duration<1||duration>1000)throw new ArgumentOutOfRangeException(nameof(duration));int next=checked(Remaining(effect)+duration);if(next>1000)throw new ArgumentOutOfRangeException(nameof(duration));active[effect]=next;}
        public int Cleanse(){int n=active.Count;active.Clear();return n;}
        public int Remaining(Effect effect){Valid(effect);return active.TryGetValue(effect,out int n)?n:0;}
        public double AttackMultiplier=>Remaining(Effect.Burn)>0?0.7:1;
        public double HealingMultiplier=>Remaining(Effect.Bleed)>0?0.7:1;
        public bool WeaponEnabled=>Remaining(Effect.Disarm)==0;
        public EffectView[] Snapshot(){var result=new List<EffectView>();foreach(var x in active)result.Add(new EffectView(x.Key,x.Value));return result.ToArray();}
        public Tick EndRound(int round,int maxHP){if(lastRound==int.MaxValue||round!=lastRound+1)throw new ArgumentOutOfRangeException(nameof(round));Formula.Number(maxHP);var entries=new List<TickEntry>();int total=0;foreach(var x in active){int damage=Formula.Dot(x.Key.ToString(),maxHP);total=checked(total+damage);entries.Add(new TickEntry(x.Key,damage,x.Value-1));}foreach(var x in entries){if(x.Remaining==0)active.Remove(x.Effect);else active[x.Effect]=x.Remaining;}lastRound=round;return new Tick(round,total,entries.ToArray());}
    }
}
