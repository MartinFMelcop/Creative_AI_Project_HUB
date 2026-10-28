using System.Text.Json;
using Eclipse.PolicyEvaluation;
try
{
    if(args.Length==4&&args[0]=="run")
    {
        var config=JsonSerializer.Deserialize<Configuration>(File.ReadAllText(args[1]),Evaluation.Json)??throw new ArgumentException("Missing configuration.");
        if(args[3].Length!=64||args[3].Any(c=>!Uri.IsHexDigit(c)))throw new ArgumentException("Need exact source closure SHA256.");
        if(File.Exists(args[2]))throw new ArgumentException("Refusing existing output.");
        var report=Evaluation.Execute(config,args[3]);
        var full=Path.GetFullPath(args[2]);Directory.CreateDirectory(Path.GetDirectoryName(full)!);
        File.WriteAllText(full,JsonSerializer.Serialize(report,Evaluation.Json)+"\n");
        Console.WriteLine(JsonSerializer.Serialize(new{games=report.Games.Length,complete=report.Games.Count(g=>g.Status=="complete"),interrupted=report.Games.Count(g=>g.Status!="complete"),configuration_hash=report.ConfigurationHash,selection_count=Evaluation.SelectionCount,total_selection_milliseconds=Evaluation.TotalSelectionMilliseconds,max_selection_milliseconds=Evaluation.MaxSelectionMilliseconds}));return 0;
    }
    if(args.Length==2&&args[0]=="verify")
    {
        var report=JsonSerializer.Deserialize<Report>(File.ReadAllText(args[1]),Evaluation.Json)??throw new ArgumentException("Missing report.");
        Evaluation.Verify(report);Console.WriteLine(JsonSerializer.Serialize(new{verified=report.Games.Length,configuration_hash=report.ConfigurationHash}));return 0;
    }
    throw new ArgumentException("Usage: run CONFIG OUTPUT SOURCE_SHA256 | verify REPORT");
}
catch(Exception e){Console.Error.WriteLine(e.GetType().Name+": "+e.Message);return 2;}
