using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;

namespace NorthStar.Domain
{
    public enum PreparedAction { Skill, Dash }
    public sealed class SkillDefinition
    {
        public string Id { get; }
        public string? ClassId { get; }
        public int MinimumLevel { get; }
        public PreparedAction Action { get; }
        public SkillDefinition(string id,string? classId,int minimumLevel,PreparedAction action)
        {
            LoadoutCatalog.Identifier(id);if(classId!=null)LoadoutCatalog.Identifier(classId);
            if(minimumLevel<1||minimumLevel>4096||!Enum.IsDefined(typeof(PreparedAction),action))throw new ArgumentException("Invalid skill prerequisite/action.");
            Id=id;ClassId=classId;MinimumLevel=minimumLevel;Action=action;
        }
    }
    public sealed class BackgroundPermission
    {
        public string ClassId { get; }
        public string BackgroundId { get; }
        public BackgroundPermission(string classId,string backgroundId){LoadoutCatalog.Identifier(classId);LoadoutCatalog.Identifier(backgroundId);ClassId=classId;BackgroundId=backgroundId;}
    }
    /// <summary>Immutable explicit four-slot proposal; empty slots are permitted, never silently sanitized.</summary>
    public sealed class PreparedLoadout
    {
        public string ClassId {get;}
        public string BackgroundId {get;}
        public IReadOnlyList<string?> Slots {get;}
        public PreparedLoadout(string classId,string backgroundId,IEnumerable<string?> slots)
        {
            LoadoutCatalog.Identifier(classId);LoadoutCatalog.Identifier(backgroundId);
            if(slots==null)throw new ArgumentNullException(nameof(slots));
            var copy=new List<string?>();foreach(var slot in slots){if(copy.Count>=4)throw new ArgumentException("Exactly four slots required.");if(slot!=null)LoadoutCatalog.Identifier(slot);copy.Add(slot);}
            if(copy.Count!=4)throw new ArgumentException("Exactly four slots required.");
            ClassId=classId;BackgroundId=backgroundId;Slots=new ReadOnlyCollection<string?>(copy);
        }
    }
    /// <summary>Bounded eligibility contract, not implementation of the described legacy abilities.</summary>
    public sealed class LoadoutCatalog
    {
        private readonly HashSet<string> classes;
        private readonly HashSet<string> backgrounds;
        private readonly HashSet<string> permissions=new HashSet<string>(StringComparer.Ordinal);
        private readonly Dictionary<string,SkillDefinition> skills=new Dictionary<string,SkillDefinition>(StringComparer.Ordinal);
        public LoadoutCatalog(IEnumerable<string> classIds,IEnumerable<string> backgroundIds,IEnumerable<BackgroundPermission> relations,IEnumerable<SkillDefinition> definitions)
        {
            classes=Unique(classIds,64);backgrounds=Unique(backgroundIds,128);
            if(relations==null||definitions==null)throw new ArgumentNullException("Catalog inputs");
            foreach(var row in relations)
            {
                if(row==null||permissions.Count>=8192||!classes.Contains(row.ClassId)||!backgrounds.Contains(row.BackgroundId)||!permissions.Add(row.ClassId+":"+row.BackgroundId))throw new ArgumentException("Unknown or duplicate background relation.");
            }
            foreach(var skill in definitions)
            {
                if(skill==null||skills.Count>=1024||skill.ClassId!=null&&!classes.Contains(skill.ClassId)||skills.ContainsKey(skill.Id))throw new ArgumentException("Unknown class or duplicate skill.");
                skills.Add(skill.Id,skill);
            }
        }
        internal static void Identifier(string value)
        {
            if(value==null||value.Length<1||value.Length>64)throw new ArgumentException("Identifier requires1–64 ASCII characters.");
            foreach(char c in value)if(!(c>='a'&&c<='z'||c>='A'&&c<='Z'||c>='0'&&c<='9'||c=='_'||c=='-'))throw new ArgumentException("Invalid identifier.");
        }
        private static HashSet<string> Unique(IEnumerable<string> values,int maximum)
        {
            if(values==null)throw new ArgumentNullException(nameof(values));var result=new HashSet<string>(StringComparer.Ordinal);
            foreach(var value in values){Identifier(value);if(result.Count>=maximum||!result.Add(value))throw new ArgumentException("Duplicate or excessive catalog IDs.");}
            if(result.Count==0)throw new ArgumentException("Catalog requires identities.");return result;
        }
        public void Validate(PreparedLoadout proposal,int level)
        {
            if(proposal==null||level<1||level>4096)throw new ArgumentException("Invalid proposal/level.");
            if(!classes.Contains(proposal.ClassId)||!backgrounds.Contains(proposal.BackgroundId)||!permissions.Contains(proposal.ClassId+":"+proposal.BackgroundId))throw new ArgumentException("Unknown or incompatible class/background.");
            var seen=new HashSet<string>(StringComparer.Ordinal);
            foreach(var id in proposal.Slots)
            {
                if(id==null)continue;
                if(!skills.TryGetValue(id,out var skill)||!seen.Add(id)||skill.ClassId!=null&&skill.ClassId!=proposal.ClassId||level<skill.MinimumLevel)throw new ArgumentException("Unknown, duplicate, incompatible or locked skill.");
            }
        }
        public PreparedAction ActionFor(PreparedLoadout proposal,int slot,int level)
        {
            Validate(proposal,level);
            if(slot<0||slot>=4||proposal.Slots[slot]==null)throw new ArgumentException("Empty or invalid slot.");
            return skills[proposal.Slots[slot]!].Action;
        }
    }
}
