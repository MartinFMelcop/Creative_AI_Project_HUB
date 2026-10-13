using Godot;
using Cinder.Core;
namespace Cinder.Native;

public partial class Main
{
    private readonly Dictionary<(Color,Color?,int),StyleBoxFlat> styles=new();
    private readonly List<AtlasTexture> portraits=new();
    private ImageTexture portraitSheet=null!;
    private readonly Dictionary<string,AudioStreamWav> cues=new();
    private AudioStreamPlayer speaker=null!;
    private Button sound=null!;
    private bool muted;
    private string lastCue="";
    private int cuePlays;
    private sealed record Card(Panel Panel,TextureRect Portrait,Label Name,Label Row,
        ProgressBar Health,Label Hp,Label Detail,Label Effect);
    private readonly Dictionary<int,Card> unitCards=new();
    private readonly Dictionary<Command,Button> actionPool=new();
    private readonly Dictionary<string,Button> campPool=new();
    private double effectTime;
    private bool closing;

    private void LoadPresentation()
    {
        using var image=Image.LoadFromFile("res://media/portraits.png");
        if(image==null||image.IsEmpty())throw new InvalidDataException("Portrait sheet could not load.");
        portraitSheet=ImageTexture.CreateFromImage(image);
        var w=image.GetWidth()/4f;var h=image.GetHeight()/2f;
        for(var i=0;i<8;i++)portraits.Add(new AtlasTexture {Atlas=portraitSheet,
            Region=new Rect2(i%4*w+12,i/4*h+12,w-24,h-24),FilterClip=true});
        foreach(var name in new[]{"strike","brace","pin","mend","shift","steam","stage"})
            cues.Add(name,AudioStreamWav.LoadFromFile($"res://media/audio/{name}.wav")
                ??throw new InvalidDataException("Action cue could not load: "+name));
        speaker=new AudioStreamPlayer {VolumeDb=-8};AddChild(speaker);
    }
    private static int PortraitIndex(string name)=>name switch
    {
        "Rook"=>0,"Vale"=>1,"Neri"=>2,"Ash hound"=>3,"Riveter"=>4,
        "Bulwark"=>5,"Patch drone"=>6,"Governor"=>7,
        _=>throw new InvalidDataException("Unknown actor portrait: "+name)
    };
    private Card CreateCard(Unit unit)
    {
        var index=unit.Hero?unit.Id:unit.Id-3;
        var panel=Panel(board,index*260,unit.Hero?34:230,250,unit.Hero?158:170);
        var portrait=Place(new TextureRect {ExpandMode=TextureRect.ExpandModeEnum.IgnoreSize,
            StretchMode=TextureRect.StretchModeEnum.KeepAspectCentered},panel,8,8,78,88);
        var name=Text(panel,"",94,5,150,31,17);
        var row=Text(panel,"",94,40,150,37,12,Muted);
        var health=Place(new ProgressBar {ShowPercentage=false},panel,94,82,145,10);
        health.AddThemeStyleboxOverride("background",Style(Ink));
        health.AddThemeStyleboxOverride("fill",Style(unit.Hero?Teal:Ember));
        var hp=Text(panel,"",94,96,145,18,13);
        var detail=Text(panel,"",10,114,232,unit.Hero?42:48,13,unit.Hero?Muted:Ember);
        var effect=Text(panel,"",8,12,80,72,17,Teal);
        effect.HorizontalAlignment=HorizontalAlignment.Center;effect.VerticalAlignment=VerticalAlignment.Center;
        effect.AddThemeColorOverride("font_shadow_color",Colors.Black);effect.AddThemeConstantOverride("shadow_offset_x",2);effect.AddThemeConstantOverride("shadow_offset_y",2);
        return new(panel,portrait,name,row,health,hp,detail,effect);
    }
    private void RefreshCards()
    {
        foreach(var card in unitCards.Values)card.Panel.Hide();
        foreach(var u in game.Units)
        {
            if(!unitCards.TryGetValue(u.Id,out var card)){card=CreateCard(u);unitCards.Add(u.Id,card);cards[u.Id]=card.Panel;}
            card.Panel.Show();card.Portrait.Texture=portraits[PortraitIndex(u.Name)];
            card.Portrait.Modulate=u.Alive?Colors.White:new Color(.4f,.4f,.4f);
            var target=selected?.Target==u.Id;
            card.Panel.AddThemeStyleboxOverride("panel",Style(new("#10242c"),target?Paper:game.Actor?.Id==u.Id?Teal:u.Hero?new Color("#38525a"):new Color("#62483a")));
            card.Name.Text=u.Name.ToUpperInvariant();card.Name.Modulate=u.Hero?Teal:Ember;
            card.Row.Text=$"{(u.Front?"FRONT":"REAR")} · AGI {u.Speed}"+(u.Armor>0?$"\nArmour {u.Armor}":"");
            card.Health.MaxValue=u.MaxHp;card.Health.Value=u.Hp;
            card.Hp.Text=$"{u.Hp}/{u.MaxHp} HP"+(u.Shield>0?$" +{u.Shield} shield":"");
            card.Detail.Text=u.Hero?(u.Covers>=0?$"Covering {game.Find(u.Covers).Name}":!u.Alive?"DOWN · salvage recovery":u.Role):game.Intent(u.Id);
            if(u.Hero&&u.Scorch>0)card.Detail.Text+=$"\nScorch {u.Scorch} · 2 HP / turn";
        }
    }
    private void Feedback(Game before,string cue)
    {
        foreach(var card in unitCards.Values)card.Effect.Text="";
        foreach(var u in game.Units)
        {
            var old=before.Units.FirstOrDefault(x=>x.Id==u.Id&&x.Name==u.Name);
            if(old==null||!unitCards.TryGetValue(u.Id,out var card))continue;
            var change=u.Hp-old.Hp;
            card.Effect.Text=change!=0?$"{change:+0;-0} HP":u.Pinned&&!old.Pinned?"PINNED":u.Shield>old.Shield?$"+{u.Shield-old.Shield}\nSHIELD":u.Front!=old.Front?"ROW\nCHANGED":u.Scorch==0&&old.Scorch>0?"SCORCH\nCLEARED":"";
            card.Effect.AddThemeColorOverride("font_color",change<0?Ember:Teal);
            card.Effect.Modulate=Colors.White;
        }
        effectTime=.8;
        PlayCue(game.Stage!=before.Stage||game.Phase==Phase.Victory?"stage":cue);
    }
    private void PlayCue(string name)
    {
        lastCue=name;
        if(muted)return;
        speaker.Stream=cues[name];speaker.Play();cuePlays++;
    }
    private void ToggleSound()
    {
        muted=!muted;if(muted)speaker.Stop();sound.Text=muted?"Sound: off":"Sound: on";
    }
    private void ResetFeedback()
    {
        speaker.Stop();speaker.Stream=null;lastCue="";effectTime=0;
        foreach(var card in unitCards.Values)card.Effect.Text="";
    }
    public override void _Process(double delta)
    {
        effectTime=Math.Max(0,effectTime-delta);
        foreach(var card in unitCards.Values)
        {
            var color=card.Effect.Modulate;color.A=(float)Math.Min(1,effectTime*3);card.Effect.Modulate=color;
            if(effectTime==0)card.Effect.Text="";
        }
    }
    public override void _Notification(int what)
    {
        if(what==NotificationApplicationFocusOut && speaker!=null)speaker.Stop();
    }
    private void WindowClose()=>_=QuitCleanly();
    private async Task QuitCleanly(int code=0)
    {
        if(closing)return;closing=true;ResetFeedback();
        foreach(var button in FindChildren("*","Button",true,false).OfType<Button>())button.Disabled=true;
        // Audio stop is processed by the mixer thread. Let it release playback
        // references before managed/native resource teardown, including OS close.
        await ToSignal(GetTree().CreateTimer(.15),SceneTreeTimer.SignalName.Timeout);
        GetTree().Quit(code);
    }
    public override void _ExitTree()
    {
        GetTree().Root.CloseRequested-=WindowClose;
        speaker?.Stop();if(speaker!=null)speaker.Stream=null;
        foreach(var card in unitCards.Values)card.Portrait.Texture=null;
        foreach(var portrait in portraits)portrait.Dispose();portraits.Clear();
        portraitSheet?.Dispose();
        foreach(var cue in cues.Values)cue.Dispose();cues.Clear();
        foreach(var style in styles.Values)style.Dispose();styles.Clear();
    }
}
