using Godot;
using Eclipse.Core;

namespace Eclipse.Board;

public partial class Main : Control
{
    public static readonly Color Ink = new("171426"), Edge = new("494054"), Gold = new("edc573"), Mint = new("8dd6c3"), Muted = new("b5aebf");
    private BoardSession session = null!;
    private MapView map = null!;
    private Label clock = null!, objective = null!, venue = null!, venueInfo = null!, notice = null!, preview = null!, turn = null!;
    private readonly Label[,] roster = new Label[4, 3];
    private VBoxContainer actions = null!;
    private RichTextLabel log = null!;
    private Button commit = null!, next = null!, hint = null!, save = null!, load = null!, response = null!;
    private CheckButton automatic = null!;
    private readonly Dictionary<Intent, Button> planButtons = [];
    private Intent? selected;
    private int destination;
    private double rivalClock;
    private bool verification;
    private string? captureDirectory;
    private readonly string[] functions = ["Sigils are sold here. Each purchase adds one curse.", "Reliable wages; a foundry rush pays more.",
        "A rite removes two curse. Processions make rites free.", "Contracts can increase wages.", "The second sigil market; the shortcut crosses the fair.",
        "High wages, but blight reduces them.", "A shortcut to the Chapel; low income.", "Claim with three sigils and no curse. Reaching it is not claiming it."];

    public override void _Ready()
    {
        var args = OS.GetCmdlineUserArgs();
        string? Option(string name) { var at = Array.IndexOf(args, name); return at >= 0 && at + 1 < args.Length ? args[at + 1] : null; }
        verification = args.Contains("--verify"); captureDirectory = Option("--capture");
        var path = Option("--save-path") ?? ProjectSettings.GlobalizePath("user://match.json");
        if (verification && Option("--save-path") == null) throw new ArgumentException("Verification requires an isolated --save-path.");
        session = new(path); Build();
        if (!verification && File.Exists(path)) session.Load();
        ResetSelection(); Refresh();
        if (verification) _ = Verify();
    }
    public static StyleBoxFlat Box(Color fill, Color border)
    {
        var style = new StyleBoxFlat { BgColor = fill, BorderColor = border, CornerRadiusTopLeft = 8, CornerRadiusTopRight = 8,
            CornerRadiusBottomLeft = 8, CornerRadiusBottomRight = 8, BorderWidthLeft = 1, BorderWidthTop = 1, BorderWidthRight = 1, BorderWidthBottom = 1,
            ContentMarginLeft = 12, ContentMarginRight = 12, ContentMarginTop = 9, ContentMarginBottom = 9 };
        return style;
    }
    private static Label Text(string text, int size = 16, Color? color = null)
    {
        var label = new Label { Text = text, AutowrapMode = TextServer.AutowrapMode.WordSmart, SizeFlagsHorizontal = SizeFlags.ExpandFill };
        label.AddThemeFontSizeOverride("font_size", size); label.AddThemeColorOverride("font_color", color ?? new Color("f4ecdf")); return label;
    }
    private static Button Button(string text, Action action)
    {
        var b = new Button { Text = text, MouseDefaultCursorShape = CursorShape.PointingHand, CustomMinimumSize = new(0, 36) };
        b.Pressed += action; return b;
    }
    private void Build()
    {
        var theme = new Theme { DefaultFontSize = 16 };
        theme.SetStylebox("normal", "Button", Box(Ink, Edge)); theme.SetStylebox("hover", "Button", Box(new Color("312940"), Gold));
        theme.SetStylebox("focus", "Button", Box(new Color(0,0,0,0), Mint)); theme.SetStylebox("pressed", "Button", Box(new Color("494038"), Gold));
        theme.SetColor("font_color", "Button", new Color("f4ecdf")); Theme = theme;
        var margin = new MarginContainer { OffsetLeft = 20, OffsetTop = 16, OffsetRight = -20, OffsetBottom = -16 };
        margin.SetAnchorsPreset(LayoutPreset.FullRect); AddChild(margin);
        var stack = new VBoxContainer(); stack.AddThemeConstantOverride("separation", 10); margin.AddChild(stack);
        var header = new HBoxContainer(); stack.AddChild(header);
        header.AddChild(Text("ECLIPSE FAIR", 29, Gold));
        header.AddChild(Button("New fair", NewDialog));
        save = Button("Save", () => { session.Save(); Refresh(); }); header.AddChild(save);
        load = Button("Resume save", () => { automatic.ButtonPressed = false; session.Load(); ResetSelection(); Refresh(); }); header.AddChild(load);
        header.AddChild(Button("How to play", Help));
        clock = Text("", 16, Muted); stack.AddChild(clock);
        objective = Text("", 17, Mint); stack.AddChild(objective);
        var people = new HBoxContainer(); people.AddThemeConstantOverride("separation", 10); stack.AddChild(people);
        for (var i = 0; i < 4; i++)
        {
            var panel = new PanelContainer { SizeFlagsHorizontal = SizeFlags.ExpandFill };
            panel.AddThemeStyleboxOverride("panel", Box(Ink, Edge));
            var lines = new VBoxContainer(); lines.AddThemeConstantOverride("separation", 3); panel.AddChild(lines);
            for (var row = 0; row < 3; row++)
            {
                roster[i, row] = Text("", 14, i == 0 ? Mint : new Color("f4ecdf"));
                roster[i, row].AutowrapMode = TextServer.AutowrapMode.Off; roster[i, row].ClipText = true;
                lines.AddChild(roster[i, row]);
            }
            people.AddChild(panel);
        }
        var main = new HBoxContainer { SizeFlagsVertical = SizeFlags.ExpandFill }; main.AddThemeConstantOverride("separation", 20); stack.AddChild(main);
        var board = new VBoxContainer { SizeFlagsHorizontal = SizeFlags.ExpandFill }; main.AddChild(board);
        board.AddChild(Text("THE FAIR  ·  faded venues are more than one edge away", 13, Muted));
        map = new MapView(); board.AddChild(map);
        map.VenueSelected += id => { destination = id; selected = null; Refresh(); };
        var controls = new HBoxContainer(); board.AddChild(controls);
        next = Button("Watch next rival", RivalTurn); controls.AddChild(next);
        automatic = new CheckButton { Text = "Auto rivals", ButtonPressed = !verification }; controls.AddChild(automatic);
        automatic.Toggled += _ => rivalClock = 0;
        turn = Text("", 15, Gold); controls.AddChild(turn);
        var sidebar = new VBoxContainer { CustomMinimumSize = new(430, 0) }; sidebar.AddThemeConstantOverride("separation", 8); main.AddChild(sidebar);
        venue = Text("", 22, Gold); sidebar.AddChild(venue); venueInfo = Text("", 14, Muted); sidebar.AddChild(venueInfo);
        var scroll = new ScrollContainer { SizeFlagsVertical = SizeFlags.ExpandFill, HorizontalScrollMode = ScrollContainer.ScrollMode.Disabled };
        sidebar.AddChild(scroll); actions = new VBoxContainer { SizeFlagsHorizontal = SizeFlags.ExpandFill }; scroll.AddChild(actions);
        preview = Text("", 15, Mint); sidebar.AddChild(preview);
        var confirm = new HBoxContainer(); sidebar.AddChild(confirm);
        commit = Button("Commit this plan", CommitTurn); commit.SizeFlagsHorizontal = SizeFlags.ExpandFill; confirm.AddChild(commit);
        hint = Button("Suggest plan", Suggest); confirm.AddChild(hint);
        response = Button("Rival response", ForecastDialog); confirm.AddChild(response);
        response.TooltipText = "Compare the next rival turns if you commit the selected plan.";
        notice = Text("", 14, Gold); notice.CustomMinimumSize = new(0, 40); stack.AddChild(notice);
        log = new RichTextLabel { BbcodeEnabled = false, ScrollFollowing = true, CustomMinimumSize = new(0, 95), SelectionEnabled = true };
        log.AddThemeFontSizeOverride("normal_font_size", 14); log.AddThemeStyleboxOverride("normal", Box(Ink, Edge)); stack.AddChild(log);
    }
    private void ResetSelection() { destination = session.Game.People[0].Position; selected = null; rivalClock = 0; }
    private void Refresh()
    {
        var game = session.Game; var p = game.People[0]; var human = game.Current == 0 && game.Result == null;
        clock.Text = $"Round {game.Round}/{game.Rules.RoundLimit} · Seed {game.Seed}   |   NOW: {game.Forecast(game.Round)}   |   NEXT: {game.Forecast(game.Round + 1)}";
        var goal = p.Sigils < game.Rules.Goal ? $"Buy {game.Rules.Goal - p.Sigils} more sigils; each adds curse." :
            p.Curse > 0 ? "Cleanse at the Chapel, then reach the Gate." : "Reach the Gate and choose Claim.";
        objective.Text = game.Result == null ? $"YOU: Vaelis   ·   {p.Sigils}/{game.Rules.Goal} sigils · {p.Curse} curse   |   {goal}" :
            (game.Result.Winners.Contains(0) ? "YOU WON" : "THE FAIR HAS ENDED") + "   ·   " + game.Result.Reason;
        for (var i = 0; i < 4; i++)
        {
            var who = game.People[i]; roster[i, 0].Text = (game.Current == i && game.Result == null ? "▶ " : "") + who.Name + (i == 0 ? " · YOU" : " · " + session.Policies[i]);
            roster[i, 1].Text = $"{who.Gold} obols · {who.Sigils}/{game.Rules.Goal} sigils";
            roster[i, 2].Text = $"Curse {who.Curse} · Ward {who.Ward} · {Game.Board[who.Position].Name}";
        }
        next.Disabled = human || game.Result != null; hint.Disabled = !human;
        response.Disabled = !human || selected == null;
        turn.Text = game.Result != null ? "Start a new fair to play again." : human ? "Your turn — compare before committing." : game.People[game.Current].Name + " is next.";
        venue.Text = Game.Board[destination].Name; venueInfo.Text = functions[destination];
        if (destination == 0 || destination == 4)
            venueInfo.Text += p.Sigils >= game.Rules.Goal ? " All your sigils are secured." : $" Next sigil: {game.Price(p)} obols (plus travel).";
        if (destination == 2) venueInfo.Text += p.Curse == 0 ? " You have no curse to remove." :
            $" Rite now: {(game.Forecast(game.Round) == Game.Events[2] ? 0 : game.Rules.RiteCost)} obols (plus travel).";
        foreach (var child in actions.GetChildren()) { actions.RemoveChild(child); child.QueueFree(); } planButtons.Clear();
        if (game.Result != null)
        {
            selected = null;
            foreach (var rank in game.Result.Standings.OrderByDescending(r => game.Result.Winners.Contains(r.Id)))
                actions.AddChild(Text((game.Result.Winners.Contains(rank.Id) ? "WINNER · " : "") + rank.Name + $"\n{rank.Sigils} sigils · {rank.Curse} curse · {rank.Gold} obols", 16));
            preview.Text = game.Result.Reason == "gate claimed" ? "The first Gate claim wins. Remaining standings: sigils, least curse, then obols." :
                "Deadline rank: most sigils, then least curse, then most obols. Exact ties share the win.";
        }
        else if (human)
        {
            var plans = game.Legal().Where(i => i.Destination == destination).ToArray();
            if (selected != null && !plans.Contains(selected)) selected = null;
            foreach (var intent in plans)
            {
                var after = session.Preview(intent).People[0];
                var title = ActionName(intent) + $"   |   {Signed(after.Gold - p.Gold)} obols";
                var b = Button(title, () => { selected = intent; Refresh(); });
                if (intent == selected) b.AddThemeStyleboxOverride("normal", Box(Gold.Darkened(.65f), Gold));
                actions.AddChild(b); planButtons[intent] = b;
            }
            if (plans.Length == 0) actions.AddChild(Text("No legal plan here. Select your current venue or an adjacent one; travel also needs an obol.", 16));
            if (selected == null) preview.Text = $"Work here: {game.Wage(destination, p)} now / {game.Wage(destination, p, game.Round + 1)} next round.\nChoose an action to see its full result.";
            else
            {
                var after = session.Preview(selected).People[0];
                var travel = destination == p.Position ? 0 : game.Rules.MoveCost;
                preview.Text = $"After {ActionName(selected)}: {after.Gold} obols · {after.Sigils} sigils\n{after.Curse} curse · {after.Ward} ward   |   Travel cost: {travel}\nOne turn; rivals may act before your next turn.";
                if (selected.Action == ActionKind.Steal)
                {
                    var victim = session.Preview(selected).People[selected.Target];
                    preview.Text += $"\n{victim.Name} after: {victim.Gold} obols · {victim.Ward} ward.";
                }
            }
        }
        else
        {
            selected = null; var advice = session.Advice();
            actions.AddChild(Text(game.People[game.Current].Name + " · " + session.Policies[game.Current], 20, Gold));
            actions.AddChild(Text(advice.Purpose, 17));
            actions.AddChild(Text("Considering: " + string.Join(" → ", advice.Route.Select(PlanName)), 15));
            actions.AddChild(Text("This turn: " + PlanName(advice.First), 17, Mint));
            preview.Text = "Plans are reconsidered after each accepted action. Watch the next turn or enable Auto rivals.";
        }
        commit.Disabled = !human || selected == null;
        notice.Text = session.Notice; save.TooltipText = "Save/replay file: " + session.SavePath; load.TooltipText = "Loading replaces only after every saved action has been validated.";
        log.Text = string.Join("\n", game.Journal.TakeLast(40).Select(e => e.Description));
        map.Match = game; map.Selected = destination; map.Plan = selected; map.Refresh();
    }
    private string ActionName(Intent i) => i.Action switch { ActionKind.Work => "Work", ActionKind.Buy => "Buy a sigil", ActionKind.Rite => "Perform a rite",
        ActionKind.Guard => "Raise a raven ward", ActionKind.Steal => "Steal from " + session.Game.People[i.Target].Name, _ => "Claim the Gate" };
    private static string Signed(int value) => value > 0 ? "+" + value : value.ToString();
    private void CommitTurn() { if (selected != null && session.Act(selected)) ResetSelection(); Refresh(); }
    private void RivalTurn() { if (session.Rival()) ResetSelection(); Refresh(); }
    private void Suggest()
    {
        if (session.Game.Result != null || session.Game.Current != 0) return;
        var advice = session.Advice(); selected = advice.First; destination = selected.Destination; Refresh();
        notice.Text = "Suggestion: " + advice.Purpose + ". Inspect the plan and compare rival replies before committing.";
    }
    private string PlanName(Intent intent) => ActionName(intent) + " at " + Game.Board[intent.Destination].Name;
    private string ForecastText(ReplyForecast forecast)
    {
        var after = forecast.After; var p = after.People[0];
        var replies = forecast.Replies.Length == 0 ? (after.Result != null ? "Your plan ends the fair before another turn." : "Your next turn follows immediately; no rival acts.")
            : string.Join("\n", forecast.Replies.Select(r => r.Description));
        var end = after.Result == null ? $"Your next turn: round {after.Round}; {p.Gold} obols, {p.Sigils} sigils, {p.Curse} curse, {p.Ward} ward."
            : "The fair ends: " + after.Result.Reason + ". Winner(s): " + string.Join(", ", after.Result.Winners.Select(i => after.People[i].Name));
        return "If you commit " + PlanName(selected!) + ":\n\n" + replies + "\n\n" + end +
            "\n\nConditional forecast: these public profiles respond to this plan. Compare another plan to see different replies. Your live match is unchanged.";
    }
    private void ForecastDialog()
    {
        if (selected == null || session.Game.Current != 0 || session.Game.Result != null) return;
        automatic.ButtonPressed = false;
        var dialog = new AcceptDialog { Title = "Compare the next rival turns", MinSize = new(840, 560), DialogText = ForecastText(session.Forecast(selected)) };
        dialog.GetLabel().AutowrapMode = TextServer.AutowrapMode.WordSmart;
        AddChild(dialog); dialog.Confirmed += () => dialog.QueueFree(); dialog.PopupCentered();
    }
    public override void _Process(double delta)
    {
        if (verification || !automatic.ButtonPressed || session.Game.Result != null || session.Game.Current == 0) return;
        rivalClock += delta; if (rivalClock >= 1) { rivalClock = 0; RivalTurn(); }
    }
    public override void _Notification(int what)
    {
        if (what == NotificationWMWindowFocusOut && automatic != null) automatic.ButtonPressed = false;
    }
    private void NewDialog()
    {
        automatic.ButtonPressed = false;
        var dialog = new ConfirmationDialog { Title = "Start a new fair", DialogText = "Choose a seed and rivals. Accepted turns or Save replace the current save.", MinSize = new(660, 245) };
        var seed = new SpinBox { MinValue = 0, MaxValue = 1000000, Value = session.Game.Seed + 1, Position = new(20, 78), Size = new(180, 36) };
        var profiles = new OptionButton { Position = new(220, 78), Size = new(410, 36) };
        profiles.AddItem("Planning rivals — forecast and adapt"); profiles.AddItem("Classic rivals — original one-turn decisions");
        var detail = Text("Planning rivals consider wages, curse and nearby competition.\nClassic preserves the previous fair; the rules are identical.", 14, Muted);
        detail.Position = new(20, 125); detail.Size = new(610, 60);
        dialog.AddChild(seed); dialog.AddChild(profiles); dialog.AddChild(detail); AddChild(dialog);
        dialog.Confirmed += () => { session.New((int)seed.Value, profiles.Selected == 0); ResetSelection(); Refresh(); dialog.QueueFree(); };
        dialog.Canceled += () => dialog.QueueFree(); dialog.PopupCentered();
    }
    private void Help()
    {
        automatic.ButtonPressed = false;
        var dialog = new AcceptDialog { Title = "Win the Eclipse Fair", MinSize = new(670, 410), DialogText =
            "1. You control Vaelis. Inspect a venue; choose an action and commit.\nMove at most one edge (one obol), then act. Staying is free.\n\n" +
            "2. Earn obols; buy three sigils at Market or Bazaar. Prices rise with\nyour sigils and again after round 10. Each purchase adds curse.\n\n" +
            "3. Visit the Chapel for rites: remove two curse for two obols,\nor free during a procession. Curse also reduces your work income.\n\n" +
            "4. Reach the Gate with three sigils and zero curse; CLAIM it.\nA raven ward costs two obols and blocks one co-located theft.\nTheft adds curse if successful. Forecasts and rival resources are public.\n\n" +
            "Planning rivals project races and replan after changes.\nRival response forecasts the next cycle for your selected plan.\nNew fair also offers Classic rivals. Saved profiles are preserved.\n\n" +
            "Initiative rotates. At round 20, rank by sigils, least curse, obols.\nAccepted turns autosave. Resume replays them; no hidden time passes.\nTab/arrow keys navigate controls; Enter/Space activates a focused button." };
        AddChild(dialog); dialog.Confirmed += () => dialog.QueueFree(); dialog.PopupCentered();
    }
}
