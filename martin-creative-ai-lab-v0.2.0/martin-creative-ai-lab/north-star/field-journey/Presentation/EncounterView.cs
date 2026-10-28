using System;
namespace NorthStar.FieldPresentation
{
    // Immutable facts captured from the existing authoritative intake, never a game owner.
    public sealed class Facts
    {
        public bool Confirmed {get;} public string? Handle {get;} public string? Accent {get;} public string? ClassId {get;}
        public string Rig {get;} public int Attempts {get;} public int Stage {get;} public bool Active {get;} public bool Won {get;} public bool Complete {get;}
        public int Beat {get;} public int Position {get;} public int Health {get;} public int Resolve {get;} public string Threat {get;}
        public Facts(bool confirmed,string? handle,string? accent,string? classId,string rig,int attempts,int stage,bool active,bool won,bool complete,int beat,int position,int health,int resolve,string threat)
        {
            if(attempts<0||stage<0||stage>1||beat<0||beat>6||position<0||position>8||health<0||resolve<0||confirmed&&(handle==null||accent==null||classId==null)||active&&(won||complete))throw new ArgumentException("Actual bounded encounter facts required.");
            Confirmed=confirmed;Handle=handle;Accent=accent;ClassId=classId;Rig=rig;Attempts=attempts;Stage=stage;Active=active;Won=won;Complete=complete;Beat=beat;Position=position;Health=health;Resolve=resolve;Threat=threat??throw new ArgumentNullException(nameof(threat));
        }
    }
    public sealed class PersonView
    {
        public string? handle {get;} public string? accent {get;} public string? class_id {get;} public string rig {get;} public bool confirmed {get;}
        internal PersonView(Facts f){confirmed=f.Confirmed;handle=f.Confirmed?f.Handle:null;accent=f.Confirmed?f.Accent:null;class_id=f.Confirmed?f.ClassId:null;rig=f.Attempts>0?f.Rig:"none";}
    }
    public sealed class Encounter
    {
        public string phase {get;} public string outcome=>phase; public int stage {get;} public int owner_stage {get;} public bool active {get;} public bool complete {get;} public bool won {get;}
        public int beat {get;} public int max_beats {get;} public int position {get;} public int required_position {get;} public int world_end=>8; public bool threshold_reached {get;} public int health {get;} public int resolve {get;} public string threat_kind {get;} public string threat_text {get;}
        internal Encounter(Facts f)
        {
            phase=f.Active?"active":f.Complete?"complete":f.Won?"survey-won":f.Attempts>0?"failed":f.Confirmed?"preparation":"unconfirmed";
            owner_stage=f.Stage;
            // Session immediately advances owner Stage on survey victory. The ended
            // encounter still belongs to its surveyed2-cell/four-beat objective.
            stage=f.Won&&!f.Complete?f.Stage-1:f.Stage;
            required_position=stage==0?2:4;max_beats=stage==0?4:6;
            active=f.Active;complete=f.Complete;won=f.Won;beat=f.Beat;position=f.Position;health=f.Health;resolve=f.Resolve;
            threshold_reached=f.Attempts>0&&position>=required_position;
            threat_kind=!active?"none":f.Threat.StartsWith("PULSE",StringComparison.Ordinal)?"pulse":"bolt";
            threat_text=active?f.Threat:"No active encounter threat.";
        }
    }
    public sealed class Response
    {
        public string command {get;} public bool accepted {get;} public string kind {get;} public long event_sequence {get;} public int from_position {get;} public int to_position {get;} public int health_lost {get;} public int resolve_spent {get;} public int resolve_gained {get;} public bool moved=>from_position!=to_position; public string contact {get;}
        internal Response(string command,bool accepted,string kind,long sequence,int from,int to,int lost,int spent,int gained,string contact)
        {this.command=command;this.accepted=accepted;this.kind=kind;event_sequence=sequence;from_position=from;to_position=to;health_lost=lost;resolve_spent=spent;resolve_gained=gained;this.contact=contact;}
    }
    public sealed class View
    {
        public PersonView person {get;} public Encounter encounter {get;} public Response action {get;}
        internal View(Facts f,Response response){person=new PersonView(f);encounter=new Encounter(f);action=response;}
    }
    public static class Projector
    {
        public static Response Initial()=>new Response("initial",false,"none",0,0,0,0,0,0,"none");
        public static View Observe(Facts facts,Response response)=>new View(facts??throw new ArgumentNullException(nameof(facts)),response??throw new ArgumentNullException(nameof(response)));
        public static Response Transition(Facts before,Facts after,string command,bool accepted,string requestedKind,long previousSequence)
        {
            if(before==null||after==null||command==null||previousSequence<0)throw new ArgumentException("Actual transition required.");
            bool beat=accepted&&before.Active&&after.Attempts==before.Attempts&&after.Beat==before.Beat+1;
            if(beat)
            {
                if(requestedKind!="walk"&&requestedKind!="dash"&&requestedKind!="skill"&&requestedKind!="wait")throw new ArgumentException("Actual action kind required.");
                int lost=Math.Max(0,before.Health-after.Health),spent=Math.Max(0,before.Resolve-after.Resolve),gained=Math.Max(0,after.Resolve-before.Resolve);
                bool pulse=before.Threat.StartsWith("PULSE",StringComparison.Ordinal);
                string contact=lost>0?"hurt":pulse&&after.Position!=before.Position?"evaded":!pulse&&requestedKind=="skill"?"protected":"none";
                return new Response(command,true,requestedKind,checked(previousSequence+1),before.Position,after.Position,lost,spent,gained,contact);
            }
            string kind=!accepted?"refused":command=="begin"&&after.Attempts==before.Attempts+1?"entry":command=="confirm"?"confirmation":command=="draft"||command=="review"||command=="allocate"?"preparation":"workshop";
            // Entry resets and non-encounter changes are never narrated as healing,
            // paid damage, protection or an accepted encounter response.
            return new Response(command,accepted,kind,previousSequence,after.Position,after.Position,0,0,0,"none");
        }
    }
}
