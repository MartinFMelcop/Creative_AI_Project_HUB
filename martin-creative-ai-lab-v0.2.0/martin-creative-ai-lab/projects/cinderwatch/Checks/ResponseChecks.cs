using Cinder.Core;
namespace Cinder.Checks;

public static class ResponseChecks
{
    public static void Run(Action<bool,string> check)
    {
        var opening=new Game();var state=Probe.State(opening);
        var first=ResponseForecast.Calculate(opening,new(Kind.Pin,3));
        check(first.EnemyActions==0&&first.NextActor=="Rook"&&first.Sparks==2,"Opening forecast stops before an unchosen Rook turn");
        check(first.Events.Any(s=>s.Contains("cancelled"))&&Probe.State(opening)==state,"Pin forecast explains cancellation without spending live supplies");
        opening.Act(new(Kind.Guard));state=Probe.State(opening);
        var guard=ResponseForecast.Calculate(opening,new(Kind.Guard));
        var strike=ResponseForecast.Calculate(opening,new(Kind.Strike,3));
        check(guard.EnemyActions==1&&guard.NextActor=="Neri"&&guard.Units.Single(u=>u.Id==0).Hp==36,"Brace forecasts screened bite and actual shield absorption");
        check(strike.Units.Single(u=>u.Id==0).Hp==29&&strike.Events.Any(s=>s.Contains("releases Bite")),"Attack alternative exposes the same bite without Brace");
        check(Probe.State(opening)==state,"Comparing alternatives leaves the selected live turn intact");
        var invalid=false;try{ResponseForecast.Calculate(opening,new(Kind.Pin,3));}catch(ArgumentException){invalid=true;}
        check(invalid&&Probe.State(opening)==state,"Unavailable response rejected without mutation");
        var cover=new Game();cover.Act(new(Kind.Pin,3));cover.Act(new(Kind.Cover,1));cover.ResolveEnemy();
        var redirected=ResponseForecast.Calculate(cover,new(Kind.Guard));
        check(redirected.EnemyActions==1&&redirected.NextActor=="Vale"&&redirected.Round==2,"Neri forecast includes enemy reply and next-round preparation");
        check(redirected.Units.Single(u=>u.Id==0).Hp==37&&redirected.Units.Single(u=>u.Id==1).Hp==30&&redirected.Events.Any(s=>s.Contains("intercepts")),"Cover consumes only the actual redirected hit");
        var fallen=new Game();fallen.Act(new(Kind.Guard));fallen.Find(2).Hp=1;fallen.Find(2).Scorch=1;
        var skipped=ResponseForecast.Calculate(fallen,new(Kind.Guard));
        check(skipped.Units.Single(u=>u.Id==2).Hp==0&&skipped.EnemyActions==2&&skipped.NextActor=="Vale","Scorch incapacity skips the next crew member and includes the following enemy");
        var finalHit=new Game();finalHit.Find(3).Hp=1;finalHit.Find(4).Hp=0;
        var camp=ResponseForecast.Calculate(finalHit,new(Kind.Strike,3));
        check(camp.Phase==Phase.Camp&&camp.NextActor==null&&camp.EnemyActions==0,"Killing the last sentry stops at salvage without choosing or entering a fight");
        var doomed=new Game();
        while(doomed.Round<12||doomed.Actor?.Id!=2){if(doomed.Actor!.Hero)doomed.Act(new(Kind.Guard));else doomed.ResolveEnemy();}
        var defeat=ResponseForecast.Calculate(doomed,new(Kind.Guard));
        check(defeat.Phase==Phase.Defeat&&defeat.EnemyActions==1&&defeat.NextActor==null,"Final enemy reply reaches the pressure deadline without forecasting another crew decision");
        var boss=new Game();
        while(boss.Stage<2||boss.Round<2){if(boss.Phase==Phase.Camp)boss.Camp(boss.Stage==0?"coolant":"edge");else if(boss.Actor!.Hero)boss.Act(boss.Stage==2?new(Kind.Guard):Probe.Choose(boss));else boss.ResolveEnemy();}
        foreach(var hero in boss.Units.Where(u=>u.Hero)){hero.Hp=hero.MaxHp;hero.Scorch=0;hero.Shield=0;}
        boss.Act(new(Kind.Guard));
        var steam=ResponseForecast.Calculate(boss,new(Kind.Cover,1));
        check(steam.Units.Single(u=>u.Id==0).Hp==32&&steam.Units.Single(u=>u.Id==1).Hp==25&&steam.Units.Single(u=>u.Id==2).Hp==14,"Gout bypasses Cover; Neri's start-turn scorch is included");
        check(steam.Describe().Contains("Stop BEFORE Neri")&&steam.Describe().Contains("No later crew action"),"Forecast names its decision boundary rather than claiming a complete plan");
        var branches=0;
        foreach(var a in new[]{"coolant","sparks"})foreach(var b in new[]{"plates","edge"})
        {
            var g=new Game();
            for(var step=0;step<512&&g.Phase is Phase.Combat or Phase.Camp;step++)
            {
                if(g.Phase==Phase.Camp){g.Camp(g.Stage==0?a:b);continue;}
                if(!g.Actor!.Hero){g.ResolveEnemy();continue;}
                var before=Probe.State(g);
                foreach(var command in g.Legal())
                {
                    var prediction=ResponseForecast.Calculate(g,command);var actual=Journal.Decode(Journal.Encode(g));var start=actual.Log.Count;
                    actual.Act(command);var enemies=0;while(actual.Phase==Phase.Combat&&!actual.Actor!.Hero){actual.ResolveEnemy();enemies++;}
                    check(prediction.Phase==actual.Phase&&prediction.NextActor==actual.Actor?.Name&&prediction.Round==actual.Round&&prediction.EnemyActions==enemies,"Forecast stop equals accepted action/enemy sequence from replay");
                    check(prediction.Sparks==actual.Sparks&&prediction.Kits==actual.Kits&&prediction.Events.SequenceEqual(actual.Log.Skip(start)),"Forecast supplies and full event chain match actual resolution");
                    check(prediction.Units.All(u=>{var v=actual.Find(u.Id);return u.Hp==v.Hp&&u.Shield==v.Shield&&u.Scorch==v.Scorch&&u.Pinned==v.Pinned&&u.Covers==v.Covers&&u.Front==v.Front;}),"Forecast unit state matches resolution including expiries and scorch");
                    check(Probe.State(g)==before,"Forecast leaves live history, threats, cursor, health and supplies unchanged");branches++;
                }
                g.Act(Probe.Choose(g));
            }
        }
        Console.Error.WriteLine($"Response forecasts compared against execution: {branches} legal branches across four declared campaign policies.");
    }
}
