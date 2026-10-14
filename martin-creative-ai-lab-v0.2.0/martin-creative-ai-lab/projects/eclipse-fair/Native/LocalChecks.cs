using Godot;
using Eclipse.Core;
using Eclipse.Cli;
using System.Text.Json;
using System.Text.Json.Nodes;

namespace Eclipse.Board;

public partial class Main
{
    private async Task VerifyLocalSeats()
    {
        // Exercise the actual configuration dialog, including its empty-selection gate.
        NewDialog(); var setup = GetChildren().OfType<ConfirmationDialog>().Single();
        var local = setup.FindChildren("*", "CheckButton", true, false).OfType<CheckButton>().ToArray();
        foreach (var b in local) b.ButtonPressed = false;
        Require(setup.GetOkButton().Disabled, "A fair with no local players could start");
        local[2].ButtonPressed = true; setup.FindChildren("*", "SpinBox", true, false).OfType<SpinBox>().Single().Value = 2;
        await Capture("local-setup");
        Require(setup.Size.X <= Size.X - 20 && setup.Size.Y <= Size.Y - 20 && setup.GetOkButton().IsVisibleInTree(), "Configuration or confirmation is outside the playable viewport");
        var controls = local.Cast<Control>().Concat(setup.FindChildren("*", "SpinBox", true, false).OfType<Control>())
            .Concat(setup.FindChildren("*", "OptionButton", true, false).OfType<Control>()).ToArray();
        foreach (var control in controls)
            Require(control.IsVisibleInTree() && control.Size.Y >= 30 && control.GlobalPosition.X >= 0 && control.GlobalPosition.Y >= 0 &&
                control.GlobalPosition.X + control.Size.X <= setup.Size.X && control.GlobalPosition.Y + control.Size.Y <= setup.Size.Y,
                "A configuration control is hidden or outside the dialog");
        for (int i = 0; i < controls.Length; i++)
            for (int j = i + 1; j < controls.Length; j++)
                Require(!controls[i].GetGlobalRect().Intersects(controls[j].GetGlobalRect()), "Configuration controls overlap");
        setup.EmitSignal(ConfirmationDialog.SignalName.Confirmed); await Frame();
        Require(session.HumanSeats.SequenceEqual(new[] { 2 }) && session.Game.Current == 2 && commit.Disabled && !hint.Disabled, "Single Nira configuration failed");
        hint.EmitSignal(BaseButton.SignalName.Pressed); await Capture("local-nira");
        Require(objective.Text.Contains("Nira") && preview.Text.Contains(session.Preview(selected!).People[2].Gold + " obols"), "Nira still received Vaelis's preview");
        var niraBefore = Fingerprint(session.Game); var selectedNira = selected!;
        foreach (var id in Enumerable.Range(0, 8))
            Require(map.Venues[id].TooltipText.Contains(session.Game.Wage(id, session.Game.People[2]) + " now"), "Map wages use a different local seat");
        response.EmitSignal(BaseButton.SignalName.Pressed); var dialog = GetChildren().OfType<AcceptDialog>().Single();
        Require(dialog.DialogText.Contains("Nira after these turns") && Fingerprint(session.Game) == niraBefore, "Nonzero-seat response mutated play or described another actor");
        await Capture("local-forecast"); dialog.EmitSignal(AcceptDialog.SignalName.Confirmed); await Frame();
        commit.EmitSignal(BaseButton.SignalName.Pressed);
        Require(session.Game.Journal.Last().Actor == 2 && session.Game.Journal.Last().Intent == selectedNira, "Nonzero local confirmation used another actor");

        // A forecast must stop at Madra, even if her configured suggestion would be legal.
        session.New(0, humanSeats: [0, 1]); ResetSelection(); Refresh();
        var waiting = Fingerprint(session.Game);
        Require(session.AwaitingPlayer && begin.Visible && commit.Disabled && hint.Disabled && response.Disabled && next.Disabled, "Handoff left a spending control enabled");
        Require(!session.Act(session.Game.Legal()[0]) && !session.Rival(), "Handoff accepted a hidden local or automatic turn");
        automatic.ButtonPressed = true; verification = false; _Process(5); verification = true;
        Require(Fingerprint(session.Game) == waiting, "Automatic rivals spent a human handoff");
        begin.GrabFocus();
        Input.ParseInputEvent(new InputEventKey { Keycode = Key.Enter, Pressed = true }); await Frame();
        Input.ParseInputEvent(new InputEventKey { Keycode = Key.Enter, Pressed = false }); await Frame();
        Require(!session.AwaitingPlayer && Fingerprint(session.Game) == waiting, "Beginning a turn spent game time");
        var work = new Intent(session.Game.People[0].Position, ActionKind.Work);
        var before = Fingerprint(session.Game); var forecast = session.Forecast(work);
        Require(forecast.Replies.Length == 0 && forecast.After.Current == 1 && forecast.After.Journal.Count == session.Game.Journal.Count + 1 && Fingerprint(session.Game) == before,
            "Forecast invented Madra's future input");
        map.Venues[work.Destination].EmitSignal(BaseButton.SignalName.Pressed); planButtons[work].EmitSignal(BaseButton.SignalName.Pressed);
        response.EmitSignal(BaseButton.SignalName.Pressed); dialog = GetChildren().OfType<AcceptDialog>().Single();
        Require(dialog.DialogText.Contains("Next local decision: Madra") && dialog.DialogText.Contains("No rival acts"), "Mixed dialog implied a human reply");
        await Capture("local-mixed-forecast"); dialog.EmitSignal(AcceptDialog.SignalName.Confirmed); await Frame();
        commit.EmitSignal(BaseButton.SignalName.Pressed); await Capture("local-handoff");
        Require(session.AwaitingPlayer && session.Game.Current == 1 && selected == null && planButtons.Count == 0, "Another local player inherited the previous plan");
        begin.EmitSignal(BaseButton.SignalName.Pressed); hint.EmitSignal(BaseButton.SignalName.Pressed); await Capture("local-madra");
        Require(objective.Text.Contains("Madra") && map.ViewSeat == 1, "Handoff failed to change the board perspective");

        session.New(0, humanSeats: [0, 2]); session.BeginTurn();
        forecast = session.Forecast(work);
        Require(forecast.Replies.Length == 1 && forecast.Replies[0].Actor == 1 && forecast.After.Current == 2, "Mixed forecast passed the next human decision");
        session.Act(work); while (!session.IsHumanTurn && session.Game.Result == null) session.Rival();
        Require(Fingerprint(session.Game) == Fingerprint(forecast.After) && session.AwaitingPlayer, "Actual mixed rival replies differ from the bounded forecast");

        session.Save(); var save = File.ReadAllText(session.SavePath); var saved = Fingerprint(session.Game);
        session.New(3, strategic: false, humanSeats: [3]);
        Require(session.Load() && session.HumanSeats.SequenceEqual(new[] { 0, 2 }) && Fingerprint(session.Game) == saved && session.AwaitingPlayer,
            "Resume lost local seats, exact next actor or handoff");
        foreach (var corrupt in new[] { "[]", "[0,0]", "[-1]", "[4]", "null" })
        {
            var data = JsonNode.Parse(save)!; data["humanSeats"] = JsonNode.Parse(corrupt);
            File.WriteAllText(session.SavePath, data.ToJsonString());
            Require(!session.Load() && Fingerprint(session.Game) == saved && session.HumanSeats.SequenceEqual(new[] { 0, 2 }), "Invalid local controls replaced the live match");
        }
        foreach (var field in new[] { "boardSchema", "match", "state" })
        {
            var data = JsonNode.Parse(save)!;
            data[field] = field == "boardSchema" ? JsonValue.Create(99) : field == "match" ? null : new JsonObject();
            File.WriteAllText(session.SavePath, data.ToJsonString());
            Require(!session.Load() && Fingerprint(session.Game) == saved, "Invalid native envelope trusted a snapshot");
        }
        var invalidAction = JsonNode.Parse(save)!; invalidAction["match"]!["actions"]![0]!["destination"] = 99;
        File.WriteAllText(session.SavePath, invalidAction.ToJsonString());
        Require(!session.Load() && Fingerprint(session.Game) == saved, "Invalid nested action replaced the live match");
        File.WriteAllText(session.SavePath, save); Require(session.Load(), "Valid native save failed after rejection");
        Require(session.ExportReplay() && Fingerprint(Journal.Load(session.ReplayPath).Game) == saved && !File.ReadAllText(session.ReplayPath).Contains("humanSeats"), "Economy export lost turns or leaked native configuration");
        Journal.Save(session.Game, ["collector", "keeper", "opportunist", "collector"], session.SavePath);
        Require(session.Load() && session.HumanSeats.SequenceEqual(new[] { 0 }) && session.Policies[1] == "keeper", "Legacy replay did not restore original Vaelis controls and policies");

        // All 15 legal human-seat sets finish through actual board controls. Suggestions
        // are scripted fixtures; their parity is not independent human strategy evidence.
        for (int mask = 1; mask < 16; mask++)
        {
            var seats = Enumerable.Range(0, 4).Where(i => (mask & 1 << i) != 0).ToArray();
            var seed = mask % 4; var strategic = mask % 2 == 1;
            session.New(seed, strategic, seats); ResetSelection(); Refresh();
            while (session.Game.Result == null)
            {
                if (session.IsHumanTurn)
                {
                    if (session.AwaitingPlayer) begin.EmitSignal(BaseButton.SignalName.Pressed);
                    hint.EmitSignal(BaseButton.SignalName.Pressed);
                    var actor = session.Game.Current;
                    Require(selected != null && preview.Text.Contains(session.Preview(selected).People[actor].Gold + " obols"), "Local journey displayed another actor's budget");
                    var accepted = session.Game.Journal.Count; commit.EmitSignal(BaseButton.SignalName.Pressed);
                    Require(session.Game.Journal.Count == accepted + 1 && session.Game.Journal.Last().Actor == actor, "Local commit did not spend exactly its own turn");
                }
                else next.EmitSignal(BaseButton.SignalName.Pressed);
                await Frame();
            }
            Require(Fingerprint(session.Game) == Fingerprint(Agents.Finish(new Game(seed), session.Policies)), "Changing local seats changed policy-fixture rules/results");
            Require(session.Game.Result.Winners.All(i => objective.Text.Contains(session.Game.People[i].Name)) && !begin.Visible && commit.Disabled && next.Disabled,
                "Local result omitted actual winner or left a spending control enabled");
            Require(Fingerprint(BoardJournal.Load(session.SavePath).Game) == Fingerprint(session.Game), "Finished local match does not replay");
        }
        await Capture("local-result");

        // Scripted choices without suggestions: everyone Works, so all 80 turns
        // reach the real deadline rather than secretly substituting suggestions.
        session.New(0, humanSeats: [0, 1, 2, 3]); ResetSelection(); Refresh();
        while (session.Game.Result == null)
        {
            begin.EmitSignal(BaseButton.SignalName.Pressed);
            work = new(session.Game.People[session.Game.Current].Position, ActionKind.Work);
            map.Venues[work.Destination].EmitSignal(BaseButton.SignalName.Pressed); planButtons[work].EmitSignal(BaseButton.SignalName.Pressed);
            commit.EmitSignal(BaseButton.SignalName.Pressed); await Frame();
        }
        Require(session.Game.Journal.Count == 80 && session.Game.Result.Reason.StartsWith("fair closed") && session.Game.Journal.All(t => t.Intent.Action == ActionKind.Work), "Four-local direct choices failed to reach the actual deadline");
        await Capture("local-deadline");
        var gate = new Game(0, new Rules(StartingGold: 30)); Intent? claim;
        while ((claim = gate.Legal().FirstOrDefault(i => i.Action == ActionKind.Claim)) == null && gate.Result == null)
            gate.Apply(Agents.Choose(gate, "collector"), out _);
        Require(claim != null, "Gate forecast fixture never reached a legal claim");
        BoardJournal.Save(gate, session.Policies, [0, 1, 2, 3], session.SavePath);
        Require(session.Load(), "Legal Gate fixture failed replay"); session.BeginTurn();
        forecast = session.Forecast(claim!);
        Require(forecast.After.Result?.Winners.Contains(gate.Current) == true && forecast.Replies.Length == 0 && forecast.After.Journal.Count == gate.Journal.Count + 1,
            "Gate forecast executed a reply after the ending");
        GD.Print(JsonSerializer.Serialize(new { local_seats = "pass", all_nonempty_seat_sets = 15, direct_four_local_deadline = true,
            next_human_forecast_boundary = true, native_envelope_and_legacy_replay = true, implementing_agent_input = true }, Journal.Json));
    }
}
