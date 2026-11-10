using System;
using System.Collections.Generic;

namespace NorthStar.FieldGate
{
    // Original discrete destination policy. This is not the source's continuous clock.
    public sealed class Gate
    {
        private readonly int entryHealth,entryResolve;
        private readonly string handle,accent,discipline,rig;
        private string position="ground",working="none",last="The road is historical. Two catches and actual exit remain.";
        private int health,resolve,integrity=3,beat,progress;
        private bool left,right,grounded,completed,failed,assistUsed;
        private string lastBlocked="none";
        public Gate(int health,int resolve,string handle,string accent,string discipline,string rig)
        {
            if(health<1||health>1000000||resolve<0||resolve>1000000)throw new ArgumentOutOfRangeException(nameof(health));
            if(string.IsNullOrWhiteSpace(handle)||string.IsNullOrWhiteSpace(accent)||string.IsNullOrWhiteSpace(discipline)||string.IsNullOrWhiteSpace(rig))throw new ArgumentException("Actual identity and outfit required.");
            this.health=entryHealth=health;this.resolve=entryResolve=resolve;
            this.handle=handle;this.accent=accent;this.discipline=discipline;this.rig=rig;
        }
        public bool Active=>!completed&&!failed;
        public static void ValidateTarget(string target)
        {if(target!="left"&&target!="right"&&target!="ground"&&target!="exit")throw new ArgumentException("Exact gate location required.");}
        private string Threat=>!Active?"none":grounded?"quiet":beat%4==0?"player":beat%4==2?"winch":"quiet";
        private void Interrupt(){progress=0;working="none";}
        private bool AtUnraisedCatch=>(position=="left"&&!left)||(position=="right"&&!right);
        private string AssistProtection=>rig=="plate"?"player":rig=="trail"?"winch":"none";
        private bool CanAssist=>Active&&!assistUsed&&resolve>0&&AtUnraisedCatch&&AssistProtection!="none";
        private List<string> Legal()
        {
            var result=new List<string>();if(!Active)return result;
            result.Add("gate-move");result.Add("gate-wait");
            if(AtUnraisedCatch)result.Add("gate-work");
            if(CanAssist)result.Add("gate-assist");
            if(resolve>0)result.Add("gate-brace");
            if(position=="ground"&&!grounded&&resolve>=2&&integrity>1)result.Add("gate-ground");
            if(position=="exit"&&left&&right)result.Add("gate-exit");
            return result;
        }
        public bool Execute(string command,string? target,out string message)
        {
            if(command=="gate-move"){if(target==null)throw new ArgumentException("Exact gate location required.");ValidateTarget(target);}
            else if(target!=null)throw new ArgumentException("Only movement has a target.");
            if(command!="gate-move"&&command!="gate-work"&&command!="gate-assist"&&command!="gate-wait"&&command!="gate-brace"&&command!="gate-ground"&&command!="gate-exit")throw new ArgumentException("Known gate command required.");
            if(!Active){message="This gate attempt has ended. No retry, healing, return or delivery is supplied.";return false;}
            if(!Legal().Contains(command)||(command=="gate-move"&&target=="exit"&&!(left&&right)))
            {message="That gate action is unavailable at the actual position, resources or catches. No beat or resource was spent.";return false;}
            string threat=Threat;
            bool assisted=command=="gate-assist";
            bool work=command=="gate-work"||assisted;
            if(!work)Interrupt();
            if(command=="gate-move")position=target!;
            if(command=="gate-brace")resolve--;
            if(command=="gate-ground"){resolve-=2;integrity--;}
            // One deliberate use of the worn rig pays before contact or work.
            // A mismatched/quiet threat still spends this gate-only opportunity.
            if(assisted){resolve--;assistUsed=true;lastBlocked=threat==AssistProtection?threat:"none";}
            string assistText=assisted?"Worn "+rig+" assist spent one resolve and its one gate use; blocked "+lastBlocked+". ":"";
            int damage=0,deviceDamage=0;
            if(command!="gate-brace")
            {
                if(threat=="player"&&!(assisted&&lastBlocked=="player")){damage=Math.Min(2,health);health-=damage;}
                if(threat=="winch"&&!(assisted&&lastBlocked=="winch")){deviceDamage=1;integrity--;}
            }
            beat++;
            // Threat and paid costs precede work, grounding and exit completion.
            if(health<=0||integrity<=0)
            {health=Math.Max(0,health);integrity=Math.Max(0,integrity);failed=true;Interrupt();last=message=assistText+"Gate failed after paid action: "+(health==0?"person fell":"mechanism broke")+". The completed road remains historical; no passage, home return or delivery occurred.";return true;}
            if(work)
            {
                if(damage>0){Interrupt();last="Player contact interrupted this work. Its partial progress is lost.";}
                else
                {
                    if(working!=position){working=position;progress=0;}
                    progress++;
                    if(progress==2){if(position=="left")left=true;else right=true;Interrupt();last="The "+position+" catch was actually raised. Both catches and a living exit remain distinct.";}
                    else last="One paid work beat retained at the "+position+" catch. Another uninterrupted work beat is required.";
                }
            }
            else if(command=="gate-ground"){grounded=true;last="Grounded after paying two resolve and one integrity, and surviving the announced threat. Shutdown alone is not completion.";}
            else if(command=="gate-exit"){completed=true;last="Both catches were raised and the person actually exited alive. Passage opened; home return and delivery remain unobserved.";}
            else if(command=="gate-brace")last="One resolve paid to brace this beat's announced contact. Partial work was interrupted.";
            else if(command=="gate-move")last="Moved to "+position+"; partial work was interrupted. Position is not passage completion.";
            else last="Wait paid one actual gate beat; partial work was interrupted.";
            last=assistText+last+" Contact paid: "+damage+" HP / "+deviceDamage+" integrity.";
            message=last;return true;
        }
        public object Snapshot()=>new {entered=true,eligible=false,active=Active,completed,failed,health,resolve,integrity,beat,position,grounded,left_raised=left,right_raised=right,progress,working,next_threat=Threat,last_text=last,legal=Legal().ToArray(),assist=new {rig,protects=AssistProtection,used=assistUsed,eligible=CanAssist,resolve_cost=1,last_blocked=lastBlocked},entry=new {health=entryHealth,resolve=entryResolve,handle,accent,class_id=discipline,rig}};
    }
}
