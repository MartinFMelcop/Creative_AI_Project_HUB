using System;
using System.Collections.Generic;
using NorthStar.Crossing;
using NorthStar.Domain;
using CrossingAction = NorthStar.Crossing.Action;

namespace NorthStar.Forge
{
    public enum Rig { Unprepared, Plate, Trail }
    /// <summary>Separate supplies experiment composing the unchanged Crossing consumer.</summary>
    public sealed class Expedition
    {
        private readonly Session session=new Session();
        private readonly CraftInventory inventory;
        private int attempt;
        public Rig CurrentRig {get;private set;}
        public string Last {get;private set;}="Two rigs worth of supplies. Failed encounters never refund them.";
        public int Attempts=>attempt;
        public int ConsumedRigs {get;private set;}
        public bool Active=>session.Active;
        public bool Complete=>session.Complete;
        public bool Won=>session.Won;
        public int Stage=>session.Stage;
        public int Beat=>session.Beat;
        public int Position=>session.Position;
        public int Health=>session.Health;
        public int Resolve=>session.Resolve;
        public int MaximumHealth=>session.MaximumHealth;
        public int MaximumResolve=>session.MaximumResolve;
        public int MaximumBeats=>session.MaximumBeats;
        public int RequiredPosition=>session.RequiredPosition;
        public string Threat=>session.Threat;
        public ProgressionView Progression=>session.Progression;
        public IReadOnlyDictionary<string,int> Inventory=>inventory.Snapshot;
        public int Transactions=>inventory.CommittedCount;
        public static CraftRecipe[] Recipes()=>new[] {
            new CraftRecipe("plate_rig","workbench","survey_license",new[]{new MaterialAmount("fiber",2),new MaterialAmount("binder",1)},new[]{new MaterialAmount("plate_rig",1)}),
            new CraftRecipe("trail_rig","workbench","survey_license",new[]{new MaterialAmount("fiber",2),new MaterialAmount("binder",1)},new[]{new MaterialAmount("trail_rig",1)}) };
        public Expedition()
        {
            inventory=new CraftInventory(new[]{new MaterialAmount("fiber",4),new MaterialAmount("binder",2)},Recipes(),new[]{"survey_license"});
        }
        public CraftResult Craft(string requestId,string recipeId,string station="workbench")
        {
            if(Active || Complete)return new CraftResult(false,false,"Crafting unavailable during or after expedition.");
            if(requestId!=null && requestId.StartsWith("entry_",StringComparison.Ordinal))return new CraftResult(false,false,"Reserved expedition request namespace.");
            var result=inventory.Craft(requestId!,recipeId,station);Last=result.Reason;return result;
        }
        public bool Allocate(Allocation axis,long amount)
        {bool accepted=session.Allocate(axis,amount);Last=accepted?"Earned allocation committed.":"Allocation rejected; state unchanged.";return accepted;}
        public bool Begin(Rig rig) => Begin(rig,rig==Rig.Trail?Approach.Lure:Approach.Anchor);
        public bool Begin(Rig rig,Approach approach)
        {
            if(Active || Complete || !Enum.IsDefined(typeof(Rig),rig) || !Enum.IsDefined(typeof(Approach),approach)) {Last="Entry rejected; state unchanged.";return false;}
            string item=rig==Rig.Plate?"plate_rig":"trail_rig";
            if(rig!=Rig.Unprepared && inventory.Quantity(item)<1){Last="Requested rig unavailable; no materials or encounter state changed.";return false;}
            // All external validation precedes consumption. Private session has matching preparation preconditions.
            if(rig!=Rig.Unprepared)
            {
                var result=inventory.Consume("entry_"+attempt,item,1);
                if(!result.Applied){Last=result.Reason;return false;}
            }
            if(!session.Prepare(approach,rig==Rig.Trail?Outfit.Trail:Outfit.Plate) || !session.Begin())
                throw new InvalidOperationException("Private encounter violated validated entry preconditions.");
            CurrentRig=rig;attempt++;if(rig!=Rig.Unprepared)ConsumedRigs++;
            Last="Encounter committed. "+(rig==Rig.Unprepared?"Unprepared: skill unavailable; walk/dash/wait remain.":"One "+rig+" rig consumed; no refund on failure.");return true;
        }
        public bool Act(CrossingAction action)
        {
            if(!Active || !Enum.IsDefined(typeof(CrossingAction),action))return false;
            if(action==CrossingAction.Skill && CurrentRig==Rig.Unprepared){Last="No prepared rig: skill rejected without advancing time or spending resources.";return false;}
            bool accepted=session.Act(action);Last=session.Last;return accepted;
        }
    }
}
