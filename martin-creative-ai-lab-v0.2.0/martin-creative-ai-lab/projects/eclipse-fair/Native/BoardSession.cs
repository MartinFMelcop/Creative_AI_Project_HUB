using Eclipse.Core;
using Eclipse.Cli;
using System.Collections.Immutable;

namespace Eclipse.Board;

// This consumer reuses the same transactions and journal as the terminal game.
public sealed class BoardSession
{
    public Game Game { get; private set; }
    public string[] Policies { get; private set; } = Planning.NativePolicies.ToArray();
    public ImmutableArray<int> HumanSeats { get; private set; } = [0];
    private int readySeat = -1, viewSeat;
    public bool IsHumanTurn => Game.Result == null && HumanSeats.Contains(Game.Current);
    public bool AwaitingPlayer => IsHumanTurn && HumanSeats.Length > 1 && readySeat != Game.Current;
    public int ViewSeat => IsHumanTurn ? Game.Current : viewSeat;
    private Game? adviceGame;
    private int adviceTurns = -1;
    private PlanAdvice? advice;
    public string SavePath { get; }
    public bool HasUnsavedChanges { get; private set; }
    public string Notice { get; private set; } = "Choose a venue, compare an action, then commit your turn.";

    public BoardSession(string savePath, int seed = 1) { SavePath = savePath; Game = new(seed); }
    public void New(int seed, bool strategic = true, IEnumerable<int>? humanSeats = null)
    {
        var seats = BoardJournal.Seats(humanSeats ?? [0]); var game = new Game(seed);
        Game = game; HumanSeats = seats; readySeat = -1; viewSeat = seats[0];
        Policies = strategic ? Planning.NativePolicies.ToArray() : ["collector", "keeper", "opportunist", "collector"];
        HasUnsavedChanges = true;
        Notice = "New fair. Previous save stays until an accepted turn or explicit Save.";
    }
    public bool Act(Intent intent)
    {
        if (!IsHumanTurn || AwaitingPlayer) { Notice = AwaitingPlayer ? "Begin the named local player's turn first." : "Wait for the rival's turn."; return false; }
        return Apply(intent);
    }
    public bool Rival()
    {
        if (Game.Result != null || IsHumanTurn) return false;
        return Apply(Advice().First);
    }
    public bool BeginTurn()
    {
        if (!IsHumanTurn || !AwaitingPlayer) return false;
        readySeat = Game.Current; Notice = Game.People[readySeat].Name + " can now compare and commit a plan."; return true;
    }
    public PlanAdvice Advice()
    {
        if (advice != null && ReferenceEquals(adviceGame, Game) && adviceTurns == Game.Journal.Count) return advice;
        var profile = Policies[Game.Current];
        if (Planning.Names.Contains(profile)) advice = Planning.Analyze(Game, profile, Policies);
        else { var intent = Agents.Choose(Game, profile); advice = new(intent, [intent], "Classic one-turn profile", 0); }
        adviceGame = Game; adviceTurns = Game.Journal.Count; return advice;
    }
    public ReplyForecast Forecast(Intent intent)
    {
        if (!IsHumanTurn || AwaitingPlayer) throw new ArgumentException("Begin a local turn before comparing replies.");
        var copy = Game.Fork();
        if (!copy.Apply(intent, out _)) throw new ArgumentException("Choose a legal plan before forecasting replies.");
        var start = copy.Journal.Count;
        while (copy.Result == null && !HumanSeats.Contains(copy.Current))
            copy.Apply(Agents.Choose(copy, Policies[copy.Current], Policies), out _);
        return new(copy, copy.Journal.Skip(start).ToImmutableArray());
    }
    private bool Apply(Intent intent)
    {
        var actor = Game.Current;
        if (!Game.Apply(intent, out var description)) { Notice = description; return false; }
        if (HumanSeats.Contains(actor)) viewSeat = actor;
        readySeat = -1;
        HasUnsavedChanges = true;
        if (Save()) Notice = description + " · Saved.";
        else Notice = description + " Progress is in memory; saving failed. " + Notice;
        return true;
    }
    public bool Save()
    {
        try { BoardJournal.Save(Game, Policies, HumanSeats, SavePath); HasUnsavedChanges = false; Notice = "Saved local seats and all accepted turns."; return true; }
        catch (Exception e) when (e is IOException or UnauthorizedAccessException or ArgumentException)
        { HasUnsavedChanges = true; Notice = "Save unavailable: " + e.Message; return false; }
    }
    public bool Load()
    {
        try
        {
            var loaded = BoardJournal.Load(SavePath);
            Game = loaded.Game; Policies = loaded.Policies; HumanSeats = loaded.Seats;
            readySeat = -1; viewSeat = IsHumanTurn ? Game.Current : HumanSeats[0];
            HasUnsavedChanges = false;
            Notice = "Saved turns replayed. Continue from the exact next participant."; return true;
        }
        catch (Exception e) when (e is IOException or UnauthorizedAccessException or ArgumentException or System.Text.Json.JsonException)
        { Notice = "Save rejected; current match kept. " + e.Message; return false; }
    }
    public string ReplayPath => Path.ChangeExtension(SavePath, ".replay.json");
    public bool ExportReplay()
    {
        try { Journal.Save(Game, Policies, ReplayPath); Notice = "Exported economy replay: " + ReplayPath; return true; }
        catch (Exception e) when (e is IOException or UnauthorizedAccessException or ArgumentException)
        { Notice = "Replay export unavailable: " + e.Message; return false; }
    }
    public Game Preview(Intent intent)
    {
        var copy = Game.Fork();
        if (!copy.Apply(intent, out _)) throw new ArgumentException("Plan is no longer legal.");
        return copy;
    }
}
