using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using NorthStar.AvailabilityHost;

internal static class Program
{
    private static readonly List<string> controls = new();
    private static void Check(bool condition, string name)
    {
        if (!condition) throw new InvalidOperationException(name);
        controls.Add(name);
    }
    private static void Do(JourneyOwner owner, params string[] commands)
    {
        foreach (string command in commands)
            if (!owner.Execute(command)) throw new InvalidOperationException("Unexpected refusal: " + command + "; " + owner.Last);
    }
    private static string Facts(JourneyOwner owner)
    {
        var j = owner.Snapshot(); var w = owner.WorkshopSnapshot();
        return JsonSerializer.Serialize(new { j.Stage, j.Route, j.TotalPhase, j.Integrity, j.Water, j.Delivered, j.WateredBeds, j.Commands, j.Encounter,
            workshop = new { w.Phase, w.Remaining, w.AdvertisedPhases, w.Advertised, w.Authority, w.Available, w.Reserved, w.WorkReady, w.Collected, w.Outcome, w.Durability, w.PotterWorkRemaining } });
    }
    private static string WorkshopFacts(JourneyOwner owner) => JsonSerializer.Serialize(owner.WorkshopSnapshot());
    private static void Refused(JourneyOwner owner, string command, string name)
    {
        string before = Facts(owner); Check(!owner.Execute(command) && Facts(owner) == before, name);
    }
    private static JourneyOwner Fired()
    {
        var owner = new JourneyOwner(); Do(owner, "reserve", "shape", "collect"); return owner;
    }
    private static JourneyOwner Patched()
    {
        var owner = new JourneyOwner(); Do(owner, "alone"); return owner;
    }
    private static void Survey(JourneyOwner owner) => Do(owner, "skill", "skill", "walk", "skill");
    private static void Crossing(JourneyOwner owner) => Do(owner, "skill", "skill", "walk", "skill", "walk", "skill");

    private static object Run()
    {
        var initial = new JourneyOwner(); var historical = initial.Snapshot();
        Check(initial.Stage == "workshop" && initial.Route == "none" && initial.TotalPhase == 0 && initial.Integrity == 0 && initial.Water == 0 && initial.Delivered == 0 && historical.Encounter == null, "initial-cargo-is-not-acquired-or-filled");
        Refused(initial, "route fast", "no-departure-before-repair");
        Refused(initial, "route sheltered", "no-sheltered-departure-before-repair");
        Refused(initial, "deliver", "no-handoff-before-actual-arrival");
        Refused(initial, "continue", "no-continuation-before-actual-survey");
        string unchanged = Facts(initial); Do(initial, "promise");
        Check(Facts(initial) == unchanged && initial.Water == 0, "promise-neither-fills-nor-acquires-cargo");
        Do(initial, "reserve", "shape");
        Check(initial.WorkshopSnapshot().WorkReady && !initial.WorkshopSnapshot().Collected && initial.Integrity == 0, "finished-uncollected-service-is-not-carried-jar");
        Refused(initial, "route fast", "ready-service-without-handoff-cannot-depart");
        Do(initial, "collect");
        Check(initial.TotalPhase == 3 && initial.WorkshopSnapshot().Durability == 3 && initial.Commands.Contains("route fast") && !initial.Commands.Contains("route sheltered"), "fired-repair-leaves-only-one-phase-approach");
        string beforeDepartureWorkshop = WorkshopFacts(initial);
        Do(initial, "route fast");
        var departed = initial.Snapshot();
        Check(departed.Stage == "crossing" && departed.TotalPhase == 4 && departed.Integrity == 1 && departed.Water == 2 && departed.Delivered == 0, "fired-fast-approach-pays-time-and-two-integrity-once");
        Check(departed.Encounter!.Active && departed.Encounter!.Stage == 0 && departed.Encounter!.Health == 10 && departed.Encounter!.Resolve == 10, "departure-starts-actual-fixed-lure-trail-crossing");
        Check(historical.Stage == "workshop" && historical.Integrity == 0 && historical.Encounter == null, "historical-journey-snapshot-does-not-track-live-owner");
        Refused(initial, "route fast", "duplicate-departure-cannot-refill-or-reset");
        Refused(initial, "route sheltered", "cannot-switch-paid-route");
        foreach (string command in new[] { "promise", "reserve", "shape", "collect", "alone", "withdraw", "leave" })
            Refused(initial, command, "workshop-frozen-during-journey:" + command);
        Refused(initial, "deliver", "active-survey-cannot-manufacture-delivery");
        Refused(initial, "continue", "active-survey-cannot-skip-to-second-encounter");
        Survey(initial);
        var survey = initial.Snapshot();
        Check(survey.Stage == "interlude" && survey.Encounter!.Won && !survey.Encounter!.Active && !survey.Encounter!.Complete && survey.Integrity == 1 && survey.Water == 2 && survey.Delivered == 0, "actual-first-win-is-not-final-arrival-or-delivery");
        Check(initial.TotalPhase == 4 && WorkshopFacts(initial) == beforeDepartureWorkshop, "actual-beats-do-not-advance-or-return-workshop-npc");
        Refused(initial, "deliver", "survey-win-cannot-handoff-water");
        Refused(initial, "walk", "interlude-requires-explicit-next-entry");
        Do(initial, "continue");
        var second = initial.Snapshot();
        Check(second.Stage == "crossing" && second.Encounter!.Active && second.Encounter!.Stage == 1 && second.Encounter!.Health == 11 && second.Integrity == 1 && second.Water == 2, "next-actual-encounter-resets-health-without-resetting-cargo");
        Refused(initial, "continue", "duplicate-next-entry-cannot-reset-second-encounter");
        Crossing(initial);
        var arrival = initial.Snapshot();
        Check(arrival.Stage == "arrival" && arrival.Encounter!.Complete && arrival.Encounter!.Won && !arrival.Encounter!.Active && arrival.Water == 2 && arrival.Delivered == 0 && arrival.WateredBeds.SequenceEqual(new[] { false, false }), "actual-final-win-still-carries-undelivered-water");
        Refused(initial, "skill", "arrival-cannot-replay-completion-action");
        Do(initial, "deliver");
        Check(initial.Stage == "delivered" && initial.Water == 0 && initial.Delivered == 2 && initial.WateredBeds.SequenceEqual(new[] { true, true }) && initial.Integrity == 1 && initial.Commands.Count == 0, "actual-two-pours-water-both-beds-once-and-empty-jar");
        Check(arrival.WateredBeds.SequenceEqual(new[] { false, false }) && arrival.Water == 2, "historical-arrival-snapshot-does-not-rewrite-beds-after-pouring");
        Refused(initial, "deliver", "repeated-handoff-cannot-rewater-or-create-water");
        Refused(initial, "route fast", "completed-journey-cannot-reacquire-repair");
        Check(WorkshopFacts(initial) == beforeDepartureWorkshop && initial.WorkshopSnapshot().PotterWorkRemaining == 2, "complete-journey-does-not-complete-maras-own-work-or-return-to-her");

        var sheltered = Patched(); Do(sheltered, "route sheltered");
        Check(sheltered.TotalPhase == 4 && sheltered.Integrity == 1 && sheltered.Water == 2 && sheltered.Route == "sheltered", "actual-patch-can-afford-sheltered-approach-without-wear");
        Survey(sheltered); Do(sheltered, "continue"); Crossing(sheltered); Do(sheltered, "deliver");
        Check(sheltered.Delivered == 2 && sheltered.Stage == "delivered", "patched-sheltered-route-actually-completes-both-crossings-and-handoff");
        var brokenApproach = Patched(); Do(brokenApproach, "route fast");
        Check(brokenApproach.Stage == "broken" && brokenApproach.TotalPhase == 3 && brokenApproach.Integrity == 0 && brokenApproach.Water == 0 && brokenApproach.Delivered == 0 && brokenApproach.Snapshot().Encounter == null, "patched-fast-route-breaks-before-starting-any-crossing");
        Refused(brokenApproach, "route sheltered", "broken-approach-cannot-refund-and-switch-routes");
        Refused(brokenApproach, "deliver", "broken-jar-cannot-deliver-lost-water");

        var late = new JourneyOwner(); Do(late, "wait", "reserve", "shape", "collect");
        Check(late.TotalPhase == 4 && late.WorkshopSnapshot().Collected && late.WorkshopSnapshot().Durability == 3, "actual-late-service-can-be-collected-at-phase-four");
        Refused(late, "route fast", "late-collection-does-not-create-missing-route-phase");
        Refused(late, "route sheltered", "late-collection-does-not-create-two-route-phases");
        var contact = Fired(); Do(contact, "route fast", "walk");
        var impact = contact.Snapshot();
        Check(impact.Stage == "broken" && impact.Integrity == 0 && impact.Water == 0 && impact.Encounter!.Health == 6 && impact.Encounter!.Beat == 1 && impact.Encounter!.Active && !impact.Encounter!.Won && !impact.Encounter!.Complete, "actual-hp-loss-breaks-jar-without-fabricating-child-defeat");
        Refused(contact, "skill", "broken-wrapper-cannot-secretly-continue-still-active-child");
        Refused(contact, "alone", "broken-journey-does-not-repair-or-refund-cargo");
        Refused(contact, "deliver", "damaged-active-survey-cannot-deliver");
        var finalContact = Patched(); Do(finalContact, "route sheltered", "skill", "skill", "walk", "walk");
        var wonButBroken = finalContact.Snapshot();
        Check(wonButBroken.Stage == "broken" && wonButBroken.Water == 0 && wonButBroken.Delivered == 0 && wonButBroken.Encounter!.Won && !wonButBroken.Encounter.Active && wonButBroken.Encounter.Stage == 1 && wonButBroken.Encounter.Health == 6 && wonButBroken.WateredBeds.SequenceEqual(new[] { false, false }), "damaging-survey-winning-action-breaks-cargo-before-any-next-entry-reset");
        var pulse = Patched(); Do(pulse, "route sheltered", "skill", "skill", "skill");
        Check(pulse.Stage == "broken" && pulse.Snapshot().Encounter!.Health == 6 && pulse.Snapshot().Encounter!.Beat == 3 && pulse.TotalPhase == 4, "actual-stationary-pulse-contact-also-consumes-jar");
        var observed = Fired(); Do(observed, "route fast"); string observation = Facts(observed);
        for (int i = 0; i < 20; i++) { observed.Snapshot(); observed.WorkshopSnapshot(); }
        Check(Facts(observed) == observation, "repeat-observation-is-not-travel-contact-or-handoff");
        Refused(observed, "walk now", "malformed-battle-command-cannot-advance-any-owner");
        Refused(observed, "route unknown", "unknown-route-cannot-consume-or-fill");
        Refused(observed, new string('x', 65), "oversize-command-preserves-all-gameplay-facts");
        return new { schema = 1, passed = controls.Count, failed = 0, controls,
            scope = "Actual original one-owner service/cargo/unchanged Crossing integration; no Unity, Windows, real water physics or human balance validation." };
    }

    private static int Main(string[] args)
    {
        try
        {
            if (args.Length != 1) throw new ArgumentException("Usage: JourneyChecks OUTPUT_JSON");
            object result = Run(); string json = JsonSerializer.Serialize(result, new JsonSerializerOptions { WriteIndented = true });
            using (var file = new FileStream(args[0], FileMode.CreateNew, FileAccess.Write))
            using (var writer = new StreamWriter(file)) writer.WriteLine(json);
            Console.WriteLine(json); return 0;
        }
        catch (Exception error) when (error is ArgumentException || error is InvalidOperationException || error is IOException)
        { Console.Error.WriteLine(error.Message); return 1; }
    }
}
