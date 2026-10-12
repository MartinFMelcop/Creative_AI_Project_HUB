using Godot;
using Eclipse.Core;

namespace Eclipse.Board;

public partial class MapView : Control
{
    public readonly Button[] Venues = new Button[8];
    public Game? Match;
    public int Selected;
    public Intent? Plan;
    public event Action<int>? VenueSelected;
    private static readonly Vector2[] Places = [new(.23f,.19f),new(.5f,.10f),new(.77f,.19f),new(.86f,.5f),
        new(.77f,.81f),new(.5f,.90f),new(.23f,.81f),new(.14f,.5f)];
    private static readonly string[] Names = ["ECLIPSE MARKET","FOUNDRY","CHAPEL","WHARF","VEIL BAZAAR","ORCHARD","RAVEN SPIRE","ECLIPSE GATE"];
    public override void _Ready()
    {
        CustomMinimumSize = new(610, 325); SizeFlagsHorizontal = SizeFlags.ExpandFill; SizeFlagsVertical = SizeFlags.ExpandFill;
        for (var i = 0; i < 8; i++)
        {
            var id = i;
            var button = new Button { Name = "Venue" + i, Size = new(142, 64), Text = Names[i], MouseDefaultCursorShape = CursorShape.PointingHand };
            button.AddThemeFontSizeOverride("font_size", 12);
            button.Pressed += () => VenueSelected?.Invoke(id); AddChild(button); Venues[i] = button;
        }
        Resized += Refresh; Refresh();
    }
    public void Refresh()
    {
        if (Match == null || Venues[0] == null) return;
        var human = Match.People[0];
        for (var i = 0; i < 8; i++)
        {
            var b = Venues[i]; b.Position = Places[i] * Size - b.Size / 2;
            var residents = string.Join(" · ", Match.People.Where(p => p.Position == i).Select(p => p.Name));
            b.Text = Names[i] + "\n" + (residents.Length > 0 ? residents : "Work: " + Match.Wage(i, human) + " obols");
            b.TooltipText = $"{Game.Board[i].Name}\nYour work income: {Match.Wage(i, human)} now / {Match.Wage(i, human, Match.Round + 1)} next round\n" + residents;
            var reachable = i == human.Position || Game.Board[human.Position].Neighbors.Contains(i);
            b.Modulate = new Color(1, 1, 1, reachable ? 1 : .6f);
            b.AddThemeStyleboxOverride("normal", Main.Box(i == Selected ? Main.Gold.Darkened(.6f) : Main.Ink,
                i == Selected ? Main.Gold : human.Position == i ? Main.Mint : Main.Edge));
        }
        QueueRedraw();
    }
    public override void _Draw()
    {
        if (Match == null) return;
        foreach (var v in Game.Board)
            foreach (var dest in v.Neighbors.Where(d => d > v.Id)) DrawLine(Places[v.Id] * Size, Places[dest] * Size, Main.Edge, 3, true);
        if (Plan != null && Match.Result == null && Match.Current == 0)
        {
            var start = Places[Match.People[0].Position] * Size; var finish = Places[Plan.Destination] * Size;
            DrawLine(start, finish, Main.Gold, 6, true); DrawCircle(finish, 49, new Color(1,.8f,.35f,.12f));
        }
        DrawString(ThemeDB.FallbackFont, new Vector2(Size.X / 2 - 65, Size.Y / 2 - 5), "FEIRA DO ECLIPSE", HorizontalAlignment.Left, -1, 14, Main.Gold);
        DrawString(ThemeDB.FallbackFont, new Vector2(Size.X / 2 - 67, Size.Y / 2 + 17), "One edge · one action", HorizontalAlignment.Left, -1, 14, Main.Muted);
    }
}
