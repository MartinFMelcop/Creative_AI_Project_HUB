using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using NorthStar.AvailabilityHost;
static class Review
{
 static readonly List<string> checks=new();
 static void Check(bool ok,string name){if(!ok)throw new InvalidOperationException(name);checks.Add(name);}
 static void Act(JourneyOwner g,params string[] cmds){foreach(string c in cmds)if(!g.Execute(c))throw new InvalidOperationException("Unexpected setup refusal: "+c);}
 static string Facts(JourneyOwner g){var s=g.Snapshot();return JsonSerializer.Serialize(new{s.Stage,s.Route,s.TotalPhase,s.Integrity,s.Water,s.Delivered,s.WateredBeds,s.Encounter});}
 static bool Dry(JourneyOwner g)=>g.Snapshot().WateredBeds.Count==2&&g.Snapshot().WateredBeds.All(x=>!x);
 static int Main()
 {
  var noJar=new JourneyOwner();string start=Facts(noJar);Check(!noJar.Execute("route fast")&&Facts(noJar)==start&&Dry(noJar),"no acquired jar cannot depart or water");
  var ready=new JourneyOwner();Act(ready,"reserve","shape");string before=Facts(ready);Check(!ready.Execute("route fast")&&Facts(ready)==before&&Dry(ready),"ready but uncollected fired work cannot become cargo");
  var edge=new JourneyOwner();Act(edge,"alone","route sheltered","skill","skill","walk");var pre=edge.Snapshot();Check(pre.Encounter!.Health==10&&pre.Encounter!.Beat==3&&pre.Integrity==1,"predeclared final-survey damage boundary reached");Act(edge,"walk");var after=edge.Snapshot();Check(after.Encounter!.Health==6&&after.Encounter!.Won&&!after.Encounter!.Complete&&!after.Encounter!.Active,"actual child won survey at positive HP after damaging last action");Check(after.Stage=="broken"&&after.Integrity==0&&after.Water==0&&Dry(edge),"survey-win transition cannot hide damaging cargo contact");before=Facts(edge);Check(!edge.Execute("deliver")&&Facts(edge)==before&&Dry(edge),"broken cargo cannot water despite positive HP and child survey win");
  var safe=new JourneyOwner();Act(safe,"reserve","shape","collect","route fast","skill","skill","walk","skill");Check(safe.Stage=="interlude"&&safe.Water==2&&Dry(safe),"actual survey alone leaves both beds dry");before=Facts(safe);Check(!safe.Execute("deliver")&&Facts(safe)==before,"survey completion cannot masquerade as final watering");Act(safe,"continue","skill","skill","walk","skill","walk","skill");var arrival=safe.Snapshot();Check(arrival.Stage=="arrival"&&arrival.Encounter!.Complete&&arrival.Encounter!.Won&&arrival.Water==2&&arrival.Delivered==0&&Dry(safe),"actual completed arrival remains carried water and unwatered beds");Act(safe,"deliver");var delivered=safe.Snapshot();Check(delivered.WateredBeds.Count==2&&delivered.WateredBeds.All(x=>x)&&delivered.Delivered==2&&delivered.Water==0,"explicit pour waters each original bed exactly once");before=Facts(safe);Check(!safe.Execute("deliver")&&Facts(safe)==before,"duplicate pour cannot rewater or increment delivered");
  bool immutable=false;try{((IList<bool>)delivered.WateredBeds)[0]=false;}catch(NotSupportedException){immutable=true;}Check(immutable&&safe.Snapshot().Delivered==2,"external view cannot edit bed facts");
  Console.WriteLine(JsonSerializer.Serialize(new{scope="Independent targeted actual C# journey checks; not participants or an independent model score",passed=checks.Count,checks,damageBoundary=after,arrival,delivered}));return 0;
 }
}
