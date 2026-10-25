using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using NorthStar.Domain;
using NorthStar.Tooling;

internal static class Program
{
    private static readonly JsonSerializerOptions Json = new() { WriteIndented = true };
    private static readonly List<string> controls = new();
    private static void Check(bool condition, string label)
    { if (!condition || controls.Contains(label)) throw new InvalidOperationException(label); controls.Add(label); }
    private static void Reject(Action action, string label)
    {
        bool rejected = false;
        try { action(); } catch (Exception e) when (e is ArgumentException || e is InvalidOperationException || e is NotSupportedException) { rejected = true; }
        Check(rejected, label);
    }
    private static MaterialAmount Amount(string id, int quantity) => new(id, quantity);
    private static CraftRecipe Core(string id, string input = "fiber", string output = "rig") => new(id, "bench", "permit", new[] { Amount(input, 1) }, new[] { Amount(output, 1) });
    private static ToolRecipe Rig() => new(new CraftRecipe("rig", "bench", "permit", new[] { Amount("fiber", 2), Amount("binder", 1) }, new[] { Amount("rig", 1) }), new[] { "gauge" });
    private static ItemCatalog Catalog() => new(new[] { "fiber", "binder", "gauge", "rig", "ink", "CON_ESSENCIA_ESPIRITUAL_COMUM" });
    private static ToolWorkshop Workshop(int gauge = 1) => new(Catalog(), new[] { Amount("fiber", 4), Amount("binder", 2), Amount("gauge", gauge) }, new[] { Rig() }, new[] { "permit" });
    private static string State(ToolWorkshop workshop) => JsonSerializer.Serialize(workshop.Snapshot);
    private static void Write(string output, object value)
    { using var stream = new FileStream(output, FileMode.CreateNew, FileAccess.Write, FileShare.None); JsonSerializer.Serialize(stream, value, Json); }
    private static void Native(string output)
    {
        var catalog = Catalog();
        Check(catalog.Count == 6 && catalog.Contains("gauge"), "catalog-retains-exact-known-identity");
        Check(!catalog.Contains("Gauge") && !catalog.Contains("gau") && !catalog.Contains("unknown") && !catalog.Contains("gauge ") && !catalog.Contains(null!), "case-substring-unknown-and-malformed-queries-do-not-resolve");
        Reject(() => new ItemCatalog(new[] { "gauge", "gauge" }), "duplicate-known-identity-refused");
        Reject(() => new ItemCatalog(new[] { "not an id" }), "malformed-known-identity-refused");
        Reject(() => new ItemCatalog(Array.Empty<string>()), "empty-catalog-refused");
        var recipe = Rig();
        Reject(() => ((ICollection<string>)recipe.RequiredTools).Add("fiber"), "retained-tool-requirements-are-not-mutable");
        var owner = Workshop(); var initial = owner.Snapshot;
        Check(owner.Craft("first", "rig", "bench").Applied && owner.Quantity("fiber") == 2 && owner.Quantity("binder") == 1 && owner.Quantity("gauge") == 1 && owner.Quantity("rig") == 1, "first-real-production-consumes-materials-and-retains-one-tool");
        Check(owner.Craft("second", "rig", "bench").Applied && owner.Quantity("fiber") == 0 && owner.Quantity("binder") == 0 && owner.Quantity("gauge") == 1 && owner.Quantity("rig") == 2, "second-real-production-reuses-same-retained-tool");
        Check(initial["fiber"] == 4 && initial["binder"] == 2 && initial["gauge"] == 1 && !initial.ContainsKey("rig"), "earlier-snapshot-is-an-isolated-copy");
        Reject(() => ((IDictionary<string, int>)owner.Snapshot).Add("fiber", 99), "published-snapshot-cannot-mutate-private-owner");
        string before = State(owner); int committed = owner.CommittedCount;
        var replay = owner.Craft("first", "rig", "bench");
        Check(!replay.Applied && replay.Replay && State(owner) == before && owner.CommittedCount == committed, "existing-core-replays-accepted-request-without-second-effect");
        var conflict = owner.Craft("first", "rig", "other_bench");
        Check(!conflict.Applied && !conflict.Replay && State(owner) == before, "conflicting-request-content-does-not-change-inventory");
        var consumeTool = owner.Consume("no_tool_loss", "gauge", 1);
        Check(!consumeTool.Applied && State(owner) == before && owner.CommittedCount == committed, "declared-tool-cannot-be-consumed-or-reserve-a-request");
        Check(owner.Consume("no_tool_loss", "rig", 1).Applied && owner.Quantity("rig") == 1 && owner.Quantity("gauge") == 1, "refused-tool-request-id-remains-available-for-valid-core-consumption");
        var missing = Workshop(0); before = State(missing);
        Check(!missing.Craft("absent", "rig", "bench").Applied && State(missing) == before && missing.CommittedCount == 0, "missing-tool-refuses-without-material-loss-or-ledger-entry");
        var made = new ToolWorkshop(Catalog(), new[] { Amount("fiber", 5), Amount("binder", 2) }, new[] { Rig(), new ToolRecipe(Core("make_tool", "fiber", "gauge"), Array.Empty<string>()) }, new[] { "permit" });
        Check(made.Quantity("gauge") == 0 && !made.Craft("pending", "rig", "bench").Applied, "catalog-presence-does-not-grant-actual-tool-ownership");
        Check(made.Craft("make", "make_tool", "bench").Applied && made.Craft("pending", "rig", "bench").Applied && made.Quantity("gauge") == 1 && made.CommittedCount == 2, "actually-produced-tool-enables-previously-refused-request");
        before = State(made);
        Check(made.Craft("make", "make_tool", "bench").Replay && State(made) == before, "tool-production-retry-also-uses-core-receipt-without-duplication");
        const string essence = "CON_ESSENCIA_ESPIRITUAL_COMUM";
        var dual = new ToolWorkshop(Catalog(), new[] { Amount(essence, 2) }, new[] { new ToolRecipe(Core("ink_batch", essence, "ink"), Array.Empty<string>()) }, new[] { "permit" });
        Check(dual.Craft("dual_use", "ink_batch", "bench").Applied && dual.Quantity(essence) == 1 && dual.Quantity("ink") == 1, "consumable-ingredient-keeps-exact-id-and-is-consumed-once");
        Check(!dual.Snapshot.ContainsKey("MAT_ESSENCIA_ESPIRITUAL") && !catalog.Contains("MAT_ESSENCIA_ESPIRITUAL"), "no-unprovided-material-alias-is-invented");
        Reject(() => new ToolWorkshop(Catalog(), new[] { Amount("Gauge", 1) }, new[] { Rig() }, new[] { "permit" }), "unknown-initial-item-refused");
        Reject(() => new ToolWorkshop(Catalog(), Array.Empty<MaterialAmount>(), new[] { new ToolRecipe(Core("bad_input", "unknown"), Array.Empty<string>()) }, new[] { "permit" }), "unknown-recipe-input-refused");
        Reject(() => new ToolWorkshop(Catalog(), Array.Empty<MaterialAmount>(), new[] { new ToolRecipe(Core("bad_output", "fiber", "unknown"), Array.Empty<string>()) }, new[] { "permit" }), "unknown-recipe-output-refused");
        Reject(() => new ToolWorkshop(Catalog(), Array.Empty<MaterialAmount>(), new[] { new ToolRecipe(Core("bad_tool"), new[] { "Gauge" }) }, new[] { "permit" }), "unknown-required-tool-refused");
        Reject(() => new ToolWorkshop(Catalog(), Array.Empty<MaterialAmount>(), new[] { Rig(), new ToolRecipe(Core("consume_tool", "gauge"), Array.Empty<string>()) }, new[] { "permit" }), "tool-input-overlap-is-refused-across-all-recipes");
        Reject(() => made.Consume("unknown_consume", "unknown", 1), "unknown-consume-id-refused-before-quantity-lookup");
        Reject(() => made.Quantity("Gauge"), "quantity-lookup-does-not-fuzz-or-grant-unknown-id");
        var capacity = new ToolWorkshop(Catalog(), new[] { Amount("fiber", 2), Amount("binder", 1), Amount("gauge", 1), Amount("rig", CraftInventory.MaximumQuantity) }, new[] { Rig() }, new[] { "permit" }); before = State(capacity);
        Check(!capacity.Craft("full", "rig", "bench").Applied && State(capacity) == before && capacity.CommittedCount == 0, "existing-atomic-core-capacity-refusal-preserves-tool-and-materials");
        Write(output, new { schema_version = 1, passed = controls.Count, failed = 0, controls, scope = "Selected exact-ID and retained-tool composition around unchanged CraftInventory. No historical recipe/unlock/price/effect runtime, source repair, Unity/Windows, account, physical tool or human quality proof." });
        Console.WriteLine("PASS: " + controls.Count + " tooling native controls");
    }
    private static void Fields(JsonElement element, params string[] names)
    {
        if (element.ValueKind != JsonValueKind.Object) throw new ArgumentException("Object required.");
        var expected = new HashSet<string>(names, StringComparer.Ordinal); var actual = new HashSet<string>(StringComparer.Ordinal);
        foreach (var property in element.EnumerateObject()) if (!expected.Contains(property.Name) || !actual.Add(property.Name)) throw new ArgumentException("Unknown or duplicate field.");
        if (actual.Count != expected.Count) throw new ArgumentException("Exact fields required.");
    }
    private static string Text(JsonElement value)
    { if (value.ValueKind != JsonValueKind.String || value.GetString()!.Length < 1 || value.GetString()!.Length > 128) throw new ArgumentException("Bounded nonempty string required."); return value.GetString()!; }
    private static int CatalogCases(string input, string output)
    {
        if (new FileInfo(input).Length > 1024 * 1024) throw new ArgumentException("Catalog case input exceeds1MiB.");
        using var doc = JsonDocument.Parse(File.ReadAllText(input), new JsonDocumentOptions { MaxDepth = 16 }); var root = doc.RootElement;
        Fields(root, "schema_version", "known_ids", "references");
        if (root.GetProperty("schema_version").ValueKind != JsonValueKind.Number || !root.GetProperty("schema_version").TryGetInt32(out int schema) || schema != 1) throw new ArgumentException("Unsupported catalog case schema.");
        var known = root.GetProperty("known_ids"); var refs = root.GetProperty("references");
        if (known.ValueKind != JsonValueKind.Array || refs.ValueKind != JsonValueKind.Array || known.GetArrayLength() > 4096 || refs.GetArrayLength() < 1 || refs.GetArrayLength() > 4096) throw new ArgumentException("Bounded known IDs and references required.");
        var catalog = new ItemCatalog(known.EnumerateArray().Select(Text).ToArray());
        var ids = new HashSet<string>(StringComparer.Ordinal); var results = new List<object>(); int passed = 0, failed = 0;
        foreach (var row in refs.EnumerateArray())
        {
            Fields(row, "id", "item_id", "expected"); string id = Text(row.GetProperty("id")), item = Text(row.GetProperty("item_id"));
            if (!ids.Add(id)) throw new ArgumentException("Duplicate reference case identity.");
            bool actual = catalog.Contains(item);
            if (row.GetProperty("expected").ValueKind is not (JsonValueKind.True or JsonValueKind.False)) throw new ArgumentException("Boolean expected value required.");
            bool expected = row.GetProperty("expected").GetBoolean(), ok = actual == expected; if (ok) passed++; else failed++;
            results.Add(new { id, item_id = item, actual, expected, passed = ok });
        }
        Write(output, new { schema_version = 1, references = results, passed, failed });
        Console.WriteLine(JsonSerializer.Serialize(new { passed, failed })); return failed == 0 ? 0 : 1;
    }
    private static int Main(string[] args)
    {
        try
        {
            if (args.Length == 2 && args[0] == "--native") { Native(args[1]); return 0; }
            if (args.Length == 3 && args[0] == "--catalog") return CatalogCases(args[1], args[2]);
            throw new ArgumentException("Usage: --native OUTPUT_JSON | --catalog INPUT_JSON OUTPUT_JSON");
        }
        catch (Exception e) when (e is ArgumentException || e is InvalidOperationException || e is IOException || e is JsonException || e is UnauthorizedAccessException || e is KeyNotFoundException)
        { Console.Error.WriteLine(e.Message); return 1; }
    }
}
