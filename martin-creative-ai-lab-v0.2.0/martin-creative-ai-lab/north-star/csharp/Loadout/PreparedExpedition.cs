using System;
using System.Collections.Generic;
using NorthStar.Crossing;
using NorthStar.Domain;
using NorthStar.Forge;
using A=NorthStar.Crossing.Action;

namespace NorthStar.Loadout
{
    /// <summary>Original preparation experiment. Catalog names are not approved class/background canon.</summary>
    public sealed class PreparedExpedition
    {
        private readonly Expedition expedition=new Expedition();
        private readonly LoadoutCatalog catalog=Catalog();
        private PreparedLoadout current=new PreparedLoadout("anchor","workshop",new string?[]{"brace",null,null,null});
        public static LoadoutCatalog Catalog()=>new LoadoutCatalog(new[]{"anchor","lure"},new[]{"workshop","trailborn"},
            new[]{new BackgroundPermission("anchor","workshop"),new BackgroundPermission("anchor","trailborn"),new BackgroundPermission("lure","trailborn")},
            new[]{new SkillDefinition("brace","anchor",1,PreparedAction.Skill),new SkillDefinition("draw","lure",1,PreparedAction.Skill),new SkillDefinition("dash",null,2,PreparedAction.Dash)});
        public PreparedLoadout Preparation=>current;
        public bool Active=>expedition.Active;
        public bool Complete=>expedition.Complete;
        public bool Won=>expedition.Won;
        public int Stage=>expedition.Stage;
        public int Health=>expedition.Health;
        public int Resolve=>expedition.Resolve;
        public int Position=>expedition.Position;
        public int Beat=>expedition.Beat;
        public int Attempts=>expedition.Attempts;
        public int ConsumedRigs=>expedition.ConsumedRigs;
        public int Transactions=>expedition.Transactions;
        public Rig CurrentRig=>expedition.CurrentRig;
        public ProgressionView Progression=>expedition.Progression;
        public IReadOnlyDictionary<string,int> Inventory=>expedition.Inventory;
        public string Last {get;private set;}="Choose an explicit four-slot proposal. Empty slots are permitted.";
        public string Threat=>expedition.Threat;
        public int RequiredPosition=>expedition.RequiredPosition;
        public int MaximumBeats=>expedition.MaximumBeats;
        public bool Replace(string classId,string backgroundId,IEnumerable<string?> slots)
        {
            if(Active||Complete){Last="Preparation is locked during/after the expedition.";return false;}
            try
            {
                var proposal=new PreparedLoadout(classId,backgroundId,slots);catalog.Validate(proposal,Progression.Level);
                current=proposal;Last="Whole preparation committed. No incompatible slots were silently erased.";return true;
            }
            catch(ArgumentException){Last="Preparation rejected; class, background and all slots unchanged.";return false;}
        }
        public CraftResult Craft(string requestId,string recipeId)
        {var result=expedition.Craft(requestId,recipeId);Last=result.Reason;return result;}
        public bool Allocate(Allocation axis,long points)
        {bool result=expedition.Allocate(axis,points);Last=expedition.Last;return result;}
        public bool Begin(Rig rig)
        {
            if(Active||Complete){Last="Entry rejected; preparation and supplies unchanged.";return false;}
            // Revalidate current level and the entire committed preparation before any rig consumption.
            try{catalog.Validate(current,Progression.Level);}catch(ArgumentException){Last="Committed preparation is invalid; entry rejected.";return false;}
            bool accepted=expedition.Begin(rig,current.ClassId=="anchor"?Approach.Anchor:Approach.Lure);
            Last=expedition.Last;return accepted;
        }
        public bool UseSlot(int slot)
        {
            if(!Active)return false;
            PreparedAction action;
            try{action=catalog.ActionFor(current,slot,Progression.Level);}
            catch(ArgumentException){Last="Empty, invalid or locked slot; no turn, resource or position changed.";return false;}
            bool accepted=expedition.Act(action==PreparedAction.Skill?A.Skill:A.Dash);Last=expedition.Last;return accepted;
        }
        public bool Walk(){bool accepted=expedition.Act(A.Walk);Last=expedition.Last;return accepted;}
        public bool Wait(){bool accepted=expedition.Act(A.Wait);Last=expedition.Last;return accepted;}
        public object Snapshot()=>new {class_id=current.ClassId,background_id=current.BackgroundId,slots=current.Slots,
            active=Active,complete=Complete,won=Won,stage=Stage,beat=Beat,position=Position,health=Health,resolve=Resolve,
            rig=CurrentRig.ToString(),attempts=Attempts,consumed_rigs=ConsumedRigs,transactions=Transactions,inventory=Inventory,
            level=Progression.Level,xp=Progression.TotalXp,unspent=Progression.UnspentMain,vitality=Progression.Vitality,focus=Progression.Focus};
    }
}
