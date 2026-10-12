namespace Cinder.Core;

public enum Phase { Combat, Camp, Victory, Defeat }
public enum Kind { Strike, Guard, Shift, Cover, Pin, Pierce, Mend }
public enum Attack { Bite, Rivet, Repair, Charge, Gout }
public sealed record Command(Kind Kind, int Target = -1);
public sealed record Entry(string Op, Command? Command = null, string? Choice = null);
public sealed record Threat(Attack Attack, int Target, int Damage);

public sealed class Unit(int id, string name, string role, bool hero, int hp, int speed, bool front, int armor = 0)
{
    public int Id { get; } = id;
    public string Name { get; } = name;
    public string Role { get; } = role;
    public bool Hero { get; } = hero;
    public int MaxHp { get; } = hp;
    public int Speed { get; } = speed;
    public int Armor { get; } = armor;
    public int Hp { get; internal set; } = hp;
    public bool Front { get; internal set; } = front;
    public int Shield { get; internal set; }
    public int Scorch { get; internal set; }
    public int Covers { get; internal set; } = -1;
    public bool Pinned { get; internal set; }
    public bool Alive => Hp > 0;
    internal Unit Copy() => new(Id, Name, Role, Hero, MaxHp, Speed, Front, Armor)
        { Hp = Hp, Shield = Shield, Scorch = Scorch, Covers = Covers, Pinned = Pinned };
}

/// <summary>Deterministic tactical campaign. UI and previews consume this one ruleset.</summary>
public sealed class Game
{
    private List<Unit> units = [];
    private List<int> order = [];
    private Dictionary<int, Threat> threats = [];
    private List<Entry> journal = [];
    private List<string> log = [];
    private int cursor;
    public IReadOnlyList<Unit> Units => units.AsReadOnly();
    public IReadOnlyList<int> Order => order.AsReadOnly();
    public IReadOnlyDictionary<int, Threat> Threats => threats.AsReadOnly();
    public IReadOnlyList<Entry> Journal => journal.AsReadOnly();
    public IReadOnlyList<string> Log => log.AsReadOnly();
    public int Cursor => cursor;
    public int Stage { get; private set; }
    public int Round { get; private set; }
    public int Sparks { get; private set; } = 3;
    public int Kits { get; private set; } = 4;
    public int Edge { get; private set; }
    public int Plates { get; private set; }
    public Phase Phase { get; private set; } = Phase.Combat;
    public Unit? Actor => Phase == Phase.Combat ? Find(order[cursor]) : null;
    public string Place => Content.Places[Stage];
    public Unit Find(int id) => units.Single(u => u.Id == id);

    public Game()
    {
        units = [new(0,"Rook","shieldwright",true,38,7,true),
            new(1,"Vale","line scout",true,30,9,true),new(2,"Neri","field medic",true,28,5,false)];
        StartBattle();
    }
    private Game(Game source)
    {
        units = source.units.Select(u => u.Copy()).ToList(); order = [..source.order];
        threats = new(source.threats); journal = [..source.journal]; log = [..source.log];
        cursor = source.cursor; Stage = source.Stage; Round = source.Round; Phase = source.Phase;
        Sparks = source.Sparks; Kits = source.Kits; Edge = source.Edge; Plates = source.Plates;
    }
    public Game Fork() => new(this);
    private void Say(string text) => log.Add(text);
    private void StartBattle()
    {
        units.RemoveAll(u => !u.Hero);
        units.AddRange(Stage switch
        {
            0 => [new Unit(3,"Ash hound","screened bite",false,23,6,true),new(4,"Riveter","rear-targeting bolt",false,20,4,false)],
            1 => [new Unit(3,"Bulwark","armoured bite",false,30,8,true,2),new(4,"Patch drone","repairs wounded allies",false,22,4,false),new(5,"Ash hound","screened bite",false,18,6,true)],
            _ => [new Unit(3,"Governor","charge / scorched gout",false,56,6,true,2),new(4,"Riveter","rear-targeting bolt",false,22,4,false)]
        });
        Phase = Phase.Combat; Round = 0; Say(Content.Arrival[Stage]); NewRound();
    }
    private void NewRound()
    {
        if (++Round > 12) { Phase = Phase.Defeat; Say("The steam line bursts before the crew can close it."); return; }
        // Initiative is snapshotted each round; stable ID ties never reshuffle mid-turn.
        order = units.Where(u => u.Alive).OrderByDescending(u => u.Speed).ThenBy(u => u.Id).Select(u => u.Id).ToList();
        cursor = 0; threats.Clear();
        foreach (var u in units.Where(u => !u.Hero && u.Alive))
        {
            u.Pinned = false;
            var target = units.Where(h => h.Hero && h.Alive).OrderBy(h => h.Hp).ThenBy(h => h.Id).First().Id;
            var attack = Attack.Bite; var damage = Stage == 0 ? 9 : 10;
            if(u.Name == "Riveter") { attack = Attack.Rivet; damage = 7; target = units.Where(h => h.Hero && h.Alive).OrderByDescending(h => h.Speed).First().Id; }
            if(u.Name == "Patch drone") { attack = Attack.Repair; damage = 7; target = units.Where(h => !h.Hero && h.Alive).OrderByDescending(h => h.MaxHp-h.Hp).ThenBy(h=>h.Id).First().Id; }
            if(u.Name == "Governor") { attack = Round % 2 == 1 ? Attack.Charge : Attack.Gout; target = -1; damage = 12; }
            threats[u.Id] = new(attack,target,damage);
        }
        Say($"Round {Round}: {string.Join(" → ",order.Select(id=>Find(id).Name))}."); PrepareTurn();
    }
    private bool FinishBattle()
    {
        if(!units.Any(u=>u.Hero && u.Alive)) { Phase=Phase.Defeat; Say("No one remains on their feet. The crew retreats from the furnace."); return true; }
        if(units.Any(u=>!u.Hero && u.Alive)) return false;
        Phase=Stage==2?Phase.Victory:Phase.Camp;
        foreach(var h in units.Where(u=>u.Hero)) { h.Shield=0; h.Covers=-1; h.Scorch=0; }
        Say(Phase==Phase.Victory?Content.Ending(this):Content.After[Stage]); return true;
    }
    private void PrepareTurn()
    {
        while(Phase==Phase.Combat)
        {
            if(FinishBattle()) return;
            if(cursor>=order.Count) { NewRound(); return; }
            var u=Find(order[cursor]);
            if(!u.Alive) { cursor++; continue; }
            u.Shield=0; u.Covers=-1;
            if(u.Scorch>0) { u.Scorch--; Damage(u,2,false); Say($"{u.Name} takes 2 scorch damage; {u.Scorch} tick(s) remain."); }
            if(!u.Alive) { cursor++; continue; }
            return;
        }
    }
    private void Advance() { cursor++; PrepareTurn(); }
    public IReadOnlyList<Command> Legal()
    {
        var a=Actor; if(a==null || !a.Hero) return Array.Empty<Command>();
        var result=new List<Command> {new(Kind.Guard),new(Kind.Shift)};
        var foes=units.Where(u=>!u.Hero && u.Alive).ToArray();
        foreach(var f in foes)
        {
            if(a.Id==2 || f.Front || !foes.Any(u=>u.Front)) result.Add(new(Kind.Strike,f.Id));
            if(a.Id==1)
            {
                result.Add(new(Kind.Pierce,f.Id));
                if(Sparks>0 && !f.Pinned && order.IndexOf(f.Id)>cursor) result.Add(new(Kind.Pin,f.Id));
            }
        }
        foreach(var h in units.Where(u=>u.Hero && u.Alive))
        {
            if(a.Id==0 && h.Id!=0) result.Add(new(Kind.Cover,h.Id));
            if(a.Id==2 && Kits>0 && (h.Hp<h.MaxHp || h.Scorch>0)) result.Add(new(Kind.Mend,h.Id));
        }
        return result;
    }
    public bool Act(Command command)
    {
        if(!Legal().Contains(command)) return false;
        var a=Actor!;
        switch(command.Kind)
        {
            case Kind.Strike:
            case Kind.Pierce:
            case Kind.Pin:
                var damage=command.Kind==Kind.Pin?4:command.Kind==Kind.Pierce?7:a.Id==0?8:a.Id==1?9:6;
                var target=Find(command.Target); var dealt=Damage(target,damage+Edge,true);
                Say($"{a.Name}: {command.Kind} → {target.Name}, {dealt} damage.");
                if(command.Kind==Kind.Pin) { Sparks--; target.Pinned=true; Say($"{target.Name}'s announced action is cancelled this round."); }
                break;
            case Kind.Guard: a.Shield=7; Say($"{a.Name} braces: 7 shield until their next turn."); break;
            case Kind.Shift: a.Front=!a.Front; Say($"{a.Name} moves to the {(a.Front?"front":"rear")} row."); break;
            case Kind.Cover: a.Covers=command.Target; a.Shield=6+Plates; Say($"Rook covers {Find(command.Target).Name}: next direct hit redirects to Rook, with {a.Shield} shield."); break;
            case Kind.Mend:
                var h=Find(command.Target); var healed=Math.Min(12,h.MaxHp-h.Hp); h.Hp+=healed; h.Scorch=0; Kits--;
                Say($"Neri treats {h.Name}: +{healed} HP, scorch cleared; {Kits} kits remain."); break;
        }
        journal.Add(new("act",command)); Advance(); return true;
    }
    private int Damage(Unit target,int amount,bool armor)
    {
        var incoming=Math.Max(0,amount-(armor?target.Armor:0));
        var absorbed=Math.Min(target.Shield,incoming); target.Shield-=absorbed; incoming-=absorbed;
        var dealt=Math.Min(target.Hp,incoming); target.Hp-=dealt; return dealt;
    }
    public Unit DirectTarget(Threat t)
    {
        var target=Find(t.Target);
        // A dead locked target wastes the attack; never secretly reacquire another hero.
        if(!target.Alive) return target;
        if(t.Attack==Attack.Bite && !target.Front)
            target=units.FirstOrDefault(u=>u.Hero && u.Alive && u.Front)??target;
        return target;
    }
    private void Hit(Unit target,int damage,bool direct,bool scorch=false)
    {
        if(!target.Alive) return;
        if(direct)
        {
            var protector=units.FirstOrDefault(u=>u.Alive && u.Hero && u.Covers==target.Id);
            if(protector!=null) { protector.Covers=-1; Say($"Rook intercepts the hit aimed at {target.Name}."); target=protector; }
        }
        var dealt=Damage(target,damage,true); if(scorch && target.Alive) target.Scorch=2;
        Say($"{target.Name} loses {dealt} HP{(scorch&&target.Alive?"; scorched for two turns":"")}.");
    }
    public bool ResolveEnemy()
    {
        var a=Actor; if(a==null || a.Hero) return false;
        var t=threats[a.Id];
        if(a.Pinned) Say($"{a.Name} cannot act: pinned.");
        else switch(t.Attack)
        {
            case Attack.Bite:
            case Attack.Rivet: Say($"{a.Name} releases {t.Attack}."); Hit(DirectTarget(t),t.Damage,true); break;
            case Attack.Repair:
                var target=Find(t.Target);
                if(target.Alive && target.Hp<target.MaxHp) { var heal=Math.Min(t.Damage,target.MaxHp-target.Hp); target.Hp+=heal; Say($"Patch drone repairs {target.Name}: +{heal} HP."); }
                else { Say("Patch drone has no repair; its weak arc hits the front line."); Hit(units.First(u=>u.Hero&&u.Alive),4,true); }
                break;
            case Attack.Charge: Say("The Governor draws steam. Next round: 12 damage to EVERY hero and two scorch ticks. Cover cannot intercept it."); break;
            case Attack.Gout: Say("The Governor opens the steam vents."); foreach(var h in units.Where(u=>u.Hero&&u.Alive).ToArray()) Hit(h,t.Damage,false,true); break;
        }
        journal.Add(new("enemy")); Advance(); return true;
    }
    public IReadOnlyList<string> CampChoices => Phase!=Phase.Camp?Array.Empty<string>():Stage==0?new[]{"coolant","sparks"}:new[]{"plates","edge"};
    public bool Camp(string choice)
    {
        if(!CampChoices.Contains(choice)) return false;
        if(choice=="coolant") foreach(var h in units.Where(u=>u.Hero)) h.Hp=Math.Min(h.MaxHp,h.Alive?h.Hp+12:h.MaxHp/2);
        else
        {
            foreach(var h in units.Where(u=>u.Hero)) h.Hp=Math.Min(h.MaxHp,h.Alive?h.Hp+6:6);
            if(choice=="sparks") Sparks=Math.Min(5,Sparks+2);
            if(choice=="plates") Plates=3;
            if(choice=="edge") Edge=2;
        }
        Say(Content.CampResponse(choice)); journal.Add(new("camp",Choice:choice)); Stage++; StartBattle(); return true;
    }
    public string Label(Command c) => c.Kind switch
    {
        Kind.Strike=>$"{(Actor?.Id==2?"Bolt":"Strike")} → {Find(c.Target).Name}",
        Kind.Guard=>"Brace · 7 shield", Kind.Shift=>$"Move to {(Actor!.Front?"rear":"front")}",
        Kind.Cover=>$"Cover {Find(c.Target).Name}", Kind.Pin=>$"Pin {Find(c.Target).Name} · 1 spark",
        Kind.Pierce=>$"Pierce → {Find(c.Target).Name}", Kind.Mend=>$"Mend {Find(c.Target).Name} · 1 kit", _=>c.Kind.ToString()
    };
    public string Intent(int id)
    {
        var u=Find(id); if(!u.Alive)return "Down";
        var t=threats[id]; if(u.Pinned)return "PINNED · action cancelled";
        return t.Attack switch
        {
            Attack.Charge=>"Charge · next round: 12 to all + scorch",
            Attack.Gout=>"Gout · 12 to ALL + 2 scorch ticks",
            Attack.Repair=>$"Repair {Find(t.Target).Name} · +7 (or weak arc 4)",
            _=>$"{t.Attack} → {DirectTarget(t).Name} · {t.Damage} before shield"+
                (units.Any(h=>h.Hero&&h.Alive&&h.Covers==DirectTarget(t).Id)?" (Rook covers)":"")
        };
    }
    public string Preview(Command c)
    {
        var copy=Fork(); if(!copy.Act(c))return "Unavailable";
        var changes=units.Select(u=>(u,v:copy.Find(u.Id))).Where(x=>x.u.Hp!=x.v.Hp)
            .Select(x=>$"{x.u.Name}: {x.u.Hp} → {x.v.Hp} HP").ToList();
        changes.AddRange(copy.log.Skip(log.Count).Take(2));
        return string.Join("\n",changes.Distinct());
    }
}
