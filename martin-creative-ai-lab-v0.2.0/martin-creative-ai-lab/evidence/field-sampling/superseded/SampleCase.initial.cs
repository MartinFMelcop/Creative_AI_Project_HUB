using System;

namespace NorthStar.FieldSampling
{
    // Original destination setup. These are observations of the existing encounter,
    // never another health, clock, inventory or completion authority.
    public sealed class Facts
    {
        public bool Confirmed {get;}
        public int Attempt {get;}
        public int Stage {get;}
        public int Position {get;}
        public int Beat {get;}
        public int Health {get;}
        public bool Active {get;}
        public bool Won {get;}
        public bool Complete {get;}
        public Facts(bool confirmed,int attempt,int stage,int position,int beat,int health,bool active,bool won,bool complete)
        {
            if(attempt<0||stage<0||stage>1||position<0||position>8||beat<0||beat>6||health<0)throw new ArgumentException("Bounded actual encounter facts required.");
            Confirmed=confirmed;Attempt=attempt;Stage=stage;Position=position;Beat=beat;Health=health;Active=active;Won=won;Complete=complete;
        }
    }
    public sealed class Receipt
    {
        public string site {get;}
        public int attempt {get;}
        public int before_beat {get;}
        public int after_beat {get;}
        public int hp_before {get;}
        public int hp_after {get;}
        public int health_lost=>hp_before-hp_after;
        public bool acquired {get;}
        internal Receipt(string site,Facts before,Facts after,bool acquired)
        {this.site=site;attempt=before.Attempt;before_beat=before.Beat;after_beat=after.Beat;hp_before=before.Health;hp_after=after.Health;this.acquired=acquired;}
    }
    public sealed class SampleCase
    {
        private string status="empty";
        private bool spent,acquired;
        private string? site;
        private int? attempt;
        private Receipt? receipt;
        public static void ValidateSite(string id)
        {if(id!="ridge"&&id!="channel")throw new ArgumentException("Exact original sampling site required.");}
        public bool CanCollect(string id,Facts facts)
        {
            ValidateSite(id);
            return status=="empty"&&!spent&&facts.Confirmed&&facts.Active&&facts.Health>0&&
                facts.Stage==(id=="ridge"?0:1)&&facts.Position==(id=="ridge"?1:2);
        }
        public void Collect(string id,Facts before,Facts after)
        {
            if(!CanCollect(id,before))throw new ArgumentException("Collection is unavailable at the actual site/state.");
            // The private adapter must first receive an accepted actual Wait. Check its
            // irreversible beat/cost facts before committing this separate case ledger.
            if(after.Attempt!=before.Attempt||after.Beat!=before.Beat+1||after.Position!=before.Position||after.Health>before.Health||!after.Confirmed)
                throw new ArgumentException("Accepted unchanged-position Wait facts required.");
            bool survived=after.Health>0&&(after.Active||after.Won||after.Complete);
            spent=true;site=id;attempt=before.Attempt;acquired=survived;
            status=survived?(after.Complete?"secured":"carried"):"lost";
            receipt=new Receipt(id,before,after,survived);
        }
        public void ObserveAcceptedTransition(Facts before,Facts after)
        {
            // Only actual accepted encounter transitions call this method. Reads,
            // preparation, new entry and old ended state cannot settle the cargo.
            if(status!="carried"||!before.Active||after.Attempt!=before.Attempt||after.Beat!=before.Beat+1)return;
            if(after.Complete&&after.Health>0)status="secured";
            else if(!after.Active&&!after.Won&&!after.Complete)status="lost";
        }
        public object Snapshot(Facts facts)=>new {
            status,case_spent=spent,acquired,site,collection_attempt=attempt,receipt,
            sites=new[]{new {id="ridge",stage=0,position=1,eligible=CanCollect("ridge",facts)},new {id="channel",stage=1,position=2,eligible=CanCollect("channel",facts)}}
        };
    }
}
