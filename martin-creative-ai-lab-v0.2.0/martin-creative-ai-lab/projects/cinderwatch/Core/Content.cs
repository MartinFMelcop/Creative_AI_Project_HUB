namespace Cinder.Core;

public static class Content
{
    public static readonly string[] Places = ["Loading Yard", "Pressure Gallery", "Furnace Governor"];
    public const string Intro = "The furnace was cold when the night crew went in. Now the pressure doors have closed behind them.\n\nRook needs the Governor's valve wheel to shut the steam line. Vale knows the service galleries; Neri carries four treatment kits. The yard sentries are running on an obsolete evacuation order: nothing is allowed through.\n\nThree encounters. Injuries and supplies carry forward. Choose a salvage stop between them. Every enemy announces its next action before the round begins.";
    public static readonly string[] Arrival = [
        "Vale finds the loading gate welded shut. 'Through the service hatch. Rook, keep that hound off Neri.'",
        "The gallery lifts under the crew's feet. Neri points at the patch drone. 'It will undo our work if we leave it behind that shield.'",
        "Rook catches the wheel with a gloved hand. The Governor turns to face them. Vale pulls the release cable; the wheel stays locked. 'We have to stop the housing first.'"
    ];
    public static readonly string[] After = [
        "The hatch opens onto a coolant locker. The crew has room for the canister or two charged cells, not both. The pressure gallery is still ahead.",
        "The gallery door opens. A wash basin holds enough clean water for the worst burns. There is enough scrap to reinforce Rook's cover or sharpen everyone's tools. The final housing is through the door.",
        "The housing stops. Rook lifts the valve wheel out of its socket and seats it on the steam line. Vale holds the release cable while Neri opens the pressure door.\n\nThe crew comes out one at a time. The last worker cannot stand; Rook leaves the wheel closed and takes the other end of the stretcher. No one waits for a second shift to finish the job."
    ];
    public static string CampLabel(string c) => c switch
    {
        "coolant"=>"Carry coolant · +12 HP each; revive down allies at half HP",
        "sparks"=>"Salvage cells · +2 sparks (max 5), +6 HP; revive at 6 HP",
        "plates"=>"Reinforce cover · +3 Rook shield, +6 HP; revive at 6 HP",
        "edge"=>"Sharpen tools · +2 damage to all attacks, +6 HP; revive at 6 HP",
        _=>throw new ArgumentException("Unknown salvage choice")
    };
    public static string CampResponse(string c) => c switch
    {
        "coolant"=>"Neri wets the dressings before passing the canister back. Vale leaves the charged cells in the locker.",
        "sparks"=>"Vale pockets the two charged cells. Neri washes the worst cuts with the water left in her flask.",
        "plates"=>"Rook bolts the scrap across the shield's split rim. 'Stay where I can reach you.'",
        "edge"=>"Vale files the tools against a broken grate. Rook tests the blade, then hands Neri her bolt driver.",
        _=>throw new ArgumentException("Unknown salvage choice")
    };
    public static string Ending(Game game)
    {
        var standing=game.Units.Where(u=>u.Hero&&u.Alive).OrderBy(u=>u.Id).ToArray();
        if(game.Phase!=Phase.Victory || standing.Length==0)throw new InvalidOperationException("Finish the rescue first.");
        var hand=standing[0].Name;
        var down=game.Units.Where(u=>u.Hero&&!u.Alive).Select(u=>u.Name).ToArray();
        return $"The housing stops. {hand} lifts the valve wheel out of its socket and seats it on the steam line. A worker reaches through the pressure door to hold the release cable. The last latch opens.\n\n"+
            (down.Length>0?$"{string.Join(" and ",down)} cannot stand. The night crew helps them clear the housing before bringing the stretcher through.\n\n":"Neri checks the night crew as they come through the door. Vale counts them against the shift card.\n\n")+
            $"The last worker needs a stretcher. {hand} takes one end; the crew takes the other. The wheel stays closed. No one waits for a second shift to finish the job.";
    }
    public const string Rules = "ONE action per hero turn. Initiative: speed, then stable ID. Enemy actions are locked at round start.\n\nFront enemies screen rear enemies from Strike. Vale's Pierce and Neri's Bolt reach either row. A front hero intercepts Bite aimed at a rear ally. Rivet ignores rows. No front hero means no screen.\n\nBrace absorbs 7 damage. Cover gives Rook 6 shield and redirects the next direct hit on that ally. Shields/Cover expire at the owner's next turn; Gout hits everyone and bypasses Cover.\n\nPin spends one shared spark, deals 4 (before armour) and cancels an enemy's UPCOMING action this round. A charge skipped by Pin still leads to Gout next round. Mend spends one shared kit: heal 12 and remove scorch. Down allies cannot act or receive treatment in combat.\n\nGovernor: odd rounds charge; even rounds Gout for 12 each + 2 scorch damage at the start of the next two hero turns. Each fight has a 12-round steam deadline. No undo. Salvage is a one-time choice.";
}
