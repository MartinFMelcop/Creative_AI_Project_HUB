using System.Text.Json;

namespace Eclipse.Board;

public enum BoardSlotStatus { Empty, Ready, Unavailable }

public sealed record BoardSlotSummary(int Slot, BoardSlotStatus Status, bool IsOccupied,
    int? Seed, int? Round, int? AcceptedTurns, string[] LocalPlayers,
    string? NextParticipant, string[] Winners, string Detail);

// Each slot is the existing validated board journal; there is no trusted index.
public sealed class BoardSlots
{
    private readonly string basePath;
    public BoardSession Current { get; private set; }
    public bool HasCurrent { get; private set; }
    public int CurrentSlot { get; private set; } = 1;
    public string Notice { get; private set; } = "Choose a slot to start or resume a fair.";

    public BoardSlots(string basePath)
    {
        this.basePath = Path.GetFullPath(basePath);
        Current = new(this.basePath);
        HasCurrent = !InspectSlot(1).IsOccupied;
    }

    public string PathFor(int slot)
    {
        if (slot is < 1 or > 3) throw new ArgumentOutOfRangeException(nameof(slot), "Choose slot 1, 2 or 3.");
        var extension = Path.GetExtension(basePath);
        return slot == 1 ? basePath : Path.Combine(Path.GetDirectoryName(basePath)!,
            Path.GetFileNameWithoutExtension(basePath) + ".slot" + slot + (extension.Length == 0 ? ".json" : extension));
    }

    public IReadOnlyList<BoardSlotSummary> Inspect() => Enumerable.Range(1, 3).Select(InspectSlot).ToArray();

    private BoardSlotSummary InspectSlot(int slot)
    {
        var path = PathFor(slot);
        try
        {
            var attributes = File.GetAttributes(path);
            if ((attributes & FileAttributes.Directory) != 0)
                return Unavailable(slot, "The save path is a directory; no fair was loaded.");
            var loaded = BoardJournal.Load(path);
            var game = loaded.Game;
            var locals = loaded.Seats.Select(i => game.People[i].Name).ToArray();
            var next = game.Result == null ? game.People[game.Current].Name : null;
            var winners = game.Result?.Winners.Select(i => game.People[i].Name).ToArray() ?? [];
            var detail = $"Seed {game.Seed} · Round {game.Round} · {game.Journal.Count} accepted turns\n" +
                "Local: " + string.Join(", ", locals) + "\n" +
                (next != null ? "Next: " + next : "Finished: " + string.Join(", ", winners) + " · " + game.Result!.Reason);
            return new(slot, BoardSlotStatus.Ready, true, game.Seed, game.Round,
                game.Journal.Count, locals, next, winners, detail);
        }
        catch (Exception e) when (e is FileNotFoundException or DirectoryNotFoundException)
        { return new(slot, BoardSlotStatus.Empty, false, null, null, null, [], null, [], "Empty slot."); }
        catch (Exception e) when (e is IOException or UnauthorizedAccessException or ArgumentException or JsonException)
        { return Unavailable(slot, "Saved fair unavailable: " + e.Message); }
    }

    private static BoardSlotSummary Unavailable(int slot, string detail) =>
        new(slot, BoardSlotStatus.Unavailable, true, null, null, null, [], null, [], detail);

    private bool PreserveCurrent()
    {
        if (!HasCurrent || !Current.HasUnsavedChanges || Current.Save()) return true;
        Notice = $"Slot {CurrentSlot} has unsaved progress. Keep this fair and retry Save before switching. " + Current.Notice;
        return false;
    }

    public bool TryLoad(int slot)
    {
        try
        {
            var path = PathFor(slot);
            // Save before reading, including resuming this same slot, so a newly
            // recovered write cannot be replaced by its older disk snapshot.
            if (!PreserveCurrent()) return false;
            var candidate = new BoardSession(path);
            if (!candidate.Load()) { Notice = $"Slot {slot}: " + candidate.Notice; return false; }
            Current = candidate; CurrentSlot = slot; HasCurrent = true;
            Notice = $"Resumed slot {slot}. " + candidate.Notice;
            return true;
        }
        catch (ArgumentException e) { Notice = e.Message; return false; }
    }

    public bool TryNew(int slot, int seed, bool strategic = true, IEnumerable<int>? humanSeats = null, bool replace = false)
    {
        try
        {
            var candidate = new BoardSession(PathFor(slot));
            candidate.New(seed, strategic, humanSeats);
            if (InspectSlot(slot).IsOccupied && !replace)
            { Notice = $"Slot {slot} already contains a save or unavailable path. Confirm replacement first."; return false; }
            if (!PreserveCurrent()) return false;
            // A successful recovery of this slot may have created its file.
            if (InspectSlot(slot).IsOccupied && !replace)
            { Notice = $"Slot {slot} is now saved. Confirm replacement first."; return false; }
            if (!candidate.Save()) { Notice = $"Could not start slot {slot}; current fair kept. " + candidate.Notice; return false; }
            Current = candidate; CurrentSlot = slot; HasCurrent = true;
            Notice = $"Started and saved slot {slot}. Other slots were kept.";
            return true;
        }
        catch (ArgumentException e) { Notice = "New fair rejected; current fair kept. " + e.Message; return false; }
    }
}
