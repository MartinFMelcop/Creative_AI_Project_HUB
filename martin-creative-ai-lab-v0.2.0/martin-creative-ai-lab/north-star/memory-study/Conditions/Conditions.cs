using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Globalization;
namespace NorthStar.Conditions
{
    public enum ConditionType { Boolean, Integer, String }
    // Values come from the owning application, never condition text or a dispatcher.
    public sealed class ConditionValue
    {
        public ConditionType Type {get;}
        internal bool Bool {get;} internal long Number {get;} internal string Word {get;}
        private ConditionValue(ConditionType type,bool boolean,long integer,string text){Type=type;Bool=boolean;Number=integer;Word=text;}
        public static ConditionValue Boolean(bool value)=>new ConditionValue(ConditionType.Boolean,value,0,"");
        public static ConditionValue Integer(long value)=>new ConditionValue(ConditionType.Integer,false,value,"");
        public static ConditionValue Text(string value){Syntax.Word(value);return new ConditionValue(ConditionType.String,false,0,value);}
    }
    public sealed class ConditionResult
    {
        public bool Satisfied {get;} public bool Complete {get;} public string Reason {get;}
        internal ConditionResult(bool satisfied,bool complete,string reason){Satisfied=satisfied;Complete=complete;Reason=reason;}
    }
    internal static class Syntax
    {
        internal static bool Character(char c)=>(c>='a'&&c<='z')||(c>='A'&&c<='Z')||(c>='0'&&c<='9')||c=='_'||c=='-'||c=='@'||c==':'||c=='.';
        internal static void Word(string value){if(value==null||value.Length<1||value.Length>64)throw new ArgumentException("A bounded ASCII token is required.");foreach(char c in value)if(!Character(c))throw new ArgumentException("An ASCII token is required.");}
        internal static void Symbol(string value){Word(value);char first=value[0];if(!((first>='a'&&first<='z')||(first>='A'&&first<='Z')||first=='_'))throw new ArgumentException("A symbol starts with an ASCII letter or underscore.");}
    }
    internal abstract class Node {internal abstract bool Evaluate(IReadOnlyDictionary<string,ConditionValue> facts);}
    internal sealed class Junction:Node
    {
        private readonly Node left,right;private readonly bool conjunction;
        internal Junction(Node left,Node right,bool conjunction){this.left=left;this.right=right;this.conjunction=conjunction;}
        internal override bool Evaluate(IReadOnlyDictionary<string,ConditionValue> facts)=>conjunction?left.Evaluate(facts)&&right.Evaluate(facts):left.Evaluate(facts)||right.Evaluate(facts);
    }
    internal sealed class Comparison:Node
    {
        private readonly string symbol,operation;private readonly ConditionValue literal;
        internal Comparison(string symbol,string operation,ConditionValue literal){this.symbol=symbol;this.operation=operation;this.literal=literal;}
        internal override bool Evaluate(IReadOnlyDictionary<string,ConditionValue> facts)
        {
            var value=facts[symbol];int comparison=value.Type==ConditionType.Boolean?value.Bool.CompareTo(literal.Bool):value.Type==ConditionType.Integer?value.Number.CompareTo(literal.Number):string.CompareOrdinal(value.Word,literal.Word);
            switch(operation){case "=":case "==":return comparison==0;case "!=":return comparison!=0;case "<":return comparison<0;case "<=":return comparison<=0;case ">":return comparison>0;case ">=":return comparison>=0;default:throw new InvalidOperationException("Compiled comparison required.");}
        }
    }
    public sealed class CompiledCondition
    {
        private readonly Node expression;private readonly IReadOnlyDictionary<string,ConditionType> references;
        public string Expression {get;}
        public IReadOnlyList<string> ReferencedSymbols {get;}
        internal CompiledCondition(string source,Node expression,Dictionary<string,ConditionType> references)
        {Expression=source;this.expression=expression;this.references=new ReadOnlyDictionary<string,ConditionType>(references);ReferencedSymbols=new ReadOnlyCollection<string>(new List<string>(references.Keys));}
        public ConditionResult Evaluate(IReadOnlyDictionary<string,ConditionValue> facts)
        {
            if(facts==null)throw new ArgumentNullException(nameof(facts));
            if(facts.Count>128)return new ConditionResult(false,false,"Fact context exceeds the declared bound.");
            // Copy by ordinal spelling instead of inheriting a caller's key comparer.
            var current=new Dictionary<string,ConditionValue>(StringComparer.Ordinal);
            foreach(var entry in facts)if(entry.Key==null||!current.TryAdd(entry.Key,entry.Value))return new ConditionResult(false,false,"Invalid or duplicate fact key.");
            // Check the whole referenced context before short-circuit evaluation.
            // Unknown is never a successful negative comparison or an OR fallback.
            foreach(var entry in references)if(!current.TryGetValue(entry.Key,out var value)||value==null||value.Type!=entry.Value)return new ConditionResult(false,false,"Missing or wrongly typed fact: "+entry.Key);
            return new ConditionResult(expression.Evaluate(current),true,"All referenced facts are present and typed.");
        }
    }
    public static class ConditionCompiler
    {
        public static CompiledCondition Compile(string source,IReadOnlyDictionary<string,ConditionType> symbols)
        {
            if(source==null||source.Length<1||source.Length>4096)throw new ArgumentException("Condition text requires1..4096 characters.");
            if(symbols==null||symbols.Count<1||symbols.Count>128)throw new ArgumentException("A bounded declared symbol table is required.");
            var declarations=new Dictionary<string,ConditionType>(StringComparer.Ordinal);
            foreach(var entry in symbols){Syntax.Symbol(entry.Key);if(!Enum.IsDefined(typeof(ConditionType),entry.Value)||!declarations.TryAdd(entry.Key,entry.Value))throw new ArgumentException("Invalid or duplicate symbol.");}
            var parser=new Parser(source,declarations);return parser.Compile();
        }
        private sealed class Parser
        {
            private readonly string source;private readonly List<string> tokens=new List<string>();private readonly Dictionary<string,ConditionType> symbols,references=new Dictionary<string,ConditionType>(StringComparer.Ordinal);private int index,depth;
            internal Parser(string source,Dictionary<string,ConditionType> symbols){this.source=source;this.symbols=symbols;Tokenize();}
            private void Add(string token){if(tokens.Count>=1024)throw new ArgumentException("Condition token limit exceeded.");tokens.Add(token);}
            private void Tokenize()
            {
                for(int i=0;i<source.Length;)
                {
                    char c=source[i];if(c==' '||c=='\t'||c=='\r'||c=='\n'){i++;continue;}
                    if(i+1<source.Length){string two=source.Substring(i,2);if(two=="=="||two=="!="||two=="<="||two==">="){Add(two);i+=2;continue;}}
                    if(c=='('||c==')'||c=='&'||c=='|'||c=='<'||c=='>'||c=='='){Add(c.ToString());i++;continue;}
                    if(Syntax.Character(c)){int start=i;while(i<source.Length&&Syntax.Character(source[i]))i++;string word=source.Substring(start,i-start);Syntax.Word(word);Add(word);continue;}
                    throw new ArgumentException("Unsupported condition character.");
                }
            }
            private string? Peek()=>index<tokens.Count?tokens[index]:null;
            private bool Eat(string token){if(Peek()!=token)return false;index++;return true;}
            private string Next(){if(index>=tokens.Count)throw new ArgumentException("Missing condition operand.");return tokens[index++];}
            internal CompiledCondition Compile(){if(tokens.Count==0)throw new ArgumentException("Empty condition is not authority.");Node node=Or();if(index!=tokens.Count)throw new ArgumentException("Trailing condition tokens.");return new CompiledCondition(source,node,references);}
            private Node Or(){Node result=And();while(Eat("|"))result=new Junction(result,And(),false);return result;}
            private Node And(){Node result=Primary();while(Eat("&"))result=new Junction(result,Primary(),true);return result;}
            private Node Primary()
            {
                if(Eat("(")){if(++depth>32)throw new ArgumentException("Condition nesting limit exceeded.");Node result=Or();if(!Eat(")"))throw new ArgumentException("Missing closing parenthesis.");depth--;return result;}
                string name=Next();if(!symbols.TryGetValue(name,out var type))throw new ArgumentException("Unknown condition symbol: "+name);
                string operation=Next();if(operation!="="&&operation!="=="&&operation!="!="&&operation!="<"&&operation!="<="&&operation!=">"&&operation!=">=")throw new ArgumentException("Comparison operator required.");
                if(type!=ConditionType.Integer&&operation!="="&&operation!="=="&&operation!="!=")throw new ArgumentException("Ordering requires an integer symbol.");
                string text=Next();ConditionValue literal;
                if(type==ConditionType.Boolean){if(text!="true"&&text!="false")throw new ArgumentException("Exact lowercase Boolean literal required.");literal=ConditionValue.Boolean(text=="true");}
                else if(type==ConditionType.Integer){if(!long.TryParse(text,NumberStyles.AllowLeadingSign,CultureInfo.InvariantCulture,out long number))throw new ArgumentException("Bounded signed integer literal required.");literal=ConditionValue.Integer(number);}
                else literal=ConditionValue.Text(text);
                references[name]=type;return new Comparison(name,operation,literal);
            }
        }
    }
}
