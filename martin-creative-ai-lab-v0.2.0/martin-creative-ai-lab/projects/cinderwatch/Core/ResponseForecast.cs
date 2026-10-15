namespace Cinder.Core;

public sealed record ProjectedUnit(int Id, string Name, bool Hero, int BeforeHp, int Hp,
    int Shield, int Scorch, bool Front, bool Pinned, int Covers);

/// <summary>A bounded branch, ending before the next crew decision or salvage/result.</summary>
public sealed record ResponseForecast(string Action, Phase Phase, string? NextActor,
    int Round, int Sparks, int Kits, int EnemyActions, IReadOnlyList<ProjectedUnit> Units,
    IReadOnlyList<string> Events)
{
    public static ResponseForecast Calculate(Game live, Command command)
    {
        var branch=live.Fork();
        var start=branch.Log.Count;
        var action=live.Label(command);
        if(!branch.Act(command))throw new ArgumentException("Select a currently legal crew action.",nameof(command));
        var enemies=0;
        while(branch.Phase==Phase.Combat && branch.Actor is {Hero:false})
        {
            branch.ResolveEnemy();enemies++;
        }
        return new(action,branch.Phase,branch.Actor?.Name,branch.Round,branch.Sparks,branch.Kits,enemies,
            branch.Units.Select(u=>new ProjectedUnit(u.Id,u.Name,u.Hero,live.Find(u.Id).Hp,u.Hp,u.Shield,
                u.Scorch,u.Front,u.Pinned,u.Covers)).ToArray(),branch.Log.Skip(start).ToArray());
    }
    public string Describe()
    {
        var lines=new List<string> {$"IF CONFIRMED: {Action}",
            EnemyActions==0?"No enemy acts before the next decision.":$"Then resolve {EnemyActions} announced enemy action(s).",
            Phase==Phase.Combat?$"Stop BEFORE {NextActor}'s turn · round {Round}.":$"Stop at {Phase}; no salvage choice is made.",
            "No later crew action is assumed. This inspection spends nothing.","","CREW AT THAT STOP"};
        foreach(var u in Units.Where(u=>u.Hero))
            lines.Add($"{u.Name}: {u.BeforeHp} → {u.Hp} HP · {(u.Hp==0?"DOWN":u.Front?"front":"rear")} · {u.Shield} shield · {u.Scorch} scorch"+
                (u.Covers>=0?$" · covering {Units.Single(v=>v.Id==u.Covers).Name}":""));
        lines.Add($"Supplies: {Sparks} sparks · {Kits} kits");
        lines.Add("");lines.Add("CALCULATED CHAIN");lines.AddRange(Events);
        return string.Join("\n",lines);
    }
}
