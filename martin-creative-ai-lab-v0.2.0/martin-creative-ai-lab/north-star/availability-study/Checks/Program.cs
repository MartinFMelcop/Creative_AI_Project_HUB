using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using NorthStar.Availability;

internal static class Program
{
    private static readonly List<string> controls = new List<string>();
    private static void Check(bool value, string name)
    {
        if (!value) throw new InvalidOperationException(name);
        controls.Add(name);
    }
    private static void Reject(System.Action action, string name)
    {
        try { action(); } catch (ArgumentException) { controls.Add(name); return; }
        throw new InvalidOperationException("Accepted: " + name);
    }
    private static string Facts(Session owner)
    {
        View v = owner.Snapshot();
        return JsonSerializer.Serialize(new { v.Phase, v.Remaining, v.Advertised, v.Authority, v.Available, v.Reserved, v.WorkReady, v.Collected, v.Outcome, v.Durability, v.PotterWorkRemaining, v.Commands });
    }
    private static void Accepted(Session owner, params string[] commands)
    {
        foreach (string command in commands) if (!owner.Execute(command)) throw new InvalidOperationException("Unexpected refusal: " + command);
    }
    private static object Native()
    {
        Reject(() => Schedule.Allows(-1, new[] { 0 }), "negative-phase-refused");
        Reject(() => Schedule.Allows(5, new[] { 0 }), "phase-past-four-refused");
        Reject(() => Schedule.Allows(0, Array.Empty<int>()), "empty-mask-not-universal-presence");
        Reject(() => Schedule.Allows(0, new[] { 0, 0 }), "duplicate-mask-refused");
        Reject(() => Schedule.Allows(0, new[] { 0, 5 }), "out-of-range-mask-refused");
        Reject(() => Schedule.Allows(0, null!), "null-mask-refused");
        Reject(() => Schedule.Available(true, (Authority)99), "undefined-authority-refused");
        Check(Schedule.Allows(4, new[] { 0, 1, 4 }) && !Schedule.Allows(2, new[] { 0, 1, 4 }), "literal-mask-is-eligibility-only");
        Check(Schedule.Available(true, Authority.Present) && !Schedule.Available(false, Authority.Present), "present-service-requires-advertised-window");
        Check(new[] { Authority.Committed, Authority.Away, Authority.Unaccounted }.All(a => !Schedule.Available(true, a)), "posted-window-cannot-overwrite-other-authority");
        var owner = new Session(); string initial = Facts(owner); View captured = owner.Snapshot();
        for (int i = 0; i < 20; i++) owner.Snapshot();
        Check(Facts(owner) == initial, "observation-is-pure");
        Accepted(owner, "promise", "promise");
        Check(Facts(owner) == initial, "promise-is-neither-reservation-nor-progress");
        foreach (string command in new[] { "return", "observe-return", "collect", "shape", "reserve now", "RESERVE", "", new string('x', 65) })
        {
            string before = Facts(owner); Check(!owner.Execute(command) && Facts(owner) == before, "invalid-or-unearned-action-preserves-facts:" + (command.Length > 20 ? "oversize" : command));
        }
        Accepted(owner, "reserve");
        Check(owner.Phase == 1 && owner.Presence == Authority.Committed && owner.Advertised && !owner.Available && !owner.WorkReady && !owner.Collected, "reservation-spends-phase-and-occupies-actual-npc");
        Check(captured.Phase == 0 && captured.Available && !captured.Reserved, "previous-snapshot-remains-historical");
        bool immutable = false;
        try { ((IList<int>)owner.AdvertisedPhases)[0] = 4; } catch (NotSupportedException) { immutable = true; }
        Check(immutable && owner.AdvertisedPhases.SequenceEqual(new[] { 0, 1, 4 }), "advertised-mask-cannot-be-mutated-by-consumer");
        string reserved = Facts(owner); Check(!owner.Execute("reserve") && Facts(owner) == reserved, "second-reservation-cannot-spend-or-duplicate");
        Accepted(owner, "shape");
        Check(owner.Phase == 3 && !owner.Advertised && owner.WorkReady && !owner.Collected && owner.Presence == Authority.Committed, "committed-work-continues-outside-advertised-window");
        string shaped = Facts(owner); Check(!owner.Execute("shape") && Facts(owner) == shaped, "shape-executes-once");
        Accepted(owner, "collect");
        Check(owner.Phase == 3 && owner.Collected && owner.Outcome == "fired" && owner.Durability == 3 && owner.Presence == Authority.Present && !owner.Available && owner.PotterWorkRemaining == 2, "actual-fired-handoff-preserves-own-unfinished-work");
        string completed = Facts(owner);
        Check(!owner.Execute("collect") && !owner.Execute("alone") && Facts(owner) == completed, "terminal-repair-cannot-duplicate-or-switch-outcome");
        var alone = new Session(); Accepted(alone, "alone");
        Check(alone.Phase == 2 && alone.Outcome == "patched" && alone.Durability == 1 && !alone.Collected && !alone.Reserved && !alone.WorkReady && alone.Presence == Authority.Present && alone.PotterWorkRemaining == 2, "alone-route-is-real-weaker-alternative-without-borrowing-potter");
        var late = new Session(); Accepted(late, "wait", "wait", "wait");
        string lateBefore = Facts(late); Check(!late.Execute("alone") && Facts(late) == lateBefore, "alone-route-cannot-hide-two-phase-cost");
        var cutoff = new Session(); Accepted(cutoff, "wait", "wait", "wait", "wait");
        string end = Facts(cutoff); Check(cutoff.Phase == 4 && cutoff.Advertised && !cutoff.Execute("reserve") && !cutoff.Execute("wait") && Facts(cutoff) == end, "final-advertised-phase-does-not-create-service-time");
        var lost = new Session(); Accepted(lost, "reserve", "leave", "wait", "wait", "wait");
        Check(lost.Phase == 4 && lost.Advertised && lost.Presence == Authority.Unaccounted && !lost.Available && !lost.Collected && !lost.WorkReady, "phase-four-never-returns-unaccounted-potter");
        string unknown = Facts(lost); Check(!lost.Execute("shape") && !lost.Execute("collect") && Facts(lost) == unknown, "unaccounted-owner-cannot-complete-outstanding-service");
        var abandoned = new Session(); Accepted(abandoned, "reserve", "shape", "leave", "wait");
        Check(abandoned.WorkReady && !abandoned.Collected && abandoned.Presence == Authority.Unaccounted && !abandoned.Execute("collect"), "ready-pot-does-not-make-unobserved-handoff");
        var withdrawn = new Session(); Accepted(withdrawn, "reserve", "withdraw");
        Check(withdrawn.Phase == 1 && !withdrawn.Reserved && withdrawn.Presence == Authority.Away && !withdrawn.WorkReady && !withdrawn.Collected, "withdrawal-refunds-neither-phase-nor-work");
        Accepted(withdrawn, "wait", "wait", "wait");
        Check(withdrawn.Advertised && !withdrawn.Available && withdrawn.Presence == Authority.Away && !withdrawn.Execute("reserve"), "schedule-cannot-resurrect-withdrawn-service");
        var salvage = new Session(); Accepted(salvage, "reserve", "withdraw", "alone");
        Check(salvage.Phase == 3 && salvage.Outcome == "patched" && salvage.Presence == Authority.Away && !salvage.Collected, "withdrawal-can-preserve-costly-alone-alternative-without-return");
        var lateService = new Session(); Accepted(lateService, "wait", "reserve", "shape");
        Check(lateService.Phase == 4 && lateService.Advertised && lateService.WorkReady && lateService.Presence == Authority.Committed && !lateService.Available, "late-service-retains-commitment-at-advertised-final-phase");
        Accepted(lateService, "collect");
        Check(lateService.Phase == 4 && lateService.Outcome == "fired" && lateService.Collected, "actual-handoff-at-phase-four-needs-no-fabricated-return");
        Check(owner.Phase == 3 && alone.Phase == 2 && owner.Durability > alone.Durability, "fired-repair-trades-additional-phase-for-durability");
        return new { schema = 1, passed = controls.Count, failed = 0, controls };
    }

    private static object SourceCases(string path)
    {
        using (JsonDocument document = JsonDocument.Parse(File.ReadAllText(path)))
        {
            JsonElement root = document.RootElement;
            if (root.GetProperty("schema").GetInt32() != 1) throw new ArgumentException("Unknown source-case schema.");
            JsonElement cases = root.GetProperty("cases");
            if (cases.GetArrayLength() < 1 || cases.GetArrayLength() > 10000) throw new ArgumentException("Invalid case count.");
            var seen = new HashSet<string>(StringComparer.Ordinal);
            var results = new List<object>(); int passed = 0;
            foreach (JsonElement item in cases.EnumerateArray())
            {
                string id = item.GetProperty("id").GetString() ?? "";
                if (id.Length < 1 || id.Length > 100 || !seen.Add(id)) throw new ArgumentException("Invalid source-case ID.");
                var mask = new List<int>(); foreach (JsonElement value in item.GetProperty("mask").EnumerateArray()) mask.Add(value.GetInt32());
                bool allowed = Schedule.Allows(item.GetProperty("phase").GetInt32(), mask), expected = item.GetProperty("expected").GetBoolean();
                if (allowed == expected) passed++;
                results.Add(new { id, allowed, expected, passed = allowed == expected });
            }
            if (passed != results.Count) throw new InvalidOperationException("Source mask parity failed.");
            return new { schema = 1, case_count = results.Count, passed, failed = results.Count - passed, results };
        }
    }
    private static int Main(string[] args)
    {
        try
        {
            object result;
            if (args.Length == 0) result = Native();
            else if (args.Length == 2 && args[0] == "--source-cases") result = SourceCases(args[1]);
            else if (args.Length == 2 && !args[0].StartsWith("--", StringComparison.Ordinal))
            {
                Native(); object source = SourceCases(args[1]);
                result = new { schema = 1, passed = controls.Count, failed = 0, controls, source_cases = source };
                using (var file = new FileStream(args[0], FileMode.CreateNew, FileAccess.Write))
                using (var writer = new StreamWriter(file)) writer.WriteLine(JsonSerializer.Serialize(result));
            }
            else throw new ArgumentException("Usage: AvailabilityChecks [--source-cases JSON_PATH | OUTPUT_JSON SOURCE_ASSAY_JSON]");
            Console.WriteLine(JsonSerializer.Serialize(result));
            return 0;
        }
        catch (Exception error) when (error is ArgumentException || error is InvalidOperationException || error is JsonException || error is IOException || error is KeyNotFoundException)
        { Console.Error.WriteLine(error.Message); return 1; }
    }
}
