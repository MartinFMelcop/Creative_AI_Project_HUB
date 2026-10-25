using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using NorthStar.Domain;

namespace NorthStar.Tooling
{
    internal static class ItemId
    {
        internal static bool Valid(string? value)
        {
            if (value == null || value.Length < 1 || value.Length > 64) return false;
            foreach (char c in value)
                if (!(c >= 'a' && c <= 'z' || c >= 'A' && c <= 'Z' || c >= '0' && c <= '9' || c == '_' || c == '-')) return false;
            return true;
        }
        internal static void Require(string? value)
        { if (!Valid(value)) throw new ArgumentException("ID requires1-64 exact ASCII identifier characters."); }
    }

    /// <summary>Exact identity only; presence does not grant price, effect, item ownership or unlock authority.</summary>
    public sealed class ItemCatalog
    {
        private readonly HashSet<string> known = new HashSet<string>(StringComparer.Ordinal);
        public int Count => known.Count;
        public ItemCatalog(IEnumerable<string> knownIds)
        {
            if (knownIds == null) throw new ArgumentNullException(nameof(knownIds));
            foreach (string id in knownIds)
            {
                ItemId.Require(id);
                if (known.Count >= 4096 || !known.Add(id)) throw new ArgumentException("Catalog requires at most4096 distinct exact IDs.");
            }
            if (known.Count == 0) throw new ArgumentException("Catalog must not be empty.");
        }
        public bool Contains(string item) => ItemId.Valid(item) && known.Contains(item);
        internal void RequireKnown(string item)
        { if (!Contains(item)) throw new ArgumentException("Unknown exact catalog item ID."); }
    }

    /// <summary>Immutable retained-tool requirements around the existing immutable transaction recipe.</summary>
    public sealed class ToolRecipe
    {
        public CraftRecipe Core { get; }
        public IReadOnlyCollection<string> RequiredTools { get; }
        public ToolRecipe(CraftRecipe core, IEnumerable<string> requiredTools)
        {
            Core = core ?? throw new ArgumentNullException(nameof(core));
            if (requiredTools == null) throw new ArgumentNullException(nameof(requiredTools));
            var distinct = new HashSet<string>(StringComparer.Ordinal);
            var tools = new List<string>();
            foreach (string tool in requiredTools)
            {
                ItemId.Require(tool);
                if (tools.Count >= 128 || !distinct.Add(tool)) throw new ArgumentException("At most128 distinct retained tools required.");
                tools.Add(tool);
            }
            RequiredTools = new ReadOnlyCollection<string>(tools);
        }
    }

    /// <summary>One private existing CraftInventory owns all quantities and committed requests.</summary>
    public sealed class ToolWorkshop
    {
        private readonly ItemCatalog catalog;
        private readonly CraftInventory inventory;
        private readonly Dictionary<string, ToolRecipe> recipes = new Dictionary<string, ToolRecipe>(StringComparer.Ordinal);
        private readonly HashSet<string> retained = new HashSet<string>(StringComparer.Ordinal);
        public IReadOnlyDictionary<string, int> Snapshot => inventory.Snapshot;
        public int CommittedCount => inventory.CommittedCount;

        public ToolWorkshop(ItemCatalog itemCatalog, IEnumerable<MaterialAmount> initial,
            IEnumerable<ToolRecipe> definitions, IEnumerable<string> knownUnlocks)
        {
            catalog = itemCatalog ?? throw new ArgumentNullException(nameof(itemCatalog));
            if (initial == null || definitions == null || knownUnlocks == null) throw new ArgumentNullException("Workshop arguments");
            var quantities = new List<MaterialAmount>();
            foreach (var row in initial)
            {
                if (row == null || quantities.Count >= 128) throw new ArgumentException("At most128 nonnull initial rows required.");
                catalog.RequireKnown(row.Item); quantities.Add(row);
            }
            var cores = new List<CraftRecipe>();
            foreach (var recipe in definitions)
            {
                if (recipe == null || recipes.Count >= 128 || recipes.ContainsKey(recipe.Core.Id)) throw new ArgumentException("Invalid or duplicate tool recipe.");
                foreach (var row in recipe.Core.Inputs) catalog.RequireKnown(row.Key);
                foreach (var row in recipe.Core.Outputs) catalog.RequireKnown(row.Key);
                foreach (string tool in recipe.RequiredTools) { catalog.RequireKnown(tool); retained.Add(tool); }
                recipes.Add(recipe.Core.Id, recipe); cores.Add(recipe.Core);
            }
            // Selected scope: a tool cannot also be a consumable input in any recipe.
            // Tools never disappear after a successful craft, so its accepted retry keeps its preconditions.
            foreach (var recipe in recipes.Values)
                foreach (var input in recipe.Core.Inputs)
                    if (retained.Contains(input.Key)) throw new ArgumentException("Retained tools cannot also be consumed recipe inputs.");
            inventory = new CraftInventory(quantities, cores, knownUnlocks);
        }

        public int Quantity(string item) { catalog.RequireKnown(item); return inventory.Quantity(item); }
        public CraftResult Craft(string requestId, string recipeId, string station)
        {
            ItemId.Require(requestId); ItemId.Require(recipeId); ItemId.Require(station);
            if (recipes.TryGetValue(recipeId, out var recipe))
                foreach (string tool in recipe.RequiredTools)
                    if (inventory.Quantity(tool) < 1) return new CraftResult(false, false, "Required retained tool is missing.");
            return inventory.Craft(requestId, recipeId, station);
        }
        public CraftResult Consume(string requestId, string item, int amount)
        {
            ItemId.Require(requestId); catalog.RequireKnown(item);
            if (amount < 1 || amount > CraftInventory.MaximumQuantity) throw new ArgumentException("Consume quantity out of bounds.");
            if (retained.Contains(item)) return new CraftResult(false, false, "Retained tools cannot be consumed.");
            return inventory.Consume(requestId, item, amount);
        }
    }
}
