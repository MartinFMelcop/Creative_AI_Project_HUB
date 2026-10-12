using System.Text.Json;
using System.Text.Json.Serialization;
namespace Cinder.Core;

public static class Journal
{
    public static readonly JsonSerializerOptions Json = new() { PropertyNamingPolicy=JsonNamingPolicy.CamelCase,
        UnmappedMemberHandling=JsonUnmappedMemberHandling.Disallow, Converters={new JsonStringEnumConverter()} };
    private sealed record Save(int Schema,string Version,Entry[] Actions);
    public static string Encode(Game game)=>JsonSerializer.Serialize(new Save(1,"0.1.0",game.Journal.ToArray()),Json);
    public static Game Decode(string text)
    {
        if(text.Length>1_000_000)throw new InvalidDataException("Save exceeds the 1 MB limit.");
        var save=JsonSerializer.Deserialize<Save>(text,Json);
        if(save==null || save.Schema!=1 || save.Version!="0.1.0" || save.Actions==null || save.Actions.Length>512)
            throw new InvalidDataException("Unsupported or incomplete save.");
        var game=new Game();
        foreach(var e in save.Actions)
        {
            if(e==null)throw new InvalidDataException("Null action.");
            var accepted=e.Op switch
            {
                "act" when e.Command!=null && e.Choice==null=>game.Act(e.Command),
                "enemy" when e.Command==null && e.Choice==null=>game.ResolveEnemy(),
                "camp" when e.Command==null && e.Choice!=null=>game.Camp(e.Choice),
                _=>false
            };
            if(!accepted)throw new InvalidDataException("Save contains an illegal campaign action.");
        }
        return game;
    }
    public static void Store(Game game,string path)
    {
        var full=Path.GetFullPath(path); Directory.CreateDirectory(Path.GetDirectoryName(full)!);
        var temp=full+"."+Guid.NewGuid().ToString("N")+".tmp";
        try { File.WriteAllText(temp,Encode(game)); File.Move(temp,full,true); }
        finally { if(File.Exists(temp))File.Delete(temp); }
    }
    public static Game Load(string path)
    {
        if(new FileInfo(path).Length>1_000_000)throw new InvalidDataException("Save exceeds the 1 MB limit.");
        return Decode(File.ReadAllText(path));
    }
}
