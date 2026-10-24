using System;
using System.IO;
using System.Linq;
using System.Text.Json;
namespace NorthStar.AuthoredScene;

// Transport adapter: gameplay still belongs to the original RequestExpedition.
public sealed class SceneSession : IDisposable
{
    private readonly Room? transient;
    private readonly RequestJournal? journal;
    private object? observation;
    public SceneSession(string? path=null,bool create=false)
    { if(path==null)transient=new Room();else {journal=new RequestJournal(path,create);observation=Observe(journal.Snapshot());} }
    private static object Observe(JournalReceipt r)=>new {
        sequence=r.revision,command=r.command,accepted=r.accepted,text=r.text,state=r.state,
        continuity=new {mode="local",run_id=r.run_id,revision=r.revision,day=r.day,
            status=r.blocked?"blocked":"saved",duplicate=r.duplicate,original_revision=r.original_revision,reason=r.reason}
    };
    public object Snapshot()=>journal==null?transient!.Snapshot():journal.Blocked?Observe(journal.Snapshot()):observation!;
    public object Execute(JsonElement document)
    {
        if(journal==null)return transient!.Execute(document);
        if(document.ValueKind!=JsonValueKind.Object)throw new ArgumentException("Object required.");
        var fields=document.EnumerateObject().ToArray();
        string[] names={"command","request_id","revision","run_id"};
        if(fields.Length!=4 || fields.Select(x=>x.Name).Distinct(StringComparer.Ordinal).Count()!=4 || fields.Any(x=>!names.Contains(x.Name)))throw new ArgumentException("Exact durable command envelope required.");
        string Text(string name)=>document.GetProperty(name).ValueKind==JsonValueKind.String?document.GetProperty(name).GetString()!:throw new ArgumentException("String required.");
        if(!document.GetProperty("revision").TryGetInt32(out int revision)||revision<0)throw new ArgumentException("Bounded revision required.");
        try{observation=Observe(journal.Submit(Text("run_id"),Text("request_id"),revision,Text("command")));return observation;}
        catch(IOException error){throw new SceneStorageException("Local save outcome is uncertain; close and reopen this validated run.",error);}
        catch(UnauthorizedAccessException error){throw new SceneStorageException("Local save could not be confirmed; close and reopen this validated run.",error);}
    }
    public void Dispose()=>journal?.Dispose();
}
public sealed class SceneStorageException : IOException
{ public SceneStorageException(string text,Exception inner):base(text,inner){} }
