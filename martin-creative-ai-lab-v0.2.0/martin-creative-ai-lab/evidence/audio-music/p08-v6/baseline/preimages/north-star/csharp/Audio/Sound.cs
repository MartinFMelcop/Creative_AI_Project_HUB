using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
namespace NorthStar.Audio
{
    /// <summary>Read-only consequence projection, separate from simulation and playback.</summary>
    public sealed class Plan
    {
        private readonly string[] cues;
        public string[] Cues => (string[])cues.Clone();
        public string Music {get;}
        private Plan(string[] cues,string music){this.cues=(string[])cues.Clone();Music=music;}
        public static Plan Observe(string command,bool accepted,string contact,string approach,bool active,bool won,bool nextPulse,int stage)
        {
            string music=active?(stage==0?"quiet":"crossing"):"silent";
            if(!accepted)return new Plan(Array.Empty<string>(),music);
            if(command=="begin")return new Plan(new[]{nextPulse?"pulse":"bolt"},music);
            if(command!="walk"&&command!="dash"&&command!="skill"&&command!="wait")return new Plan(Array.Empty<string>(),music);
            if(!active)return new Plan(new[]{won?"won":"lost"},music);
            var cues=new List<string>();
            if(contact=="hurt")cues.Add("hurt");
            else if(contact=="evaded")cues.Add("evade");
            else if(contact=="protected")cues.Add(approach=="anchor"?"block":"draw");
            cues.Add(nextPulse?"pulse":"bolt");
            return new Plan(cues.ToArray(),music);
        }
    }

    /// <summary>Original deterministic editable synthesis. No imported score, sample or fictional identity.</summary>
    public static class Composer
    {
        public const int Rate=22050;
        public const int StemFrames=Rate*8;
        public static string[] Names=>new[]{"quiet","crossing","bolt","pulse","block","draw","hurt","evade","won","lost"};
        private static double Sin(double phase)=>Math.Sin(2*Math.PI*phase);
        private static double Envelope(double t,double length)=>Math.Min(1,t/.008)*Math.Min(1,(length-t)/.015)*Math.Pow(Math.Max(0,1-t/length),.7);
        public static double[] Samples(string name)
        {
            bool stem=name=="quiet"||name=="crossing";
            if(Array.IndexOf(Names,name)<0)throw new ArgumentException("Unknown sound.");
            double length=stem?8:name=="won"||name=="lost"?.60:name=="pulse"?.36:.24;
            var result=new double[(int)Math.Round(length*Rate)];
            for(int i=0;i<result.Length;i++)
            {
                double t=(double)i/Rate,value=0;
                if(stem)
                {
                    // Both stems use this same eight-second transport and shared harmonic phase.
                    // Integer-cycle oscillators meet at the loop boundary; no random/stateful generator exists.
                    value=.022*Sin(100*t)+.014*Sin(150*t);
                    int phrase=(int)(t/2);double local=t%2;
                    double[] notes={300,400,450,350};
                    value+=.022*Sin(notes[phrase]*local)*Math.Sin(Math.PI*local/2)*Math.Exp(-1.2*local);
                    if(name=="crossing")
                    {
                        double beat=t%.5;
                        value+=.025*Sin(200*beat)*Math.Sin(Math.PI*beat/.5)*Math.Exp(-9*beat);
                        value+=.008*Sin(250*t);
                    }
                }
                else
                {
                    double e=Envelope(t,length);
                    switch(name)
                    {
                        case "bolt": {double tap=t%.08;value=.21*Sin((700+100*(int)(t/.08))*tap)*Math.Sin(Math.PI*tap/.08)*e;break;}
                        case "pulse": {double tap=t%.18;value=.21*(Sin(130*tap)+.22*Sin(275*tap))*Math.Sin(Math.PI*tap/.18)*e;break;}
                        case "block":value=.23*(Sin(240*t)+.25*Sin(631*t))*Math.Exp(-10*t)*e;break;
                        case "draw":value=.22*(Sin(1600*t-1800*t*t)+.15*Sin(2131*t))*e;break;
                        case "hurt":value=.23*(Sin(120*t-100*t*t)+.22*Sin(457*t))*Math.Exp(-4*t)*e;break;
                        case "evade":value=.20*Sin(800*t+1200*t*t)*e;break;
                        case "won":case "lost": {int note=Math.Min(2,(int)(t/.2));double[] pitches=name=="won"?new[]{250.0,350,500}:new[]{250.0,200,150};double local=t%.2;value=.22*Sin(pitches[note]*local)*Math.Sin(Math.PI*local/.2)*e;break;}
                    }
                }
                result[i]=value;
            }
            return result;
        }
        public static byte[] Wav(string name)
        {
            double[] samples=Samples(name);
            using(var output=new MemoryStream())using(var writer=new BinaryWriter(output,Encoding.ASCII,true))
            {
                writer.Write(Encoding.ASCII.GetBytes("RIFF"));writer.Write(36+samples.Length*2);writer.Write(Encoding.ASCII.GetBytes("WAVEfmt "));
                writer.Write(16);writer.Write((short)1);writer.Write((short)1);writer.Write(Rate);writer.Write(Rate*2);writer.Write((short)2);writer.Write((short)16);
                writer.Write(Encoding.ASCII.GetBytes("data"));writer.Write(samples.Length*2);
                foreach(double value in samples)
                {
                    if(double.IsNaN(value)||Math.Abs(value)>.9)throw new InvalidOperationException("Synthesis headroom exceeded; never silently clip.");
                    writer.Write((short)Math.Round(value*32767));
                }
                writer.Flush();return output.ToArray();
            }
        }
    }
}
