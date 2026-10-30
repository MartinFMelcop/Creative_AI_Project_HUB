using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;

namespace NorthStar.Combat
{
    public enum ResponseKind { CommittedStrike, Ward, BreakWard }
    public sealed class ResponseEntry
    {
        public ResponseKind Kind { get; }
        public bool Applied { get; }
        internal ResponseEntry(ResponseKind kind, bool applied) { Kind=kind;Applied=applied; }
    }
    public sealed class ResponseResolution
    {
        public int Damage { get; }
        public IReadOnlyList<ResponseEntry> Entries { get; }
        internal ResponseResolution(int damage,List<ResponseEntry> entries)
        { Damage=damage;Entries=new ReadOnlyCollection<ResponseEntry>(entries); }
    }
    /// <summary>One bounded original strike/ward response, not a general battle engine.</summary>
    public sealed class ResponseChain
    {
        private readonly int damage;
        private bool resolved;
        public bool HasWard { get; }
        public bool Pending => !resolved;
        public int PendingCount => resolved?0:HasWard?2:1;
        public ResponseChain(int committedDamage,bool ward)
        {
            if(committedDamage<0||committedDamage>1000000)throw new ArgumentOutOfRangeException(nameof(committedDamage));
            damage=committedDamage;HasWard=ward;
        }
        public ResponseResolution Resolve(bool breakWard)
        {
            if(resolved)throw new InvalidOperationException("This committed chain already resolved.");
            if(breakWard&&!HasWard)throw new ArgumentException("No ward exists to counter.",nameof(breakWard));
            var stack=new Stack<ResponseKind>(3);stack.Push(ResponseKind.CommittedStrike);
            if(HasWard)stack.Push(ResponseKind.Ward);
            if(breakWard)stack.Push(ResponseKind.BreakWard);
            var entries=new List<ResponseEntry>();bool wardBroken=false,strikeCountered=false;
            while(stack.Count>0)
            {
                var kind=stack.Pop();bool applied;
                if(kind==ResponseKind.BreakWard){wardBroken=true;applied=true;}
                else if(kind==ResponseKind.Ward){applied=!wardBroken;if(applied)strikeCountered=true;}
                else applied=!strikeCountered;
                entries.Add(new ResponseEntry(kind,applied));
            }
            resolved=true;return new ResponseResolution(strikeCountered?0:damage,entries);
        }
    }
}
