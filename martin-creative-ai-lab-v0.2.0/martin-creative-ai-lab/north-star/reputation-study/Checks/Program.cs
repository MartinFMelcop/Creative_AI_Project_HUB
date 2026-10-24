using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using NorthStar.Reputation;

internal static class Program
{
    private static readonly JsonSerializerOptions Json = new JsonSerializerOptions { WriteIndented = true };
    private static void Fields(JsonElement element, params string[] names)
    {
        if (element.ValueKind != JsonValueKind.Object) throw new ArgumentException("Object required.");
        var allowed = new HashSet<string>(names, StringComparer.Ordinal);
        var seen = new HashSet<string>(StringComparer.Ordinal);
        foreach (var property in element.EnumerateObject())
            if (!allowed.Contains(property.Name) || !seen.Add(property.Name)) throw new ArgumentException("Unknown or duplicate field.");
        if (seen.Count != allowed.Count) throw new ArgumentException("Exact fields required.");
    }
    private static int Integer(JsonElement parent, string name)
    {
        var value = parent.GetProperty(name);
        if (value.ValueKind != JsonValueKind.Number || !value.TryGetInt32(out int number)) throw new ArgumentException("Int32 required: " + name);
        return number;
    }
    private static string Text(JsonElement parent, string name)
    {
        var value = parent.GetProperty(name);
        if (value.ValueKind != JsonValueKind.String) throw new ArgumentException("String required: " + name);
        string text = value.GetString()!;
        if (text.Length < 1 || text.Length > 128) throw new ArgumentException("Bounded nonempty text required.");
        return text;
    }
    private static int Vectors(string input, string output)
    {
        if (new FileInfo(input).Length > 1024 * 1024) throw new ArgumentException("Vector input exceeds byte limit.");
        using var document = JsonDocument.Parse(File.ReadAllText(input), new JsonDocumentOptions { MaxDepth = 16 });
        var root = document.RootElement;
        Fields(root, "schema_version", "cases");
        if (Integer(root, "schema_version") != 1) throw new ArgumentException("Unsupported vector schema.");
        var cases = root.GetProperty("cases");
        if (cases.ValueKind != JsonValueKind.Array || cases.GetArrayLength() < 1 || cases.GetArrayLength() > 4096) throw new ArgumentException("One to4096 cases required.");
        var identities = new HashSet<string>(StringComparer.Ordinal);
        var results = new List<object>(); int passed = 0, failed = 0;
        foreach (var row in cases.EnumerateArray())
        {
            string operation = Text(row, "operation");
            if (operation == "set") Fields(row, "id", "operation", "value", "expected");
            else if (operation == "add") Fields(row, "id", "operation", "current", "delta", "expected");
            else throw new ArgumentException("Only set/add operations are supported.");
            string id = Text(row, "id");
            if (!identities.Add(id)) throw new ArgumentException("Duplicate case identity.");
            // Expected is compared only after the actual pure implementation computes its result.
            int actual = operation == "set" ? Standing.Set(Integer(row, "value")) : Standing.Add(Integer(row, "current"), Integer(row, "delta"));
            int expected = Integer(row, "expected");
            if (!Standing.IsLevel(expected)) throw new ArgumentException("Expected result must be a legal level.");
            bool ok = actual == expected;
            if (ok) passed++; else failed++;
            results.Add(new { id, actual, expected, passed = ok });
        }
        WriteNew(output, new { schema_version = 1, cases = results, passed, failed });
        Console.WriteLine(JsonSerializer.Serialize(new { passed, failed }));
        return failed == 0 ? 0 : 1;
    }
    private static void WriteNew(string output, object value)
    {
        using var file = new FileStream(output, FileMode.CreateNew, FileAccess.Write, FileShare.None);
        using var writer = new StreamWriter(file);
        writer.WriteLine(JsonSerializer.Serialize(value, Json));
    }
    private static void Native(string output)
    {
        var controls = new List<string>();
        void Check(string id, bool condition)
        {
            if (!condition) throw new InvalidOperationException(id);
            if (controls.Contains(id)) throw new InvalidOperationException("Duplicate native control.");
            controls.Add(id);
        }
        Check("six-exact-legal-levels-exclude-zero", Standing.IsLevel(-3) && Standing.IsLevel(-2) && Standing.IsLevel(-1) && Standing.IsLevel(1) && Standing.IsLevel(2) && Standing.IsLevel(3) && !Standing.IsLevel(0) && !Standing.IsLevel(-4) && !Standing.IsLevel(4));
        Check("set-zero-normalizes-to-positive-one", Standing.Set(0) == 1);
        Check("set-clamps-int-minimum", Standing.Set(int.MinValue) == -3);
        Check("set-clamps-int-maximum", Standing.Set(int.MaxValue) == 3);
        Check("set-retains-legal-signs", Standing.Set(-1) == -1 && Standing.Set(1) == 1 && Standing.Set(-2) == -2 && Standing.Set(2) == 2);
        Check("outward-saturation-at-negative-limit", Standing.Add(-3, -1) == -3);
        Check("outward-saturation-at-positive-limit", Standing.Add(3, 1) == 3);
        Check("inward-movement-from-limits-remains-possible", Standing.Add(-3, 1) == -2 && Standing.Add(3, -1) == 2);
        Check("zero-delta-retains-every-legal-level", Standing.Add(-3, 0) == -3 && Standing.Add(-2, 0) == -2 && Standing.Add(-1, 0) == -1 && Standing.Add(1, 0) == 1 && Standing.Add(2, 0) == 2 && Standing.Add(3, 0) == 3);
        Check("minor-positive-act-cannot-cross-negative-one", Standing.Add(-1, 1) == -1);
        Check("minor-negative-act-cannot-cross-positive-one", Standing.Add(1, -1) == 1);
        int stalled = -1;
        for (int i = 0; i < 100; i++) stalled = Standing.Add(stalled, 1);
        Check("repeated-minor-positive-acts-remain-stalled", stalled == -1);
        stalled = 1;
        for (int i = 0; i < 100; i++) stalled = Standing.Add(stalled, -1);
        Check("repeated-minor-negative-acts-remain-stalled", stalled == 1);
        Check("threshold-positive-act-crosses-sign", Standing.Add(-1, 2) == 1);
        Check("threshold-negative-act-crosses-sign", Standing.Add(1, -2) == -1);
        Check("zero-result-at-threshold-selects-delta-sign", Standing.Add(-2, 2) == 1 && Standing.Add(2, -2) == -1);
        Check("large-exact-zero-crossing-selects-delta-sign", Standing.Add(-3, 3) == 1 && Standing.Add(3, -3) == -1);
        Check("int-max-addition-clamps-without-overflow", Standing.Add(-3, int.MaxValue) == 3 && Standing.Add(1, int.MaxValue) == 3);
        Check("int-min-addition-clamps-without-abs-overflow", Standing.Add(3, int.MinValue) == -3 && Standing.Add(-1, int.MinValue) == -3);
        foreach (int invalid in new[] { int.MinValue, -4, 0, 4, int.MaxValue })
        {
            bool rejected = false;
            try { Standing.Add(invalid, 1); }
            catch (ArgumentOutOfRangeException) { rejected = true; }
            Check("invalid-current-refused-" + invalid.ToString(System.Globalization.CultureInfo.InvariantCulture), rejected);
        }
        bool closed = true;
        foreach (int current in new[] { -3, -2, -1, 1, 2, 3 })
            foreach (int delta in new[] { int.MinValue, -1000, -6, -3, -2, -1, 0, 1, 2, 3, 6, 1000, int.MaxValue })
                closed &= Standing.IsLevel(Standing.Add(current, delta));
        Check("selected-domain-remains-in-six-level-range", closed);
        WriteNew(output, new { schema_version = 1, passed = controls.Count, failed = 0, controls, scope = "Selected arithmetic only; no historical Ruby/RMXP, social policy, effects catalog, Unity/Windows or human balance execution." });
        Console.WriteLine("PASS: " + controls.Count + " reputation arithmetic controls.");
    }
    private static int Main(string[] args)
    {
        try
        {
            if (args.Length == 3 && args[0] == "--vectors") return Vectors(args[1], args[2]);
            if (args.Length == 2 && args[0] == "--native") { Native(args[1]); return 0; }
            throw new ArgumentException("Usage: --native OUTPUT_JSON | --vectors INPUT_JSON OUTPUT_JSON");
        }
        catch (Exception error) when (error is ArgumentException || error is InvalidOperationException || error is IOException || error is JsonException || error is UnauthorizedAccessException || error is KeyNotFoundException)
        { Console.Error.WriteLine(error.Message); return 1; }
    }
}
