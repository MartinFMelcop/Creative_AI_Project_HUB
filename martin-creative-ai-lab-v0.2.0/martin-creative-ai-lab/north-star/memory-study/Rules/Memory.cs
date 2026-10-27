using System;
using System.Collections.Generic;

namespace NorthStar.Memory
{
    public enum FlagScope { Global, Npc, Relation }
    public sealed class FlagDefinition
    {
        public string Id {get;} public FlagScope Scope {get;} public int? Ttl {get;}
        public FlagDefinition(string id,FlagScope scope,int? ttl){Bounds.Id(id);Bounds.Ttl(ttl);if(!Enum.IsDefined(typeof(FlagScope),scope))throw new ArgumentException("Unknown scope.");Id=id;Scope=scope;Ttl=ttl;}
    }
    public sealed class EventDefinition
    {
        public string Id {get;} public int? Ttl {get;}
        public EventDefinition(string id,int? ttl){Bounds.Id(id);Bounds.Ttl(ttl);Id=id;Ttl=ttl;}
    }
    internal static class Bounds
    {
        internal static void Id(string value){if(value==null||value.Length<1||value.Length>64)throw new ArgumentException("Known bounded identity required.");foreach(char c in value)if(!(c>='A'&&c<='Z'||c>='a'&&c<='z'||c>='0'&&c<='9'||c=='_'||c=='-'))throw new ArgumentException("ASCII identifier required.");}
        internal static void Ttl(int? ttl){if(ttl.HasValue&&(ttl.Value< -4096||ttl.Value>4096))throw new ArgumentException("Bounded integer TTL required.");}
        internal static long Advance(long turn,int count){if(count>4096)throw new ArgumentException("Bounded turn increment required.");return checked(turn+Math.Max(1,count));}
    }
    public sealed class FlagMemory
    {
        private sealed class Entry {internal readonly bool Value;internal readonly long? Expiry;internal Entry(bool value,long? expiry){Value=value;Expiry=expiry;}}
        private readonly Dictionary<string,FlagDefinition> definitions=new Dictionary<string,FlagDefinition>(StringComparer.Ordinal);
        private readonly Dictionary<string,Entry> entries=new Dictionary<string,Entry>(StringComparer.Ordinal);
        public long Turn {get;private set;}
        public FlagMemory(IEnumerable<FlagDefinition> values){if(values==null)throw new ArgumentNullException(nameof(values));foreach(var d in values){if(d==null||definitions.Count>=256||definitions.ContainsKey(d.Id))throw new ArgumentException("Unique bounded definitions required.");definitions.Add(d.Id,d);}if(definitions.Count==0)throw new ArgumentException("Definitions required.");}
        private FlagDefinition Definition(string id){Bounds.Id(id);if(!definitions.TryGetValue(id,out var d))throw new ArgumentException("Unknown flag; no implicit GLOBAL fallback.");return d;}
        private static string Key(string id,FlagScope scope,string? subject){if(!Enum.IsDefined(typeof(FlagScope),scope))throw new ArgumentException("Unknown scope.");if(scope==FlagScope.Global){if(subject!=null)throw new ArgumentException("GLOBAL has no subject.");}else Bounds.Id(subject!);return ((int)scope)+":"+(subject??"")+":"+id;}
        public void Set(string id,bool value,string? subject=null,FlagScope? scope=null,int? ttlOverride=null){var d=Definition(id);var s=scope??d.Scope;string key=Key(id,s,subject);int? ttl=ttlOverride??d.Ttl;Bounds.Ttl(ttl);long? expiry=ttl.HasValue?checked(Turn+ttl.Value):(long?)null;if(entries.Count>=4096&&!entries.ContainsKey(key))throw new ArgumentException("Memory capacity reached.");entries[key]=new Entry(value,expiry);}
        public bool Exact(string id,FlagScope scope,string? subject=null){Definition(id);return entries.TryGetValue(Key(id,scope,subject),out var e)&&e.Value&&(!e.Expiry.HasValue||e.Expiry.Value>Turn);}
        // Explicit source-style union: a false local entry does not mask a true global fact.
        public bool Any(string id,string? subject=null){Definition(id);if(subject!=null)Bounds.Id(subject);return Exact(id,FlagScope.Global)||(subject!=null&&(Exact(id,FlagScope.Npc,subject)||Exact(id,FlagScope.Relation,subject)));}
        public void Clear(string id,string? subject=null,FlagScope? scope=null){var d=Definition(id);entries.Remove(Key(id,scope??d.Scope,subject));}
        public void Tick(int count=1){Turn=Bounds.Advance(Turn,count);var expired=new List<string>();foreach(var pair in entries)if(pair.Value.Expiry.HasValue&&pair.Value.Expiry.Value<=Turn)expired.Add(pair.Key);foreach(string key in expired)entries.Remove(key);}
    }
    public sealed class RecentMemory
    {
        private sealed class Entry {internal readonly string Id;internal readonly string? Subject;internal readonly long? Expiry;internal Entry(string id,string? subject,long? expiry){Id=id;Subject=subject;Expiry=expiry;}}
        private readonly Dictionary<string,EventDefinition> definitions=new Dictionary<string,EventDefinition>(StringComparer.Ordinal);
        private readonly List<Entry> entries=new List<Entry>();
        public long Turn {get;private set;}
        public RecentMemory(IEnumerable<EventDefinition> values){if(values==null)throw new ArgumentNullException(nameof(values));foreach(var d in values){if(d==null||definitions.Count>=256||definitions.ContainsKey(d.Id))throw new ArgumentException("Unique bounded definitions required.");definitions.Add(d.Id,d);}if(definitions.Count==0)throw new ArgumentException("Definitions required.");}
        private EventDefinition Definition(string id){Bounds.Id(id);if(!definitions.TryGetValue(id,out var d))throw new ArgumentException("Unknown event.");return d;}
        private bool Active(Entry e)=>!e.Expiry.HasValue||e.Expiry.Value>Turn;
        public void Push(string id,string? subject=null,int? ttlOverride=null){var d=Definition(id);if(subject!=null)Bounds.Id(subject);int? ttl=ttlOverride??d.Ttl;Bounds.Ttl(ttl);long? expiry=ttl.HasValue?checked(Turn+ttl.Value):(long?)null;if(entries.Count>=4096)throw new ArgumentException("Memory capacity reached.");entries.Add(new Entry(id,subject,expiry));}
        // Source query deliberately treats an unspecified event subject or query as a wildcard.
        public bool Any(string id,string? subject=null){Definition(id);if(subject!=null)Bounds.Id(subject);foreach(var e in entries)if(e.Id==id&&Active(e)&&(subject==null||e.Subject==null||e.Subject==subject))return true;return false;}
        // Consumer evidence must name the actual witness; a global event is not private observation.
        public bool Exact(string id,string subject){Definition(id);Bounds.Id(subject);foreach(var e in entries)if(e.Id==id&&e.Subject==subject&&Active(e))return true;return false;}
        public long? ExactExpiry(string id,string subject){Definition(id);Bounds.Id(subject);long? expiry=null;foreach(var e in entries)if(e.Id==id&&e.Subject==subject&&Active(e)){if(!e.Expiry.HasValue)return null;if(!expiry.HasValue||e.Expiry.Value>expiry.Value)expiry=e.Expiry;}return expiry;}
        public void Clear(string id,string? subject=null){Definition(id);if(subject!=null)Bounds.Id(subject);entries.RemoveAll(e=>e.Id==id&&(subject==null||e.Subject==subject));}
        public void Tick(int count=1){Turn=Bounds.Advance(Turn,count);entries.RemoveAll(e=>!Active(e));}
    }
}
