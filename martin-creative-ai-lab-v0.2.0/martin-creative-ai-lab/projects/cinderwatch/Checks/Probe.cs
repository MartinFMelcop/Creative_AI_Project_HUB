using Cinder.Core;
namespace Cinder.Checks;

/// <summary>Declared synthetic controller for repeatable journeys, not a balance oracle.</summary>
public static class Probe
{
    public static Command Choose(Game g,bool simple=false)
    {
        var legal=g.Legal(); var a=g.Actor!;
        if(simple) return legal.First(c=>c.Kind==Kind.Strike);
        if(a.Id==1 && legal.FirstOrDefault(c=>c.Kind==Kind.Pin && g.Threats[c.Target].Attack==Attack.Gout) is {} pin) return pin;
        if(a.Id==1 && g.Stage==1 && g.Sparks>2 && legal.FirstOrDefault(c=>c.Kind==Kind.Pin && g.Threats[c.Target].Attack==Attack.Bite) is {} screenPin) return screenPin;
        if(a.Id==2)
        {
            var mend=legal.Where(c=>c.Kind==Kind.Mend).OrderBy(c=>g.Find(c.Target).Hp/(double)g.Find(c.Target).MaxHp).FirstOrDefault();
            if(mend!=null && (g.Find(mend.Target).Hp<=16 || g.Find(mend.Target).Scorch>0))return mend;
        }
        var attacks=legal.Where(c=>c.Kind is Kind.Strike or Kind.Pierce).ToArray();
        var drone=attacks.FirstOrDefault(c=>g.Find(c.Target).Name=="Patch drone");
        if(drone!=null)return drone;
        return attacks.OrderBy(c=>g.Find(c.Target).Hp).ThenByDescending(c=>c.Kind==Kind.Strike).First();
    }
    public static Game Finish(string first="coolant",string second="edge",bool simple=false)
    {
        var g=new Game();
        for(var i=0;i<512 && g.Phase is Phase.Combat or Phase.Camp;i++)
        {
            if(g.Phase==Phase.Camp)g.Camp(g.Stage==0?first:second);
            else if(g.Actor!.Hero)g.Act(Choose(g,simple)); else g.ResolveEnemy();
        }
        return g;
    }
    public static string State(Game g)=>System.Text.Json.JsonSerializer.Serialize(new {g.Stage,g.Round,g.Phase,g.Cursor,g.Sparks,g.Kits,g.Edge,g.Plates,g.Units,g.Order,g.Threats,g.Journal,g.Log},Journal.Json);
}
