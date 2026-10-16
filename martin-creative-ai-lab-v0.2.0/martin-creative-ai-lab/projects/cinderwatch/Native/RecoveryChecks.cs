using Godot;
using Cinder.Core;
using Cinder.Checks;
namespace Cinder.Native;

public partial class Main
{
    private async Task RecoveryChecks()
    {
        var realPath=savePath;
        var blockedPath=Path.GetDirectoryName(realPath)!;
        var scratch=Path.Combine(blockedPath,"cinderwatch-recovery-"+Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(scratch);
        var copyPath=Path.Combine(scratch,"accepted-run.json");
        var invalidPath=Path.Combine(scratch,"invalid.json");
        var oversizedPath=Path.Combine(scratch,"oversized.json");
        var initialChecks=checks;

        void Advance()
        {
            var count=game.Journal.Count;
            if(game.Actor is {Hero:true})
            {
                choices[new Command(Kind.Guard)].EmitSignal(BaseButton.SignalName.Pressed);
                confirm.EmitSignal(BaseButton.SignalName.Pressed);
            }
            else resolve.EmitSignal(BaseButton.SignalName.Pressed);
            Require(game.Journal.Count==count+1,"Recovery fixture did not accept exactly one real turn");
        }
        void GuardedInputs(string frozen)
        {
            var selection=selected;
            Require(restart.Disabled&&resume.Disabled&&confirm.Disabled&&resolve.Disabled&&inspect.Disabled&&runFiles.Disabled,
                "Leave guard or file chooser leaves underlying controls enabled");
            foreach(var control in choices.Values.Concat(salvage.Values).ToArray())control.EmitSignal(BaseButton.SignalName.Pressed);
            Require(selected==selection,"Hidden selection changed the selected action through the recovery boundary");
            foreach(var control in new[]{confirm,resolve,restart,resume,save,rules,inspect,begin})control.EmitSignal(BaseButton.SignalName.Pressed);
            Require(Probe.State(game)==frozen&&selected==selection&&!intro&&!showingRules&&!showResponse,
                "Hidden game controls changed the run through the recovery input boundary");
        }
        void Menu(long id)=>runFiles.GetPopup().EmitSignal(PopupMenu.SignalName.IdPressed,id);
        void Custom(string action)=>leaveDialog.EmitSignal(AcceptDialog.SignalName.CustomAction,action);
        async Task SelectedFile(string path)
        {
            // A real selection follows a visible chooser, never its opening frame.
            await Frame();
            Require(fileDialog.Visible&&filePurpose!=FilePurpose.None,"File selection requires the visible recovery chooser");
            // FileDialog hides before emitting this signal in ordinary selection.
            fileDialog.Hide();fileDialog.EmitSignal(FileDialog.SignalName.FileSelected,path);
        }
        async Task CancelGuard()
        {
            leaveDialog.GetCancelButton().GrabFocus();await KeyboardEnter();
            Require(!leaveDialog.Visible&&pendingLeave==null,"Keep current run did not cancel the pending departure");
        }

        try
        {
            restart.EmitSignal(BaseButton.SignalName.Pressed);begin.EmitSignal(BaseButton.SignalName.Pressed);
            choices[new Command(Kind.Pin,3)].EmitSignal(BaseButton.SignalName.Pressed);confirm.EmitSignal(BaseButton.SignalName.Pressed);
            var savedOne=Probe.State(game);var originalBytes=File.ReadAllText(realPath);
            Require(game.Journal.Count==1&&!HasUnpreserved&&Probe.State(Journal.Load(realPath))==savedOne,
                "Recovery fixture did not preserve its first accepted turn");
            Menu(0);await SelectedFile(realPath);await Frame();
            Require(!fileDialog.Visible&&!leaveDialog.Visible&&!HasUnpreserved&&Probe.State(game)==savedOne&&savePath==realPath&&
                File.ReadAllText(realPath)==originalBytes&&notice.TooltipText.Contains("different file",StringComparison.OrdinalIgnoreCase),
                "Recovery copy at the primary path was not rejected before touching the saved journal");
            savePath=blockedPath;Advance();var acceptedTwo=Probe.State(game);
            Require(game.Journal.Count==2&&HasUnpreserved&&notice.Text.Contains("failed",StringComparison.OrdinalIgnoreCase),
                "Failed autosave did not distinguish accepted memory from the saved first turn");
            Require(File.ReadAllText(realPath)==originalBytes,"Failed autosave changed the older usable journal");

            restart.GrabFocus();await KeyboardEnter();
            Require(leaveDialog.Visible&&pendingLeave!=null&&Probe.State(game)==acceptedTwo,
                "New run replaced accepted unsaved progress without asking");
            GuardedInputs(acceptedTwo);await Capture("recovery-leave-guard");
            await CancelGuard();
            Require(HasUnpreserved&&Probe.State(game)==acceptedTwo,"Keep current run lost accepted progress");

            restart.EmitSignal(BaseButton.SignalName.Pressed);Custom("retry");
            Require(leaveDialog.Visible&&pendingLeave!=null&&HasUnpreserved&&Probe.State(game)==acceptedTwo,
                "Failed retry left the guard or discarded its current run");
            Custom("copy");await Frame();
            Require(fileDialog.Visible&&!leaveDialog.Visible&&Probe.State(game)==acceptedTwo,
                "Save copy did not open a chooser without replacing the run");
            GuardedInputs(acceptedTwo);
            fileDialog.GetCancelButton().EmitSignal(BaseButton.SignalName.Pressed);await Frame();
            Require(!fileDialog.Visible&&leaveDialog.Visible&&HasUnpreserved&&Probe.State(game)==acceptedTwo,
                "Cancelling Save copy did not return to the unresolved leave guard");

            Custom("copy");await SelectedFile(blockedPath);await Frame();
            Require(!fileDialog.Visible&&leaveDialog.Visible&&HasUnpreserved&&Probe.State(game)==acceptedTwo,
                "A failed alternate copy silently allowed the queued departure");
            Require(File.ReadAllText(realPath)==originalBytes,"Failed alternate copy altered the original save");
            Custom("copy");await SelectedFile(copyPath);await Frame();
            Require(!fileDialog.Visible&&!leaveDialog.Visible&&pendingLeave==null&&!HasUnpreserved,
                "Verified copy did not clear the warning and cancel the queued new run");
            Require(Probe.State(game)==acceptedTwo&&Probe.State(Journal.Load(copyPath))==acceptedTwo&&savePath==blockedPath,
                "Save copy changed the current run, next turn or primary autosave destination");
            Require(File.ReadAllText(realPath)==originalBytes,"Save copy replaced the earlier primary journal");
            var copyBytes=File.ReadAllText(copyPath);await Capture("recovery-copy-preserved");

            Advance();var acceptedThree=Probe.State(game);
            Require(game.Journal.Count==3&&HasUnpreserved&&File.ReadAllText(copyPath)==copyBytes,
                "A turn after Save copy was incorrectly treated as already preserved");
            Menu(1);await SelectedFile(copyPath);await Frame();
            Require(leaveDialog.Visible&&Probe.State(game)==acceptedThree,"Opening a valid older copy replaced unsaved work without asking");
            await CancelGuard();

            Menu(1);await SelectedFile(copyPath);await Frame();
            Require(leaveDialog.Visible&&Probe.State(game)==acceptedThree,$"Changed-source fixture did not wait at the leave guard: visible={leaveDialog.Visible}, dirty={HasUnpreserved}, actions={game.Journal.Count}, pending={pendingLeave!=null}, file={filePurpose}, notice={notice.Text}");
            File.WriteAllText(copyPath,"{\"schema\":99}");
            var changedBytes=File.ReadAllText(copyPath);
            leaveDialog.GetOkButton().EmitSignal(BaseButton.SignalName.Pressed);await Frame();
            Require(!leaveDialog.Visible&&pendingLeave==null&&HasUnpreserved&&Probe.State(game)==acceptedThree&&
                File.ReadAllText(copyPath)==changedBytes&&File.ReadAllText(realPath)==originalBytes&&
                notice.Text.Contains("rejected",StringComparison.OrdinalIgnoreCase),
                "A candidate changed after inspection replaced live progress or was silently rewritten");
            File.WriteAllText(copyPath,copyBytes);

            File.WriteAllText(invalidPath,"{\"schema\":99}");
            Menu(1);await SelectedFile(invalidPath);await Frame();
            Require(!fileDialog.Visible&&!leaveDialog.Visible&&Probe.State(game)==acceptedThree&&HasUnpreserved,
                "Invalid Open run lost live progress or requested permission to replace it");
            File.WriteAllText(oversizedPath,new string(' ',1_000_001));
            Menu(1);await SelectedFile(oversizedPath);await Frame();
            Require(!fileDialog.Visible&&!leaveDialog.Visible&&Probe.State(game)==acceptedThree&&HasUnpreserved,
                "Oversized Open run lost live progress or requested permission to replace it");

            savePath=realPath;resume.EmitSignal(BaseButton.SignalName.Pressed);await Frame();
            Require(leaveDialog.Visible&&Probe.State(game)==acceptedThree,"Resume silently discarded accepted unsaved turns");
            await CancelGuard();
            Require(Probe.State(game)==acceptedThree&&File.ReadAllText(realPath)==originalBytes,"Cancelled Resume changed memory or its older save");
            resume.EmitSignal(BaseButton.SignalName.Pressed);leaveDialog.GetOkButton().EmitSignal(BaseButton.SignalName.Pressed);await Frame();
            Require(!leaveDialog.Visible&&Probe.State(game)==savedOne&&!HasUnpreserved,
                "Explicit Leave without saving did not resume the validated older journal");
            Require(File.ReadAllText(realPath)==originalBytes&&File.ReadAllText(copyPath)==copyBytes,
                "Explicit Resume changed either source journal");

            Menu(1);await SelectedFile(copyPath);await Frame();
            Require(Probe.State(game)==acceptedTwo&&!HasUnpreserved&&savePath==realPath,
                "Open run did not restore the selected copy while retaining the primary destination");
            Require(File.ReadAllText(realPath)==originalBytes&&File.ReadAllText(copyPath)==copyBytes,
                "Opening the selected copy rewrote a source before any accepted turn");
            Advance();
            Require(game.Journal.Count==3&&!HasUnpreserved&&Probe.State(Journal.Load(realPath))==Probe.State(game)&&File.ReadAllText(copyPath)==copyBytes,
                "Play after Open run did not autosave to the primary path while preserving its source copy");

            savePath=blockedPath;Advance();var acceptedFour=Probe.State(game);
            Require(HasUnpreserved&&game.Journal.Count==4,"Quit fixture did not contain a newly unsaved accepted turn");
            GetTree().Root.EmitSignal(Window.SignalName.CloseRequested);await Frame();
            Require(leaveDialog.Visible&&pendingLeave!=null&&Probe.State(game)==acceptedFour,
                "Window close failed to protect newly accepted unsaved progress");
            await CancelGuard();
            Require(Probe.State(game)==acceptedFour&&HasUnpreserved,"Cancelling window close lost its current turn");
            restart.EmitSignal(BaseButton.SignalName.Pressed);savePath=realPath;Custom("retry");await Frame();
            Require(!leaveDialog.Visible&&pendingLeave==null&&!HasUnpreserved&&Probe.State(game)==acceptedFour&&Probe.State(Journal.Load(realPath))==acceptedFour,
                "Successful primary retry executed the queued new run or failed to preserve the current one");
            Require(File.ReadAllText(copyPath)==copyBytes,"Primary retry overwrote the independently retained copy");

            GD.Print(System.Text.Json.JsonSerializer.Serialize(new{recoveryChecks=checks-initialChecks,
                savedActions=1,failedAcceptedActions=2,copyActions=2,reloadedNextAutosaveActions=3,
                quitProtectedActions=4,sourceCopyUnchanged=true,
                assessment="Native signals and keyboard execution; not independent player feedback"},Journal.Json));
        }
        finally
        {
            savePath=realPath;
            if(Directory.Exists(scratch))Directory.Delete(scratch,true);
        }
        restart.EmitSignal(BaseButton.SignalName.Pressed);begin.EmitSignal(BaseButton.SignalName.Pressed);
        save.EmitSignal(BaseButton.SignalName.Pressed);
        Require(!intro&&!leaveDialog.Visible&&!fileDialog.Visible&&game.Journal.Count==0&&!HasUnpreserved,
            "Recovery checks did not return a fresh entered run to the existing gameplay journey");
    }
}
