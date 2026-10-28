using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using NorthStar.MemoryStudy;
using NorthStar.Conditions;
static class Program
{
 static readonly List<string> controls=new();
 static JsonElement View(Room r)=>JsonSerializer.SerializeToElement(r.Snapshot());
 static JsonElement B(Room r,string id)=>View(r).GetProperty("benches").EnumerateArray().Single(b=>b.GetProperty("id").GetString()==id);
 static bool F(JsonElement e,string n)=>e.GetProperty(n).GetBoolean();
 static int N(JsonElement e,string n)=>e.GetProperty(n).GetInt32();
 static void Check(string id,bool v){if(!v)throw new Exception(id);controls.Add(id);}
 static JsonElement Act(Room r,string command,string? bench=null){var d=new Dictionary<string,object?>{{"command",command},{"revision",N(View(r),"sequence")}};if(bench!=null)d.Add("bench",bench);return JsonSerializer.SerializeToElement(r.Execute(JsonSerializer.SerializeToElement(d)));}
 static string Facts(Room r)=>JsonSerializer.Serialize(new{turn=View(r).GetProperty("turn"),parts=View(r).GetProperty("parts"),coins=View(r).GetProperty("coins"),benches=View(r).GetProperty("benches"),history=View(r).GetProperty("history")});
 static void Main(string[] args)
 {
  if(args.Length!=2)throw new ArgumentException("Output JSON and actual source assay required");
  var independent=new Room();var explicitIndependent=new Room("independent");Check("Default and explicit independent policy have identical original observation",View(independent).GetRawText()==View(explicitIndependent).GetRawText());
  Act(independent,"help","east");Check("Independent actual east help opens its paid service",F(B(independent,"east"),"eligible"));Act(independent,"serve","east");Check("Independent actual east service pays turn and coin",F(B(independent,"east"),"delivered")&&N(View(independent),"coins")==1&&N(View(independent),"turn")==2);
  var ordered=new Room("ordered");Check("Ordered policy starts with no supplied conditions or goods",!F(B(ordered,"east"),"condition_satisfied")&&!F(B(ordered,"east"),"delivered"));Act(ordered,"help","east");Check("Real east help cannot stand in for actual west delivery",F(B(ordered,"east"),"recent")&&!F(B(ordered,"east"),"condition_satisfied")&&!F(B(ordered,"east"),"eligible"));
  string before=Facts(ordered);Check("Ordered east refusal spends no turn part coin or fitting",!F(Act(ordered,"serve","east"),"accepted")&&Facts(ordered)==before);
  Act(ordered,"help","west");Check("West help alone does not satisfy the other-delivered fact",!F(B(ordered,"east"),"condition_satisfied"));Act(ordered,"serve","west");Check("Actual west service changes east condition but does not supply east fitting",F(B(ordered,"east"),"condition_satisfied")&&F(B(ordered,"east"),"eligible")&&!F(B(ordered,"east"),"delivered"));
  Check("Actual rule is visible and complete",F(B(ordered,"east"),"condition_complete")&&B(ordered,"east").GetProperty("condition_expression").GetString()!.Contains("OtherDelivered=true"));
  Act(ordered,"serve","east");Check("Eligibility checked before actual one-turn cost can deliver at expiry boundary",F(B(ordered,"east"),"delivered")&&!F(B(ordered,"east"),"recent")&&N(View(ordered),"turn")==4&&N(View(ordered),"coins")==0);
  before=Facts(ordered);Check("Acquired fitting cannot be supplied again by true historical condition",!F(Act(ordered,"serve","east"),"accepted")&&Facts(ordered)==before);
  var expired=new Room("ordered");Act(expired,"help","east");Act(expired,"wait");Act(expired,"help","west");Act(expired,"serve","west");Check("Other delivery never substitutes for expired local evidence",F(B(expired,"west"),"delivered")&&!F(B(expired,"east"),"recent")&&!F(B(expired,"east"),"eligible"));before=Facts(expired);Check("Expired refusal has no costs or acquired output",!F(Act(expired,"serve","east"),"accepted")&&Facts(expired)==before);
  Act(expired,"demonstrate","east");Check("Actual paid demonstration can renew the ordered opportunity",F(B(expired,"east"),"eligible"));Act(expired,"decline","east");Check("Withdrawal retains west output while closing actual east authority",F(B(expired,"west"),"delivered")&&!F(B(expired,"east"),"condition_satisfied")&&!F(B(expired,"east"),"eligible"));
  before=Facts(expired);var stale=expired.Execute(JsonSerializer.SerializeToElement(new{command="serve",revision=0,bench="east"}));Check("Stale intent cannot pay for a changed condition",!F(JsonSerializer.SerializeToElement(stale),"accepted")&&Facts(expired)==before);
  foreach(string extra in new[]{"policy","OtherDelivered","condition"}){string raw="{\"command\":\"serve\",\"revision\":"+N(View(expired),"sequence")+",\"bench\":\"east\",\""+extra+"\":true}";try{expired.Execute(JsonDocument.Parse(raw).RootElement);throw new Exception("Forged fields accepted");}catch(ArgumentException){}Check("Forged "+extra+" cannot change private facts",Facts(expired)==before);}
  try{_=new Room("Ordered");throw new Exception("Unknown policy accepted");}catch(ArgumentException){}Check("Unknown startup policy refuses rather than silently falling back",true);
  var source=JsonDocument.Parse(File.ReadAllText(args[1]));var rows=new List<object>();var symbols=new Dictionary<string,ConditionType>{{"Mood",ConditionType.String},{"Stress",ConditionType.Integer},{"Trust_Player",ConditionType.Integer}};var context=new Dictionary<string,ConditionValue>{{"Mood",ConditionValue.Text("CALM")},{"Stress",ConditionValue.Integer(20)},{"Trust_Player",ConditionValue.Integer(50)}};
  foreach(var row in source.RootElement.GetProperty("nonempty_scalar_comparison_rows").EnumerateArray()){string expression=row.GetProperty("expression").GetString()!;var c=ConditionCompiler.Compile(expression,symbols);var result=c.Evaluate(context);if(!result.Complete)throw new Exception("Exact scalar source syntax not evaluated");rows.Add(new{variant_id=row.GetProperty("variant_id").GetString(),expression,result.Satisfied,result.Complete});}
  Check("Eight exact preserved scalar rows compile in explicit declared context",rows.Count==8);
  File.WriteAllText(args[0],JsonSerializer.Serialize(new{schema_version=1,checks=new{passed=controls.Count,failed=0},controls,source_scalar_rows=rows,source_context=new{Mood="CALM",Stress=20,Trust_Player=50},ordered=View(ordered),expired=View(expired),limits="Source scalar syntax in a declared typed destination context, not Ruby/coercion/function/scoring equivalence, actual source NPCs or human validation."},new JsonSerializerOptions{WriteIndented=true})+"\n");Console.WriteLine($"PASS: {controls.Count} actual condition service controls");
 }
}
