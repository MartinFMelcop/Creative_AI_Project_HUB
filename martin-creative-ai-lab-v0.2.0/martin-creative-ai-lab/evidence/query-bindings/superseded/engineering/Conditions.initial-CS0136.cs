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
    public enum QueryKind { Tag, Flag, RecentEvent }
    public sealed class QueryReference : IEquatable<QueryReference>
    {
        public QueryKind Kind {get;} public string Argument {get;}
        public QueryReference(QueryKind kind,string argument)
        {if(!Enum.IsDefined(typeof(QueryKind),kind))throw new ArgumentException("Unknown query kind.");Syntax.Word(argument);Kind=kind;Argument=argument;}
        public bool Equals(QueryReference? other)=>other!=null&&Kind==other.Kind&&string.Equals(Argument,other.Argument,StringComparison.Ordinal);
        public override bool Equals(object? other)=>other is QueryReference value&&Equals(value);
        public override int GetHashCode()=>((int)Kind*397)^StringComparer.Ordinal.GetHashCode(Argument);
    }
    public sealed class QueryObservation
    {
        public QueryReference Reference {get;} public bool Value {get;}
        public QueryObservation(QueryReference reference,bool value){Reference=reference??throw new ArgumentNullException(nameof(reference));Value=value;}
    }
    // An immutable owner observation, never a callback, dispatcher or source of actions.
    public sealed class QuerySnapshot
    {
        private readonly Dictionary<QueryReference,bool> values=new Dictionary<QueryReference,bool>();
        public string Context {get;}
        public QuerySnapshot(string context,IEnumerable<QueryObservation> observations)
        {
            Syntax.Word(context);if(observations==null)throw new ArgumentNullException(nameof(observations));Context=context;
            foreach(var observation in observations)
            {if(observation==null||values.Count>=128||!values.TryAdd(observation.Reference,observation.Value))throw new ArgumentException("Bounded unique query observations required.");}
        }
        internal bool TryGet(QueryReference reference,out bool value)=>values.TryGetValue(reference,out value);
        internal bool Get(QueryReference reference)=>values[reference];
    }
    internal abstract class Node {internal abstract bool Evaluate(IReadOnlyDictionary<string,ConditionValue> facts,QuerySnapshot? queries);}
    internal sealed class Junction:Node
    {
        private readonly Node left,right;private readonly bool conjunction;
        internal Junction(Node left,Node right,bool conjunction){this.left=left;this.right=right;this.conjunction=conjunction;}
        internal override bool Evaluate(IReadOnlyDictionary<string,ConditionValue> facts,QuerySnapshot? queries)=>conjunction?left.Evaluate(facts,queries)&&right.Evaluate(facts,queries):left.Evaluate(facts,queries)||right.Evaluate(facts,queries);
    }
    internal sealed class Comparison:Node
    {
        private readonly string symbol,operation;private readonly ConditionValue literal;
        internal Comparison(string symbol,string operation,ConditionValue literal){this.symbol=symbol;this.operation=operation;this.literal=literal;}
        internal override bool Evaluate(IReadOnlyDictionary<string,ConditionValue> facts,QuerySnapshot? queries)
        {
            var value=facts[symbol];int comparison=value.Type==ConditionType.Boolean?value.Bool.CompareTo(literal.Bool):value.Type==ConditionType.Integer?value.Number.CompareTo(literal.Number):string.CompareOrdinal(value.Word,literal.Word);
            switch(operation){case "=":case "==":return comparison==0;case "!=":return comparison!=0;case "<":return comparison<0;case "<=":return comparison<=0;case ">":return comparison>0;case ">=":return comparison>=0;default:throw new InvalidOperationException("Compiled comparison required.");}
        }
    }
    internal sealed class QueryComparison:Node
    {
        private readonly QueryReference reference;private readonly bool wanted;
        internal QueryComparison(QueryReference reference,bool wanted){this.reference=reference;this.wanted=wanted;}
        internal override bool Evaluate(IReadOnlyDictionary<string,ConditionValue> facts,QuerySnapshot? queries)=>queries!.Get(reference)==wanted;
    }
    public sealed class CompiledCondition
    {
        private readonly Node expression;private readonly IReadOnlyDictionary<string,ConditionType> references;private readonly string? queryContext;
        public string Expression {get;}
        public IReadOnlyList<string> ReferencedSymbols {get;}
        public IReadOnlyList<QueryReference> ReferencedQueries {get;}
        internal CompiledCondition(string source,Node expression,Dictionary<string,ConditionType> references,string? queryContext,IEnumerable<QueryReference> queryReferences)
        {Expression=source;this.expression=expression;this.references=new ReadOnlyDictionary<string,ConditionType>(references);ReferencedSymbols=new ReadOnlyCollection<string>(new List<string>(references.Keys));this.queryContext=queryContext;ReferencedQueries=new ReadOnlyCollection<QueryReference>(new List<QueryReference>(queryReferences));}
        public ConditionResult Evaluate(IReadOnlyDictionary<string,ConditionValue> facts)=>Evaluate(facts,null);
        public ConditionResult Evaluate(IReadOnlyDictionary<string,ConditionValue> facts,QuerySnapshot? queries)
        {
            if(facts==null)throw new ArgumentNullException(nameof(facts));
            if(facts.Count>128)return new ConditionResult(false,false,"Fact context exceeds the declared bound.");
            // Copy by ordinal spelling instead of inheriting a caller's key comparer.
            var current=new Dictionary<string,ConditionValue>(StringComparer.Ordinal);
            foreach(var entry in facts)if(entry.Key==null||!current.TryAdd(entry.Key,entry.Value))return new ConditionResult(false,false,"Invalid or duplicate fact key.");
            // Check the whole referenced context before short-circuit evaluation.
            // Unknown is never a successful negative comparison or an OR fallback.
            foreach(var entry in references)if(!current.TryGetValue(entry.Key,out var value)||value==null||value.Type!=entry.Value)return new ConditionResult(false,false,"Missing or wrongly typed fact: "+entry.Key);
            if(queryContext!=null)
            {
                if(queries==null||!string.Equals(queryContext,queries.Context,StringComparison.Ordinal))return new ConditionResult(false,false,"Missing or foreign query context.");
                foreach(var reference in ReferencedQueries)if(!queries.TryGet(reference,out _))return new ConditionResult(false,false,"Missing declared query observation: "+reference.Argument);
            }
            return new ConditionResult(expression.Evaluate(current,queries),true,"All referenced facts and queries are present and typed.");
        }
    }
    public static class ConditionCompiler
    {
        public static CompiledCondition Compile(string source,IReadOnlyDictionary<string,ConditionType> symbols)
        {if(symbols==null||symbols.Count<1)throw new ArgumentException("A bounded declared symbol table is required.");return CompileCore(source,symbols,null,Array.Empty<QueryReference>());}
        public static CompiledCondition Compile(string source,IReadOnlyDictionary<string,ConditionType> symbols,string context,IEnumerable<QueryReference> queries)
        {Syntax.Word(context);if(queries==null)throw new ArgumentNullException(nameof(queries));return CompileCore(source,symbols,context,queries);}
        private static CompiledCondition CompileCore(string source,IReadOnlyDictionary<string,ConditionType> symbols,string? context,IEnumerable<QueryReference> queries)
        {
            if(source==null||source.Length<1||source.Length>4096)throw new ArgumentException("Condition text requires1..4096 characters.");
            if(symbols==null||symbols.Count>128)throw new ArgumentException("A bounded declared symbol table is required.");
            var declarations=new Dictionary<string,ConditionType>(StringComparer.Ordinal);
            foreach(var entry in symbols){Syntax.Symbol(entry.Key);if(!Enum.IsDefined(typeof(ConditionType),entry.Value)||!declarations.TryAdd(entry.Key,entry.Value))throw new ArgumentException("Invalid or duplicate symbol.");}
            var queryDeclarations=new HashSet<QueryReference>();
            foreach(var query in queries)if(query==null||queryDeclarations.Count>=128||!queryDeclarations.Add(query))throw new ArgumentException("Bounded unique query declarations required.");
            if(declarations.Count==0&&queryDeclarations.Count==0)throw new ArgumentException("A declared condition context is required.");
            var parser=new Parser(source,declarations,context,queryDeclarations);return parser.Compile();
        }
        private sealed class Parser
        {
            private readonly string source;private readonly List<string> tokens=new List<string>();private readonly Dictionary<string,ConditionType> symbols,references=new Dictionary<string,ConditionType>(StringComparer.Ordinal);private int index,depth;private readonly string? queryContext;private readonly HashSet<QueryReference> declaredQueries,queryReferences=new HashSet<QueryReference>();
            internal Parser(string source,Dictionary<string,ConditionType> symbols,string? context,HashSet<QueryReference> queries){this.source=source;this.symbols=symbols;queryContext=context;declaredQueries=queries;Tokenize();}
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
            internal CompiledCondition Compile(){if(tokens.Count==0)throw new ArgumentException("Empty condition is not authority.");Node node=Or();if(index!=tokens.Count)throw new ArgumentException("Trailing condition tokens.");return new CompiledCondition(source,node,references,queryContext,queryReferences);}
            private Node Or(){Node result=And();while(Eat("|"))result=new Junction(result,And(),false);return result;}
            private Node And(){Node result=Primary();while(Eat("&"))result=new Junction(result,Primary(),true);return result;}
            private Node Primary()
            {
                if(Eat("(")){if(++depth>32)throw new ArgumentException("Condition nesting limit exceeded.");Node result=Or();if(!Eat(")"))throw new ArgumentException("Missing closing parenthesis.");depth--;return result;}
                string name=Next();
                if(Peek()=="(")
                {
                    QueryKind kind;
                    switch(name){case "HasTag":kind=QueryKind.Tag;break;case "HasFlag":kind=QueryKind.Flag;break;case "HasRecentEvent":kind=QueryKind.RecentEvent;break;default:throw new ArgumentException("Unknown query function.");}
                    if(queryContext==null)throw new ArgumentException("Queries require an explicitly declared owner context.");
                    Eat("(");string argument=Next();Syntax.Word(argument);if(!Eat(")"))throw new ArgumentException("One exact query argument required.");
                    var reference=new QueryReference(kind,argument);if(!declaredQueries.Contains(reference))throw new ArgumentException("Unknown declared query ID.");
                    bool wanted=true;
                    if(Eat("=")||Eat("==")){string literal=Next();if(literal!="true"&&literal!="false")throw new ArgumentException("Exact Boolean query comparison required.");wanted=literal=="true";}
                    queryReferences.Add(reference);return new QueryComparison(reference,wanted);
                }
                if(!symbols.TryGetValue(name,out var type))throw new ArgumentException("Unknown condition symbol: "+name);
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
