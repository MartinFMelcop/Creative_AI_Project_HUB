using Godot;
using Eclipse.Core;
using Eclipse.Cli;
using System.Text.Json;

namespace Eclipse.Board;

public partial class Main
{
    private int assertions;
    private void Require(bool condition, string message)
    {
        assertions++; if (!condition) throw new InvalidOperationException(message);
    }
    private static string Fingerprint(Game game) => JsonSerializer.Serialize(new { game.Round, game.Current, game.People, game.Ledger, game.Result,
        Actions = game.Journal.Select(e => e.Intent) }, Journal.Json);
    private async Task Frame() => await ToSignal(GetTree(), SceneTree.SignalName.ProcessFrame);
    private async Task Capture(string name)
    {
        // Allow native container layout and the render thread to settle before readback.
        for (var i = 0; i < 4; i++) await Frame();
        Require(log.GlobalPosition.Y + log.Size.Y <= Size.Y, "Native layout clips the turn journal");
        if (captureDirectory == null || DisplayServer.GetName() == "headless") return;
        Directory.CreateDirectory(captureDirectory); await ToSignal(RenderingServer.Singleton, RenderingServer.SignalName.FramePostDraw);
        var error = GetViewport().GetTexture().GetImage().SavePng(Path.Combine(captureDirectory, name + ".png"));
        Require(error == Error.Ok, "Could not capture the actual native viewport");
    }
    private async Task Verify()
    {
        try
        {
            await Frame(); await Capture("opening");
            // Activate an actual focused venue control through the engine input path.
            map.Venues[3].GrabFocus();
            Input.ParseInputEvent(new InputEventKey { Keycode = Key.Enter, Pressed = true }); await Frame();
            Input.ParseInputEvent(new InputEventKey { Keycode = Key.Enter, Pressed = false }); await Frame();
            Require(destination == 3 && session.Game.Journal.Count == 0, "Keyboard venue inspection must not spend a turn");
            while (session.Game.Current != 0) { next.EmitSignal(BaseButton.SignalName.Pressed); await Frame(); }
            var untouched = Fingerprint(session.Game);
            foreach (var intent in session.Game.Legal())
            {
                map.Venues[intent.Destination].EmitSignal(BaseButton.SignalName.Pressed);
                Require(planButtons.ContainsKey(intent), "UI omitted a legal transaction");
                planButtons[intent].EmitSignal(BaseButton.SignalName.Pressed);
                Require(selected == intent && !commit.Disabled, "Plan selection failed");
                Require(Fingerprint(session.Game) == untouched, "Preview changed the live match");
                Require(preview.Text.Contains(session.Preview(intent).People[0].Gold + " obols"), "Preview omitted actual budget");
            }
            hint.EmitSignal(BaseButton.SignalName.Pressed); await Capture("plan");
            var suggestedForecast = session.Forecast(selected!);
            var workForecast = session.Forecast(new Intent(session.Game.People[0].Position, ActionKind.Work));
            var beforeResponse = Fingerprint(session.Game);
            response.EmitSignal(BaseButton.SignalName.Pressed);
            var openingResponse = GetChildren().OfType<AcceptDialog>().Single();
            Require(Fingerprint(session.Game) == beforeResponse, "Comparing the suggested response spent a turn");
            await Capture("suggested-response"); openingResponse.EmitSignal(AcceptDialog.SignalName.Confirmed); await Frame();
            Require(!suggestedForecast.Replies.Select(r => r.Intent).SequenceEqual(workForecast.Replies.Select(r => r.Intent)), "Suggested protection did not change the opening rival responses");
            GD.Print(JsonSerializer.Serialize(new { opening_response = new { seed = 1, suggested = selected,
                suggested_replies = suggestedForecast.Replies.Select(r => r.Description), work_replies = workForecast.Replies.Select(r => r.Description) } }, Journal.Json));
            var humanCount = session.Game.Journal.Count;
            commit.EmitSignal(BaseButton.SignalName.Pressed);
            Require(session.Game.Journal.Count == humanCount + 1, "Confirmation did not accept exactly one turn");
            Require(session.Game.Current != 0, "Rivals should follow the first human turn");
            var saved = File.ReadAllText(session.SavePath); var saveState = Fingerprint(session.Game);
            await Capture("rivals");
            var accepted = session.Act(new Intent(0, ActionKind.Work));
            Require(!accepted && Fingerprint(session.Game) == saveState, "Human acted during a rival turn");
            next.EmitSignal(BaseButton.SignalName.Pressed);
            // Use the same saved file in both consumers, then restore it for UI loading.
            Require(Fingerprint(BoardJournal.Load(session.SavePath).Game) == Fingerprint(session.Game), "CLI-compatible journal diverged");
            File.WriteAllText(session.SavePath, saved); load.EmitSignal(BaseButton.SignalName.Pressed);
            Require(Fingerprint(session.Game) == saveState, "Resume changed the exact next turn");
            File.WriteAllText(session.SavePath, "{\"schema\":99}"); load.EmitSignal(BaseButton.SignalName.Pressed);
            Require(Fingerprint(session.Game) == saveState && notice.Text.Contains("rejected"), "Invalid load destroyed the current match");
            File.WriteAllText(session.SavePath, saved); load.EmitSignal(BaseButton.SignalName.Pressed);
            // A legal shared-location fixture exercises blocked theft, successful theft and protection through the UI.
            var fixture = new Game(0, new Rules(StartingGold: 30));
            Intent[] setup = [new(0,ActionKind.Work),new(1,ActionKind.Guard),new(3,ActionKind.Work),new(7,ActionKind.Work),
                new(0,ActionKind.Work),new(4,ActionKind.Work),new(0,ActionKind.Work)];
            foreach (var intent in setup) Require(fixture.Apply(intent, out _), "Invalid shared-location fixture");
            foreach (var intent in new Intent[] { new(0,ActionKind.Steal,1), new(0,ActionKind.Steal,3), new(0,ActionKind.Guard) })
            {
                Journal.Save(fixture, session.Policies, session.SavePath); load.EmitSignal(BaseButton.SignalName.Pressed);
                var expected = fixture.Fork(); Require(expected.Apply(intent, out _), "Fixture action unavailable");
                planButtons[intent].EmitSignal(BaseButton.SignalName.Pressed); commit.EmitSignal(BaseButton.SignalName.Pressed);
                Require(Fingerprint(session.Game) == Fingerprint(expected), "Theft/ward UI changed transaction effects");
                await Frame();
            }
            // Compare the actual response dialog with subsequently accepted rival turns.
            session.New(0); ResetSelection(); Refresh();
            var forecastIntent = new Intent(1, ActionKind.Work);
            map.Venues[1].EmitSignal(BaseButton.SignalName.Pressed); planButtons[forecastIntent].EmitSignal(BaseButton.SignalName.Pressed);
            var liveBeforeForecast = Fingerprint(session.Game); var forecast = session.Forecast(forecastIntent);
            response.EmitSignal(BaseButton.SignalName.Pressed);
            var forecastWindow = GetChildren().OfType<AcceptDialog>().Single();
            Require(forecastWindow.DialogText.Contains("Conditional forecast") && forecastWindow.DialogText.Contains("6 obols"), "Response dialog omitted actual replies");
            Require(Fingerprint(session.Game) == liveBeforeForecast && !automatic.ButtonPressed, "Response comparison advanced live play");
            await Capture("response"); forecastWindow.EmitSignal(AcceptDialog.SignalName.Confirmed); await Frame();
            commit.EmitSignal(BaseButton.SignalName.Pressed); await Capture("rival-plan");
            Require(session.Advice().Route.Length > 1 && actions.GetChildCount() >= 4, "Native rival plan omitted its route/purpose");
            while(session.Game.Result == null && session.Game.Current != 0) { next.EmitSignal(BaseButton.SignalName.Pressed); await Frame(); }
            Require(Fingerprint(session.Game) == Fingerprint(forecast.After), "Native rival turns diverged from the displayed forecast");
            NewDialog(); var newWindow = GetChildren().OfType<ConfirmationDialog>().Single();
            newWindow.FindChildren("*", "OptionButton", true, false).OfType<OptionButton>().Single().Select(1); newWindow.EmitSignal(ConfirmationDialog.SignalName.Confirmed); await Frame();
            Require(session.Policies.SequenceEqual(new[]{"collector","keeper","opportunist","collector"}), "Classic mode changed original profiles");
            session.Save(); var classicPolicies = session.Policies.ToArray(); session.New(4); load.EmitSignal(BaseButton.SignalName.Pressed);
            Require(session.Policies.SequenceEqual(classicPolicies), "Loading an old-policy save silently upgraded its rivals");
            var seen = new HashSet<ActionKind>();
            foreach (var seed in new[] { 0, 1, 2, 3, 4, 5, 6, 7, 18 })
            {
                session.New(seed); ResetSelection(); Refresh();
                while (session.Game.Result == null)
                {
                    if (session.Game.Current == 0)
                    {
                        hint.EmitSignal(BaseButton.SignalName.Pressed);
                        Require(selected != null && session.Game.Legal().Contains(selected), "Suggestion is not a legal human option");
                        seen.Add(selected!.Action); commit.EmitSignal(BaseButton.SignalName.Pressed);
                    }
                    else next.EmitSignal(BaseButton.SignalName.Pressed);
                    await Frame();
                }
                var expected = Agents.Finish(new Game(seed), session.Policies);
                Require(Fingerprint(session.Game) == Fingerprint(expected), "Native turns differ from the unchanged C# rules/agents");
                Require(commit.Disabled && next.Disabled && actions.GetChildCount() == 4, "End screen still allows turns or omits ranks");
                Require(Fingerprint(BoardJournal.Load(session.SavePath).Game) == Fingerprint(session.Game), "Finished save does not replay");
            }
            Require(seen.Contains(ActionKind.Buy) && seen.Contains(ActionKind.Rite) && seen.Contains(ActionKind.Claim), "Full journeys missed the objective loop");
            Require(actions.GetChild<Label>(0).Text.StartsWith("WINNER"), "Gate winner must be presented first");
            await Capture("result");
            // Income-only policies exercise a genuine deadline, distinct from Gate victory.
            Journal.Save(new Game(1), ["worker", "worker", "worker", "worker"], session.SavePath);
            load.EmitSignal(BaseButton.SignalName.Pressed);
            while (session.Game.Result == null)
            {
                if (session.Game.Current == 0)
                {
                    var plan = Agents.Choose(session.Game, "worker"); destination = plan.Destination; Refresh();
                    planButtons[plan].EmitSignal(BaseButton.SignalName.Pressed); commit.EmitSignal(BaseButton.SignalName.Pressed);
                }
                else next.EmitSignal(BaseButton.SignalName.Pressed);
                await Frame();
            }
            Require(session.Game.Result.Reason.StartsWith("fair closed") && session.Game.Journal.Count == 80, "Deadline match did not close at 20 rounds");
            await Capture("deadline");
            var failure = new BoardSession(Path.GetDirectoryName(session.SavePath)!, 0);
            Require(failure.Act(new Intent(failure.Game.People[0].Position, ActionKind.Work)), "Write failure rejected an accepted in-memory turn");
            Require(failure.Game.Journal.Count == 1 && failure.Notice.Contains("in memory"), "Write failure concealed recoverable progress");
            Require(!failure.Act(new Intent(99, ActionKind.Claim)), "Rival-period invalid input accepted");
            session.New(1); ResetSelection(); Refresh();
            verification = false; automatic.ButtonPressed = true;
            await ToSignal(GetTree().CreateTimer(1.15), SceneTreeTimer.SignalName.Timeout);
            automatic.ButtonPressed = false; verification = true;
            Require(session.Game.Journal.Count == 1, "Auto rivals did not execute exactly one paced turn");
            automatic.ButtonPressed = true; Notification((int)NotificationWMWindowFocusOut);
            Require(!automatic.ButtonPressed, "Window focus-out must stop automatic rival turns");
            var afterFocus = Fingerprint(session.Game); verification = false;
            await ToSignal(GetTree().CreateTimer(1.1), SceneTreeTimer.SignalName.Timeout); verification = true;
            Require(Fingerprint(session.Game) == afterFocus, "Auto rivals advanced after focus-out");
            await VerifyLocalSeats();
            GD.Print(JsonSerializer.Serialize(new { native_board = "pass", assertions, complete_gate_or_deadline_matches = 26, local_seat_sets = 15,
                source_rule_parity = true, journal_replay = true, keyboard_venue_input = true,
                strategic_profiles = true, conditional_forecast = true, classic_mode = true,
                auto_rival_clock = true, controlled_focus_out = true,
                rendered = DisplayServer.GetName() != "headless" }, Journal.Json));
            GetTree().Quit(0);
        }
        catch (Exception error) { GD.PushError(error.ToString()); GetTree().Quit(1); }
    }
}
