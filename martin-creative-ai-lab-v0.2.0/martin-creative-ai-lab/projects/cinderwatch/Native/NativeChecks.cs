using Godot;
using Cinder.Core;
using Cinder.Checks;
using System.Text.Json;
namespace Cinder.Native;

public partial class Main
{
    private int checks;
    private void Require(bool value,string description) {checks++;if(!value)throw new InvalidOperationException(description);}
    private async Task Frame() => await ToSignal(GetTree(),SceneTree.SignalName.ProcessFrame);
    private async Task KeyboardEnter()
    {
        Input.ParseInputEvent(new InputEventKey {Keycode=Key.Enter,Pressed=true});await Frame();
        Input.ParseInputEvent(new InputEventKey {Keycode=Key.Enter,Pressed=false});await Frame();
    }
    private async Task Capture(string name)
    {
        for(var i=0;i<3;i++)await Frame();
        Require(forecast.GlobalPosition.Y+forecast.Size.Y<=confirm.GlobalPosition.Y,"Forecast overlaps confirmation");
        Require(modalText.Position.Y+modalText.Size.Y<begin.Position.Y,"Brief or tactics clips its button");
        Require(actionArea.GlobalPosition.Y+actionArea.Size.Y<=forecast.GlobalPosition.Y,"Scrollable actions overlap forecast");
        foreach(var label in FindChildren("*","Label",true,false).OfType<Label>().Where(l=>l.IsVisibleInTree()))
            Require(label.GetLineCount()*label.GetLineHeight()<=label.Size.Y,$"Clipped native label: {label.Text} ({label.GetLineCount()} x {label.GetLineHeight()} > {label.Size.Y})");
        if(captureDirectory==null || DisplayServer.GetName()=="headless")return;
        Directory.CreateDirectory(captureDirectory);await ToSignal(RenderingServer.Singleton,RenderingServer.SignalName.FramePostDraw);
        Require(GetViewport().GetTexture().GetImage().SavePng(Path.Combine(captureDirectory,name+".png"))==Error.Ok,"Native frame readback failed");
    }
    private async Task Verify()
    {
        try
        {
            await Frame();await PresentationChecks();await Capture("brief");
            Require(intro && confirm.Disabled && rules.Disabled,"Opening modal must disable underlying input");
            confirm.EmitSignal(BaseButton.SignalName.Pressed);Require(game.Journal.Count==0,"Modal accepted a hidden turn");
            begin.GrabFocus();await KeyboardEnter();
            Require(!intro && game.Journal.Count==0,"Keyboard entry spends no turn");await Capture("opening");
            var before=Probe.State(game);
            foreach(var c in game.Legal())
            {
                Require(choices.ContainsKey(c),"UI omitted a legal action");choices[c].EmitSignal(BaseButton.SignalName.Pressed);
                Require(Probe.State(game)==before && forecast.Text==game.Preview(c),"Native selection changed state or invented forecast");
            }
            var first=new Command(Kind.Pin,3);choices[first].GrabFocus();await KeyboardEnter();
            Require(selected==first && !confirm.Disabled,"Keyboard selection failed");await Capture("preview");
            confirm.GrabFocus();await KeyboardEnter();
            Require(game.Journal.Count==1 && game.Sparks==2 && game.Actor!.Id==0,"Keyboard confirmation must spend exactly one turn and spark");
            Require(lastCue=="pin" && unitCards[3].Effect.Text=="-4 HP" && unitCards[3].Detail.Text.Contains("PINNED"),"Pin feedback does not describe actual damage/cancellation");
            Require(GetViewport().GuiGetFocusOwner()==choices.Values.First(),"Accepted turn loses keyboard focus");
            await Capture("pin-feedback");
            Require(Probe.State(Journal.Load(savePath))==Probe.State(game),"Accepted native action did not autosave exact state");
            before=Probe.State(game);rules.EmitSignal(BaseButton.SignalName.Pressed);await Capture("tactics");
            resolve.EmitSignal(BaseButton.SignalName.Pressed);confirm.EmitSignal(BaseButton.SignalName.Pressed);await Frame();
            Require(Probe.State(game)==before && showingRules,"Tactics advanced play");begin.EmitSignal(BaseButton.SignalName.Pressed);
            var original=File.ReadAllText(savePath);File.WriteAllText(savePath,"{\"schema\":99}");resume.EmitSignal(BaseButton.SignalName.Pressed);
            Require(Probe.State(game)==before && notice.Text.Contains("rejected"),"Invalid resume lost live progress");
            File.WriteAllText(savePath,original);resume.EmitSignal(BaseButton.SignalName.Pressed);
            Require(Probe.State(game)==before && !intro,"Valid resume changed the next actor");
            var realPath=savePath;savePath=Path.GetDirectoryName(realPath)!;var chosen=game.Legal().First();choices[chosen].EmitSignal(BaseButton.SignalName.Pressed);confirm.EmitSignal(BaseButton.SignalName.Pressed);
            Require(game.Journal.Count==2 && notice.Text.Contains("failed"),"Failed save should preserve accepted memory progress");savePath=realPath;Save();
            var journeys=new List<object>();
            foreach(var a in new[]{"coolant","sparks"})foreach(var b in new[]{"plates","edge"})
            {
                restart.EmitSignal(BaseButton.SignalName.Pressed);begin.EmitSignal(BaseButton.SignalName.Pressed);
                Require(game.Journal.Count==0 && game.Kits==4 && game.Sparks==3,"New run retained previous effects");
                var seen=new HashSet<int>();
                for(var step=0;step<512 && game.Phase is Phase.Combat or Phase.Camp;step++)
                {
                    seen.Add(game.Stage);
                    if(game.Phase==Phase.Camp)
                    {
                        Require(salvage.Count==2,"Camp requires two real choices");
                        if(a=="coolant"&&b=="edge")await Capture("salvage-"+game.Stage);
                        var option=game.Stage==0?a:b;salvage[option].EmitSignal(BaseButton.SignalName.Pressed);
                    }
                    else if(game.Actor!.Hero)
                    {
                        var cmd=Probe.Choose(game);Require(choices.Keys.ToHashSet().SetEquals(game.Legal()),"Legal controls diverged during journey");
                        choices[cmd].EmitSignal(BaseButton.SignalName.Pressed);confirm.EmitSignal(BaseButton.SignalName.Pressed);
                    }
                    else
                    {
                        Require(resolve.Visible && forecast.Text.Contains(game.Intent(game.Actor.Id)),"Enemy preview omits announced threat");
                        resolve.EmitSignal(BaseButton.SignalName.Pressed);
                    }
                    await Frame();
                    if(a=="coolant"&&b=="edge"&&game.Stage==2&&game.Round==2&&game.Actor?.Id==1)await Capture("governor-gout");
                }
                Require(game.Phase==Phase.Victory && seen.SetEquals(new[]{0,1,2}),"Full native campaign not completed");
                Require(showEnding && modalText.Text.Contains("stretcher"),"Connected ending absent from native experience");
                Require(Probe.State(Journal.Load(savePath))==Probe.State(game),"Complete campaign save diverged");
                if(a=="coolant"&&b=="edge")await Capture("ending");
                journeys.Add(new{first=a,second=b,actions=game.Journal.Count,hp=game.Units.Where(u=>u.Hero).Select(u=>u.Hp).ToArray(),game.Kits,game.Sparks});
                begin.EmitSignal(BaseButton.SignalName.Pressed);
                Require(!showEnding && !confirm.Visible && !resolve.Visible,"Ending board offered combat actions");
            }
            // Deliberately allow the boss attack; the winning policies interrupt it.
            restart.EmitSignal(BaseButton.SignalName.Pressed);begin.EmitSignal(BaseButton.SignalName.Pressed);
            while(game.Stage<2 || game.Round<2)
            {
                if(game.Phase==Phase.Camp)salvage[game.Stage==0?"coolant":"edge"].EmitSignal(BaseButton.SignalName.Pressed);
                else if(game.Actor!.Hero) {choices[Probe.Choose(game)].EmitSignal(BaseButton.SignalName.Pressed);confirm.EmitSignal(BaseButton.SignalName.Pressed);}
                else resolve.EmitSignal(BaseButton.SignalName.Pressed);
                await Frame();
            }
            while(game.Actor!.Id!=2)
            {
                if(game.Actor.Hero) {choices[new(Kind.Guard)].EmitSignal(BaseButton.SignalName.Pressed);confirm.EmitSignal(BaseButton.SignalName.Pressed);}
                else resolve.EmitSignal(BaseButton.SignalName.Pressed);
                await Frame();
            }
            Require(game.Units.Count(u=>u.Hero&&u.Scorch>0)==3,"Native Gout did not apply three actual scorch states");
            choices[new(Kind.Guard)].EmitSignal(BaseButton.SignalName.Pressed);confirm.EmitSignal(BaseButton.SignalName.Pressed);await Frame();
            Require(game.Find(2).Shield==7 && game.Find(2).Scorch==1,"Shield and timed scorch are not both visible");
            foreach(var hero in game.Units.Where(u=>u.Hero))
            {
                var label=unitCards[hero.Id].Detail;
                GD.Print(JsonSerializer.Serialize(new{status=label.Text,height=label.Size.Y,lineHeight=label.GetLineHeight(),lines=label.GetLineCount(),visible=label.GetVisibleLineCount()},Journal.Json));
                Require(label.GetVisibleLineCount()==label.GetLineCount(),"Scorch status is clipped despite its stored text");
            }
            await Capture("scorch");
            restart.EmitSignal(BaseButton.SignalName.Pressed);begin.EmitSignal(BaseButton.SignalName.Pressed);
            for(var step=0;step<512 && game.Phase==Phase.Combat;step++)
            {
                if(game.Actor!.Hero) {choices[new(Kind.Guard)].EmitSignal(BaseButton.SignalName.Pressed);confirm.EmitSignal(BaseButton.SignalName.Pressed);}
                else resolve.EmitSignal(BaseButton.SignalName.Pressed);
                await Frame();
            }
            Require(game.Phase==Phase.Defeat && !confirm.Visible && !resolve.Visible,"Deadline loss cannot be inspected/restarted");await Capture("defeat");
            Require(unitCards.Count==6 && actionPool.Count<=32 && campPool.Count==4 && styles.Count<=20,"Presentation resources grow with campaign length");
            GD.Print(JsonSerializer.Serialize(new{nativeChecks=checks,journeys,deadline=game.Round,presentation=new{portraits=portraits.Count,cards=unitCards.Count,actions=actionPool.Count,camps=campPool.Count,styles=styles.Count,cuePlays},display=DisplayServer.GetName(),assessment="Scripted controls and implementing-agent visual review; not a human playtest"},Journal.Json));
            await QuitCleanly();
        }
        catch(Exception e) {GD.PrintErr(e.ToString());await QuitCleanly(1);}
    }
    private async Task PresentationChecks()
    {
        Require(portraits.Count==8 && portraitSheet.GetWidth()==1774 && portraitSheet.GetHeight()==887,"Actual eight-cell atlas did not load");
        for(var i=0;i<8;i++)Require(portraits[i].Region.End.X<=1774 && portraits[i].Region.End.Y<=887 && portraits[i].Atlas==portraitSheet,"Portrait region escapes the original sheet");
        Require(cues.Count==7 && cues.Values.All(c=>c.GetLength()>.1 && c.MixRate==44100),"Real action PCM streams are absent");
        var frozen=Probe.State(game);var cardsBefore=unitCards.Values.Select(c=>c.Panel.GetInstanceId()).ToArray();
        var buttonsBefore=actionPool.Values.Select(b=>b.GetInstanceId()).ToArray();var styleCount=styles.Count;
        for(var i=0;i<100;i++){selected=new(Kind.Guard);Refresh();await Frame();}
        Require(Probe.State(game)==frozen && unitCards.Values.Select(c=>c.Panel.GetInstanceId()).SequenceEqual(cardsBefore),"Selection rebuilds actor nodes or changes the campaign");
        Require(actionPool.Values.Select(b=>b.GetInstanceId()).SequenceEqual(buttonsBefore) && styles.Count==styleCount,"Selection rebuilds buttons/materials");selected=null;Refresh();
        var bus=AudioServer.BusCount;AudioServer.AddBus();AudioServer.SetBusName(bus,"CinderCapture");
        using var capture=new AudioEffectCapture();AudioServer.AddBusEffect(bus,capture);speaker.Bus="CinderCapture";
        PlayCue("steam");await ToSignal(GetTree().CreateTimer(.3),SceneTreeTimer.SignalName.Timeout);
        var samples=capture.GetBuffer(capture.GetFramesAvailable());var peak=samples.Select(v=>Math.Max(Math.Abs(v.X),Math.Abs(v.Y))).DefaultIfEmpty().Max();
        Require(samples.Length>4000 && peak>.01f && peak<1,"Actual AudioServer action capture is silent/clipped/incomplete");
        GD.Print(JsonSerializer.Serialize(new{audioCaptureFrames=samples.Length,peak},Journal.Json));
        sound.EmitSignal(BaseButton.SignalName.Pressed);var played=cuePlays;PlayCue("strike");
        Require(muted && !speaker.Playing && cuePlays==played,"Mute leaves an action sound active");
        sound.EmitSignal(BaseButton.SignalName.Pressed);Require(!muted && sound.Text=="Sound: on","Sound does not re-arm explicitly");
        speaker.Bus="Master";AudioServer.RemoveBus(bus);ResetFeedback();
    }
}
