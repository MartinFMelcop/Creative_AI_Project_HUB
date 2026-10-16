using Godot;
using Eclipse.Core;
using System.Text.Json;

namespace Eclipse.Board;

public partial class Main
{
    private async Task KeyPress(Key key)
    {
        Input.ParseInputEvent(new InputEventKey { Keycode = key, Pressed = true }); await Frame();
        Input.ParseInputEvent(new InputEventKey { Keycode = key, Pressed = false }); await Frame();
    }
    private T DialogNamed<T>(string name) where T : Window => FindChildren("*", "Window", true, false).OfType<T>().Single(d => d.Name == name);
    private static T Named<T>(Node parent, string name) where T : Node => (T)parent.FindChild(name, true, false);
    private async Task VerifySlotOnly()
    {
        try { await Frame(); VerifySlots(); await VerifySlotInterface(); GD.Print($"SLOT_CHECKS_PASS assertions={assertions}"); GetTree().Quit(0); }
        catch (Exception error) { GD.PushError(error.ToString()); GetTree().Quit(1); }
    }
    private async Task VerifySlotInterface()
    {
        var original = saves;
        var directory = Path.Combine(Path.GetDirectoryName(session.SavePath)!, "slot-ui-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(directory);
        try
        {
            saves = new(Path.Combine(directory, "match.json"));
            Require(saves.TryNew(1, 0, strategic: false, humanSeats: [0, 2]), "UI fixture could not create Fair 1");
            session.BeginTurn(); session.Act(new(session.Game.People[0].Position, ActionKind.Work)); session.Rival();
            var a = Fingerprint(session.Game); var aBytes = File.ReadAllBytes(session.SavePath);
            ResetSelection(); Refresh();
            load.EmitSignal(BaseButton.SignalName.Pressed); await Frame();
            var chooser = DialogNamed<AcceptDialog>("SavedFairs");
            Require(!automatic.ButtonPressed && Named<Button>(chooser, "ContinueSlot2").Disabled && Named<Button>(chooser, "ContinueSlot3").Disabled,
                "Empty fairs could be resumed or opening saves left rivals running");
            var labels = chooser.FindChildren("*", "Label", true, false).OfType<Label>().Select(l => l.Text).ToArray();
            Require(labels.Any(t => t.Contains("Vaelis, Nira") && t.Contains("Next: Nira") && t.Contains("2 accepted turns")),
                "Saved fairs omitted the actual shared match summary");
            await Capture("saved-fairs");
            Require(chooser.Size.X <= Size.X && chooser.Size.Y <= Size.Y && Fingerprint(session.Game) == a && File.ReadAllBytes(saves.PathFor(1)).SequenceEqual(aBytes),
                $"Browsing fairs clipped the dialog {chooser.Size} / {Size} or changed play/saved data (live {Fingerprint(session.Game) == a}, bytes {File.ReadAllBytes(saves.PathFor(1)).SequenceEqual(aBytes)})");
            chooser.EmitSignal(AcceptDialog.SignalName.Canceled); await Frame();
            Require(Fingerprint(session.Game) == a, "Cancelling the save selector changed the fair");

            NewDialogForSlot(2); await Frame(); var setup = DialogNamed<ConfirmationDialog>("NewFair");
            var locals = setup.FindChildren("*", "CheckButton", true, false).OfType<CheckButton>().ToArray();
            foreach (var local in locals) local.ButtonPressed = false;
            Require(setup.GetOkButton().Disabled, "Slot configuration allowed zero local seats");
            locals[3].ButtonPressed = true;
            setup.FindChildren("*", "SpinBox", true, false).OfType<SpinBox>().Single().Value = 3;
            Named<OptionButton>(setup, "RivalProfiles").Select(1);
            Require(Named<OptionButton>(setup, "SlotChoice").Selected == 1 && setup.GetOkButton().Text == "Create fair", "New fair chose another slot or hid its empty state");
            await Capture("new-fair-slot");
            Require(setup.Size.X <= Size.X - 20 && setup.Size.Y <= Size.Y - 20, "New fair setup is outside the playable viewport");
            setup.EmitSignal(ConfirmationDialog.SignalName.Confirmed); await Frame();
            Require(saves.CurrentSlot == 2 && session.Game.Seed == 3 && session.HumanSeats.SequenceEqual(new[] { 3 }) &&
                session.Game.Journal.Count == 0 && !session.HasUnsavedChanges && File.Exists(saves.PathFor(2)) &&
                File.ReadAllBytes(saves.PathFor(1)).SequenceEqual(aBytes), "Creating Fair 2 overwrote Fair 1 or waited for a turn to save configuration");
            session.Act(new(session.Game.People[3].Position, ActionKind.Work)); var bBytes = File.ReadAllBytes(saves.PathFor(2));
            load.EmitSignal(BaseButton.SignalName.Pressed); await Frame(); chooser = DialogNamed<AcceptDialog>("SavedFairs");
            Named<Button>(chooser, "ContinueSlot1").GrabFocus(); await KeyPress(Key.Enter); await Frame();
            Require(saves.CurrentSlot == 1 && Fingerprint(session.Game) == a && session.AwaitingPlayer && begin.Visible && commit.Disabled && !automatic.ButtonPressed,
                "Keyboard Continue lost Fair 1's history, next local handoff or stopped-clock state");
            await Capture("resumed-fair");

            NewDialogForSlot(1); await Frame(); setup = DialogNamed<ConfirmationDialog>("NewFair");
            setup.EmitSignal(ConfirmationDialog.SignalName.Confirmed); await Frame();
            var replace = DialogNamed<ConfirmationDialog>("ReplaceFair");
            Require(replace.GetParent() == setup && replace.Visible && replace.Title.Contains("Fair 1") && replace.DialogText.Contains("Vaelis, Nira") && replace.DialogText.Contains("replaced immediately"),
                "Replacement omitted the exact destination and saved group");
            Require(Fingerprint(session.Game) == a && File.ReadAllBytes(saves.PathFor(1)).SequenceEqual(aBytes), "Opening replacement confirmation already replaced a fair");
            await Capture("replace-fair"); await KeyPress(Key.Escape); await Frame();
            Require(setup.Visible && !setup.FindChildren("ReplaceFair", "Window", true, false).Any(), "Escape did not return from replacement to its setup");
            setup.EmitSignal(ConfirmationDialog.SignalName.Canceled); await Frame();
            Require(Fingerprint(session.Game) == a && File.ReadAllBytes(saves.PathFor(1)).SequenceEqual(aBytes), "Cancelling replacement changed saved progress");

            NewDialogForSlot(2); await Frame(); setup = DialogNamed<ConfirmationDialog>("NewFair");
            setup.FindChildren("*", "SpinBox", true, false).OfType<SpinBox>().Single().Value = 8;
            setup.EmitSignal(ConfirmationDialog.SignalName.Confirmed); await Frame();
            replace = DialogNamed<ConfirmationDialog>("ReplaceFair"); replace.GetOkButton().GrabFocus(); await KeyPress(Key.Enter); await Frame();
            Require(saves.CurrentSlot == 2 && session.Game.Seed == 8 && File.ReadAllBytes(saves.PathFor(1)).SequenceEqual(aBytes),
                "Confirmed replacement changed another fair or did not create the chosen seed");
            Require(saves.TryLoad(1), "The replacement journey could not return to Fair 1"); ResetSelection(); Refresh();

            File.WriteAllText(saves.PathFor(2), "{\"boardSchema\":99}");
            load.EmitSignal(BaseButton.SignalName.Pressed); await Frame(); chooser = DialogNamed<AcceptDialog>("SavedFairs");
            Require(Named<Button>(chooser, "ContinueSlot2").Disabled && chooser.FindChildren("*", "Label", true, false).OfType<Label>().Any(l => l.Text.Contains("Unavailable")),
                "An invalid save appeared resumable or lost its failure explanation");
            chooser.EmitSignal(AcceptDialog.SignalName.Canceled); await Frame(); File.WriteAllBytes(saves.PathFor(2), bBytes);

            File.Delete(saves.PathFor(1)); Directory.CreateDirectory(saves.PathFor(1));
            session.BeginTurn(); session.Act(new(session.Game.People[session.Game.Current].Position, ActionKind.Work));
            var dirty = Fingerprint(session.Game); Refresh();
            load.EmitSignal(BaseButton.SignalName.Pressed); await Frame(); chooser = DialogNamed<AcceptDialog>("SavedFairs");
            Named<Button>(chooser, "ContinueSlot2").EmitSignal(BaseButton.SignalName.Pressed); await Frame();
            Require(saves.CurrentSlot == 1 && session.HasUnsavedChanges && Fingerprint(session.Game) == dirty && notice.Text.Contains("unsaved progress") &&
                File.ReadAllBytes(saves.PathFor(2)).SequenceEqual(bBytes), "Failed autosave allowed the UI to discard memory while switching");
            await Capture("save-failure-kept"); Directory.Delete(saves.PathFor(1));
            Named<Button>(chooser, "ContinueSlot2").EmitSignal(BaseButton.SignalName.Pressed); await Frame();
            Require(saves.CurrentSlot == 2 && Fingerprint(BoardJournal.Load(saves.PathFor(1)).Game) == dirty && !session.HasUnsavedChanges,
                "Retrying Continue after recovery did not preserve accepted turns before switching");
            var badPath = Path.Combine(directory, "bad-startup.json"); File.WriteAllText(badPath, "{\"boardSchema\":99}");
            var badBytes = File.ReadAllBytes(badPath); saves = new(badPath);
            Require(!saves.TryLoad(1), "Invalid startup save was accepted"); ResetSelection(); Refresh();
            Require(!saves.HasCurrent && commit.Disabled && next.Disabled && save.Disabled && replay.Disabled && !begin.Visible &&
                notice.Text.Contains("rejected"), "Invalid startup left fallback gameplay/save enabled or hid its rejection");
            RivalTurn(); CommitTurn();
            Require(File.ReadAllBytes(badPath).SequenceEqual(badBytes), "Fallback input overwrote the unavailable startup save");
            SavedFairsDialog(); await Frame(); chooser = DialogNamed<AcceptDialog>("SavedFairs"); await Capture("unavailable-startup");
            Named<Button>(chooser, "NewSlot2").EmitSignal(BaseButton.SignalName.Pressed); await Frame();
            setup = DialogNamed<ConfirmationDialog>("NewFair"); setup.EmitSignal(ConfirmationDialog.SignalName.Confirmed); await Frame();
            Require(saves.HasCurrent && saves.CurrentSlot == 2 && File.ReadAllBytes(badPath).SequenceEqual(badBytes),
                "Recovery in an empty slot replaced the unavailable startup save");
            GD.Print(JsonSerializer.Serialize(new { fair_slots = "pass", slots = 3, keyboard_continue = true,
                cancelled_replacement_kept = true, blocked_save_kept = true, validated_summaries = true,
                boundary = "Engine input and virtual display; not independent shared-device usability." }));
        }
        finally
        {
            saves = original; ResetSelection(); Refresh();
            Directory.Delete(directory, true);
        }
    }
}
