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
    private Button commit = null!, next = null!, hint = null!, save = null!, load = null!, response = null!, begin = null!, replay = null!;
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
        GetTree().AutoAcceptQuit = false;
        GetWindow().CloseRequested += () => GetTree().Quit();
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
        replay = Button("Export replay", () => { session.ExportReplay(); Refresh(); }); header.AddChild(replay);
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
        begin = Button("Begin local turn", () => { session.BeginTurn(); ResetSelection(); Refresh(); map.Venues[destination].GrabFocus(); }); controls.AddChild(begin);
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
        response = Button("Next turns", ForecastDialog); confirm.AddChild(response);
        response.TooltipText = "Compare rival turns until the next local player; their decision is never predicted.";
        notice = Text("", 14, Gold); notice.CustomMinimumSize = new(0, 40); stack.AddChild(notice);
        log = new RichTextLabel { BbcodeEnabled = false, ScrollFollowing = true, CustomMinimumSize = new(0, 95), SelectionEnabled = true };
        log.AddThemeFontSizeOverride("normal_font_size", 14); log.AddThemeStyleboxOverride("normal", Box(Ink, Edge)); stack.AddChild(log);
    }
    private void ResetSelection() { destination = session.Game.People[session.ViewSeat].Position; selected = null; rivalClock = 0; }
    private void Refresh()
    {
        var game = session.Game; var p = game.People[session.ViewSeat]; var human = session.IsHumanTurn && !session.AwaitingPlayer;
        clock.Text = $"Round {game.Round}/{game.Rules.RoundLimit} · Seed {game.Seed}   |   NOW: {game.Forecast(game.Round)}   |   NEXT: {game.Forecast(game.Round + 1)}";
        var goal = p.Sigils < game.Rules.Goal ? $"Buy {game.Rules.Goal - p.Sigils} more sigils; each adds curse." :
            p.Curse > 0 ? "Cleanse at the Chapel, then reach the Gate." : "Reach the Gate and choose Claim.";
        objective.Text = game.Result == null ? $"LOCAL: {p.Name}   ·   {p.Sigils}/{game.Rules.Goal} sigils · {p.Curse} curse   |   {goal}" :
            "WINNER(S): " + string.Join(", ", game.Result.Winners.Select(i => game.People[i].Name)) + "   ·   " + game.Result.Reason;
        for (var i = 0; i < 4; i++)
        {
            var who = game.People[i]; roster[i, 0].Text = (game.Current == i && game.Result == null ? "▶ " : "") + who.Name + (session.HumanSeats.Contains(i) ? " · LOCAL" : " · " + session.Policies[i]);
            roster[i, 0].AddThemeColorOverride("font_color", session.HumanSeats.Contains(i) ? Mint : new Color("f4ecdf"));
            roster[i, 0].TooltipText = session.HumanSeats.Contains(i) ? "Local control. Suggestion profile: " + session.Policies[i] + ". Other local choices are unknown."
                : "Automatic rival profile: " + session.Policies[i];
            roster[i, 1].Text = $"{who.Gold} obols · {who.Sigils}/{game.Rules.Goal} sigils";
            roster[i, 2].Text = $"Curse {who.Curse} · Ward {who.Ward} · {Game.Board[who.Position].Name}";
        }
        begin.Visible = session.AwaitingPlayer; begin.Text = "Begin " + game.People[game.Current].Name + "’s turn";
        if (session.AwaitingPlayer) begin.GrabFocus();
        next.Disabled = session.IsHumanTurn || game.Result != null; hint.Disabled = !human;
        automatic.Disabled = session.HumanSeats.Length == 4;
        if (automatic.Disabled) automatic.SetPressedNoSignal(false);
        hint.TooltipText = "Advice models all seats using the listed profiles; other local players may choose differently.";
        response.Disabled = !human || selected == null;
        turn.Text = game.Result != null ? "Start a new fair to play again." : session.AwaitingPlayer ? "Pass control to " + p.Name + "." : human ? p.Name + "’s turn — compare before committing." : game.People[game.Current].Name + " is next.";
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
                var after = session.Preview(intent).People[session.ViewSeat];
                var title = ActionName(intent) + $"   |   {Signed(after.Gold - p.Gold)} obols";
                var b = Button(title, () => { selected = intent; Refresh(); });
                if (intent == selected) b.AddThemeStyleboxOverride("normal", Box(Gold.Darkened(.65f), Gold));
                actions.AddChild(b); planButtons[intent] = b;
            }
            if (plans.Length == 0) actions.AddChild(Text("No legal plan here. Select your current venue or an adjacent one; travel also needs an obol.", 16));
            if (selected == null) preview.Text = $"Work here: {game.Wage(destination, p)} now / {game.Wage(destination, p, game.Round + 1)} next round.\nChoose an action to see its full result.";
            else
            {
                var after = session.Preview(selected).People[session.ViewSeat];
                var travel = destination == p.Position ? 0 : game.Rules.MoveCost;
                preview.Text = $"After {ActionName(selected)}: {after.Gold} obols · {after.Sigils} sigils\n{after.Curse} curse · {after.Ward} ward   |   Travel cost: {travel}\nOne turn; initiative determines the next participant.";
                if (selected.Action == ActionKind.Steal)
                {
                    var victim = session.Preview(selected).People[selected.Target];
                    preview.Text += $"\n{victim.Name} after: {victim.Gold} obols · {victim.Ward} ward.";
                }
            }
        }
        else if (session.AwaitingPlayer)
        {
            selected = null;
            actions.AddChild(Text("Pass control to " + p.Name, 22, Gold));
            actions.AddChild(Text("The board and all resources are public. Begin the named turn before selecting a plan. No time passes while waiting.", 17));
            preview.Text = "Beginning a local turn changes no resources or accepted actions.";
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
        notice.Text = session.Notice; save.TooltipText = "Local controls and accepted-action save: " + session.SavePath;
        replay.TooltipText = "Economy replay without local controls: " + session.ReplayPath;
        load.TooltipText = "Loading replaces only after every saved action and local seat has been validated.";
        log.Text = string.Join("\n", game.Journal.TakeLast(40).Select(e => e.Description));
        map.Match = game; map.ViewSeat = session.ViewSeat; map.CanPlan = human; map.Selected = destination; map.Plan = selected; map.Refresh();
    }
    private string ActionName(Intent i) => i.Action switch { ActionKind.Work => "Work", ActionKind.Buy => "Buy a sigil", ActionKind.Rite => "Perform a rite",
        ActionKind.Guard => "Raise a raven ward", ActionKind.Steal => "Steal from " + session.Game.People[i.Target].Name, _ => "Claim the Gate" };
    private static string Signed(int value) => value > 0 ? "+" + value : value.ToString();
    private void CommitTurn() { if (selected != null && session.Act(selected)) ResetSelection(); Refresh(); }
    private void RivalTurn() { if (session.Rival()) ResetSelection(); Refresh(); }
    private void Suggest()
    {
        if (!session.IsHumanTurn || session.AwaitingPlayer) return;
        var advice = session.Advice(); selected = advice.First; destination = selected.Destination; Refresh();
        notice.Text = "Suggestion: " + advice.Purpose + ". Other local choices are modelled, not known; inspect before committing.";
    }
    private string PlanName(Intent intent) => ActionName(intent) + " at " + Game.Board[intent.Destination].Name;
    private string ForecastText(ReplyForecast forecast)
    {
        var after = forecast.After; var p = after.People[session.Game.Current];
        var replies = forecast.Replies.Length == 0 ? "No rival acts before the next local decision or ending."
            : string.Join("\n", forecast.Replies.Select(r => r.Description));
        var end = after.Result == null ? $"Next local decision: {after.People[after.Current].Name}, round {after.Round}."
            : "The fair ends: " + after.Result.Reason + ". Winner(s): " + string.Join(", ", after.Result.Winners.Select(i => after.People[i].Name));
        return "If " + p.Name + " commits " + PlanName(selected!) + ":\n\n" + replies + "\n\n" + end +
            $"\n{p.Name} after these turns: {p.Gold} obols, {p.Sigils} sigils, {p.Curse} curse, {p.Ward} ward." +
            "\n\nConditional forecast: only configured rivals are executed. It stops before the next local player chooses. Your live match is unchanged.";
    }

    private void ForecastDialog()
    {
        if (selected == null || !session.IsHumanTurn || session.AwaitingPlayer) return;
        automatic.ButtonPressed = false;
        var dialog = new AcceptDialog { Title = "Compare until the next local decision", MinSize = new(840, 560), DialogText = ForecastText(session.Forecast(selected)) };
        dialog.GetLabel().AutowrapMode = TextServer.AutowrapMode.WordSmart;
        AddChild(dialog); dialog.Confirmed += () => dialog.QueueFree(); dialog.PopupCentered();
    }
    public override void _Process(double delta)
    {
        if (verification || !automatic.ButtonPressed || session.Game.Result != null || session.IsHumanTurn) return;
        rivalClock += delta; if (rivalClock >= 1) { rivalClock = 0; RivalTurn(); }
    }
    public override void _Notification(int what)
    {
        if (what == NotificationWMWindowFocusOut && automatic != null) automatic.ButtonPressed = false;
    }
    private void NewDialog()
    {
        automatic.ButtonPressed = false;
        var dialog = new ConfirmationDialog { Title = "Start a new fair", MinSize = new(700, 365) };
        var layout = new VBoxContainer(); layout.AddThemeConstantOverride("separation", 12);
        var instructions = Text("Choose 1–4 LOCAL participants; unchecked seats are rivals.\nPass control and Begin each named turn. All resources are public.\nAccepted turns or Save replace the current save.", 15, Muted);
        instructions.AutowrapMode = TextServer.AutowrapMode.Off; layout.AddChild(instructions);
        var settings = new HBoxContainer(); settings.AddThemeConstantOverride("separation", 12); layout.AddChild(settings);
        var seedLabel = Text("Seed", 15, Muted); seedLabel.AutowrapMode = TextServer.AutowrapMode.Off; settings.AddChild(seedLabel);
        var seed = new SpinBox { MinValue = 0, MaxValue = 1000000, Value = session.Game.Seed + 1, CustomMinimumSize = new(140, 36) };
        var profiles = new OptionButton { SizeFlagsHorizontal = SizeFlags.ExpandFill, CustomMinimumSize = new(390, 36) };
        profiles.AddItem("Planning rivals — forecast and adapt"); profiles.AddItem("Classic rivals — original one-turn decisions");
        settings.AddChild(seed); settings.AddChild(profiles);
        var grid = new GridContainer { Columns = 2, SizeFlagsHorizontal = SizeFlags.ExpandFill };
        grid.AddThemeConstantOverride("h_separation", 16); grid.AddThemeConstantOverride("v_separation", 8); layout.AddChild(grid);
        var local = new CheckButton[4];
        for (int i = 0; i < 4; i++)
        {
            local[i] = new CheckButton { Text = session.Game.People[i].Name + " · LOCAL", ButtonPressed = session.HumanSeats.Contains(i),
                SizeFlagsHorizontal = SizeFlags.ExpandFill, CustomMinimumSize = new(300, 36) };
            local[i].Toggled += _ => dialog.GetOkButton().Disabled = !local.Any(b => b != null && b.ButtonPressed);
            grid.AddChild(local[i]);
        }
        var boundary = Text("Forecasts stop before the next local choice.\nSuggestions use policy models; other local players may choose differently.", 14, Muted);
        boundary.AutowrapMode = TextServer.AutowrapMode.Off; layout.AddChild(boundary);
        dialog.AddChild(layout); AddChild(dialog);
        dialog.Confirmed += () => {
            var seats = Enumerable.Range(0, 4).Where(i => local[i].ButtonPressed).ToArray();
            if (seats.Length == 0) return;
            session.New((int)seed.Value, profiles.Selected == 0, seats); ResetSelection(); Refresh(); dialog.QueueFree();
        };
        dialog.Canceled += () => dialog.QueueFree(); dialog.PopupCentered();
    }

    private void Help()
    {
        automatic.ButtonPressed = false;
        var dialog = new AcceptDialog { Title = "Win the Eclipse Fair", MinSize = new(670, 410), DialogText =
            "1. New fair selects 1–4 local seats. Begin the named turn when passing\ncontrol. Inspect a venue; choose an action and commit.\nMove at most one edge (one obol), then act. Staying is free.\n\n" +
            "2. Earn obols; buy three sigils at Market or Bazaar. Prices rise with\nyour sigils and again after round 10. Each purchase adds curse.\n\n" +
            "3. Visit the Chapel for rites: remove two curse for two obols,\nor free during a procession. Curse also reduces your work income.\n\n" +
            "4. Reach the Gate with three sigils and zero curse; CLAIM it.\nA raven ward costs two obols and blocks one co-located theft.\nTheft adds curse if successful. Forecasts and rival resources are public.\n\n" +
            "Planning rivals project races and replan after changes.\nNext turns stops BEFORE another local player chooses.\nAdvice uses policy models for human seats, not known human decisions.\nNew fair also offers Classic rivals. Saved seats/profiles are preserved.\n\n" +
            "Initiative rotates. At round 20, rank by sigils, least curse, obols.\nAccepted turns autosave. Resume replays them and requires local handoff.\nExport replay omits local controls for the economy/CLI journal.\nTab/arrow keys navigate controls; Enter/Space activates a focused button." };
        AddChild(dialog); dialog.Confirmed += () => dialog.QueueFree(); dialog.PopupCentered();
    }
}
