using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using NorthStar.Conditions;
static class Program
{
 static readonly List<string> controls=new();
 static readonly Dictionary<string,ConditionType> symbols=new(StringComparer.Ordinal){{"Helped",ConditionType.Boolean},{"Support",ConditionType.Boolean},{"Recent",ConditionType.Boolean},{"OtherDelivered",ConditionType.Boolean},{"Coins",ConditionType.Integer},{"Mood",ConditionType.String},{"Stress",ConditionType.Integer},{"Trust_Player",ConditionType.Integer}};
 static Dictionary<string,ConditionValue> Facts()=>new(StringComparer.Ordinal){{"Helped",ConditionValue.Boolean(true)},{"Support",ConditionValue.Boolean(true)},{"Recent",ConditionValue.Boolean(true)},{"OtherDelivered",ConditionValue.Boolean(false)},{"Coins",ConditionValue.Integer(2)},{"Mood",ConditionValue.Text("CALM")},{"Stress",ConditionValue.Integer(50)},{"Trust_Player",ConditionValue.Integer(40)}};
 static void Check(string id,bool value){if(!value)throw new Exception(id);if(controls.Contains(id))throw new Exception("Unique control identity required");controls.Add(id);}
 static ConditionResult Run(string expression,IReadOnlyDictionary<string,ConditionValue>? facts=null)=>ConditionCompiler.Compile(expression,symbols).Evaluate(facts??Facts());
 static void Reject(string expression,string id){bool rejected=false;try{ConditionCompiler.Compile(expression,symbols);}catch(ArgumentException){rejected=true;}Check(id,rejected);}
 static void Main(string[] args)
 {
  if(args.Length!=1)throw new ArgumentException("Output JSON required");
  Check("Actual default typed rule accepts complete observed facts",Run("Helped=true & Support=true & Recent=true").Satisfied);
  Check("Declared ordered-bench rule refuses until other delivery",!Run("Helped=true & Support=true & Recent=true & OtherDelivered=true").Satisfied);
  var facts=Facts();facts["OtherDelivered"]=ConditionValue.Boolean(true);Check("Observed other delivery satisfies ordered rule",Run("Helped=true & Support=true & Recent=true & OtherDelivered=true",facts).Satisfied);
  facts["Recent"]=ConditionValue.Boolean(false);Check("Current expiry refuses without erasing other known facts",!Run("Helped=true & Support=true & Recent=true & OtherDelivered=true",facts).Satisfied);
  Check("Equals alias retains Boolean equality",Run("Helped==true").Satisfied);
  Check("Exact Boolean inequality uses present fact",Run("OtherDelivered!=true").Satisfied);
  Check("Integer greater-or-equal includes boundary",Run("Trust_Player>=40").Satisfied);
  Check("Integer less-or-equal includes boundary",Run("Coins<=2").Satisfied);
  Check("Integer greater comparison is strict",!Run("Coins>2").Satisfied);
  Check("Integer less comparison is strict",!Run("Coins<2").Satisfied);
  Check("Integer equals remains typed",Run("Coins=2").Satisfied);
  Check("Integer inequality remains typed",Run("Coins!=3").Satisfied);
  Check("Source-shaped Mood inequality uses exact known token",Run("Mood!=OUTBURST").Satisfied);
  Check("String comparison is ordinal case-sensitive",!Run("Mood=calm").Satisfied);
  Check("String comparison accepts exact equality",Run("Mood==CALM").Satisfied);
  Check("Conjunction binds more tightly than disjunction",Run("Helped=true | Support=false & Recent=false").Satisfied);
  Check("Parentheses change grouping rather than being ignored",!Run("(Helped=true | Support=false) & Recent=false").Satisfied);
  Check("Nested parentheses preserve actual grouping",Run("((Helped=true & Recent=true) | (Mood=OUTBURST & Coins=0))").Satisfied);
  Check("ASCII formatting whitespace does not change grammar",Run(" \tHelped = true\r\n& Coins >= 2 ").Satisfied);
  var limits=Facts();limits["Coins"]=ConditionValue.Integer(long.MinValue);Check("Signed minimum integer does not overflow comparison",Run("Coins=-9223372036854775808",limits).Satisfied);
  limits["Coins"]=ConditionValue.Integer(long.MaxValue);Check("Signed maximum integer remains exact",Run("Coins=9223372036854775807",limits).Satisfied);
  foreach(var pair in new[]{("","Empty condition is not true"),("   ","Whitespace-only condition is not true"),("Helped=true#","Unknown punctuation is not skipped"),("Helped=true;Coins=0","Statement punctuation cannot smuggle a second expression"),("Helped=true Coins=0","Trailing comparison is rejected"),("Helped=true)","Trailing closing parenthesis is rejected"),("(Helped=true","Missing closing parenthesis is rejected"),("()","Empty parentheses do not become true"),("Helped=true &","Missing conjunction operand is rejected"),("Helped=true |","Missing disjunction operand is rejected"),("& Helped=true","Leading conjunction is rejected"),("Helped=true && Recent=true","Doubled conjunction is not silently repaired"),("Helped=true || Recent=true","Doubled disjunction is not silently repaired"),("Helped","Bare symbol is not implicit true"),("Helped=","Missing typed literal is rejected"),("Helped===true","Extra comparison token is rejected"),("Helped!true","Lone bang is not skipped"),("Unknown!=true","Undeclared negative symbol cannot grant authority"),("helped=true","Symbol case is exact"),("Helped=TRUE","Boolean literal case is explicit"),("Helped=1","Integer does not coerce to Boolean"),("Coins=true","Boolean does not coerce to integer"),("Coins=1.5","Fraction does not coerce to integer"),("Coins=9223372036854775808","Integer overflow is rejected"),("Helped>true","Boolean ordering is rejected"),("Mood<CALM","String ordering is outside selected grammar"),("Mood='CALM'","Quoted text is outside selected bare-token grammar"),("HasFlag(Helped)=true","Function dispatch is not silently mapped to scalar facts"),("Helped=true\u00a0& Recent=true","Non-ASCII whitespace is not skipped"),("Hélped=true","Non-ASCII symbol is rejected"),("Helped=true\0","Embedded null is rejected")})Reject(pair.Item1,pair.Item2);
  Reject(new string('(',33)+"Helped=true"+new string(')',33),"Nesting depth is bounded before evaluation");
  Reject(string.Concat(Enumerable.Repeat("Coins=0|",257))+"Coins=0","Token work is bounded");
  Reject(new string(' ',4097),"Condition text allocation is bounded");
  var missing=Facts();missing.Remove("Mood");var result=Run("Mood!=OUTBURST",missing);Check("Missing string never satisfies negative comparison",!result.Complete&&!result.Satisfied);
  missing=Facts();missing.Remove("Helped");result=Run("Helped!=false",missing);Check("Missing Boolean never satisfies negative comparison",!result.Complete&&!result.Satisfied);
  missing=Facts();missing.Remove("Coins");result=Run("Coins!=0",missing);Check("Missing integer never satisfies negative comparison",!result.Complete&&!result.Satisfied);
  result=Run("Helped=true | Coins=0",missing);Check("True OR branch cannot hide missing referenced authority",!result.Complete&&!result.Satisfied);
  result=Run("Helped=false & Coins=0",missing);Check("False AND result still reports incomplete context",!result.Complete&&!result.Satisfied);
  var wrong=Facts();wrong["Coins"]=ConditionValue.Text("2");result=Run("Coins=2",wrong);Check("Wrong fact type is unknown rather than coerced",!result.Complete&&!result.Satisfied);
  Check("False with complete facts is distinct from unknown",Run("Coins=0").Complete&&!Run("Coins=0").Satisfied);
  var declaration=new Dictionary<string,ConditionType>{{"Helped",ConditionType.Boolean}};var compiled=ConditionCompiler.Compile("Helped=true",declaration);declaration["Helped"]=ConditionType.Integer;Check("Compiled declarations are isolated from later schema mutation",compiled.Evaluate(Facts()).Satisfied);
  Check("Compiled expression and unique references remain inspectable",compiled.Expression=="Helped=true"&&compiled.ReferencedSymbols.SequenceEqual(new[]{"Helped"}));
  var changed=Facts();changed["Helped"]=ConditionValue.Boolean(false);Check("Evaluation reads current facts rather than cached result",!compiled.Evaluate(changed).Satisfied);
  bool badSchema=false;try{ConditionCompiler.Compile("Helped=true",new Dictionary<string,ConditionType>{{"Helped",(ConditionType)100}});}catch(ArgumentException){badSchema=true;}Check("Unknown declared type cannot compile",badSchema);
  badSchema=false;try{ConditionCompiler.Compile("Helped=true",new Dictionary<string,ConditionType>{{"1Helped",ConditionType.Boolean}});}catch(ArgumentException){badSchema=true;}Check("Invalid declared symbol cannot compile",badSchema);
  var insensitive=new Dictionary<string,ConditionValue>(StringComparer.OrdinalIgnoreCase){{"helped",ConditionValue.Boolean(true)}};result=compiled.Evaluate(insensitive);Check("Fact key case cannot be widened by caller dictionary comparer",!result.Complete&&!result.Satisfied);
  var excessive=new Dictionary<string,ConditionValue>();for(int n=0;n<129;n++)excessive["Fact"+n]=ConditionValue.Boolean(true);result=compiled.Evaluate(excessive);Check("Fact context work is bounded",!result.Complete&&!result.Satisfied);
  File.WriteAllText(args[0],JsonSerializer.Serialize(new{schema_version=1,kind="actual_typed_condition_library",checks=new{passed=controls.Count,failed=0},controls,limits="Library controls, not source Ruby/RGSS execution, full dialogue scoring/functions, human assessment or Unity/Windows delivery."},new JsonSerializerOptions{WriteIndented=true})+"\n");Console.WriteLine($"PASS: {controls.Count} typed condition controls");
 }
}
