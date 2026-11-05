using System;
namespace NorthStar.Combat
{
    public enum ControlWeight { Light = 1, Hard = 3 }
    // Selected source semantics; crossing and refill timing are explicit destination policy.
    public sealed class Breakbar
    {
        public int Capacity { get; }
        public int Value { get; private set; }
        public bool Protected { get; private set; } = true;
        public Breakbar(int capacity)
        {
            if(capacity < 1 || capacity > 1000000) throw new ArgumentOutOfRangeException(nameof(capacity));
            Capacity=capacity; Value=capacity;
        }
        public ControlResult Apply(ControlWeight weight, bool specificallyImmune=false)
        {
            if(weight!=ControlWeight.Light && weight!=ControlWeight.Hard) throw new ArgumentOutOfRangeException(nameof(weight));
            if(specificallyImmune) return new ControlResult(false,0,0);
            int amount=(int)weight;
            if(Protected)
            {
                int drained=Math.Min(Value,amount); Value-=drained;
                if(Value==0) Protected=false;
                // The breaking application drains only; the next application can control.
                return new ControlResult(false,drained,0);
            }
            int refilled=Math.Min(Capacity-Value,amount); Value+=refilled;
            if(Value==Capacity) Protected=true;
            // An application which completes refill still applies before immunity returns.
            return new ControlResult(true,0,refilled);
        }
    }
    public sealed class ControlResult
    {
        public bool Applied { get; }
        public int Drained { get; }
        public int Refilled { get; }
        public ControlResult(bool applied,int drained,int refilled) { Applied=applied; Drained=drained; Refilled=refilled; }
    }
}
