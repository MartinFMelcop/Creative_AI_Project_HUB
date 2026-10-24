using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using NorthStar.Narrative;

namespace NorthStar.AuthoredScene;

public sealed record JournalReceipt(bool accepted, bool duplicate, bool blocked, int revision,
    int original_revision, int day, string run_id, string command, string reason, string text, JsonElement state);

/// <summary>One local replay journal for the unchanged RequestExpedition; not an account or shared-world boundary.</summary>
public sealed class RequestJournal : IDisposable
{
    public const int MaximumEntries = 4096;
    public const int MaximumBytes = 2 * 1024 * 1024;
    private const string Kind = "north-star-request-journal";
    private static readonly HashSet<string> Commands = new(StringComparer.Ordinal)
    {
        "open", "hear", "offer", "terms dusk", "terms open", "confirm", "defer", "decline", "withdraw", "work", "survey",
        "depart guided", "depart solo", "skill", "walk", "dash", "wait", "restart"
    };
    private sealed record Entry(int Sequence, string RequestId, string Command, int Day, string StateHash);
    private readonly string path;
    private readonly FileStream lease;
    private readonly object ownership = new();
    private string journalId = Guid.NewGuid().ToString("N");
    private List<Entry> entries = new();
    private RequestExpedition game = new();
    private int day = 1;
    private string lastCommand = "initial";
    private bool blocked;
    private bool disposed;
    public static string RulesIdentity { get; } = ComputeRulesIdentity();
    public int Revision { get { lock (ownership) return entries.Count; } }
    public bool Blocked { get { lock (ownership) return blocked; } }

    public RequestJournal(string filename, bool create)
    {
        path = Path.GetFullPath(filename);
        Directory.CreateDirectory(Path.GetDirectoryName(path)!);
        RegularOrAbsent(path); RegularOrAbsent(path + ".lock");
        lease = new FileStream(path + ".lock", FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.None);
        try
        {
            if (create)
            {
                if (Exists(path)) throw new IOException("Existing request run is never overwritten by new.");
                Write(entries, false, null);
            }
            else
            {
                if (!File.Exists(path)) throw new IOException("Request run is missing; resume never creates a replacement.");
                Read();
            }
        }
        catch { lease.Dispose(); throw; }
    }

    private static string Hash(string value) => Convert.ToHexStringLower(SHA256.HashData(Encoding.UTF8.GetBytes(value)));
    private static string ComputeRulesIdentity()
    {
        var assemblies = new[] { typeof(RequestJournal).Assembly, typeof(RequestExpedition).Assembly,
            typeof(NorthStar.Crossing.Session).Assembly, typeof(NorthStar.Domain.ProgressionState).Assembly };
        return Hash("north-star-request-journal-v1\n" + string.Join("\n", assemblies.Select(a => a.GetName().Name + ":" + a.ManifestModule.ModuleVersionId.ToString("D"))));
    }
    private static bool Exists(string name)
    {
        try { File.GetAttributes(name); return true; }
        catch (FileNotFoundException) { return false; }
        catch (DirectoryNotFoundException) { return false; }
    }
    private static void RegularOrAbsent(string name)
    {
        if (Exists(name) && (File.GetAttributes(name) & (FileAttributes.Directory | FileAttributes.ReparsePoint)) != 0)
            throw new IOException("Request run and lease must be regular, unlinked files.");
    }
    private static void Fields(JsonElement value, params string[] names)
    {
        if (value.ValueKind != JsonValueKind.Object) throw new InvalidDataException("Expected journal object.");
        var seen = new HashSet<string>(StringComparer.Ordinal);
        foreach (var field in value.EnumerateObject())
            if (!names.Contains(field.Name) || !seen.Add(field.Name)) throw new InvalidDataException("Unknown or duplicate journal field.");
        if (seen.Count != names.Length) throw new InvalidDataException("Missing journal field.");
    }
    private static string Text(JsonElement value, int maximum = 256)
    {
        if (value.ValueKind != JsonValueKind.String || value.GetString()!.Length > maximum) throw new InvalidDataException("Expected bounded journal string.");
        return value.GetString()!;
    }
    private static int Integer(JsonElement value)
    {
        if (value.ValueKind != JsonValueKind.Number || !value.TryGetInt32(out int number)) throw new InvalidDataException("Expected journal integer.");
        return number;
    }
    private static bool Identifier(string? value) => value != null && value.Length >= 1 && value.Length <= 64
        && value.All(c => c >= 'a' && c <= 'z' || c >= 'A' && c <= 'Z' || c >= '0' && c <= '9' || c == '_' || c == '-');
    private static object[] Body(IEnumerable<Entry> rows) => rows.Select(row => (object)new
    { sequence = row.Sequence, request_id = row.RequestId, command = row.Command, day = row.Day, state_hash = row.StateHash }).ToArray();
    private string Payload(IEnumerable<Entry> rows) => JsonSerializer.Serialize(new
    { schema_version = 1, kind = Kind, journal_id = journalId, rules_id = RulesIdentity, entries = Body(rows) });
    private string Encode(IEnumerable<Entry> rows) => JsonSerializer.Serialize(new
    { schema_version = 1, kind = Kind, journal_id = journalId, rules_id = RulesIdentity, entries = Body(rows), checksum = Hash(Payload(rows)) });
    private static string StateHash(RequestExpedition owner) => Hash(JsonSerializer.Serialize(owner.Snapshot()));
    private static (RequestExpedition Game, int Day, string Command) Replay(IEnumerable<Entry> rows)
    {
        var candidate = new RequestExpedition(); int currentDay = 1, sequence = 0; string last = "initial";
        var identities = new HashSet<string>(StringComparer.Ordinal);
        foreach (var row in rows)
        {
            if (row.Sequence != ++sequence || !Identifier(row.RequestId) || !identities.Add(row.RequestId) || !Commands.Contains(row.Command))
                throw new InvalidDataException("Illegal, duplicated or reordered request entry.");
            if (row.Command == "restart") { candidate = new RequestExpedition(); currentDay = checked(currentDay + 1); }
            else if (!candidate.Command(row.Command)) throw new InvalidDataException("Request history contains a refused command.");
            if (row.Day != currentDay || row.StateHash != StateHash(candidate)) throw new InvalidDataException("Request history state/day mismatch.");
            last = row.Command;
        }
        return (candidate, currentDay, last);
    }

    private void Read()
    {
        if (new FileInfo(path).Length > MaximumBytes) throw new InvalidDataException("Request run exceeds byte limit.");
        string text = File.ReadAllText(path);
        if (Encoding.UTF8.GetByteCount(text) > MaximumBytes) throw new InvalidDataException("Request run exceeds byte limit.");
        using var document = JsonDocument.Parse(text, new JsonDocumentOptions { MaxDepth = 16 });
        var root = document.RootElement;
        Fields(root, "schema_version", "kind", "journal_id", "rules_id", "entries", "checksum");
        if (Integer(root.GetProperty("schema_version")) != 1 || Text(root.GetProperty("kind")) != Kind || Text(root.GetProperty("rules_id")) != RulesIdentity)
            throw new InvalidDataException("Unsupported request run schema, kind or compiled rules; explicit migration required.");
        string id = Text(root.GetProperty("journal_id"));
        if (!Guid.TryParseExact(id, "N", out var guid) || guid.ToString("N") != id) throw new InvalidDataException("Invalid request journal identity.");
        journalId = id;
        var rows = root.GetProperty("entries");
        if (rows.ValueKind != JsonValueKind.Array || rows.GetArrayLength() > MaximumEntries) throw new InvalidDataException("Request entry count exceeds limit.");
        var candidate = new List<Entry>();
        foreach (var row in rows.EnumerateArray())
        {
            Fields(row, "sequence", "request_id", "command", "day", "state_hash");
            candidate.Add(new Entry(Integer(row.GetProperty("sequence")), Text(row.GetProperty("request_id"), 64),
                Text(row.GetProperty("command"), 64), Integer(row.GetProperty("day")), Text(row.GetProperty("state_hash"), 64)));
        }
        if (Text(root.GetProperty("checksum")) != Hash(Payload(candidate))) throw new InvalidDataException("Request run checksum mismatch.");
        var replayed = Replay(candidate); game = replayed.Game; day = replayed.Day; lastCommand = replayed.Command; entries = candidate;
    }

    private void Write(List<Entry> rows, bool replace, Action<string>? fault)
    {
        string text = Encode(rows);
        if (Encoding.UTF8.GetByteCount(text) > MaximumBytes) throw new InvalidDataException("Request run exceeds byte limit.");
        string temporary = path + "." + Guid.NewGuid().ToString("N") + ".tmp";
        try
        {
            using (var output = new FileStream(temporary, FileMode.CreateNew, FileAccess.Write, FileShare.None, 4096, FileOptions.WriteThrough))
            { byte[] bytes = Encoding.UTF8.GetBytes(text); output.Write(bytes); output.Flush(true); }
            fault?.Invoke("before_replace"); File.Move(temporary, path, replace); fault?.Invoke("after_replace");
        }
        finally { if (File.Exists(temporary)) File.Delete(temporary); }
    }
    private string RunId => journalId + "-day-" + day;
    private JournalReceipt Receipt(bool accepted, bool duplicate, int original, string command, string reason, string? text = null) => new
        (accepted, duplicate, blocked, entries.Count, original, day, RunId, command, reason, text ?? game.Last, JsonSerializer.SerializeToElement(game.Snapshot()));
    public JournalReceipt Snapshot()
    {
        lock (ownership)
        {
            if (disposed) throw new ObjectDisposedException(nameof(RequestJournal));
            return Receipt(!blocked, false, entries.Count, lastCommand, blocked ? "Storage outcome is uncertain; close and resume before another action." : "Current committed request run.",
                blocked ? "Storage is blocked. These are the last published facts, not confirmation of the uncertain disk outcome. Close and resume the validated run." : null);
        }
    }

    public JournalReceipt Submit(string runId, string requestId, int expectedRevision, string command, Action<string>? fault = null)
    {
        lock (ownership)
        {
            if (disposed) throw new ObjectDisposedException(nameof(RequestJournal));
            if (blocked) throw new IOException("Request owner is blocked after uncertain storage; close and resume the validated run.");
            if (runId != RunId) return Receipt(false, false, 0, command ?? "", "Stale run/day identity; observe the current committed run.");
            if (!Identifier(requestId) || command == null || !Commands.Contains(command) || expectedRevision < 0) throw new ArgumentException("Invalid exact request identity, command or revision.");
            var previous = entries.FirstOrDefault(row => row.RequestId == requestId);
            if (previous != null)
                return Receipt(previous.Command == command, previous.Command == command, previous.Sequence, command,
                    previous.Command == command ? "Already committed; no repeated effect." : "Request identity content conflict.");
            if (expectedRevision != entries.Count) return Receipt(false, false, 0, command, "Stale request revision; observe current facts before a fresh decision.");
            if (entries.Count >= MaximumEntries) return Receipt(false, false, 0, command, "Request journal limit reached.");
            var replayed = Replay(entries); var candidate = replayed.Game; int nextDay = replayed.Day;
            if (command == "restart") { candidate = new RequestExpedition(); nextDay = checked(nextDay + 1); }
            else if (!candidate.Command(command)) return Receipt(false, false, 0, command, "Action refused; committed narrative unchanged.", candidate.Last);
            var next = new List<Entry>(entries) { new(entries.Count + 1, requestId, command, nextDay, StateHash(candidate)) };
            try { Write(next, true, fault); }
            catch { blocked = true; throw; }
            entries = next; game = candidate; day = nextDay; lastCommand = command;
            return Receipt(true, false, entries.Count, command, "Committed before receipt.");
        }
    }
    public void Dispose()
    {
        lock (ownership) { if (disposed) return; disposed = true; lease.Dispose(); }
    }
}
