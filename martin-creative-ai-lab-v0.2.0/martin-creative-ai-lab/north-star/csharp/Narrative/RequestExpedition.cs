using System;
using System.Collections.Generic;
using NorthStar.Crossing;
using A=NorthStar.Crossing.Action;

namespace NorthStar.Narrative
{
    /// <summary>Original bounded request scene. Facts are owned here; callers cannot mark objectives complete.</summary>
    public sealed class RequestExpedition
    {
        private readonly Session encounter=new Session();
        private readonly List<object> receipts=new List<object>();
        private int consentRevision=-1,draftRevision=-1;
        private string? draftTerm;
        private string encounterKind="none";
        private bool deliveryStarted;
        public int Revision {get;private set;}
        public int Shift {get;private set;}
        public int Remaining=>4-Shift;
        public int Crates {get;private set;}
        public int Capacity=>GuideAvailable?2:1;
        public bool GuideAvailable {get;private set;}=true;
        public string GuideLocation=>GuideAvailable?"local":!deliveryStarted?"local-preparing":Status=="failed"?"unaccounted":"travelling";
        public bool Surveyed {get;private set;}
        public bool Delivered {get;private set;}
        public bool Returned {get;private set;}
        public bool Active=>encounter.Active;
        public string Status {get;private set;}="open";
        public string Conversation {get;private set;}="closed";
        public string? Term {get;private set;}
        public string Last {get;private set;}="Edda sets a coil beside five shutter crates. 'The shutters close our store before dark. The coil is for the far bank.' Rill hooks a boot under the board. 'Not on an unchecked route. Survey it first. This line stays here.'";
        public bool DueElapsed=>Term=="dusk"&&Remaining==0&&!Returned&&Status!="deferred";
        public RequestExpedition(){encounter.Prepare(Approach.Lure,Outfit.Trail);}
        private bool Refuse(string message){Last=message;return false;}
        private bool CanTalk=>!Active&&Status!="committed"&&Status!="delivered"&&Status!="failed"&&Status!="declined";
        private void Changed(){Revision++;consentRevision=-1;draftRevision=-1;draftTerm=null;Conversation="closed";}
        public bool Open()
        {
            if(!CanTalk)return Refuse("The request cannot reopen during travel or after commitment/result.");
            Conversation="table";consentRevision=-1;draftRevision=-1;draftTerm=null;
            Last=$"Edda unfolds a clean slip beside the work list: {5-Crates} crates remain, {Remaining} shifts of light, capacity {Capacity} per shift. No coil or guide has left.";return true;
        }
        public bool Hear()
        {
            if(!CanTalk||Conversation!="table")return Refuse("Open a current consultation first.");
            if(!Surveyed||!GuideAvailable||Remaining<2)return Refuse("Rill tightens the line on its peg. 'No offer from me without a surveyed route and two shifts for this trip.'");
            consentRevision=Revision;
            Last=$"Rill sets his hook beside the coil. 'I can guide this trip. {5-Crates} shutters still need carrying here. Write my limit, then ask me to sign.'";return true;
        }
        public bool Offer()
        {
            if(!CanTalk||Conversation!="table"||consentRevision!=Revision)return Refuse("No fresh guide offer: hear Rill against the current work list.");
            draftRevision=Revision;draftTerm=null;Conversation="terms";
            Last=$"Edda leaves the line on its peg. 'An offer is not a departure. Guided travel takes two shifts; {Remaining} remain. Once signed, Rill prepares the coil and is unavailable for shutters even before departure; local capacity becomes one crate per shift.'";return true;
        }
        public bool Terms(string term)
        {
            if(!CanTalk||Conversation!="terms"||draftRevision!=Revision||term!="dusk"&&term!="open")return Refuse("Terms rejected; no commitment or resource changed.");
            draftTerm=term;Conversation="ready";
            Last=term=="dusk"?"Edda writes 'return due before dark'. The return box stays empty. Rill waits for confirmation.":"Edda writes 'no return time agreed'. The return box stays empty. Rill waits for confirmation.";return true;
        }
        public bool Confirm()
        {
            if(!CanTalk||Conversation!="ready"||draftRevision!=Revision||consentRevision!=Revision||!GuideAvailable||Remaining<2||draftTerm==null)return Refuse("Confirmation refused: facts, offer and written terms must still be current.");
            Term=draftTerm;GuideAvailable=false;Status="committed";
            receipts.Add(new {kind="commitment",revision=Revision,shift=Shift,crates=Crates,term=Term,guide="Rill",delivered=false,returned=false});
            Changed();Last="Rill signs his own name, takes down the line and starts rigging the coil. Edda marks him unavailable for shutters. Departure is still pending; neither delivery nor return is checked.";return true;
        }
        public bool Defer()
        {
            if(!CanTalk)return Refuse("An accepted journey cannot be deferred through conversation.");
            Status="deferred";Changed();Last="Edda folds the unsigned slip. Rill replaces his hook and helps at the shutters. Nothing is promised; a later request needs the list and his answer as they stand then.";return true;
        }
        public bool Decline()
        {
            if(!CanTalk)return Refuse("An accepted journey cannot be refused retroactively.");
            Status="declined";Changed();Last="Edda writes 'no guide supplied'. Rill takes the near end of a shutter crate. The coil stays on the board; its far-bank delivery is not reported.";return true;
        }
        public bool Withdraw()
        {
            if(Status!="committed"||deliveryStarted||Active)return Refuse("Only a commitment before departure can be withdrawn; elapsed travel is never refunded.");
            GuideAvailable=true;Status="deferred";
            receipts.Add(new {kind="withdrawal",revision=Revision,shift=Shift,crates=Crates,term=Term,guide="Rill",delivered=false,returned=false});
            Term=null;Changed();Last="Rill hangs the line back on its peg. Edda adds a withdrawal below the signed commitment, keeping both entries readable. No departure occurred.";return true;
        }
        public bool Work()
        {
            if(Active||Remaining==0||Crates==5)return Refuse("Shutter work unavailable; no time or cargo changed.");
            int moved=Math.Min(Capacity,5-Crates);Crates+=moved;Shift++;Changed();
            Last=$"{(GuideAvailable?"Rill takes the other end. Together you":!deliveryStarted?"With Rill preparing the coil, you":Status=="failed"?"With Rill unaccounted for, you":"With Rill away, you")} carry {moved} shutter crate(s). {5-Crates} remain; {Remaining} shifts of light. Any unsigned offer needs a fresh conversation.";return true;
        }
        public bool Survey()
        {
            if(Active||Surveyed||Remaining<1||Status=="committed"||Status=="delivered"||Status=="failed")return Refuse("Survey entry unavailable.");
            if(!encounter.Begin())return Refuse("Survey model refused entry.");
            Shift++;Changed();encounterKind="survey";
            Last="You spend one shift reaching the route. Rill stays with the shutter crates. Survey is not yet complete: cross the actual announced threats.";return true;
        }
        public bool Depart(string mode)
        {
            bool guided=mode=="guided";
            if(mode!="guided"&&mode!="solo")return Refuse("Departure mode must be guided or solo.");
            int cost=guided?2:3;
            if(Active||!Surveyed||deliveryStarted||Remaining<cost||Delivered||Status=="failed"||guided&&Status!="committed"||!guided&&(!GuideAvailable||Status=="committed"))return Refuse("Departure refused: survey, time and actual ownership must permit this journey.");
            if(!encounter.Begin())return Refuse("Delivery model refused entry.");
            deliveryStarted=true;Shift+=cost;Changed();encounterKind=guided?"guided":"solo";
            if(!guided){Status="committed";Term="solo";receipts.Add(new {kind="solo_departure",revision=Revision,shift=Shift,crates=Crates,term=Term,guide="none",delivered=false,returned=false});}
            Last=$"You leave for the coil handoff by the {mode} route, spending {cost} shifts. {5-Crates} local shutter crates remain. The coil is carried, not delivered; the actual crossing still has to finish.";return true;
        }
        public bool Act(A action)
        {
            if(!Active)return Refuse("No active route; conversation cannot manufacture a crossing result.");
            if(!encounter.Act(action))return Refuse(encounter.Last);
            Last=encounter.Last;
            if(!Active)
            {
                if(encounterKind=="survey")
                {
                    Surveyed=encounter.Won;Changed();
                    Last+=Surveyed?" You return with the route survey. Rill checks the marked bolt lanes, then loosens the line. He has not offered this trip yet.":" The survey failed. Rill keeps the line on its peg; no guide or delivery was supplied.";
                }
                else
                {
                    Delivered=encounter.Complete&&encounter.Won;
                    Returned=Delivered;Status=Delivered?"delivered":"failed";
                    if(!Delivered)Last=Last.Replace("Reprepare and retry; no completion reward.","This delivery attempt has ended; no completion reward. Local work may continue if light remains.");
                    if(Delivered&&encounterKind=="guided")GuideAvailable=true;
                    receipts.Add(new {kind=Delivered?"observed_return":"failed_crossing",revision=Revision,shift=Shift,crates=Crates,term=Term,guide=encounterKind=="guided"?"Rill":"none",delivered=Delivered,returned=Returned});
                    Changed();
                    Last+=Delivered?$" You come back from the actual handoff{(encounterKind=="guided"?" with Rill":" alone")}. Edda checks coil delivered and return observed, then points at {5-Crates} shutter crates still here. The unfinished work is not erased.":$" You retreat to Edda's board without a completed handoff. She leaves delivery and completed-journey return unchecked. {(encounterKind=="guided"?"Rill is unaccounted for; this is not a confirmed death or return.":"You have returned from the failed attempt; no delivered coil or completed journey is recorded.")} {5-Crates} local crates remain.";
                }
            }
            return true;
        }
        public object Snapshot()=>new {revision=Revision,shift=Shift,remaining=Remaining,crates=Crates,crates_required=5,capacity=Capacity,guide_available=GuideAvailable,guide_location=GuideLocation,surveyed=Surveyed,delivered=Delivered,returned=Returned,status=Status,conversation=Conversation,term=Term,due_elapsed=DueElapsed,delivery_started=deliveryStarted,receipts=receipts.ToArray(),encounter=new {kind=encounterKind,active=Active,stage=encounter.Stage,beat=encounter.Beat,position=encounter.Position,health=encounter.Health,resolve=encounter.Resolve,required_position=encounter.RequiredPosition,maximum_beats=encounter.MaximumBeats,threat=encounter.Threat,xp=encounter.Progression.TotalXp},scope="In-session original experiment; no persistent quest, Unity/Windows or human validation"};
        public bool Command(string text)
        {
            string[] parts=(text??"").Trim().Split(' ',StringSplitOptions.RemoveEmptyEntries);
            if(parts.Length==0)return Refuse("Choose an explicit action.");
            if(parts.Length==2&&parts[0]=="terms")return Terms(parts[1]);
            if(parts.Length==2&&parts[0]=="depart")return Depart(parts[1]);
            if(parts.Length!=1)return Refuse("Unknown command shape; state unchanged.");
            switch(parts[0]){case "open":return Open();case "hear":return Hear();case "offer":return Offer();case "confirm":return Confirm();case "defer":return Defer();case "decline":return Decline();case "withdraw":return Withdraw();case "work":return Work();case "survey":return Survey();case "skill":return Act(A.Skill);case "walk":return Act(A.Walk);case "dash":return Act(A.Dash);case "wait":return Act(A.Wait);default:return Refuse("Unknown command; state unchanged.");}
        }
    }
}
