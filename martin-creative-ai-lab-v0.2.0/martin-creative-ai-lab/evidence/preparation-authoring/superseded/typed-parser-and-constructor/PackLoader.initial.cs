using System;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text.Json;
using NorthStar.Preparation;
using NorthStar.Loadout;

namespace NorthStar.FieldJourney;

// This host decoder supplies typed values to the portable contract; no fallback or repair.
public static class PackLoader
{
    public static Book Default()=>Load(Path.Combine(AppContext.BaseDirectory,"preparations.json"));
    public static Book Load(string path)
    {
        using var stream=File.OpenRead(path);using var buffer=new MemoryStream();
        var block=new byte[4096];int count;
        while((count=stream.Read(block,0,block.Length))>0)
        {if(buffer.Length+count>65536)throw new ArgumentException("Preparation pack exceeds65536bytes.");buffer.Write(block,0,count);}
        return Parse(buffer.ToArray());
    }
    public static Book Parse(byte[] bytes)
    {
        if(bytes==null||bytes.Length<1||bytes.Length>65536)throw new ArgumentException("Bounded nonempty preparation pack required.");
        using var document=JsonDocument.Parse(bytes,new JsonDocumentOptions{AllowTrailingCommas=false,CommentHandling=JsonCommentHandling.Disallow,MaxDepth=12});
        var root=document.RootElement;Fields(root,"schema_version","cards");
        if(Integer(root,"schema_version")!=1)throw new ArgumentException("Unsupported preparation schema.");
        var rows=root.GetProperty("cards");if(rows.ValueKind!=JsonValueKind.Array||rows.GetArrayLength()<1||rows.GetArrayLength()>32)throw new ArgumentException("Need1..32cards.");
        var cards=rows.EnumerateArray().Select(row=>{
            Fields(row,"id","title","description","class_id","background_id","slots","minimum_level","recommended_rig");
            var values=row.GetProperty("slots");if(values.ValueKind!=JsonValueKind.Array||values.GetArrayLength()!=4)throw new ArgumentException("Exactly four authored slots required.");
            var slots=values.EnumerateArray().Select(x=>x.ValueKind==JsonValueKind.Null?null:x.ValueKind==JsonValueKind.String?x.GetString():throw new ArgumentException("Slot must be exact string/null.")).ToArray();
            return new Card(Text(row,"id"),Text(row,"title"),Text(row,"description"),Text(row,"class_id"),Text(row,"background_id"),slots,Integer(row,"minimum_level"),Text(row,"recommended_rig"));
        }).ToArray();
        string sha=Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant();
        return new Book(cards,PreparedExpedition.Catalog(),sha);
    }
    private static string Text(JsonElement value,string name)=>value.GetProperty(name).ValueKind==JsonValueKind.String?value.GetProperty(name).GetString()!:throw new ArgumentException("Exact authored string required.");
    private static int Integer(JsonElement value,string name)=>value.GetProperty(name).TryGetInt32(out int number)?number:throw new ArgumentException("Exact authored integer required.");
    private static void Fields(JsonElement value,params string[] names)
    {
        if(value.ValueKind!=JsonValueKind.Object)throw new ArgumentException("Preparation object required.");
        var fields=value.EnumerateObject().ToArray();
        if(fields.Length!=names.Length||fields.Select(x=>x.Name).Distinct(StringComparer.Ordinal).Count()!=fields.Length||fields.Any(x=>!names.Contains(x.Name,StringComparer.Ordinal)))throw new ArgumentException("Exact unique authored fields required.");
    }
}
