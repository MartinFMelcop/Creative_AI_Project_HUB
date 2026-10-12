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
            await Frame();await Capture("brief");
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
            await Capture("scorch");
            restart.EmitSignal(BaseButton.SignalName.Pressed);begin.EmitSignal(BaseButton.SignalName.Pressed);
            for(var step=0;step<512 && game.Phase==Phase.Combat;step++)
            {
                if(game.Actor!.Hero) {choices[new(Kind.Guard)].EmitSignal(BaseButton.SignalName.Pressed);confirm.EmitSignal(BaseButton.SignalName.Pressed);}
                else resolve.EmitSignal(BaseButton.SignalName.Pressed);
                await Frame();
            }
            Require(game.Phase==Phase.Defeat && !confirm.Visible && !resolve.Visible,"Deadline loss cannot be inspected/restarted");await Capture("defeat");
            GD.Print(JsonSerializer.Serialize(new{nativeChecks=checks,journeys,deadline=game.Round,display=DisplayServer.GetName(),assessment="Scripted controls and implementing-agent visual review; not a human playtest"},Journal.Json));
            GetTree().Quit();
        }
        catch(Exception e) {GD.PrintErr(e.ToString());GetTree().Quit(1);}
    }
}
