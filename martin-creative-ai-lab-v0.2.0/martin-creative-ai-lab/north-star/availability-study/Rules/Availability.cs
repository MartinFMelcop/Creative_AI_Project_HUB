using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;

namespace NorthStar.Availability
{
    public enum Authority { Present, Committed, Away, Unaccounted }

    /// <summary>Eligibility is a literal advertised mask; it never proves observed presence.</summary>
    public static class Schedule
    {
        public static bool Allows(int phase, IEnumerable<int> advertised)
        {
            if (phase < 0 || phase > 4) throw new ArgumentOutOfRangeException(nameof(phase));
            if (advertised == null) throw new ArgumentNullException(nameof(advertised));
            var seen = new HashSet<int>();
            foreach (int value in advertised)
                if (value < 0 || value > 4 || !seen.Add(value)) throw new ArgumentException("Mask requires unique phases0–4.", nameof(advertised));
            if (seen.Count == 0) throw new ArgumentException("Mask must advertise at least one phase.", nameof(advertised));
            return seen.Contains(phase);
        }

        public static bool Available(bool scheduled, Authority authority)
        {
            if (!Enum.IsDefined(typeof(Authority), authority)) throw new ArgumentOutOfRangeException(nameof(authority));
            return scheduled && authority == Authority.Present;
        }
    }

    /// <summary>Immutable snapshot of one original, session-only service opportunity.</summary>
    public sealed class View
    {
        public int Phase { get; }
        public int Remaining { get; }
        public IReadOnlyList<int> AdvertisedPhases { get; }
        public bool Advertised { get; }
        public string Authority { get; }
        public bool Available { get; }
        public bool Reserved { get; }
        public bool WorkReady { get; }
        public bool Collected { get; }
        public string Outcome { get; }
        public int Durability { get; }
        public int PotterWorkRemaining { get; }
        public string Last { get; }
        public IReadOnlyList<string> Commands { get; }

        internal View(Session owner, IReadOnlyList<string> commands)
        {
            Phase = owner.Phase; Remaining = owner.Remaining;
            AdvertisedPhases = owner.AdvertisedPhases; Advertised = owner.Advertised;
            Authority = owner.Presence.ToString().ToLowerInvariant(); Available = owner.Available;
            Reserved = owner.Reserved; WorkReady = owner.WorkReady; Collected = owner.Collected;
            Outcome = owner.Outcome; Durability = owner.Durability; PotterWorkRemaining = owner.PotterWorkRemaining;
            Last = owner.Last; Commands = commands;
        }
    }

    /// <summary>No wall clock, host timer or read mutates this original experimental service owner.</summary>
    public sealed class Session
    {
        private readonly IReadOnlyList<int> advertised = new ReadOnlyCollection<int>(new[] { 0, 1, 4 });
        private static readonly string[] vocabulary = { "promise", "reserve", "shape", "collect", "leave", "withdraw", "alone", "wait" };
        public int Phase { get; private set; }
        public int Remaining => 4 - Phase;
        public IReadOnlyList<int> AdvertisedPhases => advertised;
        public bool Advertised => Schedule.Allows(Phase, advertised);
        public Authority Presence { get; private set; } = Authority.Present;
        public bool Available => Schedule.Available(Advertised, Presence);
        public bool Reserved { get; private set; }
        public bool WorkReady { get; private set; }
        public bool Collected { get; private set; }
        public string Outcome { get; private set; } = "unfinished";
        public int Durability { get; private set; }
        public int PotterWorkRemaining => 2;
        public string Last { get; private set; } = "The kiln window: Mara has two of her own pots waiting. Your cracked water jar needs a repair. Her board advertises phases0,1,4; she is observed here now. A promise reserves nobody. A fired repair diverts her work; a temporary patch can be made alone.";
        private bool Finished => Outcome != "unfinished";

        private bool Can(string command)
        {
            if (Finished) return false;
            switch (command)
            {
                case "promise": return true;
                case "reserve": return !Reserved && !WorkReady && Available && Remaining >= 3;
                case "shape": return Reserved && !WorkReady && Presence == Authority.Committed && Remaining >= 2;
                case "collect": return Reserved && WorkReady && Presence == Authority.Committed;
                case "withdraw": return Reserved && Presence == Authority.Committed;
                case "leave": return Presence == Authority.Present || Presence == Authority.Committed;
                case "alone": return !Reserved && Remaining >= 2;
                case "wait": return Remaining >= 1;
                default: return false;
            }
        }

        public bool Execute(string command)
        {
            if (command == null || command.Length > 64) { Last = "Unknown command; no time, work or authority changed."; return false; }
            command = command.Trim();
            if (!Can(command)) { Last = "Action refused against the actual phase, commitment and work. No time, repair or NPC state changed."; return false; }
            switch (command)
            {
                case "promise":
                    Last = "You say you might ask for a repair. Mara keeps her own pots. No time, reservation, repair or delivery is recorded.";
                    break;
                case "reserve":
                    Reserved = true; Presence = Authority.Committed; Phase++;
                    Last = "Mara accepts this repair and sets her own two pots aside. One phase is spent agreeing and preparing. Her posted window is no longer a free service slot; the repair has not been made or handed over.";
                    break;
                case "shape":
                    WorkReady = true; Phase += 2;
                    Last = "You hold the jar while Mara shapes and fires the repair, spending two phases. The repaired jar remains in her working yard: ready is not collected. Her own two pots still wait.";
                    break;
                case "collect":
                    Collected = true; Reserved = false; Presence = Authority.Present; Outcome = "fired"; Durability = 3;
                    Last = "Mara actually hands over the fired repair. The jar has three durability units in this experiment. Her two pots are still unfinished. This observed handoff frees her commitment; the posted phase mask alone did not return her.";
                    break;
                case "withdraw":
                    Reserved = false; Presence = Authority.Away;
                    Last = "You withdraw the service. Mara takes her own work away from the counter. Spent phases are not refunded; no jar has been collected. A later advertised phase cannot prove her return.";
                    break;
                case "leave":
                    Presence = Reserved ? Authority.Unaccounted : Authority.Away;
                    Last = Reserved ? "You leave the working yard with a reservation outstanding. Mara's next location is unaccounted for; the jar is not handed over. Advancing to a posted phase will not manufacture her return." : "You leave the counter. Mara is no longer observed here. The board remains an advertisement, not proof that she has returned.";
                    break;
                case "alone":
                    Phase += 2; Outcome = "patched"; Durability = 1;
                    Last = "You spend two phases making your own temporary patch. The jar has one durability unit in this experiment. Mara was not borrowed and no fired service or handoff occurred; her own two pots remain her work.";
                    break;
                case "wait":
                    Phase++;
                    Last = "One explicit phase passes. The board may change eligibility; no presence, repair, handoff or return is inferred from it.";
                    break;
            }
            return true;
        }

        public View Snapshot()
        {
            var commands = new List<string>();
            foreach (string command in vocabulary) if (Can(command)) commands.Add(command);
            return new View(this, new ReadOnlyCollection<string>(commands));
        }
    }
}
