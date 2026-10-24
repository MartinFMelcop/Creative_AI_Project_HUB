using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Nodes;
using NorthStar.AuthoredScene;

internal static class Program
{
    private static readonly List<string> controls = new();
    private static int request;
    private static void Check(bool value, string label)
    { if (!value) throw new InvalidOperationException(label); controls.Add(label); }
    private static void Reject(Action action, string label)
    {
        try { action(); }
        catch (Exception error) when (error is IOException || error is InvalidDataException || error is JsonException || error is ArgumentException || error is ObjectDisposedException)
        { controls.Add(label); return; }
        throw new InvalidOperationException("Unexpected acceptance: " + label);
    }
    private static JournalReceipt Do(RequestJournal owner, params string[] commands)
    {
        JournalReceipt receipt = owner.Snapshot();
        foreach (string command in commands)
        {
            var before = owner.Snapshot();
            receipt = owner.Submit(before.run_id, "native_" + ++request, before.revision, command);
            if (!receipt.accepted) throw new InvalidOperationException("Unexpected refusal: " + command + "; " + receipt.reason + "; " + receipt.text);
        }
        return receipt;
    }
    private static string State(RequestJournal owner) => owner.Snapshot().state.GetRawText();
    private static string Read(string path) => File.ReadAllText(path);
    private static void Survey(RequestJournal owner) => Do(owner, "survey", "skill", "skill", "walk", "skill");
    private static void Commit(RequestJournal owner)
    { Survey(owner); Do(owner, "open", "hear", "offer", "terms dusk", "confirm"); }
    private static string Rechecksum(JsonObject root)
    {
        var body = new JsonObject();
        foreach (string key in new[] { "schema_version", "kind", "journal_id", "rules_id", "entries" }) body[key] = root[key]!.DeepClone();
        byte[] bytes = System.Text.Encoding.UTF8.GetBytes(body.ToJsonString(new JsonSerializerOptions { WriteIndented = false }));
        root["checksum"] = Convert.ToHexStringLower(System.Security.Cryptography.SHA256.HashData(bytes));
        return root.ToJsonString(new JsonSerializerOptions { WriteIndented = false });
    }
    private static object Run(string work)
    {
        Directory.CreateDirectory(work); string consentPath = Path.Combine(work, "consent.json");
        string afterHear, runId;
        using (var owner = new RequestJournal(consentPath, true))
        {
            var initial = owner.Snapshot(); runId = initial.run_id;
            Check(initial.revision == 0 && initial.day == 1 && initial.accepted && !initial.blocked && File.Exists(consentPath), "explicit-create-persists-empty-request-run");
            Survey(owner); Do(owner, "open", "hear"); afterHear = State(owner);
            Check(owner.Snapshot().state.GetProperty("conversation").GetString() == "table" && owner.Snapshot().state.GetProperty("surveyed").GetBoolean(), "actual-survey-and-heard-consent-committed");
        }
        using (var owner = new RequestJournal(consentPath, false))
        {
            Check(State(owner) == afterHear && owner.Snapshot().run_id == runId, "reopen-preserves-public-state-and-stable-day-identity");
            var offered = Do(owner, "offer"); Check(offered.state.GetProperty("conversation").GetString() == "terms", "replayed-private-heard-consent-still-permits-real-offer");
            Do(owner, "terms dusk");
        }
        string prepared;
        using (var owner = new RequestJournal(consentPath, false))
        {
            Check(owner.Snapshot().state.GetProperty("conversation").GetString() == "ready", "reopen-restores-unsigned-private-draft-context");
            var signed = Do(owner, "confirm");
            Check(signed.state.GetProperty("status").GetString() == "committed" && signed.state.GetProperty("term").GetString() == "dusk" && signed.state.GetProperty("guide_location").GetString() == "local-preparing" && signed.state.GetProperty("capacity").GetInt32() == 1 && !signed.state.GetProperty("delivered").GetBoolean(), "replayed-private-terms-confirm-real-reservation-without-delivery");
            prepared = State(owner);
        }
        string active;
        using (var owner = new RequestJournal(consentPath, false))
        {
            Check(State(owner) == prepared, "preparing-reservation-survives-process-owner-replacement");
            var receipt = Do(owner, "depart guided", "skill", "skill"); active = State(owner);
            var encounter = receipt.state.GetProperty("encounter");
            Check(receipt.state.GetProperty("guide_location").GetString() == "travelling" && encounter.GetProperty("active").GetBoolean() && encounter.GetProperty("beat").GetInt32() == 2 && encounter.GetProperty("health").GetInt32() == 11 && encounter.GetProperty("resolve").GetInt32() == 5, "actual-guided-next-beat-hp-resource-and-location-committed");
        }
        string complete;
        using (var owner = new RequestJournal(consentPath, false))
        {
            Check(State(owner) == active && owner.Snapshot().state.GetProperty("encounter").GetProperty("threat").GetString()!.Contains("PULSE", StringComparison.Ordinal), "active-reopen-restores-exact-next-threat-without-advancing");
            Do(owner, "walk", "skill", "walk", "skill");
            var result = owner.Snapshot().state;
            Check(result.GetProperty("delivered").GetBoolean() && result.GetProperty("returned").GetBoolean() && result.GetProperty("guide_available").GetBoolean() && result.GetProperty("receipts").GetArrayLength() == 2, "only-real-restored-final-action-records-return-and-handoff");
            Do(owner, "work"); complete = State(owner);
        }
        using (var owner = new RequestJournal(consentPath, false))
        {
            var state = owner.Snapshot().state;
            Check(State(owner) == complete && state.GetProperty("crates").GetInt32() == 2 && state.GetProperty("remaining").GetInt32() == 0, "completed-reopen-retains-three-unfinished-crates-and-paid-daylight");
            var before = owner.Snapshot(); string bytes = Read(consentPath);
            var receipt = owner.Submit(before.run_id, "no_delivery_twice", before.revision, "depart guided");
            Check(!receipt.accepted && State(owner) == complete && Read(consentPath) == bytes, "completed-recovery-cannot-repeat-departure-or-repay-results");
        }
        string openTermsPath = Path.Combine(work, "open-terms.json");
        using (var owner = new RequestJournal(openTermsPath, true)) { Survey(owner); Do(owner, "open", "hear", "offer", "terms open"); }
        using (var owner = new RequestJournal(openTermsPath, false))
        { Check(Do(owner, "confirm").state.GetProperty("term").GetString() == "open", "open-ended-private-terms-remain-distinct-after-reopen"); }

        string withdrawnPath = Path.Combine(work, "withdrawn.json");
        using (var owner = new RequestJournal(withdrawnPath, true)) { Commit(owner); Do(owner, "withdraw"); }
        using (var owner = new RequestJournal(withdrawnPath, false))
        {
            var state = owner.Snapshot().state; var receipts = state.GetProperty("receipts");
            Check(receipts.GetArrayLength() == 2 && receipts[0].GetProperty("kind").GetString() == "commitment" && receipts[1].GetProperty("kind").GetString() == "withdrawal" && state.GetProperty("guide_available").GetBoolean() && !state.GetProperty("delivered").GetBoolean(), "withdrawal-reopen-keeps-both-receipts-without-inventing-departure");
        }
        string failedPath = Path.Combine(work, "failed.json");
        using (var owner = new RequestJournal(failedPath, true)) { Commit(owner); Do(owner, "depart guided", "wait", "wait"); }
        using (var owner = new RequestJournal(failedPath, false))
        {
            var state = owner.Snapshot().state;
            Check(state.GetProperty("status").GetString() == "failed" && state.GetProperty("guide_location").GetString() == "unaccounted" && !state.GetProperty("returned").GetBoolean() && !state.GetProperty("delivered").GetBoolean(), "failed-reopen-preserves-unaccounted-guide-without-return-or-death-claim");
            Do(owner, "work"); state = owner.Snapshot().state;
            Check(state.GetProperty("remaining").GetInt32() == 0 && state.GetProperty("guide_location").GetString() == "unaccounted" && state.GetProperty("crates").GetInt32() == 1, "recovered-dusk-does-not-return-failed-guide-or-restore-capacity");
        }
        string declinedPath = Path.Combine(work, "declined.json");
        using (var owner = new RequestJournal(declinedPath, true)) Do(owner, "open", "decline");
        using (var owner = new RequestJournal(declinedPath, false))
        {
            var before = owner.Snapshot(); string bytes = Read(declinedPath);
            var refusal = owner.Submit(before.run_id, "declined_open", before.revision, "open");
            Check(!refusal.accepted && Read(declinedPath) == bytes && owner.Snapshot().text == before.text && State(owner) == before.state.GetRawText(), "recovered-decline-and-last-accepted-text-cannot-be-erased-by-refused-reopening");
        }

        string retryPath = Path.Combine(work, "retry.json");
        string retryRun;
        using (var owner = new RequestJournal(retryPath, true))
        {
            retryRun = owner.Snapshot().run_id;
            Check(owner.Submit(retryRun, "work_once", 0, "work").accepted, "actual-work-commits-before-first-receipt");
        }
        using (var owner = new RequestJournal(retryPath, false))
        {
            string bytes = Read(retryPath); var current = owner.Snapshot();
            var duplicate = owner.Submit(retryRun, "work_once", 0, "work");
            Check(duplicate.accepted && duplicate.duplicate && duplicate.original_revision == 1 && duplicate.revision == 1 && duplicate.state.GetProperty("crates").GetInt32() == 2 && Read(retryPath) == bytes, "lost-response-retry-is-deduplicated-before-stale-revision-check");
            var conflict = owner.Submit(retryRun, "work_once", 1, "survey");
            Check(!conflict.accepted && !conflict.duplicate && Read(retryPath) == bytes, "same-request-content-substitution-cannot-change-narrative");
            var stale = owner.Submit(retryRun, "stale_intent", 0, "work");
            Check(!stale.accepted && Read(retryPath) == bytes && State(owner) == current.state.GetRawText(), "unique-stale-revision-intent-cannot-act-on-new-facts");
            var restarted = owner.Submit(retryRun, "new_day", 1, "restart");
            Check(restarted.accepted && restarted.day == 2 && restarted.revision == 2 && restarted.run_id != retryRun && restarted.state.GetProperty("crates").GetInt32() == 0, "explicit-new-day-appends-history-and-changes-day-identity");
            bytes = Read(retryPath);
            var oldDay = owner.Submit(retryRun, "work_once", 0, "work");
            Check(!oldDay.accepted && !oldDay.duplicate && Read(retryPath) == bytes, "old-day-identity-is-refused-before-an-existing-request-duplicate");
            var history = JsonNode.Parse(bytes)!["entries"]!.AsArray();
            Check(history.Count == 2 && history[0]!["command"]!.GetValue<string>() == "work" && history[1]!["command"]!.GetValue<string>() == "restart", "new-day-retains-prior-work-history-instead-of-truncating");
        }
        using (var owner = new RequestJournal(retryPath, false))
        {
            Check(owner.Snapshot().day == 2 && owner.Snapshot().revision == 2 && owner.Snapshot().run_id.EndsWith("-day-2", StringComparison.Ordinal), "new-day-identity-and-full-history-survive-reopen");
            string bytes = Read(retryPath);
            Reject(() => owner.Submit(owner.Snapshot().run_id, "bad id", 2, "work"), "invalid-request-envelope-rejects-before-mutation");
            Check(Read(retryPath) == bytes, "invalid-request-does-not-rewrite-run");
            Reject(() => new RequestJournal(retryPath, false).Dispose(), "cooperating-competing-request-owner-is-excluded");
        }
        string existing = Read(retryPath);
        Reject(() => new RequestJournal(retryPath, true).Dispose(), "new-never-overwrites-existing-narrative-run");
        Check(Read(retryPath) == existing, "existing-run-bytes-remain-after-new-refusal");
        string missing = Path.Combine(work, "missing.json");
        Reject(() => new RequestJournal(missing, false).Dispose(), "resume-never-creates-missing-narrative-run");
        Check(!File.Exists(missing), "missing-resume-leaves-no-replacement-save");
        string oldFormat = Path.Combine(work, "prepared-expedition.json");
        File.WriteAllText(oldFormat, "{\"schema_version\":1,\"rules_id\":\"old-prepared-expedition\",\"entries\":[],\"checksum\":\"old\"}");
        string oldBytes = Read(oldFormat); Reject(() => new RequestJournal(oldFormat, false).Dispose(), "prepared-expedition-journal-is-not-a-narrative-save");
        Check(Read(oldFormat) == oldBytes, "incompatible-old-format-is-preserved-for-explicit-migration");
        foreach (string mutation in new[] { "rules", "state" })
        {
            var root = JsonNode.Parse(existing)!.AsObject();
            if (mutation == "rules") root["rules_id"] = new string('0', 64);
            else root["entries"]![0]!["state_hash"] = new string('0', 64);
            string wrong = Path.Combine(work, mutation + ".json"); File.WriteAllText(wrong, Rechecksum(root)); string bytes = Read(wrong);
            Reject(() => new RequestJournal(wrong, false).Dispose(), "recomputed-checksum-cannot-authorize-incompatible-" + mutation);
            Check(Read(wrong) == bytes, "rejected-incompatible-input-is-not-replaced:" + mutation);
        }
        string uncertain = Path.Combine(work, "uncertain.json"); string uncertainRun;
        using (var owner = new RequestJournal(uncertain, true))
        {
            uncertainRun = owner.Snapshot().run_id;
            Reject(() => owner.Submit(uncertainRun, "uncertain_work", 0, "work", point => { if (point == "after_replace") throw new IOException("Targeted acknowledgement-boundary failure."); }), "uncertain-after-replace-failure-is-retained");
            var blocked = owner.Snapshot();
            Check(blocked.blocked && !blocked.accepted && blocked.revision == 0 && blocked.state.GetProperty("crates").GetInt32() == 0, "uncertain-live-owner-labels-last-published-facts-blocked");
            Reject(() => owner.Submit(uncertainRun, "must_reopen", 0, "work"), "blocked-owner-cannot-issue-another-narrative-command");
        }
        using (var owner = new RequestJournal(uncertain, false))
        {
            var recovered = owner.Snapshot();
            Check(!recovered.blocked && recovered.revision == 1 && recovered.state.GetProperty("crates").GetInt32() == 2, "reopen-observes-actual-complete-prefix-after-uncertain-replacement");
            Check(owner.Submit(uncertainRun, "uncertain_work", 0, "work").duplicate && owner.Snapshot().state.GetProperty("crates").GetInt32() == 2, "uncertain-acknowledgement-retry-does-not-repeat-work");
        }
        return new { schema = 1, passed = controls.Count, failed = 0, controls, rules_identity = RequestJournal.RulesIdentity,
            scope = "Actual unchanged narrative owner replay, local storage/reopen and targeted uncertainty; process/browser observations are separate. No Unity, Windows, account authorization or power-loss durability claim." };
    }
    private static int Main(string[] args)
    {
        try
        {
            if (args.Length != 2) throw new ArgumentException("Usage: JournalChecks OUTPUT_JSON FRESH_WORKDIR");
            if (Directory.Exists(args[1])) throw new IOException("Native work directory must be fresh.");
            string text = JsonSerializer.Serialize(Run(args[1]), new JsonSerializerOptions { WriteIndented = true });
            using (var output = new FileStream(args[0], FileMode.CreateNew, FileAccess.Write))
            using (var writer = new StreamWriter(output)) writer.WriteLine(text);
            Console.WriteLine(text); return 0;
        }
        catch (Exception error) when (error is ArgumentException || error is InvalidOperationException || error is IOException || error is JsonException)
        { Console.Error.WriteLine(error.Message); return 1; }
    }
}
