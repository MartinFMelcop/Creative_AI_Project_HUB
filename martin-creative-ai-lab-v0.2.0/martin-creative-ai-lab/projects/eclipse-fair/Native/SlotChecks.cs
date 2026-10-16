using Eclipse.Core;
using Eclipse.Cli;

namespace Eclipse.Board;

public partial class Main
{
    private void VerifySlots()
    {
        var directory = Path.Combine(Path.GetDirectoryName(session.SavePath)!, "slot-checks-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(directory);
        try
        {
            var path = Path.Combine(directory, "match.json");
            var slots = new BoardSlots(path);
            Require(slots.HasCurrent, "An empty initial slot incorrectly blocked a fresh fair");
            Require(slots.PathFor(1) == path && slots.PathFor(2) == Path.Combine(directory, "match.slot2.json") &&
                slots.PathFor(3) == Path.Combine(directory, "match.slot3.json"), "Slot paths changed the legacy file or collided");
            Require(slots.Inspect().All(s => s.Status == BoardSlotStatus.Empty && !s.IsOccupied) && !Directory.GetFiles(directory).Any(),
                "Inspecting empty slots created files or reported an unavailable save");
            Require(slots.TryNew(1, 0, strategic: false, humanSeats: [0, 2]) && !slots.Current.HasUnsavedChanges,
                "Starting a fair did not immediately save its validated configuration");
            Require(slots.Current.BeginTurn() && slots.Current.Act(new(slots.Current.Game.People[0].Position, ActionKind.Work)) && slots.Current.Rival(),
                "The first saved multi-local fair could not advance to its next handoff");
            var a = Fingerprint(slots.Current.Game); var aBytes = File.ReadAllBytes(path);
            var summary = slots.Inspect()[0];
            Require(summary.Status == BoardSlotStatus.Ready && summary.Seed == 0 && summary.Round == slots.Current.Game.Round &&
                summary.AcceptedTurns == 2 && summary.LocalPlayers.SequenceEqual(new[] { "Vaelis", "Nira" }) && summary.NextParticipant == "Nira" && summary.Winners.Length == 0,
                "The slot summary did not derive actual local controls and next participant");
            Require(File.ReadAllBytes(path).SequenceEqual(aBytes) && Fingerprint(slots.Current.Game) == a,
                "Inspecting slots changed saved bytes or live state");

            Require(slots.TryNew(2, 3, humanSeats: [3]) && slots.Current.Act(new(slots.Current.Game.People[3].Position, ActionKind.Work)),
                "A second fair could not retain independent local controls and progress");
            var b = Fingerprint(slots.Current.Game); var bBytes = File.ReadAllBytes(slots.PathFor(2));
            Require(slots.TryNew(3, 7, strategic: false, humanSeats: [1, 3]), "A third fair could not be created");
            var cBytes = File.ReadAllBytes(slots.PathFor(3));
            Require(slots.Inspect().All(s => s.Status == BoardSlotStatus.Ready), "All three independently saved slots were not discoverable");
            Require(slots.TryLoad(1) && Fingerprint(slots.Current.Game) == a && slots.Current.HumanSeats.SequenceEqual(new[] { 0, 2 }) &&
                slots.Current.AwaitingPlayer && slots.Current.Policies[1] == "keeper", "Switching B to A lost its exact turn, handoff or profiles");
            var reopened = new BoardSlots(path);
            Require(!reopened.HasCurrent && reopened.TryLoad(2) && reopened.HasCurrent && Fingerprint(reopened.Current.Game) == b && reopened.Current.HumanSeats.SequenceEqual(new[] { 3 }),
                "Restarting lost the second fair's accepted history or seats");
            Require(reopened.TryLoad(3) && reopened.Current.Game.Seed == 7 && reopened.Current.HumanSeats.SequenceEqual(new[] { 1, 3 }),
                "Restarting could not resume the third fair");
            Require(File.ReadAllBytes(path).SequenceEqual(aBytes) && File.ReadAllBytes(slots.PathFor(2)).SequenceEqual(bBytes) &&
                File.ReadAllBytes(slots.PathFor(3)).SequenceEqual(cBytes), "Switching or restarting rewrote another fair");

            var live = slots.Current;
            Require(!slots.TryNew(2, 9) && ReferenceEquals(slots.Current, live) && File.ReadAllBytes(slots.PathFor(2)).SequenceEqual(bBytes),
                "An occupied slot was replaced without explicit confirmation");
            Require(!slots.TryNew(2, -1, replace: true) && !slots.TryNew(2, 9, humanSeats: [], replace: true) &&
                File.ReadAllBytes(slots.PathFor(2)).SequenceEqual(bBytes), "Invalid new-fair settings overwrote an existing slot");
            Require(!slots.TryLoad(0) && !slots.TryNew(4, 3) && ReferenceEquals(slots.Current, live), "An invalid slot changed the active fair");
            File.WriteAllText(slots.PathFor(2), "{\"boardSchema\":99}");
            var invalid = File.ReadAllBytes(slots.PathFor(2));
            Require(slots.Inspect()[1] is { Status: BoardSlotStatus.Unavailable, IsOccupied: true, Seed: null } &&
                !slots.TryLoad(2) && ReferenceEquals(slots.Current, live) && Fingerprint(slots.Current.Game) == a,
                "An invalid saved slot replaced live play or exposed unvalidated summary data");
            Require(!slots.TryNew(2, 4) && File.ReadAllBytes(slots.PathFor(2)).SequenceEqual(invalid),
                "An invalid occupied slot did not require replacement confirmation");
            Require(slots.TryNew(2, 4, humanSeats: [0, 3], replace: true) && slots.CurrentSlot == 2 &&
                slots.Inspect()[1].Seed == 4 && File.ReadAllBytes(path).SequenceEqual(aBytes) && File.ReadAllBytes(slots.PathFor(3)).SequenceEqual(cBytes),
                "Confirmed replacement failed or altered other slots");

            File.Delete(slots.PathFor(3)); Directory.CreateDirectory(slots.PathFor(3));
            var beforeBlocked = slots.Current;
            Require(slots.Inspect()[2] is { Status: BoardSlotStatus.Unavailable, IsOccupied: true } &&
                !slots.TryLoad(3) && !slots.TryNew(3, 5, replace: true) && ReferenceEquals(slots.Current, beforeBlocked) && slots.CurrentSlot == 2,
                "A directory was treated as empty or a failed candidate write replaced the active fair");
            Directory.Delete(slots.PathFor(3)); File.WriteAllBytes(slots.PathFor(3), cBytes);

            var currentPath = slots.Current.SavePath;
            File.Delete(currentPath); Directory.CreateDirectory(currentPath);
            Require(!slots.Current.Save() && slots.Current.HasUnsavedChanges, "A failed explicit save marked the active fair as safely saved");
            Require(slots.Current.BeginTurn() && slots.Current.Act(new(slots.Current.Game.People[0].Position, ActionKind.Work)) && slots.Current.HasUnsavedChanges,
                "An accepted action with a failed autosave was lost or marked saved");
            var dirty = Fingerprint(slots.Current.Game);
            Require(!slots.TryLoad(1) && !slots.TryNew(3, 12, replace: true) && ReferenceEquals(slots.Current, beforeBlocked) &&
                Fingerprint(slots.Current.Game) == dirty && slots.Current.HasUnsavedChanges && File.ReadAllBytes(path).SequenceEqual(aBytes) &&
                File.ReadAllBytes(slots.PathFor(3)).SequenceEqual(cBytes), "Switching silently discarded progress after a failed autosave");
            Directory.Delete(currentPath);
            Require(slots.TryLoad(2) && Fingerprint(slots.Current.Game) == dirty && !slots.Current.HasUnsavedChanges &&
                Fingerprint(BoardJournal.Load(currentPath).Game) == dirty,
                "Same-slot recovery loaded an old snapshot instead of preserving newly saved progress");
            Require(slots.TryLoad(1) && Fingerprint(slots.Current.Game) == a, "Recovery prevented an independent fair from resuming");

            var recovery = new BoardSlots(Path.Combine(directory, "recovery.json"));
            recovery.Current.New(8, humanSeats: [0, 2]); var recovered = Fingerprint(recovery.Current.Game);
            Require(recovery.Current.HasUnsavedChanges && !recovery.TryNew(1, 9) && !recovery.Current.HasUnsavedChanges &&
                Fingerprint(recovery.Current.Game) == recovered && Fingerprint(BoardJournal.Load(recovery.PathFor(1)).Game) == recovered,
                "Saving active progress into an empty slot let a new fair overwrite it without confirmation");

            var unavailablePath = Path.Combine(directory, "invalid-first.json");
            File.WriteAllText(unavailablePath, "{\"boardSchema\":99}");
            var unavailableBytes = File.ReadAllBytes(unavailablePath); var unavailable = new BoardSlots(unavailablePath);
            Require(!unavailable.HasCurrent && !unavailable.TryLoad(1) && !unavailable.HasCurrent &&
                unavailable.TryNew(2, 12) && unavailable.HasCurrent && unavailable.CurrentSlot == 2 &&
                File.ReadAllBytes(unavailablePath).SequenceEqual(unavailableBytes),
                "An invalid startup save opened a phantom fair or was overwritten when creating another slot");
            var directoryPath = Path.Combine(directory, "directory-first.json"); Directory.CreateDirectory(directoryPath);
            var directoryFirst = new BoardSlots(directoryPath);
            Require(!directoryFirst.HasCurrent && !directoryFirst.TryLoad(1) && !directoryFirst.HasCurrent &&
                directoryFirst.TryNew(2, 13) && directoryFirst.HasCurrent && Directory.Exists(directoryPath),
                "A directory at startup opened a phantom fair or prevented another independent slot");

            var extensionlessPath = Path.Combine(directory, "fair"); var extensionless = new BoardSlots(extensionlessPath);
            Require(extensionless.PathFor(1) == extensionlessPath && extensionless.PathFor(2) == extensionlessPath + ".slot2.json" &&
                extensionless.PathFor(3) == extensionlessPath + ".slot3.json", "Extensionless save paths changed slot one or lacked distinct added filenames");
            var exports = new List<string>();
            for (var slot = 1; slot <= 3; slot++)
            {
                Require(extensionless.TryNew(slot, slot + 20) && extensionless.Current.ExportReplay(), "An extensionless slot could not save and export");
                exports.Add(extensionless.Current.ReplayPath);
            }
            Require(exports.Distinct().Count() == 3 && exports.All(File.Exists) &&
                exports.Select(p => Journal.Load(p).Game.Seed).SequenceEqual(new[] { 21, 22, 23 }),
                "Replay exports from extensionless slots collided or replaced another fair's replay");

            Require(slots.Current.ExportReplay(), "The first slot's economy replay could not be exported");
            var replayA = slots.Current.ReplayPath; var replayABytes = File.ReadAllBytes(replayA);
            Require(slots.TryLoad(2) && slots.Current.ExportReplay() && slots.Current.ReplayPath != replayA &&
                File.ReadAllBytes(replayA).SequenceEqual(replayABytes) && Fingerprint(Journal.Load(slots.Current.ReplayPath).Game) == dirty,
                "Economy replay exports collided across slots or lost accepted history");

            Journal.Save(new Game(6), ["collector", "keeper", "opportunist", "collector"], path);
            var legacy = new BoardSlots(path);
            Require(legacy.TryLoad(1) && legacy.Current.Game.Seed == 6 && legacy.Current.HumanSeats.SequenceEqual(new[] { 0 }) &&
                legacy.Current.Policies[1] == "keeper" && legacy.Inspect()[0].LocalPlayers.SequenceEqual(new[] { "Vaelis" }),
                "The existing plain legacy journal stopped loading as slot one");
            Require(legacy.TryNew(3, 2, humanSeats: [0, 1, 2, 3], replace: true), "The finished-summary fixture could not start");
            while (legacy.Current.Game.Result == null)
            {
                legacy.Current.BeginTurn(); var actor = legacy.Current.Game.Current;
                Require(legacy.Current.Act(new(legacy.Current.Game.People[actor].Position, ActionKind.Work)), "The saved deadline fixture rejected legal local work");
            }
            var finished = legacy.Inspect()[2];
            var result = legacy.Current.Game.Result!;
            Require(finished.NextParticipant == null && finished.Winners.SequenceEqual(result.Winners.Select(i => legacy.Current.Game.People[i].Name)) &&
                finished.Detail.Contains("Finished:") && finished.AcceptedTurns == 80, "The finished-slot summary invented a next turn or lost winners");
        }
        finally { Directory.Delete(directory, true); }
    }
}
