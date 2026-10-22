using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;

namespace NorthStar.Domain
{
    /// <summary>Bounded material quantities; duplicate ingredient rows aggregate before validation.</summary>
    public sealed class MaterialAmount
    {
        public string Item { get; }
        public int Quantity { get; }
        public MaterialAmount(string item, int quantity) { Item = item; Quantity = quantity; }
    }
    public sealed class CraftRecipe
    {
        public string Id { get; }
        public string Station { get; }
        public string Unlock { get; }
        public IReadOnlyDictionary<string,int> Inputs { get; }
        public IReadOnlyDictionary<string,int> Outputs { get; }
        public CraftRecipe(string id, string station, string unlock, IEnumerable<MaterialAmount> inputs, IEnumerable<MaterialAmount> outputs)
        {
            CraftInventory.Identifier(id); CraftInventory.Identifier(station); CraftInventory.Identifier(unlock);
            Id=id; Station=station; Unlock=unlock;
            Inputs=Aggregate(inputs); Outputs=Aggregate(outputs);
        }
        private static IReadOnlyDictionary<string,int> Aggregate(IEnumerable<MaterialAmount> amounts)
        {
            if(amounts==null)throw new ArgumentNullException(nameof(amounts));
            var result=new Dictionary<string,int>(StringComparer.Ordinal); int rows=0;
            foreach(var row in amounts)
            {
                if(++rows>128 || row==null)throw new ArgumentException("At most128 material rows required.");
                CraftInventory.Identifier(row.Item);
                if(row.Quantity<1 || row.Quantity>CraftInventory.MaximumQuantity)throw new ArgumentException("Material quantity out of bounds.");
                result.TryGetValue(row.Item,out int previous);
                if(row.Quantity>CraftInventory.MaximumQuantity-previous)throw new ArgumentException("Aggregated quantity exceeds bound.");
                result[row.Item]=previous+row.Quantity;
            }
            if(result.Count==0)throw new ArgumentException("Recipes require nonempty inputs and outputs.");
            return new ReadOnlyDictionary<string,int>(result);
        }
    }
    public sealed class CraftResult
    {
        public bool Applied { get; }
        public bool Replay { get; }
        public string Reason { get; }
        public CraftResult(bool applied,bool replay,string reason){Applied=applied;Replay=replay;Reason=reason;}
    }
    /// <summary>Single-owner in-memory crafting ledger. No durable/network exactly-once claim.</summary>
    public sealed class CraftInventory
    {
        public const int MaximumQuantity=1000000;
        private readonly Dictionary<string,int> quantities=new Dictionary<string,int>(StringComparer.Ordinal);
        private readonly Dictionary<string,CraftRecipe> recipes=new Dictionary<string,CraftRecipe>(StringComparer.Ordinal);
        private readonly HashSet<string> unlocks=new HashSet<string>(StringComparer.Ordinal);
        private readonly Dictionary<string,string> committed=new Dictionary<string,string>(StringComparer.Ordinal);
        public int CommittedCount=>committed.Count;
        public IReadOnlyDictionary<string,int> Snapshot=>new ReadOnlyDictionary<string,int>(new Dictionary<string,int>(quantities,StringComparer.Ordinal));
        public CraftInventory(IEnumerable<MaterialAmount> initial,IEnumerable<CraftRecipe> definitions,IEnumerable<string> knownUnlocks)
        {
            if(initial==null || definitions==null || knownUnlocks==null)throw new ArgumentNullException("Inventory arguments");
            int count=0;
            foreach(var row in initial)
            {
                if(++count>128 || row==null)throw new ArgumentException("Inventory requires at most128 unique rows.");
                Identifier(row.Item);
                if(row.Quantity<0 || row.Quantity>MaximumQuantity || quantities.ContainsKey(row.Item))throw new ArgumentException("Invalid or duplicate inventory quantity.");
                quantities.Add(row.Item,row.Quantity);
            }
            foreach(var recipe in definitions)
            {
                if(recipe==null || recipes.Count>=128 || recipes.ContainsKey(recipe.Id))throw new ArgumentException("Invalid or duplicate recipe.");
                recipes.Add(recipe.Id,recipe);
            }
            foreach(var id in knownUnlocks){Identifier(id);if(unlocks.Count>=128 || !unlocks.Add(id))throw new ArgumentException("Invalid or duplicate unlock.");}
        }
        public int Quantity(string item){Identifier(item);return quantities.TryGetValue(item,out int value)?value:0;}
        internal static void Identifier(string value)
        {
            if(value==null || value.Length<1 || value.Length>64)throw new ArgumentException("ID requires1–64 ASCII identifier characters.");
            foreach(char c in value)if(!(c>='a'&&c<='z'||c>='A'&&c<='Z'||c>='0'&&c<='9'||c=='_'||c=='-'))throw new ArgumentException("Invalid identifier.");
        }
        public CraftResult Craft(string requestId,string recipeId,string station)
        {
            Identifier(requestId);Identifier(recipeId);Identifier(station);
            string fingerprint="craft:"+recipeId+":"+station;
            var replay=Replay(requestId,fingerprint);if(replay!=null)return replay;
            if(!recipes.TryGetValue(recipeId,out var recipe))return new CraftResult(false,false,"Unknown recipe.");
            if(recipe.Station!=station)return new CraftResult(false,false,"Wrong station.");
            if(!unlocks.Contains(recipe.Unlock))return new CraftResult(false,false,"Recipe locked.");
            return Apply(requestId,fingerprint,recipe.Inputs,recipe.Outputs);
        }
        public CraftResult Consume(string requestId,string item,int amount)
        {
            Identifier(requestId);Identifier(item);
            if(amount<1 || amount>MaximumQuantity)throw new ArgumentException("Consume quantity out of bounds.");
            string fingerprint="consume:"+item+":"+amount.ToString(System.Globalization.CultureInfo.InvariantCulture);
            var replay=Replay(requestId,fingerprint);if(replay!=null)return replay;
            return Apply(requestId,fingerprint,new Dictionary<string,int>{{item,amount}},new Dictionary<string,int>());
        }
        private CraftResult? Replay(string requestId,string fingerprint)
        {
            if(committed.TryGetValue(requestId,out var previous))return previous==fingerprint?new CraftResult(false,true,"Already committed."):new CraftResult(false,false,"Request identity conflict.");
            if(committed.Count>=10000)return new CraftResult(false,false,"Transaction ledger full.");
            return null;
        }
        private CraftResult Apply(string requestId,string fingerprint,IReadOnlyDictionary<string,int> inputs,IReadOnlyDictionary<string,int> outputs)
        {
            var next=new Dictionary<string,int>(quantities,StringComparer.Ordinal);
            foreach(var row in inputs)
            {
                int available=next.TryGetValue(row.Key,out int value)?value:0;
                if(available<row.Value)return new CraftResult(false,false,"Insufficient materials.");
                next[row.Key]=available-row.Value;
            }
            foreach(var row in outputs)
            {
                int available=next.TryGetValue(row.Key,out int value)?value:0;
                if(row.Value>MaximumQuantity-available)return new CraftResult(false,false,"Output capacity exceeded.");
                next[row.Key]=available+row.Value;
            }
            if(next.Count>128)return new CraftResult(false,false,"Inventory item limit exceeded.");
            // All expected failures precede mutation. A rejected request does not reserve its ID.
            committed.Add(requestId,fingerprint);
            quantities.Clear();foreach(var row in next)quantities.Add(row.Key,row.Value);
            return new CraftResult(true,false,"Committed.");
        }
    }
}
