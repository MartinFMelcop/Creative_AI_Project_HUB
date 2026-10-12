using Eclipse.Core;
using Eclipse.Cli;

namespace Eclipse.Board;

// This consumer reuses the same transactions and journal as the terminal game.
public sealed class BoardSession
{
    public Game Game { get; private set; }
    public string[] Policies { get; private set; } = ["collector", "keeper", "opportunist", "collector"];
    public string SavePath { get; }
    public string Notice { get; private set; } = "Choose a venue, compare an action, then commit your turn.";

    public BoardSession(string savePath, int seed = 1) { SavePath = savePath; Game = new(seed); }
    public void New(int seed)
    {
        Game = new(seed); Policies = ["collector", "keeper", "opportunist", "collector"];
        Notice = "New fair. Previous save stays until an accepted turn or explicit Save.";
    }
    public bool Act(Intent intent)
    {
        if (Game.Result != null || Game.Current != 0) { Notice = "Wait for the rival's turn."; return false; }
        return Apply(intent);
    }
    public bool Rival()
    {
        if (Game.Result != null || Game.Current == 0) return false;
        return Apply(Agents.Choose(Game, Policies[Game.Current]));
    }
    private bool Apply(Intent intent)
    {
        if (!Game.Apply(intent, out var description)) { Notice = description; return false; }
        if (Save()) Notice = description + " · Saved.";
        else Notice = description + " Progress is in memory; saving failed. " + Notice;
        return true;
    }
    public bool Save()
    {
        try { Journal.Save(Game, Policies, SavePath); Notice = "Saved all accepted turns."; return true; }
        catch (Exception e) when (e is IOException or UnauthorizedAccessException or ArgumentException)
        { Notice = "Save unavailable: " + e.Message; return false; }
    }
    public bool Load()
    {
        try
        {
            var loaded = Journal.Load(SavePath);
            Game = loaded.Game; Policies = loaded.Policies;
            Notice = "Saved turns replayed. Continue from the exact next participant."; return true;
        }
        catch (Exception e) when (e is IOException or UnauthorizedAccessException or ArgumentException or System.Text.Json.JsonException)
        { Notice = "Save rejected; current match kept. " + e.Message; return false; }
    }
    public Game Preview(Intent intent)
    {
        var copy = Game.Fork();
        if (!copy.Apply(intent, out _)) throw new ArgumentException("Plan is no longer legal.");
        return copy;
    }
}
