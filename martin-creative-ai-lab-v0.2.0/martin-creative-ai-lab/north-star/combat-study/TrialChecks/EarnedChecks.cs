using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using NorthStar.CombatStudy;

static class EarnedChecks
{
    static readonly List<string> controls=new();
    static readonly List<object> traces=new();
    static JsonElement J(object v)=>JsonSerializer.SerializeToElement(v);
    static JsonElement V(Room r)=>J(r.Snapshot());
    static JsonElement E(Room r)=>V(r).GetProperty("earned");
    static JsonElement A(Room r,string command)=>J(r.Execute(J(new{command})));
    static void Check(string id,bool yes){if(!yes)throw new Exception(id);controls.Add(id);}
    static void Atomic(string id,Room r,object command)
    {string before=V(r).GetRawText();bool refused=false;try{r.Execute(J(command));}catch(ArgumentException){refused=true;}Check(id,refused&&V(r).GetRawText()==before);}
    static Room Start(string profile="toxic"){var r=new Room();A(r,"prepare earned "+profile);A(r,"begin");return r;}
    public static void Run(string? path)
    {
        bool complete=false;string? failure=null;
        try
        {
            Check("Fresh old schema excludes acquisition",!V(new Room()).TryGetProperty("earned",out _));
            var r=new Room();A(r,"prepare earned toxic");
            Check("Earned draft is not an attempt",E(r).GetProperty("attempt").GetInt64()==0&&!E(r).GetProperty("unlocked").GetBoolean());
            Atomic("Forged locked selection is atomic",r,new{command="equip lining heavy"});
            Atomic("Unknown acquisition field is atomic",r,new{command="begin",unlocked=true});
            A(r,"begin");Check("Actual Begin counts one attempt",E(r).GetProperty("attempt").GetInt64()==1);
            foreach(string c in new[]{"prepare earned heated","prepare toxic","prepare responses heated","prepare controls toxic","prepare initiative toxic","restart heated"})Atomic("Paid active reset refused: "+c,r,new{command=c});
            for(int i=0;i<3;i++)A(r,"strike");string before=V(r).GetRawText();
            for(int i=0;i<3;i++)
            {var f=J(r.Forecast(J(new{command="strike"})));Check("Winning forecast grants nothing "+i,f.GetProperty("forecast").GetProperty("state").GetProperty("outcome").GetString()=="secured"&&V(r).GetRawText()==before&&!E(r).GetProperty("unlocked").GetBoolean());}
            long reviewed=V(r).GetProperty("sequence").GetInt64();var win=J(r.Execute(J(new{command="strike",reviewed_sequence=reviewed})));var receipt=E(r).GetProperty("receipt");string award=receipt.GetRawText();
            Check("Live victory records exact one-time award",E(r).GetProperty("unlocked").GetBoolean()&&receipt.GetProperty("kind").GetString()=="earned-practice-clear"&&receipt.GetProperty("sequence").GetInt64()==win.GetProperty("sequence").GetInt64()&&receipt.GetProperty("attempt").GetInt64()==1&&receipt.GetProperty("profile").GetString()=="toxic");
            Atomic("Lost winning receipt is never replayed",r,new{command="strike",reviewed_sequence=reviewed});
            V(r);V(r);var post=A(r,"strike");Check("Reads and terminal actions cannot duplicate award",!post.GetProperty("accepted").GetBoolean()&&E(r).GetProperty("receipt").GetRawText()==award);
            A(r,"prepare earned toxic");A(r,"equip lining heavy");A(r,"begin");var lining=A(r,"guard");Check("Lining uses existing paid hit rule",lining.GetProperty("state").GetProperty("hp").GetInt32()==82&&E(r).GetProperty("attempt").GetInt64()==2&&E(r).GetProperty("receipt").GetRawText()==award);
            var swap=A(r,"equip last-thread heavy");Check("Unlocked still cannot swap in combat",!swap.GetProperty("accepted").GetBoolean()&&swap.GetProperty("preparation").GetProperty("passive").GetString()=="lining");
            A(r,"retreat");A(r,"prepare earned toxic");A(r,"equip lining heavy");A(r,"equip last-thread heavy");A(r,"begin");var exclusive=A(r,"guard");Check("LastThread replaces rather than stacks Lining",exclusive.GetProperty("state").GetProperty("hp").GetInt32()==81&&exclusive.GetProperty("preparation").GetProperty("passive").GetString()=="last-thread");
            traces.Add(new{label="actual clear and earned effects",win,lining,exclusive,final=V(r)});
            var loss=Start();for(int i=0;i<12&&V(loss).GetProperty("phase").GetString()=="active";i++)A(loss,"guard");Check("Actual defeat grants nothing",V(loss).GetProperty("state").GetProperty("outcome").GetString()=="defeated"&&!E(loss).GetProperty("unlocked").GetBoolean()&&E(loss).GetProperty("receipt").ValueKind==JsonValueKind.Null);
            var withdrawn=Start("heated");A(withdrawn,"retreat");Check("Withdrawal grants nothing",!E(withdrawn).GetProperty("unlocked").GetBoolean());A(withdrawn,"prepare earned toxic");Check("Retry draft counts no attempt",E(withdrawn).GetProperty("attempt").GetInt64()==1);A(withdrawn,"begin");Check("Retry actual Begin counts attempt",E(withdrawn).GetProperty("attempt").GetInt64()==2);
            var free=new Room();A(free,"strike");Atomic("Active free encounter cannot be reset into earned",free,new{command="prepare earned toxic"});A(free,"retreat");A(free,"prepare earned toxic");Check("Ended free encounter may enter earned",!E(free).GetProperty("unlocked").GetBoolean());
            var preset=new Room();A(preset,"prepare toxic");A(preset,"equip lining heavy");A(preset,"begin");for(int i=0;i<4;i++)A(preset,"strike");Check("Free preset victory grants nothing",V(preset).GetProperty("state").GetProperty("outcome").GetString()=="secured"&&!V(preset).TryGetProperty("earned",out _));A(preset,"prepare earned toxic");Atomic("Free preset cannot smuggle earned selection",preset,new{command="equip last-thread light"});
            Check("New Room never carries the award",!V(new Room()).TryGetProperty("earned",out _));complete=true;
        }
        catch(Exception e){failure=e.Message;throw;}
        finally
        {if(path!=null)File.WriteAllText(Path.Combine(Path.GetDirectoryName(path)!,"earned-native.json"),JsonSerializer.Serialize(new{complete,failure,checks=new{passed=controls.Count,failed=complete?0:1},controls,traces,scope="Actual earned preparation in one ephemeral Room; no XP, persistence, people or balance validation."},new JsonSerializerOptions{WriteIndented=true})+"\n");Console.WriteLine("Earned controls: "+controls.Count+"; complete: "+complete);}
    }
}
