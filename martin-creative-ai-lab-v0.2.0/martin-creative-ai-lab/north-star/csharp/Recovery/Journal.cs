using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using NorthStar.Domain;
using NorthStar.Forge;
using NorthStar.Loadout;

namespace NorthStar.Recovery
{
    public sealed record RecoveryCommand(string Op,string? A=null,string? B=null,long? Number=null,string?[]? Slots=null)
    {
        public static RecoveryCommand Parse(JsonElement e)
        {
            string op=Protocol.Text(e.GetProperty("op"));
            switch(op)
            {
                case "craft": Protocol.Fields(e,"op","recipe");return new(op,Protocol.Text(e.GetProperty("recipe")));
                case "begin": Protocol.Fields(e,"op","rig");return new(op,Protocol.Text(e.GetProperty("rig")));
                case "allocate": Protocol.Fields(e,"op","axis","points");return new(op,Protocol.Text(e.GetProperty("axis")),Number:Protocol.Integer(e.GetProperty("points")));
                case "replace":
                    Protocol.Fields(e,"op","class_id","background_id","slots");var rows=Protocol.Array(e.GetProperty("slots"),4);if(rows.Length!=4)throw new FormatException("Four slots required.");
                    return new(op,Protocol.Text(e.GetProperty("class_id")),Protocol.Text(e.GetProperty("background_id")),Slots:rows.Select(x=>x.ValueKind==JsonValueKind.Null?null:Protocol.Text(x)).ToArray());
                case "slot":Protocol.Fields(e,"op","slot");return new(op,Number:Protocol.Integer(e.GetProperty("slot")));
                case "walk":case "wait":Protocol.Fields(e,"op");return new(op);
                default:throw new FormatException("Unsupported command.");
            }
        }
        public string Canonical()=>Op switch {
            "craft"=>JsonSerializer.Serialize(new{op=Op,recipe=A}),"begin"=>JsonSerializer.Serialize(new{op=Op,rig=A}),
            "allocate"=>JsonSerializer.Serialize(new{op=Op,axis=A,points=Number}),
            "replace"=>JsonSerializer.Serialize(new{op=Op,class_id=A,background_id=B,slots=Slots}),
            "slot"=>JsonSerializer.Serialize(new{op=Op,slot=Number}),"walk" or "wait"=>JsonSerializer.Serialize(new{op=Op}),
            _=>throw new FormatException("Unsupported command.")};
        internal RecoveryCommand Normalized()
        {using var doc=JsonDocument.Parse(Canonical());return Parse(doc.RootElement);}
        internal bool Apply(PreparedExpedition game,string requestId)
        {
            switch(Op)
            {
                case "craft":return game.Craft(requestId,A!).Applied;
                case "begin":return A switch {"plate"=>game.Begin(Rig.Plate),"trail"=>game.Begin(Rig.Trail),"unprepared"=>game.Begin(Rig.Unprepared),_=>false};
                case "allocate":return A switch {"focus"=>game.Allocate(Allocation.Focus,Number!.Value),"vitality"=>game.Allocate(Allocation.Vitality,Number!.Value),_=>false};
                case "replace":return game.Replace(A!,B!,Slots!);
                case "slot":return Number>=0&&Number<4&&game.UseSlot((int)Number.Value);
                case "walk":return game.Walk();case "wait":return game.Wait();default:return false;
            }
        }
    }
    public static class Protocol
    {
        public static void Fields(JsonElement e,params string[] names)
        {if(e.ValueKind!=JsonValueKind.Object)throw new FormatException("Expected object.");var seen=new HashSet<string>(StringComparer.Ordinal);foreach(var p in e.EnumerateObject())if(!names.Contains(p.Name)||!seen.Add(p.Name))throw new FormatException("Unknown/duplicate field.");if(seen.Count!=names.Length)throw new FormatException("Missing field.");}
        public static string Text(JsonElement e){if(e.ValueKind!=JsonValueKind.String||e.GetString()!.Length>256)throw new FormatException("Expected bounded string.");return e.GetString()!;}
        public static long Integer(JsonElement e){if(e.ValueKind!=JsonValueKind.Number||!e.TryGetInt64(out long n))throw new FormatException("Expected integer.");return n;}
        public static JsonElement[] Array(JsonElement e,int bound){if(e.ValueKind!=JsonValueKind.Array||e.GetArrayLength()>bound)throw new FormatException("Expected bounded array.");return e.EnumerateArray().ToArray();}
        public static void Id(string value){if(value.Length<1||value.Length>64||value.Any(c=>!(c>='a'&&c<='z'||c>='A'&&c<='Z'||c>='0'&&c<='9'||c=='_'||c=='-')))throw new FormatException("Invalid request identity.");}
        public static string Hash(string text)=>Convert.ToHexStringLower(SHA256.HashData(Encoding.UTF8.GetBytes(text)));
    }
    internal sealed record Entry(int Sequence,string RequestId,RecoveryCommand Command,string StateHash);
    public sealed record Receipt(bool Accepted,bool Duplicate,int OriginalRevision,int CurrentRevision,string Reason,JsonElement State);
    /// <summary>Exclusive local writer and replay journal; not account trust or distributed durability.</summary>
    public sealed class RecoverySession:IDisposable
    {
        public const int MaximumEntries=4096;
        public const int MaximumBytes=2*1024*1024;
        private readonly string path;
        private readonly FileStream lease;
        private List<Entry> entries=new();
        private PreparedExpedition game=new();
        private bool blocked;
        private bool disposed;
        private readonly object ownership=new();
        public static string RulesIdentity {get;}=RulesHash();
        public int Revision=>entries.Count;
        public string StateJson=>JsonSerializer.Serialize(game.Snapshot());
        public JsonElement State=>JsonSerializer.SerializeToElement(game.Snapshot());
        public bool Blocked=>blocked;
        public string Advice=>game.Active?game.Threat+" Need position "+game.RequiredPosition+" by beat "+game.MaximumBeats+". Use an equipped slot, Walk or Wait.":game.Complete?"Expedition complete; accepted results are preserved.":"Prepare explicit identity/slots, craft finite supplies, allocate earned points or enter an encounter.";
        private static string RulesHash()
        {
            var assembly=typeof(RecoverySession).Assembly;var text=new StringBuilder("north-star-recovery-rules-v1\n");
            var resources=assembly.GetManifestResourceNames();if(resources.Length<6)throw new InvalidOperationException("Gameplay source resources are missing.");
            foreach(string name in resources.OrderBy(x=>x,StringComparer.Ordinal))
            {using var stream=assembly.GetManifestResourceStream(name)!;using var reader=new StreamReader(stream);text.Append(name).Append('\n').Append(Protocol.Hash(reader.ReadToEnd())).Append('\n');}
            return Protocol.Hash(text.ToString());
        }
        public RecoverySession(string filename,bool create)
        {
            path=Path.GetFullPath(filename);Directory.CreateDirectory(Path.GetDirectoryName(path)!);
            RegularOrAbsent(path);RegularOrAbsent(path+".lock");
            lease=new FileStream(path+".lock",FileMode.OpenOrCreate,FileAccess.ReadWrite,FileShare.None);
            try
            {
                if(create)
                {if(Exists(path))throw new IOException("Existing run is never overwritten by new.");Write(entries,false,null);}
                else
                {if(!File.Exists(path))throw new IOException("Run is missing; open never creates a replacement.");Read();}
            }
            catch{lease.Dispose();throw;}
        }
        private static void RegularOrAbsent(string p)
        {if(Exists(p)&&(File.GetAttributes(p)&(FileAttributes.Directory|FileAttributes.ReparsePoint))!=0)throw new IOException("Run and lease must be regular, unlinked files.");}
        private static bool Exists(string p){try{File.GetAttributes(p);return true;}catch(FileNotFoundException){return false;}catch(DirectoryNotFoundException){return false;}}
        private static object[] Body(IEnumerable<Entry> rows)=>rows.Select(e=>(object)new{sequence=e.Sequence,request_id=e.RequestId,command=JsonSerializer.Deserialize<JsonElement>(e.Command.Canonical()),state_hash=e.StateHash}).ToArray();
        private static string Payload(IEnumerable<Entry> rows)=>JsonSerializer.Serialize(new{schema_version=1,rules_id=RulesIdentity,entries=Body(rows)});
        private static string Encode(IEnumerable<Entry> rows)=>JsonSerializer.Serialize(new{schema_version=1,rules_id=RulesIdentity,entries=Body(rows),checksum=Protocol.Hash(Payload(rows))});
        private static PreparedExpedition Replay(IEnumerable<Entry> rows)
        {
            var candidate=new PreparedExpedition();var ids=new HashSet<string>(StringComparer.Ordinal);int sequence=0;
            foreach(var e in rows)
            {
                Protocol.Id(e.RequestId);
                if(e.Sequence!=++sequence||!ids.Add(e.RequestId)||!e.Command.Apply(candidate,e.RequestId)||Protocol.Hash(JsonSerializer.Serialize(candidate.Snapshot()))!=e.StateHash)throw new InvalidDataException("Illegal, reordered or incompatible journal entry.");
            }
            return candidate;
        }
        private void Read()
        {
            var info=new FileInfo(path);if(info.Length>MaximumBytes)throw new InvalidDataException("Run exceeds size limit.");
            using var doc=JsonDocument.Parse(File.ReadAllText(path),new JsonDocumentOptions{MaxDepth=16});var root=doc.RootElement;
            Protocol.Fields(root,"schema_version","rules_id","entries","checksum");
            if(Protocol.Integer(root.GetProperty("schema_version"))!=1||Protocol.Text(root.GetProperty("rules_id"))!=RulesIdentity)throw new InvalidDataException("Unsupported run schema/rules; explicit migration required.");
            var list=new List<Entry>();foreach(var row in Protocol.Array(root.GetProperty("entries"),MaximumEntries))
            {Protocol.Fields(row,"sequence","request_id","command","state_hash");long n=Protocol.Integer(row.GetProperty("sequence"));if(n<1||n>MaximumEntries)throw new FormatException("Invalid sequence.");list.Add(new((int)n,Protocol.Text(row.GetProperty("request_id")),RecoveryCommand.Parse(row.GetProperty("command")),Protocol.Text(row.GetProperty("state_hash"))));}
            if(Protocol.Text(root.GetProperty("checksum"))!=Protocol.Hash(Payload(list)))throw new InvalidDataException("Run checksum mismatch.");
            game=Replay(list);entries=list;
        }
        private void Write(List<Entry> rows,bool replace,System.Action<string>? fault)
        {
            string text=Encode(rows);if(Encoding.UTF8.GetByteCount(text)>MaximumBytes)throw new InvalidDataException("Run exceeds size limit.");
            string temporary=path+"."+Guid.NewGuid().ToString("N")+".tmp";
            try
            {
                fault?.Invoke("before_write");
                using(var file=new FileStream(temporary,FileMode.CreateNew,FileAccess.Write,FileShare.None,4096,FileOptions.WriteThrough))
                {byte[] bytes=Encoding.UTF8.GetBytes(text);file.Write(bytes);file.Flush(true);}
                fault?.Invoke("before_replace");File.Move(temporary,path,replace);
                fault?.Invoke("after_replace");
            }
            finally{if(File.Exists(temporary))File.Delete(temporary);}
        }
        public Receipt Submit(string requestId,RecoveryCommand command,System.Action<string>? fault=null)
        {
            lock(ownership)
            {
            if(disposed)throw new ObjectDisposedException(nameof(RecoverySession));
            if(blocked)throw new IOException("Session is blocked after an uncertain write; close and reopen the validated run.");
            Protocol.Id(requestId);command=command.Normalized();
            var old=entries.FirstOrDefault(e=>e.RequestId==requestId);
            if(old!=null)return new(old.Command.Canonical()==command.Canonical(),old.Command.Canonical()==command.Canonical(),old.Sequence,Revision,old.Command.Canonical()==command.Canonical()?"Already committed; no replayed effect.":"Request identity conflict.",State);
            if(entries.Count>=MaximumEntries)return new(false,false,0,Revision,"Journal limit reached.",State);
            var candidate=Replay(entries);
            if(!command.Apply(candidate,requestId))return new(false,false,0,Revision,"Unavailable command; all persisted gameplay unchanged.",State);
            var next=new List<Entry>(entries){new(entries.Count+1,requestId,command,Protocol.Hash(JsonSerializer.Serialize(candidate.Snapshot())))};
            try{Write(next,true,fault);}catch{blocked=true;throw;}
            entries=next;game=candidate;
            return new(true,false,Revision,Revision,"Committed before receipt.",State);
            }
        }
        public void Dispose(){lock(ownership){if(disposed)return;disposed=true;lease.Dispose();}}
    }
}
