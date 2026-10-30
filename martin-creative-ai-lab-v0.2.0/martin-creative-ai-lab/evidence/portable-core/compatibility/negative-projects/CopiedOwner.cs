using System;
using NorthStar.Domain;

namespace NorthStar.Crossing
{
    public enum Approach { Anchor, Lure }
    public enum Outfit { Plate, Trail }
    public enum Action { Walk, Dash, Skill, Wait }
    /// <summary>Original turn-based C# destination experiment; not a port or final class canon.</summary>
    public sealed class Session
    {
        private readonly ProgressionState progression;
        public ProgressionView Progression => new ProgressionView(progression);
        public Approach Approach { get; private set; }
        public Outfit Outfit { get; private set; }
        public int Stage { get; private set; }
        public int Beat { get; private set; }
        public int Position { get; private set; }
        public int Health { get; private set; }
        public int Resolve { get; private set; }
        public int MaximumHealth { get; private set; }
        public int MaximumResolve { get; private set; }
        public int SpentResolve { get; private set; }
        public int Rejected { get; private set; }
        public bool Active { get; private set; }
        public bool Won { get; private set; }
        public bool Complete { get; private set; }
        public string Last { get; private set; } = "Prepare an approach, outfit and earned points.";
        public const int WorldEnd = 8;
        public int RequiredPosition => Stage == 0 ? 2 : 4;
        public int MaximumBeats => Stage == 0 ? 4 : 6;
        public bool Pulse => Stage == 0 ? Beat == 2 : Beat == 2 || Beat == 4;
        public string Threat => Pulse ? "PULSE at your current position: walking or dashing leaves it." : "BOLT: moving exposes health; the approach skill spends resolve to protect.";
        public Session()
        {
            // These are original experimental destination values, not the 180-level legacy balance.
            var curve = new ProgressionCurve(new[] {
                new LevelDefinition(1,0,0,0,0), new LevelDefinition(2,10,2,1,1),
                new LevelDefinition(3,25,2,1,1), new LevelDefinition(4,45,2,1,1) });
            progression = new ProgressionState(curve);
        }
        public bool Prepare(Approach approach, Outfit outfit)
        {
            if (Active || Complete || !Enum.IsDefined(typeof(Approach), approach) || !Enum.IsDefined(typeof(Outfit), outfit)) return false;
            Approach = approach; Outfit = outfit; return true;
        }
        public bool Allocate(Allocation allocation, long points)
        {
            if (Active || Complete) return false;
            try { progression.Allocate(allocation, points); return true; }
            catch (ArgumentException) { return false; }
        }
        public bool Begin()
        {
            if (Active || Complete) return false;
            MaximumHealth = checked((Outfit == Outfit.Plate ? 14 : 10) + (int)Progression.BonusHealth + (int)Progression.Vitality * 2);
            MaximumResolve = checked((Outfit == Outfit.Plate ? 6 : 10) + (int)Progression.BonusResolve + (int)Progression.Focus * 2);
            Health = MaximumHealth; Resolve = MaximumResolve; Beat = 0; Position = 0;
            SpentResolve = 0; Rejected = 0; Active = true; Won = false; Last = "Encounter committed. Preparation is locked."; return true;
        }
        public bool Act(Action action)
        {
            if (!Active || !Enum.IsDefined(typeof(Action), action)) return false;
            int cost = action == Action.Dash ? 1 : action == Action.Skill ? (Approach == Approach.Anchor ? 2 : 3) : 0;
            if (cost > Resolve) { Rejected++; Last = "Not enough resolve. No time, position or health changed."; return false; }
            Resolve -= cost; SpentResolve += cost;
            int previousPosition = Position;
            bool moved = action == Action.Walk || action == Action.Dash;
            // Lure draws the bolt while advancing one cell; Anchor protects in place.
            if (!Pulse && action == Action.Skill && Approach == Approach.Lure) Position = Math.Min(WorldEnd, Position + 1);
            if (moved) Position = Math.Min(WorldEnd, Position + (action == Action.Dash ? 2 : 1));
            if (action == Action.Walk) Resolve = Math.Min(MaximumResolve, Resolve + 2);
            int damage;
            if (Pulse) damage = Position != previousPosition ? 0 : (Stage == 0 ? 4 : 6);
            else damage = action == Action.Skill ? 0 : (Stage == 0 ? 4 : 6);
            Health = Math.Max(0, Health - damage); Beat++;
            Last = action + ": " + damage + " damage, " + cost + " resolve spent.";
            if (Health == 0 || Beat >= MaximumBeats)
            {
                Active = false; Won = Health > 0 && Position >= RequiredPosition;
                if (Won)
                {
                    var reward = progression.Grant(Stage == 0 ? "survey_complete" : "crossing_complete", Stage == 0 ? 10 : 15);
                    if (!reward.Applied) throw new InvalidOperationException("Completion cannot pay twice.");
                    Last += " Completed; reward committed. Level " + Progression.Level + ", " + Progression.UnspentMain + " unspent points.";
                    if (Stage == 0) Stage = 1; else Complete = true;
                }
                else Last += " Crossing failed. Reprepare and retry; no completion reward.";
            }
            return true;
        }
    }
}
