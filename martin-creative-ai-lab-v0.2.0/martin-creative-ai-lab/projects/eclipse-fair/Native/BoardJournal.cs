using System.Collections.Immutable;
using System.Text.Json;
using Eclipse.Core;
using Eclipse.Cli;

namespace Eclipse.Board;

public sealed record BoardSave(int BoardSchema, int[] HumanSeats, SaveData Match);

// The native envelope retains local controls; the nested economy journal is unchanged.
public static class BoardJournal
{
    public static ImmutableArray<int> Seats(IEnumerable<int> seats)
    {
        var values = seats.ToArray();
        if (values.Length is < 1 or > 4 || values.Any(i => i is < 0 or > 3) || values.Distinct().Count() != values.Length)
            throw new ArgumentException("Choose one to four distinct local seats, numbered 0–3.");
        return values.Order().ToImmutableArray();
    }
    public static void Save(Game game, string[] policies, ImmutableArray<int> seats, string filename)
    {
        var data = new BoardSave(1, Seats(seats).ToArray(), Journal.Snapshot(game, policies));
        var path = Path.GetFullPath(filename); Directory.CreateDirectory(Path.GetDirectoryName(path)!);
        var temporary = path + "." + Guid.NewGuid().ToString("N") + ".tmp";
        try { File.WriteAllText(temporary, JsonSerializer.Serialize(data, Journal.Json)); File.Move(temporary, path, true); }
        finally { if (File.Exists(temporary)) File.Delete(temporary); }
    }
    public static (Game Game, string[] Policies, ImmutableArray<int> Seats) Load(string filename)
    {
        var file = new FileInfo(filename);
        if (!file.Exists || file.Length > 200_000) throw new ArgumentException("Native save is missing or exceeds 200 KB.");
        var text = File.ReadAllText(filename);
        using var json = JsonDocument.Parse(text);
        if (json.RootElement.ValueKind != JsonValueKind.Object) throw new ArgumentException("Invalid native save.");
        if (!json.RootElement.TryGetProperty("boardSchema", out _))
        {
            var legacy = Journal.Load(filename);
            return (legacy.Game, legacy.Policies, [0]);
        }
        var data = JsonSerializer.Deserialize<BoardSave>(text, Journal.Json);
        if (data == null || data.BoardSchema != 1 || data.HumanSeats == null || data.Match == null)
            throw new ArgumentException("Unsupported or incomplete native save.");
        var seats = Seats(data.HumanSeats);
        var match = Journal.Replay(data.Match);
        return (match.Game, match.Policies, seats);
    }
}
