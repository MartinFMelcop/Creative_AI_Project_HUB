using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using NorthStar.Audio;
using NorthStar.Presentation;
public static class AudioChecks
{
    private static readonly List<object> controls=new();private static readonly List<object> events=new();
    private static void Check(bool ok,string name){controls.Add(new{name,passed=ok});if(!ok)throw new Exception(name);}
    private static JsonElement Do(Room room,string command){using var input=JsonDocument.Parse(command);var result=JsonSerializer.SerializeToElement(room.Execute(input.RootElement));events.Add(result);return result;}
    private static string[] Cues(JsonElement e)=>e.GetProperty("audio").GetProperty("cues").EnumerateArray().Select(x=>x.GetString()!).ToArray();
    private static string Music(JsonElement e)=>e.GetProperty("audio").GetProperty("music").GetString()!;
    private static string Sha(byte[] b)=>Convert.ToHexString(SHA256.HashData(b)).ToLowerInvariant();
    public static int Main(string[] args)
    {
        try
        {
            if(args.Length<1||args.Length>2)throw new ArgumentException("Usage: NorthStar.AudioChecks OUTPUT [ASSETDIR]");
            string assetDir=args.Length==2?args[1]:Path.Combine(Path.GetDirectoryName(Path.GetFullPath(args[0]))!,"audio-assets");Directory.CreateDirectory(assetDir);
            var assets=new List<object>();
            foreach(string name in Composer.Names)
            {
                byte[] wav=Composer.Wav(name);double[] samples=Composer.Samples(name);bool stem=name=="quiet"||name=="crossing";
                Check(wav.SequenceEqual(Composer.Wav(name)),"Deterministic WAV "+name);
                Check(Encoding.ASCII.GetString(wav,0,4)=="RIFF"&&Encoding.ASCII.GetString(wav,8,8)=="WAVEfmt "&&BitConverter.ToInt32(wav,4)==wav.Length-8&&BitConverter.ToInt16(wav,20)==1&&BitConverter.ToInt16(wav,22)==1&&BitConverter.ToInt32(wav,24)==Composer.Rate&&BitConverter.ToInt16(wav,34)==16&&BitConverter.ToInt32(wav,40)==samples.Length*2,"Actual PCM16 mono WAV contract "+name);
                double peak=samples.Max(Math.Abs),rms=Math.Sqrt(samples.Sum(x=>x*x)/samples.Length);
                Check(peak>.001&&peak<(stem?.10:.30)&&rms>.001,"Non-silent bounded source headroom "+name);
                Check(stem?samples.Length==Composer.StemFrames:samples.Length<Composer.Rate,"Bounded frame count "+name);
                File.WriteAllBytes(Path.Combine(assetDir,name+".wav"),wav);assets.Add(new{name,sha256=Sha(wav),frames=samples.Length,sample_rate=Composer.Rate,channels=1,peak,rms});
            }
            double[] quiet=Composer.Samples("quiet"),crossing=Composer.Samples("crossing");
            Check(quiet.Length==crossing.Length&&quiet.Length==Composer.StemFrames,"Shared equal-length eight-second transport");
            Check(Math.Abs(quiet[0]-quiet[^1])<.002&&Math.Abs(crossing[0]-crossing[^1])<.002,"Bounded actual loop endpoint step");
            Check(!quiet.SequenceEqual(crossing),"Adaptive stems actually differ");
            double worst=0;foreach(double mix in new[]{0.0,.25,.5,.75,1.0})for(int i=0;i<quiet.Length;i++)worst=Math.Max(worst,Math.Abs(quiet[i]*Math.Cos(mix*Math.PI/2)+crossing[i]*Math.Sin(mix*Math.PI/2)));
            Check(worst<.14,"Equal-power nominal stem mix retains cue headroom");
            // Source signal bounds do not prove browser mix output or human masking/recognition.
            foreach(string name in Composer.Names.Where(n=>n!="quiet"&&n!="crossing"))Check(worst+2*Composer.Samples(name).Max(Math.Abs)<.75,"Two-voice conservative nominal mix bound "+name);
            var room=new Room();var refused=Do(room,"{\"op\":\"action\",\"action\":\"skill\"}");Check(Cues(refused).Length==0&&Music(refused)=="silent","Inactive refused action is silent");
            var prepared=Do(room,"{\"op\":\"prepare\",\"approach\":\"anchor\",\"outfit\":\"plate\"}");Check(Cues(prepared).Length==0,"Prepare does not replay contact");
            var begin=Do(room,"{\"op\":\"begin\"}");Check(Cues(begin).SequenceEqual(new[]{"bolt"})&&Music(begin)=="quiet","Begin announces actual next bolt");
            var block=Do(room,"{\"op\":\"action\",\"action\":\"skill\"}");Check(Cues(block).SequenceEqual(new[]{"block","bolt"}),"Actual Anchor block then next threat");
            var hurt=Do(room,"{\"op\":\"action\",\"action\":\"walk\"}");Check(Cues(hurt).SequenceEqual(new[]{"hurt","pulse"}),"Actual bolt harm then different next pulse");
            var evade=Do(room,"{\"op\":\"action\",\"action\":\"dash\"}");Check(Cues(evade).SequenceEqual(new[]{"evade","bolt"}),"Actual pulse evasion then next bolt");
            var won=Do(room,"{\"op\":\"action\",\"action\":\"skill\"}");Check(Cues(won).SequenceEqual(new[]{"won"})&&Music(won)=="silent","Terminal reward has exclusive cue priority");
            var repeated=Do(room,"{\"op\":\"action\",\"action\":\"skill\"}");Check(Cues(repeated).Length==0,"Rejected post-result skill cannot replay victory");
            var second=Do(room,"{\"op\":\"begin\"}");Check(Music(second)=="crossing","Actual second encounter selects stress stem");
            string beforeRead=JsonSerializer.Serialize(room.Snapshot());Check(beforeRead==JsonSerializer.Serialize(room.Snapshot()),"Reads preserve same sequence/plan without new event");
            var reset=Do(room,"{\"op\":\"restart\"}");Check(Cues(reset).Length==0&&Music(reset)=="silent","Restart drops old audio plan");
            Do(room,"{\"op\":\"prepare\",\"approach\":\"lure\",\"outfit\":\"trail\"}");Do(room,"{\"op\":\"begin\"}");var draw=Do(room,"{\"op\":\"action\",\"action\":\"skill\"}");Check(Cues(draw).SequenceEqual(new[]{"draw","bolt"})&&draw.GetProperty("moved").GetInt32()==1,"Actual Lure advance has distinct draw response");
            for(int n=0;n<2;n++)Do(room,"{\"op\":\"action\",\"action\":\"skill\"}");var scarce=Do(room,"{\"op\":\"action\",\"action\":\"skill\"}");Check(!scarce.GetProperty("accepted").GetBoolean()&&Cues(scarce).Length==0,"Scarce resolve refusal cannot sound protection");
            Do(room,"{\"op\":\"restart\"}");Do(room,"{\"op\":\"begin\"}");JsonElement lost=default;for(int n=0;n<4;n++)lost=Do(room,"{\"op\":\"action\",\"action\":\"wait\"}");Check(Cues(lost).SequenceEqual(new[]{"lost"})&&Music(lost)=="silent","Actual defeat suppresses next threat and emits loss");
            Check(events.Cast<JsonElement>().All(e=>Cues(e).Length<=2),"All real event plans bound simultaneous semantic cues");
            File.WriteAllText(args[0],JsonSerializer.Serialize(new{schema_version=1,kind="actual_csharp_audio_composition_and_projection",checks=controls.Count,controls,assets,events,nominal_equal_power_peak=worst,limits="Source PCM and actual C# semantic projection; browser playback/capture, devices and human listening require separate evidence."},NorthStar.Presentation.Program.Json)+"\n");Console.WriteLine($"AUDIO_CHECKS {controls.Count} passed; {assets.Count} WAV assets");return 0;
        }
        catch(Exception e){Console.Error.WriteLine(e.Message);return 1;}
    }
}
