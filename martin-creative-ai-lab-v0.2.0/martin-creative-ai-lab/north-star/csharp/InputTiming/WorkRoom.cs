using System;
using System.Collections.Generic;
namespace NorthStar.InputTiming
{
    // Integer monotonic milliseconds, separate from rendering and transport. Original bounded migration experiment.
    public sealed class WorkRoom
    {
        public const long Lease=600;
        public long Now {get;private set;}
        private long heartbeat, started=-1;
        public bool Held {get;private set;}
        public bool Paused {get;private set;}
        public bool NeedNeutral {get;private set;}
        public string Target {get;private set;}="catch-a";
        public int Health {get;private set;}=3;
        public int Integrity {get;private set;}=3;
        public bool CatchA {get;private set;}
        public bool CatchB {get;private set;}
        public bool Grounded {get;private set;}
        public bool Won {get;private set;}
        public int Paid {get;private set;}
        public int Completions {get;private set;}
        public string Last {get;private set;}="Raise both catches, then deliberately cross the exit alive. Grounding is optional and costs one integrity.";
        public string LastCause {get;private set;}="none";
        public long LastProgress {get;private set;}
        public int LastCost {get;private set;}
        public bool Lost=>Health==0||Integrity==0;
        public long Required=>Target=="ground"?1500:1000;
        public long Progress=>started<0?0:Math.Min(Required,Now-started);
        public bool Working=>started>=0;
        private readonly List<string> events=new List<string>();
        private bool Available=>!Paused&&!NeedNeutral&&!Lost&&!Won&&(Target=="ground"?!Grounded&&Integrity>1:Target=="catch-a"?!CatchA:!CatchB);
        private void Cancel(string cause)
        {
            if(started<0)return;
            if(started>=0){LastProgress=Progress;LastCost=0;LastCause=cause;events.Add(cause+":"+LastProgress);}
            started=-1;Last=cause+": partial work discarded. A fresh deliberate hold must start from zero.";
        }
        public void Advance(long now,bool harm=false,bool renew=false)
        {
            if(now<Now||now>86400000)throw new ArgumentOutOfRangeException(nameof(now));
            // An expired input lease stops at its own deadline, not at the later polling frame.
            if(!Paused&&Held&&now>heartbeat+Lease){Now=heartbeat+Lease;Cancel("input timeout");Paused=true;NeedNeutral=true;}
            Now=now;
            if(harm&&!Grounded&&!Lost&&!Won){Health--;Integrity--;Cancel("hit");NeedNeutral=Held;Last="Hit interrupted work before completion; no work cost was paid.";}
            if(renew)heartbeat=now;
            if(started>=0&&Available&&Now-started>=Required)
            {
                LastProgress=Required;LastCause="completed";LastCost=Target=="ground"?1:0;
                if(Target=="ground"){Integrity--;Paid++;Grounded=true;}else if(Target=="catch-a")CatchA=true;else CatchB=true;
                Completions++;events.Add("completed:"+Target);started=-1;NeedNeutral=true;
                Last=Target=="ground"?"Grounded: paid one integrity. Shutdown alone does not open the passage.":"Catch raised. Both catches and an actual living exit still own success.";
            }
        }
        public void Input(bool held)
        {
            if(!held){if(Held)Cancel("release");Held=false;NeedNeutral=false;return;}
            if(Held)return;
            Held=true;
            if(Available){started=Now;Last="Working: remain still and hold deliberately. Release, move, pause or harm discards progress.";}
        }
        public void Pause(string cause="pause"){Cancel(cause);Paused=true;NeedNeutral=true;}
        public void Resume(){Paused=false;NeedNeutral=Held;Last=NeedNeutral?"Release held input before rearming.":"Resumed. A new hold starts a complete attempt.";}
        public void Select(string target)
        {
            if(target!="catch-a"&&target!="ground"&&target!="catch-b")throw new ArgumentException("Unknown station.");
            Cancel("movement");NeedNeutral=Held;Target=target;
        }
        public bool Exit()
        {
            if(Paused||Lost||Won||!CatchA||!CatchB){Last="Exit refused: both catches, health and integrity are required.";return false;}
            Cancel("exit");Won=true;Last="Both catches raised; living exit observed. Passage complete.";events.Add("exit");return true;
        }
        public object Snapshot()=>new {now_ms=Now,target=Target,required_ms=Required,progress_ms=Progress,working=Working,held=Held,paused=Paused,need_neutral=NeedNeutral,health=Health,integrity=Integrity,catch_a=CatchA,catch_b=CatchB,grounded=Grounded,won=Won,lost=Lost,paid=Paid,completions=Completions,last=Last,last_cause=LastCause,last_progress_ms=LastProgress,last_cost=LastCost,events=events.ToArray()};
    }
}
