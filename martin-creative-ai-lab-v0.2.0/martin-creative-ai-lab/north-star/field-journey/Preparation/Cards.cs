using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using NorthStar.Domain;

namespace NorthStar.Preparation
{
    // An immutable authored proposal. It is never permission, inventory or an equipped rig.
    public sealed class Card
    {
        public string Id {get;}
        public string Title {get;}
        public string Description {get;}
        public PreparedLoadout Proposal {get;}
        public int MinimumLevel {get;}
        public string RecommendedRig {get;}
        public Card(string id,string title,string description,string classId,string backgroundId,IEnumerable<string?> slots,int minimumLevel,string recommendedRig)
        {
            Identifier(id);Text(title,80);Text(description,400);
            if(minimumLevel<1||minimumLevel>4096||recommendedRig!="plate"&&recommendedRig!="trail")throw new ArgumentException("Unsupported card level or rig recommendation.");
            Id=id;Title=title;Description=description;Proposal=new PreparedLoadout(classId,backgroundId,slots);MinimumLevel=minimumLevel;RecommendedRig=recommendedRig;
        }
        private static void Identifier(string value)
        {
            if(value==null||value.Length<1||value.Length>64)throw new ArgumentException("Exact bounded card identity required.");
            foreach(char c in value)if(!(c>='a'&&c<='z'||c>='A'&&c<='Z'||c>='0'&&c<='9'||c=='_'||c=='-'))throw new ArgumentException("Invalid card identity.");
        }
        private static void Text(string value,int maximum)
        {
            if(string.IsNullOrWhiteSpace(value)||value.Length>maximum)throw new ArgumentException("Bounded authored card text required.");
            foreach(char c in value)if(char.IsControl(c))throw new ArgumentException("Card text cannot contain control characters.");
        }
    }
    public sealed class Book
    {
        private readonly Dictionary<string,Card> byId=new Dictionary<string,Card>(StringComparer.Ordinal);
        private readonly LoadoutCatalog catalog;
        public IReadOnlyList<Card> Cards {get;}
        public string Sha256 {get;}
        public Book(IEnumerable<Card> cards,LoadoutCatalog catalog,string sha256)
        {
            if(cards==null||catalog==null)throw new ArgumentNullException("Complete book inputs required.");
            if(sha256==null||sha256.Length!=64)throw new ArgumentException("Source SHA256 required.");
            foreach(char c in sha256)if(!(c>='0'&&c<='9'||c>='a'&&c<='f'))throw new ArgumentException("Lowercase source SHA256 required.");
            var copy=new List<Card>();
            foreach(var card in cards)
            {
                if(card==null||copy.Count>=32||byId.ContainsKey(card.Id))throw new ArgumentException("Duplicate, null or excessive preparation cards.");
                // Validate the entire authored pack at declared prerequisites before any owner exists.
                catalog.Validate(card.Proposal,card.MinimumLevel);byId.Add(card.Id,card);copy.Add(card);
            }
            if(copy.Count==0)throw new ArgumentException("At least one authored card required.");
            Cards=new ReadOnlyCollection<Card>(copy);this.catalog=catalog;Sha256=sha256;
        }
        public Card Find(string id)
        {if(id==null||!byId.TryGetValue(id,out var result))throw new ArgumentException("Unknown exact preparation card.");return result;}
        public bool Eligible(Card card,int actualLevel)
        {
            if(card==null||!byId.TryGetValue(card.Id,out var owned)||!object.ReferenceEquals(card,owned)||actualLevel<card.MinimumLevel)return false;
            try{catalog.Validate(card.Proposal,actualLevel);return true;}catch(ArgumentException){return false;}
        }
    }
}
