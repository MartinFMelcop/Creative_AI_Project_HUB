using Godot;
using Cinder.Core;
namespace Cinder.Native;

public partial class Main : Control
{
    private Game game=new();
    private Command? selected;
    private readonly Dictionary<Command,Button> choices=new();
    private readonly Dictionary<string,Button> salvage=new();
    private readonly Dictionary<int,Panel> cards=new();
    private Label heading=null!, resources=null!, turn=null!, notice=null!, story=null!,queue=null!;
    private RichTextLabel history=null!,forecast=null!;
    private Button confirm=null!, resolve=null!, restart=null!, resume=null!, save=null!, rules=null!, begin=null!;
    private Control board=null!, actionArea=null!, modal=null!;
    private VBoxContainer actionList=null!;
    private Label modalText=null!;
    private bool intro=true, showingRules,showEnding;
    private string savePath="";
    private static readonly Color Ink=new("#08151b"), Paper=new("#dce8df"), Muted=new("#9eb8b6"), Teal=new("#57d4bb"), Ember=new("#ffae69");
    private string? captureDirectory;
    private bool verifying;

    public override void _Ready()
    {
        GetTree().AutoAcceptQuit=false;
        GetTree().Root.CloseRequested+=WindowClose;
        savePath=ProjectSettings.GlobalizePath("user://cinderwatch-save.json");
        var args=OS.GetCmdlineUserArgs();
        for(var i=0;i<args.Length;i++)
        {
            if(args[i]=="--verify")verifying=true;
            if(args[i]=="--save-path" && i+1<args.Length)savePath=args[++i];
            if(args[i]=="--capture-dir" && i+1<args.Length)captureDirectory=args[++i];
        }
        if(verifying && !args.Contains("--save-path"))savePath=ProjectSettings.GlobalizePath("user://cinderwatch-check-save.json");
        try { LoadPresentation();Build(); Refresh(); }
        catch(IOException error) { GD.PrintErr("Cinderwatch could not start. " + error.Message);GetTree().Quit(1);return; }
        if(verifying)_=Verify();
    }
    private StyleBoxFlat Style(Color color,Color? border=null,int radius=10)
    {
        if(styles.TryGetValue((color,border,radius),out var existing))return existing;
        var s=new StyleBoxFlat {BgColor=color,CornerRadiusTopLeft=radius,CornerRadiusTopRight=radius,CornerRadiusBottomLeft=radius,CornerRadiusBottomRight=radius,
            ContentMarginLeft=12,ContentMarginRight=12,ContentMarginTop=8,ContentMarginBottom=8};
        if(border is {} c) {s.BorderColor=c;s.BorderWidthLeft=1;s.BorderWidthRight=1;s.BorderWidthTop=1;s.BorderWidthBottom=1;}
        styles.Add((color,border,radius),s);return s;
    }
    private static T Place<T>(T node,Node parent,float x,float y,float w,float h) where T:Control
    {parent.AddChild(node);node.Position=new(x,y);node.Size=new(w,h);return node;}
    private static Label Text(Node parent,string text,float x,float y,float w,float h,int size=17,Color? color=null)
    {
        var l=Place(new Label {Text=text,ClipText=true,AutowrapMode=TextServer.AutowrapMode.WordSmart},parent,x,y,w,h);
        l.AddThemeFontSizeOverride("font_size",size);l.AddThemeColorOverride("font_color",color??Paper);return l;
    }
    private Button Button(Node parent,string text,float x,float y,float w,float h,Action action)
    {
        var b=Place(new Button {Text=text,FocusMode=FocusModeEnum.All},parent,x,y,w,h);
        b.AddThemeFontSizeOverride("font_size",16); b.AddThemeColorOverride("font_color",Paper);
        b.AddThemeStyleboxOverride("normal",Style(new("#193139"),new("#38525a")));
        b.AddThemeStyleboxOverride("hover",Style(new("#29474e"),Teal));
        b.AddThemeStyleboxOverride("pressed",Style(new("#37665e"),Teal));
        b.AddThemeStyleboxOverride("focus",Style(new Color(0,0,0,0),Teal));
        b.Pressed+=action;return b;
    }
    private Panel Panel(Node parent,float x,float y,float w,float h,Color? border=null)
    {
        var p=Place(new Panel(),parent,x,y,w,h);p.AddThemeStyleboxOverride("panel",Style(new("#10242c"),border));return p;
    }
    private void Build()
    {
        Text(this,"CINDERWATCH",24,8,490,48,32);
        Text(this,"A three-encounter tactical rescue",26,58,480,25,16,Muted);
        sound=Button(this,"Sound: on",625,24,125,40,ToggleSound);
        restart=Button(this,"New run",760,24,110,40,NewRun);
        resume=Button(this,"Resume",878,24,105,40,Load);
        save=Button(this,"Save",991,24,98,40,Save);
        rules=Button(this,"Tactics",1097,24,158,40,ToggleRules);
        heading=Text(this,"",24,96,700,34,24);
        resources=Text(this,"",750,99,505,28,19,Ember);
        board=Place(new Control(),this,24,142,780,412);
        queue=Text(this,"",24,548,780,23,14,Muted);
        Text(board,"CREW · choose one action on your turn",12,0,740,26,17,Teal);
        Text(board,"SENTRIES · announced actions remain visible",12,196,744,26,17,Ember);
        var side=Panel(this,822,142,433,412);
        turn=Text(side,"",16,12,400,52,20,Teal);
        actionArea=Place(new ScrollContainer {FollowFocus=true},side,16,68,400,210);
        actionList=new VBoxContainer {SizeFlagsHorizontal=SizeFlags.ExpandFill,CustomMinimumSize=new(375,0)};
        actionArea.AddChild(actionList);
        forecast=Place(new RichTextLabel {ScrollActive=true},side,16,286,400,68);
        forecast.AddThemeFontSizeOverride("normal_font_size",16);forecast.AddThemeColorOverride("default_color",Muted);
        confirm=Button(side,"Confirm action",16,362,400,38,Confirm);
        resolve=Button(side,"Resolve announced enemy action",16,68,400,48,Enemy);
        resolve.Visible=false;
        var storyPanel=Panel(this,24,572,780,174);
        story=Text(storyPanel,"",14,8,750,72,16,Ember);
        history=Place(new RichTextLabel {ScrollActive=true,ScrollFollowing=true},storyPanel,14,88,750,76);
        history.AddThemeFontSizeOverride("normal_font_size",15);history.AddThemeColorOverride("default_color",Muted);
        var details=Panel(this,822,572,433,174);
        Text(details,"READ THE NEXT THREAT",16,12,400,25,17,Teal);
        Text(details,"Strike cannot reach a screened rear foe.\nPierce / Bolt can. Pin cancels this round only.\nShields expire at the owner's next turn.\nGout hits everyone; Cover cannot intercept it.",16,43,400,112,16,Muted);
        notice=Text(this,"Accepted turns autosave. Tab + Enter works on every button.",24,758,1230,28,15,Muted);
        modal=Panel(this,150,90,980,620,Teal);
        Text(modal,"CINDERWATCH / FIELD BRIEF",28,20,924,42,28,Teal);
        modalText=Text(modal,"",28,84,920,420,20);
        begin=Button(modal,"Enter the loading yard",28,530,924,56,CloseModal);
    }
    public override void _Draw()
    {
        DrawLine(new(24,130),new(1254,130),new Color("#38525a"),1);
    }
    private void Refresh()
    {
        heading.Text=$"{game.Stage+1}/3 · {game.Place}   /   Round {game.Round} of 12";
        resources.Text=$"{game.Sparks} sparks    {game.Kits} kits    {(game.Edge>0?"sharpened tools":game.Plates>0?"reinforced cover":"field tools")}";
        queue.Text=game.Phase==Phase.Combat?"NEXT  "+string.Join("  →  ",game.Order.Skip(game.Cursor).Where(id=>game.Find(id).Alive).Select(id=>game.Find(id).Name)):"Encounter complete · salvage and results do not spend combat turns";
        RefreshCards();
        foreach(var button in actionPool.Values.Concat(campPool.Values))button.Hide();choices.Clear();salvage.Clear();
        confirm.Visible=game.Phase==Phase.Combat && game.Actor!.Hero;
        resolve.Visible=game.Phase==Phase.Combat && !game.Actor!.Hero;
        if(game.Phase==Phase.Combat)
        {
            var actor=game.Actor!;
            turn.Text=actor.Hero?$"{actor.Name}'s turn · {actor.Role}":$"{actor.Name} is ready";
            if(actor.Hero)
            {
                var legal=game.Legal();
                for(var i=0;i<legal.Count;i++)
                {
                    var c=legal[i];
                    if(!actionPool.TryGetValue(c,out var button)){button=Button(actionList,"",0,0,375,34,()=>Select(c));button.CustomMinimumSize=new(375,34);actionPool.Add(c,button);}
                    button.Show();button.Text=game.Label(c);actionList.MoveChild(button,i);choices[c]=button;
                    button.TooltipText=game.Preview(c);
                }
            }
            else {forecast.Text=game.Intent(actor.Id)+"\nResolve when you have inspected the crew and queue.";selected=null;}
            if(selected!=null && !game.Legal().Contains(selected))selected=null;
            confirm.Disabled=selected==null;
            if(actor.Hero)forecast.Text=selected==null?"Select an action. Preview spends no turn or supplies.":game.Preview(selected);
        }
        else
        {
            selected=null;confirm.Disabled=true;
            turn.Text=game.Phase==Phase.Camp?"Salvage · choose once":game.Phase==Phase.Victory?"Pressure line closed":"Rescue failed";
            forecast.Text=game.Phase==Phase.Camp?"Injuries and supplies carry forward. Each option enters the next encounter immediately.":game.Phase==Phase.Victory?$"Crew rescued. {game.Units.Count(u=>u.Hero&&u.Alive)}/3 rescuers standing.\nInspect the log, save, or start a new run.":"The line burst or every rescuer fell.\nStart a new run and change your plan.";
            var i=0;foreach(var c in game.CampChoices)
            {
                var name=c;
                if(!campPool.TryGetValue(c,out var b)){b=Button(actionList,Content.CampLabel(c),0,0,375,68,()=>Camp(name));b.CustomMinimumSize=new(375,68);b.AutowrapMode=TextServer.AutowrapMode.WordSmart;campPool.Add(c,b);}
                b.Show();actionList.MoveChild(b,i++);salvage[c]=b;
            }
        }
        story.Text=game.Phase==Phase.Combat?Content.Arrival[game.Stage]:game.Phase==Phase.Defeat?game.Log.Last():Content.After[game.Stage];
        if(game.Phase==Phase.Victory) {story.Text="The valve wheel is seated. The night crew comes out through the pressure door.";history.Text=Content.Ending(game);}
        else history.Text=string.Join("\n",game.Log);
        modal.Visible=intro||showingRules||showEnding;
        modalText.Text=showingRules?Content.Rules:showEnding?Content.Ending(game)+$"\n\n{game.Units.Count(u=>u.Hero&&u.Alive)}/3 rescuers standing · {game.Kits} kits · {game.Sparks} sparks left.":Content.Intro;
        modalText.AddThemeFontSizeOverride("font_size",showingRules?17:22);
        begin.Text=showingRules?"Return to the current turn":showEnding?"Inspect the final board":"Enter the loading yard";
        // A modal is also an input boundary for keyboard focus, not only an overlay.
        foreach(var b in choices.Values.Concat(salvage.Values).Concat(new[]{confirm,resolve,restart,resume,save,rules}))b.Disabled=(intro||showingRules||showEnding)||(b==confirm&&selected==null);
        if(modal.Visible)begin.GrabFocus();
    }
    private void Select(Command c) {selected=c;Refresh();confirm.GrabFocus();}
    private void Accepted()
    {
        selected=null;showEnding=game.Phase==Phase.Victory;Save();Refresh();
        if(modal.Visible)return;
        if(choices.Count>0)choices.Values.First().GrabFocus();
        else if(resolve.Visible)resolve.GrabFocus();
        else if(salvage.Count>0)salvage.Values.First().GrabFocus();
    }
    private void Confirm() {if(intro||showingRules||selected==null)return;var before=game.Fork();var cue=selected.Kind switch{Kind.Guard or Kind.Cover=>"brace",Kind.Pin=>"pin",Kind.Mend=>"mend",Kind.Shift=>"shift",_=>"strike"};if(game.Act(selected)){Accepted();Feedback(before,cue);}}
    private void Enemy() {if(intro||showingRules||game.Actor is not {Hero:false} actor)return;var before=game.Fork();var threat=game.Threats[actor.Id];var cue=actor.Pinned?"pin":threat.Attack==Attack.Gout?"steam":threat.Attack==Attack.Repair?"mend":threat.Attack==Attack.Charge?"brace":"strike";if(game.ResolveEnemy()){if(threat.Attack==Attack.Repair&&!game.Units.Any(u=>u.Hp>before.Find(u.Id).Hp))cue="strike";Accepted();Feedback(before,cue);}}
    private void Camp(string c) {if(intro||showingRules)return;var before=game.Fork();if(game.Camp(c)){Accepted();Feedback(before,"stage");}}
    private void CloseModal() {intro=false;showingRules=false;showEnding=false;Refresh();if(choices.Count>0)choices.Values.First().GrabFocus();}
    private void ToggleRules() {showingRules=!showingRules;if(showingRules)speaker.Stop();Refresh();}
    private void NewRun() {ResetFeedback();game=new();selected=null;intro=true;showingRules=false;showEnding=false;notice.Text="New run is in memory. Enter and accept a turn to replace the previous save.";Refresh();}
    private void Save()
    {
        try {Journal.Store(game,savePath);notice.Text="Saved accepted actions. Resume restores the exact next turn.";}
        catch(Exception e)when(e is IOException or UnauthorizedAccessException) {notice.Text="Save failed; current progress remains in memory. "+e.Message;}
        notice.TooltipText=notice.Text;
    }
    private void Load()
    {
        try {var loaded=Journal.Load(savePath);ResetFeedback();game=loaded;selected=null;intro=false;showingRules=false;showEnding=game.Phase==Phase.Victory;notice.Text="Resumed the exact next turn and supplies.";Refresh();}
        catch(Exception e)when(e is IOException or UnauthorizedAccessException or System.Text.Json.JsonException or InvalidDataException) {notice.Text="Resume rejected; current run preserved. "+e.Message;}
        notice.TooltipText=notice.Text;
    }
}
