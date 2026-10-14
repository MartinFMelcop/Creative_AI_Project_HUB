using System.Text.Json;
using System.Text.Json.Serialization;
using Eclipse.Core;

namespace Eclipse.Cli;
public sealed record SaveData(int Schema, string Version, int Seed, Rules Rules, string[] Policies, Intent[] Actions);
public static class Journal
{
    public static readonly JsonSerializerOptions Json = new()
    {
        PropertyNamingPolicy=JsonNamingPolicy.CamelCase,WriteIndented=true,
        UnmappedMemberHandling=JsonUnmappedMemberHandling.Disallow,
        Converters={new JsonStringEnumConverter<ActionKind>()}
    };
    public static void Save(Game game,string[] policies,string filename)
    {
        Agents.ValidatePolicies(policies);
        var path=Path.GetFullPath(filename);Directory.CreateDirectory(Path.GetDirectoryName(path)!);
        var temporary=path+"."+Guid.NewGuid().ToString("N")+".tmp";
        try
        {
            var data=Snapshot(game,policies);
            File.WriteAllText(temporary,JsonSerializer.Serialize(data,Json));File.Move(temporary,path,true);
        }
        finally {if(File.Exists(temporary))File.Delete(temporary);}
    }
    public static (Game Game,string[] Policies) Load(string filename)
    {
        var file=new FileInfo(filename);
        if(!file.Exists || file.Length>200_000)throw new ArgumentException("Journal is missing or exceeds 200 KB.");
        var data=JsonSerializer.Deserialize<SaveData>(File.ReadAllText(filename),Json)??throw new ArgumentException("Invalid journal.");
        return Replay(data);
    }
    public static SaveData Snapshot(Game game,string[] policies)
    {
        Agents.ValidatePolicies(policies);
        return new(1,Game.Version,game.Seed,game.Rules,policies,game.Journal.Select(t=>t.Intent).ToArray());
    }
    public static (Game Game,string[] Policies) Replay(SaveData data)
    {
        if(data.Schema!=1 || data.Version!=Game.Version || data.Rules==null || data.Actions==null || data.Policies==null)
            throw new ArgumentException("Unsupported or incomplete journal.");
        Agents.ValidatePolicies(data.Policies);var game=new Game(data.Seed,data.Rules);
        if(data.Actions.Length>4*game.Rules.RoundLimit)throw new ArgumentException("Journal exceeds this match's turn limit.");
        foreach(var plan in data.Actions)if(plan==null || !game.Apply(plan,out _))throw new ArgumentException("Journal contains an unavailable action; no state was accepted.");
        return (game,data.Policies);
    }
}
