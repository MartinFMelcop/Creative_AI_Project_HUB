using System;

namespace NorthStar.Combat
{
    public enum Passive { None, Lining, LastThread }
    public enum Armor { Light, Heavy }
    public enum PassiveContext { Preparation, Combat, Cutscene, Ended }
    public enum DamageKind { PhysicalDirect, OtherDirect, Dot }

    public static class PassiveIds
    {
        public static string Name(Passive value)
        {switch(value){case Passive.None:return "none";case Passive.Lining:return "lining";case Passive.LastThread:return "last-thread";default:throw new ArgumentException("Unknown passive.");}}
        public static Passive Parse(string value)
        {switch(value){case "none":return Passive.None;case "lining":return Passive.Lining;case "last-thread":return Passive.LastThread;default:throw new ArgumentException("Exact original passive ID required.");}}
        public static string Name(Armor value)
        {switch(value){case Armor.Light:return "light";case Armor.Heavy:return "heavy";default:throw new ArgumentException("Unknown armor.");}}
        public static Armor ParseArmor(string value)
        {switch(value){case "light":return Armor.Light;case "heavy":return Armor.Heavy;default:throw new ArgumentException("Exact armor ID required.");}}
    }

    // One explicit slot. The owning application supplies context, never the client.
    public sealed class PassiveSlot
    {
        public Passive Selection {get;private set;}=Passive.None;
        public Armor Armor {get;private set;}=Armor.Light;
        public bool Equip(Passive selection,Armor armor,PassiveContext context)
        {
            PassiveIds.Name(selection);PassiveIds.Name(armor);
            if(!Enum.IsDefined(typeof(PassiveContext),context))throw new ArgumentException("Unknown preparation context.");
            if(context!=PassiveContext.Preparation)return false;
            Selection=selection;Armor=armor;return true;
        }
        public PassiveEncounter CreateEncounter()=>new PassiveEncounter(Selection,Armor);
    }

    public sealed class HitResult
    {
        public int HpBefore {get;}
        public int Incoming {get;}
        public int EffectiveDamage {get;}
        public int HpAfter {get;}
        public int DamageReduced {get;}
        public int ActualHpLost {get;}
        public int AvoidedHpLoss {get;}
        // Compatibility alias: raw damage reduction, not counterfactual HP saved.
        public int Prevented=>DamageReduced;
        public bool Rescued {get;}
        public DamageKind Kind {get;}
        internal HitResult(int hp,int incoming,int effective,int after,bool rescued,DamageKind kind)
        {HpBefore=hp;Incoming=incoming;EffectiveDamage=effective;HpAfter=after;DamageReduced=incoming-effective;ActualHpLost=hp-after;AvoidedHpLoss=Math.Min(hp,incoming)-ActualHpLost;Rescued=rescued;Kind=kind;}
    }

    // Bound to one actual encounter. Swapping a preparation card cannot rearm this owner.
    public sealed class PassiveEncounter
    {
        public Passive Selection {get;}
        public Armor Armor {get;}
        public bool RescueSpent {get;private set;}
        public PassiveEncounter(Passive selection,Armor armor)
        {PassiveIds.Name(selection);PassiveIds.Name(armor);Selection=selection;Armor=armor;}
        public HitResult Resolve(int hp,int incoming,DamageKind kind)
        {
            if(hp<0||hp>1000000||incoming<0||incoming>1000000||!Enum.IsDefined(typeof(DamageKind),kind))throw new ArgumentException("Bounded typed hit required.");
            int effective=incoming;
            if(Selection==Passive.Lining&&Armor==Armor.Heavy&&kind==DamageKind.PhysicalDirect)
                effective=(int)Math.Round(incoming*0.9,MidpointRounding.AwayFromZero);
            int after=Math.Max(0,hp-effective);
            bool rescued=hp>0&&effective>=hp&&kind!=DamageKind.Dot&&Selection==Passive.LastThread&&!RescueSpent;
            if(rescued){after=1;RescueSpent=true;}
            return new HitResult(hp,incoming,effective,after,rescued,kind);
        }
    }
}
