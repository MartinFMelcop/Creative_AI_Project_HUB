using Cinder.Core;
using Cinder.Checks;

var count=0;
void Check(bool value,string message) { count++; if(!value)throw new Exception(message); }
var game=new Game();
Check(game.Actor!.Name=="Vale" && game.Order.SequenceEqual(new[]{1,0,3,2,4}),"Opening initiative");
Check(!game.Legal().Contains(new(Kind.Strike,4)) && game.Legal().Contains(new(Kind.Pierce,4)),"Enemy front screens Strike, not Pierce");
var unchanged=Probe.State(game);
Check(!game.Act(new(Kind.Mend,0)) && Probe.State(game)==unchanged,"Illegal action has no effects");
Check(!game.ResolveEnemy() && Probe.State(game)==unchanged,"No enemy resolution on hero turn");
foreach(var c in game.Legal()) { Check(game.Preview(c)!="Unavailable","Legal preview"); Check(Probe.State(game)==unchanged,"Preview must not mutate live state"); }
game.Act(new(Kind.Pin,3));
Check(game.Sparks==2 && game.Find(3).Hp==19 && game.Actor!.Id==0,"Pin spends one shared cell and one turn");
Check(game.Threats[3].Attack==Attack.Bite && game.Find(3).Pinned,"Pin cancels locked intent");
game.Act(new(Kind.Cover,1)); var hp=game.Find(0).Hp; game.ResolveEnemy();
Check(game.Find(0).Hp==hp,"Pinned bite cannot land");
game.Act(new(Kind.Guard)); game.ResolveEnemy();
Check(game.Find(0).Hp==hp-1 && game.Find(1).Hp==30 && game.Find(0).Covers==-1,"Cover redirects one 7-damage bolt through 6 shield");
game.Act(new(Kind.Strike,3));
Check(!game.Legal().Any(c=>c.Kind==Kind.Cover && c.Target==0),"No self cover");
Check(game.Find(0).Shield==0,"Shield expires at owner's next turn");
Check(!game.Legal().Any(c=>c.Kind==Kind.Pin && game.Order.Take(game.Cursor+1).Contains(c.Target)),"Pin cannot spend cells on an already resolved enemy");
var rows=new Game(); rows.Act(new(Kind.Shift)); rows.Act(new(Kind.Shift)); rows.ResolveEnemy();
Check(rows.Find(2).Hp==19 && rows.Find(0).Hp==38,"All-rear formation has no melee screen");
var losses=new Game();
while(losses.Phase==Phase.Combat) { if(losses.Actor!.Hero)losses.Act(new(Kind.Guard));else losses.ResolveEnemy(); }
Check(losses.Phase==Phase.Defeat && losses.Round==13,"Brace-only strategy cannot defeat the pressure deadline");
var journeys=new List<object>();
foreach(var first in new[]{"coolant","sparks"}) foreach(var second in new[]{"plates","edge"})
{
    var g=Probe.Finish(first,second);
    journeys.Add(new { first,second,g.Phase,g.Sparks,g.Kits,hp=g.Units.Where(u=>u.Hero).Select(u=>u.Hp).ToArray(),actions=g.Journal.Count });
    Console.Error.WriteLine($"{first}/{second}: {g.Phase}; HP {string.Join(',',g.Units.Where(u=>u.Hero).Select(u=>u.Hp))}; kits {g.Kits}; cells {g.Sparks}");
    Check(g.Phase==Phase.Victory,$"Complete journey failed: {first}/{second}");
    Check(g.Stage==2 && g.Sparks>=0 && g.Kits>=0 && g.Log.Any(s=>s.Contains("gallery")),"Actual connected encounters and supplies");
    Check(Probe.State(Journal.Decode(Journal.Encode(g)))==Probe.State(g),"Full campaign save replay");
    Check(!g.Camp("edge") && !g.Act(new(Kind.Guard)) && !g.ResolveEnemy(),"Terminal state blocks further play");
}
var repair=new Game();
while(repair.Phase==Phase.Combat) {if(repair.Actor!.Hero)repair.Act(Probe.Choose(repair));else repair.ResolveEnemy();}
repair.Camp("coolant");
while(repair.Round==1) {if(repair.Actor!.Hero)repair.Act(new(Kind.Strike,3));else repair.ResolveEnemy();}
Check(repair.Log.Any(s=>s.StartsWith("Patch drone repairs Bulwark")),"Leaving the screened drone alive repairs real damage");
var burn=new Game();
while(burn.Stage<2) {if(burn.Phase==Phase.Camp)burn.Camp(burn.Stage==0?"coolant":"edge");else if(burn.Actor!.Hero)burn.Act(Probe.Choose(burn));else burn.ResolveEnemy();}
while(burn.Round<3 && burn.Phase==Phase.Combat) {if(burn.Actor!.Hero)burn.Act(new(Kind.Guard));else burn.ResolveEnemy();}
Check(burn.Log.Any(s=>s.Contains("scorched for two turns")) && burn.Units.Any(u=>u.Hero&&u.Scorch>0),"Gout applies actual timed scorch");
// Controlled injury fixture isolates Mend from the campaign controller's prior kit use.
var treatment=new Game();treatment.Find(2).Hp=18;treatment.Find(2).Scorch=2;
treatment.Act(new(Kind.Guard));treatment.Act(new(Kind.Guard));treatment.ResolveEnemy();
var kit=treatment.Kits;
Check(treatment.Find(2).Scorch==1 && treatment.Find(2).Hp==16,"Scorch ticks at the owner's turn before input");
Check(treatment.Act(new(Kind.Mend,2)) && treatment.Find(2).Scorch==0 && treatment.Kits==kit-1 && treatment.Find(2).Hp==28,"Treatment clears scorch and consumes a kit");
var expiry=new Game();expiry.Find(2).Scorch=2;
while(expiry.Round<2 || expiry.Actor!.Id!=2) {if(expiry.Actor!.Hero)expiry.Act(new(Kind.Guard));else expiry.ResolveEnemy();}
Check(expiry.Find(2).Scorch==0 && expiry.Find(2).Hp==24,"Two scorch ticks expire at own turns, through expired Brace");
var incapacitated=Probe.Finish();incapacitated.Find(0).Hp=0;incapacitated.Find(2).Hp=0;
var ending=Content.Ending(incapacitated);
Check(ending.Contains("Vale lifts") && ending.Contains("Rook and Neri cannot stand") && !ending.Contains("Rook takes"),"Ending respects declared down-hero fixture");
var partial=new Game();
for(var i=0;i<20;i++)
{
    if(partial.Phase==Phase.Camp) partial.Camp("coolant");
    else if(partial.Actor!.Hero)partial.Act(Probe.Choose(partial)); else partial.ResolveEnemy();
    Check(Probe.State(Journal.Decode(Journal.Encode(partial)))==Probe.State(partial),"Replay preserves every intermediate turn");
}
foreach(var text in new[]{"null","{}","{\"schema\":99,\"version\":\"0.1.0\",\"actions\":[]}","{\"schema\":1,\"version\":\"0.1.0\",\"actions\":[{\"op\":\"enemy\"}]}","{\"schema\":1,\"version\":\"0.1.0\",\"actions\":[null]}"})
{
    var rejected=false; try {Journal.Decode(text);}catch(Exception e)when(e is System.Text.Json.JsonException or InvalidDataException){rejected=true;}
    Check(rejected,"Malformed or impossible save rejected");
}
var naive=Probe.Finish(simple:true);
Console.WriteLine(System.Text.Json.JsonSerializer.Serialize(new {checks=count,journeys,naive=new{naive.Phase,actions=naive.Journal.Count},assessment="Synthetic implementing-agent policies; no human balance evidence"},Journal.Json));
