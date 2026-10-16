using Godot;
using Cinder.Core;
using System.Text.Json;
namespace Cinder.Native;

public partial class Main
{
    private MenuButton runFiles=null!;
    private FileDialog fileDialog=null!;
    private ConfirmationDialog leaveDialog=null!;
    private RichTextLabel leaveText=null!;
    private enum FilePurpose { None, Copy, Open }
    private FilePurpose filePurpose;
    private Action? pendingLeave;
    private string leaveDescription="", lastWriteError="";
    private string? preservedJournal,lastCopyPath;
    private Control? leaveReturnFocus,fileReturnFocus;
    private bool HasUnpreserved=>game.Journal.Count>0&&Journal.Encode(game)!=preservedJournal;
    private bool ContinuityBlocked=>pendingLeave!=null||filePurpose!=FilePurpose.None;

    private void BuildRunFiles()
    {
        runFiles=Place(new MenuButton {Text="Run files",FocusMode=FocusModeEnum.All},this,977,24,125,40);
        runFiles.AddThemeFontSizeOverride("font_size",16);runFiles.AddThemeColorOverride("font_color",Paper);
        runFiles.AddThemeStyleboxOverride("normal",Style(new("#193139"),new("#38525a")));
        runFiles.AddThemeStyleboxOverride("hover",Style(new("#29474e"),Teal));
        runFiles.AddThemeStyleboxOverride("focus",Style(new Color(0,0,0,0),Teal));
        runFiles.GetPopup().AddItem("Save recovery copy…",0);
        runFiles.GetPopup().AddItem("Open run…",1);
        runFiles.GetPopup().IdPressed+=OpenRunFiles;
        fileDialog=new FileDialog {Title="Cinderwatch run",Access=FileDialog.AccessEnum.Filesystem,
            Filters=new[]{"*.json ; Cinderwatch run"},UseNativeDialog=false,Exclusive=true,Transient=true};
        AddChild(fileDialog);fileDialog.FileSelected+=FileChosen;fileDialog.Canceled+=CancelFile;
        leaveDialog=new ConfirmationDialog {Title="Keep this run before leaving",OkButtonText="Leave without saving",
            CancelButtonText="Keep this run",Exclusive=true,Transient=true};
        AddChild(leaveDialog);
        // A bounded scrolling body avoids wrapped Label minimum-height feedback.
        leaveText=new RichTextLabel {CustomMinimumSize=new(800,270),ScrollActive=true,SelectionEnabled=true,FocusMode=FocusModeEnum.All};
        leaveText.AddThemeFontSizeOverride("normal_font_size",17);leaveDialog.AddChild(leaveText);
        leaveDialog.AddButton("Retry autosave",true,"retry");
        leaveDialog.AddButton("Save recovery copy…",true,"copy");
        leaveDialog.Confirmed+=DiscardAndLeave;leaveDialog.Canceled+=CancelLeave;
        leaveDialog.CustomAction+=RecoveryAction;
    }
    private void RefreshRunFiles()
    {
        var otherModal=showingRules||showEnding||showResponse;
        runFiles.Disabled=otherModal||ContinuityBlocked;
        resume.Disabled=otherModal||ContinuityBlocked;
        runFiles.GetPopup().SetItemDisabled(0,game.Journal.Count==0);
        runFiles.TooltipText="Portable recovery copies use the existing action journal. Opening a copy keeps its source file unchanged.";
        begin.Disabled=ContinuityBlocked;
        if(ContinuityBlocked)
            foreach(var b in choices.Values.Concat(salvage.Values).Concat(new[]{confirm,resolve,restart,resume,save,rules,inspect,runFiles}))b.Disabled=true;
    }
    private static bool FileFailure(Exception e)=>e is IOException or UnauthorizedAccessException or JsonException or InvalidDataException or ArgumentException;
    private void Notify(string text,string? detail=null) {notice.Text=text;notice.TooltipText=detail??text;}
    private bool PersistRun(string path,bool copy)
    {
        try
        {
            if(copy&&string.Equals(Path.GetFullPath(path),Path.GetFullPath(savePath),
                OperatingSystem.IsWindows()?StringComparison.OrdinalIgnoreCase:StringComparison.Ordinal))
                throw new IOException("Choose a different file for the recovery copy; Save retries the autosave.");
            var accepted=Journal.Encode(game);
            Journal.Store(game,path);
            if(Journal.Encode(Journal.Load(path))!=accepted)throw new IOException("Written journal did not replay the current run.");
            preservedJournal=accepted;lastWriteError="";
            if(copy)lastCopyPath=Path.GetFullPath(path);
            Notify(copy?"Recovery copy verified. Current run continues; future turns use the autosave.":
                "Saved accepted actions. Resume restores the exact next turn.",
                $"Verified journal: {path}\nAutosave: {savePath}");
            return true;
        }
        catch(Exception e)when(FileFailure(e))
        {
            lastWriteError=e.Message;
            Notify((copy?"Recovery copy failed":"Save failed")+"; current progress remains in memory. Use Run files to preserve it elsewhere.",e.Message);
            return false;
        }
    }
    private void Save() {if(!ContinuityBlocked&&!intro&&!showingRules&&!showEnding&&!showResponse)PersistRun(savePath,false);}
    private void NewRun()
    {
        if(ContinuityBlocked||intro||showingRules||showEnding||showResponse)return;
        RequestLeave("Start a new run",()=>
        {
            ResetFeedback();game=new();preservedJournal=null;selected=null;intro=true;
            showingRules=false;showEnding=false;showResponse=false;
            Notify("New run is in memory. Its first accepted turn replaces the autosave. Use Run files to keep separate recovery copies.");Refresh();
        });
    }
    private void Load()
    {
        if(ContinuityBlocked||showingRules||showEnding||showResponse)return;
        ReadRun(savePath,"Resume the autosave");
    }
    private void ReadRun(string path,string description)
    {
        // Validate a candidate before asking the player to leave live progress.
        try
        {
            _=Journal.Load(path);
            RequestLeave(description,()=>
            {
                // The file may have changed while the leave decision was open.
                try
                {
                    var candidate=Journal.Load(path);
                    ResetFeedback();game=candidate;preservedJournal=Journal.Encode(game);selected=null;
                    intro=false;showingRules=false;showResponse=false;showEnding=game.Phase==Phase.Victory;
                    Notify("Resumed the exact next turn and supplies. Future accepted turns use the autosave.",
                        $"Opened: {path}\nAutosave: {savePath}");Refresh();
                }
                catch(Exception e)when(FileFailure(e)) {Notify("Resume rejected; current run preserved. Choose a valid Cinderwatch journal.",e.Message);Refresh();}
            });
        }
        catch(Exception e)when(FileFailure(e)) {Notify("Resume rejected; current run preserved. Choose a valid Cinderwatch journal.",e.Message);Refresh();}
    }
    private void RequestQuit()
    {
        if(ContinuityBlocked||closing)return;
        RequestLeave("Quit Cinderwatch",()=>_=QuitCleanly());
    }
    private void RequestLeave(string description,Action action)
    {
        if(!HasUnpreserved){action();return;}
        pendingLeave=action;leaveDescription=description;leaveReturnFocus=GetViewport().GuiGetFocusOwner();
        speaker.Stop();ShowLeave();
    }
    private void ShowLeave()
    {
        var next=game.Actor?.Name??(game.Phase==Phase.Camp?"salvage choice":game.Phase.ToString());
        leaveText.Text=$"{leaveDescription} would leave accepted progress that has not been preserved.\n\n"+
            $"Current run: {game.Place}, round {game.Round}; {game.Journal.Count} accepted actions. Next: {next}.\n\n"+
            "Keep this run, retry the autosave, or save a recovery copy to another file. A successful save returns to this run; request navigation again when ready."+
            (lastWriteError.Length>0?"\n\nLast write failed: "+(lastWriteError.Length>220?lastWriteError[..220]+"…":lastWriteError):"");
        leaveText.TooltipText=lastWriteError;
        Refresh();leaveDialog.Hide();leaveDialog.PopupCentered(new(820,360));leaveDialog.GetCancelButton().GrabFocus();
    }
    private void CancelLeave()
    {
        pendingLeave=null;leaveDialog.Hide();Refresh();
        if(leaveReturnFocus?.IsInsideTree()==true&&!leaveReturnFocus.IsQueuedForDeletion())leaveReturnFocus.GrabFocus();
    }
    private void DiscardAndLeave()
    {
        var action=pendingLeave;pendingLeave=null;leaveDialog.Hide();action?.Invoke();
    }
    private void RecoveryAction(StringName action)
    {
        if(pendingLeave==null)return;
        if(action=="retry")
        {
            if(PersistRun(savePath,false))CancelLeave();else ShowLeave();
        }
        else if(action=="copy") {leaveDialog.Hide();ShowFile(FilePurpose.Copy);}
    }
    private void OpenRunFiles(long id)
    {
        if(ContinuityBlocked||showingRules||showEnding||showResponse)return;
        if(id==0&&game.Journal.Count>0)ShowFile(FilePurpose.Copy);
        else if(id==1)ShowFile(FilePurpose.Open);
    }
    private void ShowFile(FilePurpose purpose)
    {
        filePurpose=purpose;fileReturnFocus=GetViewport().GuiGetFocusOwner();speaker.Stop();
        fileDialog.FileMode=purpose==FilePurpose.Copy?FileDialog.FileModeEnum.SaveFile:FileDialog.FileModeEnum.OpenFile;
        fileDialog.Title=purpose==FilePurpose.Copy?"Save a Cinderwatch recovery copy":"Open a Cinderwatch run";
        var preferred=purpose==FilePurpose.Open&&lastCopyPath!=null?lastCopyPath:Path.GetFullPath(savePath);
        var directory=Path.GetDirectoryName(preferred);
        fileDialog.CurrentDir=Directory.Exists(directory)?directory!:System.Environment.CurrentDirectory;
        fileDialog.CurrentFile=purpose==FilePurpose.Copy?"cinderwatch-recovery.json":lastCopyPath!=null?Path.GetFileName(preferred):"";
        Refresh();fileDialog.PopupCentered(new(1000,620));
    }
    private void CancelFile()
    {
        filePurpose=FilePurpose.None;fileDialog.Hide();
        if(pendingLeave!=null)ShowLeave();
        else {Refresh();if(fileReturnFocus?.IsInsideTree()==true)fileReturnFocus.GrabFocus();}
    }
    private void FileChosen(string path)
    {
        var purpose=filePurpose;filePurpose=FilePurpose.None;fileDialog.Hide();
        if(purpose==FilePurpose.Copy)
        {
            if(PersistRun(path,true)) {if(pendingLeave!=null)CancelLeave();else Refresh();}
            else if(pendingLeave!=null)ShowLeave();else Refresh();
        }
        else if(purpose==FilePurpose.Open)ReadRun(path,"Open the selected run");
    }
}
