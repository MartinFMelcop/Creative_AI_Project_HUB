using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using NorthStar.Availability;
using CrossingAction = NorthStar.Crossing.Action;
using CrossingSession = NorthStar.Crossing.Session;

namespace NorthStar.AvailabilityHost;

/// <summary>Immutable observation of the actual nested Crossing owner.</summary>
public sealed class EncounterView
{
    public int Stage { get; }
    public int Beat { get; }
    public int Position { get; }
    public int Health { get; }
    public int Resolve { get; }
    public int MaximumHealth { get; }
    public int MaximumResolve { get; }
    public int RequiredPosition { get; }
    public int MaximumBeats { get; }
    public bool Active { get; }
    public bool Won { get; }
    public bool Complete { get; }
    public bool Pulse { get; }
    public string Threat { get; }
    internal EncounterView(CrossingSession owner)
    {
        Stage = owner.Stage; Beat = owner.Beat; Position = owner.Position;
        Health = owner.Health; Resolve = owner.Resolve;
        MaximumHealth = owner.MaximumHealth; MaximumResolve = owner.MaximumResolve;
        RequiredPosition = owner.RequiredPosition; MaximumBeats = owner.MaximumBeats;
        Active = owner.Active; Won = owner.Won; Complete = owner.Complete;
        Pulse = owner.Pulse; Threat = owner.Threat;
    }
}

public sealed class JourneyView
{
    public string Stage { get; }
    public string Route { get; }
    public int TotalPhase { get; }
    public int Integrity { get; }
    public int Water { get; }
    public int Delivered { get; }
    public IReadOnlyList<bool> WateredBeds { get; }
    public string Last { get; }
    public IReadOnlyList<string> Commands { get; }
    public EncounterView? Encounter { get; }
    internal JourneyView(JourneyOwner owner, CrossingSession encounter)
    {
        Stage = owner.Stage; Route = owner.Route; TotalPhase = owner.TotalPhase;
        Integrity = owner.Integrity; Water = owner.Water; Delivered = owner.Delivered; WateredBeds = owner.WateredBeds;
        Last = owner.Last; Commands = owner.Commands; Encounter = encounter.MaximumHealth > 0 ? new EncounterView(encounter) : null;
    }
}

/// <summary>One original service-to-cargo journey; private existing owners retain their rules.</summary>
public sealed class JourneyOwner
{
    private readonly Session workshop = new();
    private readonly CrossingSession crossing = new();
    private int routePhases;
    private bool[] wateredBeds = new bool[2];
    public string Stage { get; private set; } = "workshop";
    public string Route { get; private set; } = "none";
    public int TotalPhase => workshop.Phase + routePhases;
    public int Integrity { get; private set; }
    public int Water { get; private set; }
    public int Delivered => (wateredBeds[0] ? 1 : 0) + (wateredBeds[1] ? 1 : 0);
    public IReadOnlyList<bool> WateredBeds => new ReadOnlyCollection<bool>((bool[])wateredBeds.Clone());
    public string Last { get; private set; }
    public JourneyOwner() { Last = workshop.Last; }

    private bool Acquired => workshop.Outcome == "patched" || workshop.Outcome == "fired" && workshop.Collected;
    private bool CanDepart(int cost) => Stage == "workshop" && Acquired && Route == "none" && workshop.Remaining >= cost;

    public IReadOnlyList<string> Commands
    {
        get
        {
            var result = new List<string>();
            if (Stage == "workshop")
            {
                result.AddRange(workshop.Snapshot().Commands);
                if (CanDepart(1)) result.Add("route fast");
                if (CanDepart(2)) result.Add("route sheltered");
            }
            else if (Stage == "crossing") result.AddRange(new[] { "walk", "dash", "skill", "wait" });
            else if (Stage == "interlude") result.Add("continue");
            else if (Stage == "arrival") result.Add("deliver");
            return new ReadOnlyCollection<string>(result);
        }
    }

    public View WorkshopSnapshot() => workshop.Snapshot();
    public JourneyView Snapshot() => new(this, crossing);
    private bool Refuse(string message) { Last = message; return false; }

    private bool Depart(bool sheltered)
    {
        int cost = sheltered ? 2 : 1, wear = sheltered ? 0 : 2;
        if (!CanDepart(cost)) return Refuse("Departure refused: obtain the actual repair and leave enough local phases for the chosen route. No jar, water, time or encounter changed.");
        int integrity = Math.Max(0, workshop.Durability - wear);
        if (integrity > 0 && (!crossing.Prepare(NorthStar.Crossing.Approach.Lure, NorthStar.Crossing.Outfit.Trail) || !crossing.Begin()))
            throw new InvalidOperationException("Private Crossing owner refused validated first entry.");
        routePhases = cost; Route = sheltered ? "sheltered" : "fast"; Integrity = integrity;
        // Filling two units at the local well is explicit departure setup, not an NPC delivery.
        Water = integrity > 0 ? 2 : 0;
        if (integrity == 0)
        {
            Stage = "broken";
            Last = "You fill the actual repaired jar at the well and take the fast approach. Its two units of route wear break the temporary patch; both water units are lost before the Crossing. The paid phase is not refunded. Mara's own work and location are not changed.";
        }
        else
        {
            Stage = "crossing";
            Last = "You fill the actual repaired jar with two water units at the well and commit to the " + Route + " approach, paying " + cost + " local phase(s) and " + wear + " jar wear. The jar is carried, not delivered. The actual Lure/Trail Crossing begins; encounter beats are separate from paid local phases.";
        }
        return true;
    }

    private bool Act(CrossingAction action)
    {
        if (Stage != "crossing") return Refuse("No active carrying encounter; no cargo or threat advanced.");
        int beforeHealth = crossing.Health;
        if (!crossing.Act(action)) return Refuse(crossing.Last + " Cargo unchanged.");
        bool contact = crossing.Health < beforeHealth;
        if (contact) Integrity = Math.Max(0, Integrity - 1);
        Last = crossing.Last + (contact ? " Actual damaging contact wears one jar integrity, independently of the HP amount." : " No damaging contact: jar integrity unchanged.");
        if (Integrity == 0)
        {
            Water = 0; Stage = "broken";
            Last += " The jar breaks and both water units are lost. This journey has ended; no water was delivered and no repair or phase is refunded.";
        }
        else if (!crossing.Active && !crossing.Won)
        {
            Water = 0; Stage = "failed";
            Last += " The actual encounter failed. Water is not handed over; no delivery, repair reset or NPC return is recorded.";
        }
        else if (crossing.Complete && crossing.Won)
        {
            Stage = "arrival";
            Last += " You reach the far landing with water still carried. Arrival is not handoff: explicitly pour one unit into each of the two original seedbeds.";
        }
        else if (!crossing.Active && crossing.Won)
        {
            Stage = "interlude";
            Last += " The first actual Crossing is complete. The water remains carried; continue into the second actual encounter without resetting jar integrity.";
        }
        return true;
    }

    public bool Execute(string command)
    {
        if (command == null || command.Length > 64) return Refuse("Unknown command; journey facts unchanged.");
        command = command.Trim();
        if (command == "route fast") return Depart(false);
        if (command == "route sheltered") return Depart(true);
        if (Stage == "workshop")
        {
            bool accepted = workshop.Execute(command); Last = workshop.Last; return accepted;
        }
        if (command == "continue")
        {
            if (Stage != "interlude" || Water == 0 || Integrity == 0) return Refuse("Continue refused: no completed first encounter with intact carried water.");
            if (!crossing.Begin()) throw new InvalidOperationException("Private Crossing owner refused validated continuation.");
            Stage = "crossing"; Last = "You enter the second actual Crossing with the same carried jar and water. Integrity, paid route phases and Mara's unfinished work are not reset."; return true;
        }
        if (command == "deliver")
        {
            if (Stage != "arrival" || !crossing.Complete || !crossing.Won || Water != 2 || Integrity < 1 || Delivered != 0) return Refuse("Handoff refused: actual arrival and intact carried water are required; no delivery changed.");
            // Stage the two actual pours before publishing the new local owner state.
            bool[] candidate = (bool[])wateredBeds.Clone(); int remaining = Water;
            for (int bed = 0; bed < candidate.Length; bed++) { remaining--; candidate[bed] = true; }
            wateredBeds = candidate; Water = remaining; Stage = "delivered";
            Last = "You pour one carried water unit into each of the two original seedbeds. Both beds are observed watered now, once. The jar is empty; repair and route costs remain paid. Mara's two pots remain unfinished and no return to her yard is claimed."; return true;
        }
        switch (command)
        {
            case "walk": return Act(CrossingAction.Walk);
            case "dash": return Act(CrossingAction.Dash);
            case "skill": return Act(CrossingAction.Skill);
            case "wait": return Act(CrossingAction.Wait);
            default: return Refuse("Action unavailable in the current journey stage; cargo and encounter unchanged.");
        }
    }
}
