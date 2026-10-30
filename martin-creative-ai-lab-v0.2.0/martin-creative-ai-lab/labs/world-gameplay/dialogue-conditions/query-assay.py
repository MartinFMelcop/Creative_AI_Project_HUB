#!/usr/bin/env python3
"""Inspect literal named-query source branches; never execute historical Ruby.

The Python evaluator covers only fully known inspected source syntax. Strict C#
unknown/typing/suffix refusals are a separately declared destination contract.
"""
import argparse,csv,hashlib,io,itertools,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'references/rave-master/snapshots/36af1651271422ae33856e8b5d7b45702215f165/source'
FILES=['RM_ACT1/DATA/DEV/RGSS/RM_DIALOGUE_SCORING_RUNTIME.rb','RM_DIST/RMXP_BASE/ScriptsCustom/RM_DIALOGUE_SCORING_RUNTIME.rb','RM_ACT1/DATA/DEV/DIALOGUE_VARIANTS.csv','RM_DIST/RMXP_BASE/Data/RM_CSV/DIALOGUE_VARIANTS.csv']
PINS=['07682a3205ea2850d748e4f3ffeef7febe51df1ddb10d5e8689bef7d26d1a735']*2+['7434223aa7fe25a8449796d1648b04257efa355bced6d62a0224e3b3f2606787']*2
FUNCTIONS=('HasTag','HasFlag','HasRecentEvent')
QUERY=re.compile(r'\b(HasTag|HasFlag|HasRecentEvent)\(([A-Za-z0-9_\-@:.]+)\)')
TOKEN=re.compile(r'\s*(==|!=|>=|<=|[()&|=<>]|[A-Za-z0-9_\-@:.]+)')
def fingerprints():return {str((BASE/n).relative_to(ROOT)):hashlib.sha256((BASE/n).read_bytes()).hexdigest() for n in FILES}
def evaluate(expression,queries,facts):
    """Independent small recursive evaluator, only the fully-known literal subset."""
    pos=0;tokens=[]
    while pos<len(expression):
        m=TOKEN.match(expression,pos)
        if not m:raise ValueError('Unknown oracle character')
        tokens.append(m.group(1));pos=m.end()
    q={(q['function'],q['argument']):q['value'] for q in queries};f={v['name']:v['value'] for v in facts};i=0
    def eat(value):
        nonlocal i
        if i<len(tokens) and tokens[i]==value:i+=1;return True
        return False
    def take():
        nonlocal i
        if i>=len(tokens):raise ValueError('Incomplete oracle expression')
        t=tokens[i];i+=1;return t
    def atom():
        if eat('('):
            value=disjunction()
            if not eat(')'):raise ValueError('Unclosed oracle grouping')
            return value
        name=take()
        if name in FUNCTIONS:
            if not eat('('):raise ValueError('Oracle call opening required')
            arg=take()
            if not eat(')'):raise ValueError('Oracle call closing required')
            if (name,arg) not in q:raise ValueError('Known-source oracle needs complete declared queries')
            lhs=q[(name,arg)];op=take();right=take()
            if op not in ('=','==') or right not in ('true','false'):raise ValueError('Unsupported known source query comparison')
            return lhs==(right=='true')
        if name not in f:raise ValueError('Known-source oracle needs complete scalar facts')
        op=take();rhs=take();lhs=f[name]
        if isinstance(lhs,int) and not isinstance(lhs,bool):rhs=int(rhs)
        if op in ('=','=='):return lhs==rhs
        if op=='!=':return lhs!=rhs
        if op=='>':return lhs>rhs
        if op=='<':return lhs<rhs
        if op=='>=':return lhs>=rhs
        if op=='<=':return lhs<=rhs
        raise ValueError('Unknown oracle comparison')
    def conjunction():
        result=atom()
        while eat('&'):
            right=atom();result=result and right
        return result
    def disjunction():
        result=conjunction()
        while eat('|'):
            right=conjunction();result=result or right
        return result
    result=disjunction()
    if i!=len(tokens):raise ValueError('Trailing oracle tokens')
    return result

def verify_results(cases,actual):
    if not isinstance(actual,list) or len(actual)!=len(cases):raise ValueError('Exact query result count required')
    by={x['id']:x for x in actual}
    if len(by)!=len(actual) or set(by)!={c['id'] for c in cases}:raise ValueError('Exact unique query case identities required')
    for case in cases:
        row=by[case['id']];expected=evaluate(case['expression'],case['queries'],case['facts'])
        if type(row.get('complete')) is not bool or type(row.get('satisfied')) is not bool or not row['complete'] or row['satisfied']!=expected:raise ValueError('Actual query result differs: '+case['id'])

def inspect():
    before=fingerprints()
    if list(before.values())!=PINS:raise ValueError('Exact preserved query source pins differ')
    texts=[(BASE/n).read_text(encoding='utf-8-sig') for n in FILES]
    if texts[0]!=texts[1] or texts[2]!=texts[3]:raise ValueError('DEV/DIST source/table identity changed')
    runtime=texts[0]
    anchors={
      'three_function_dispatch':'tok[1] == "HasTag" || tok[1] == "HasFlag" || tok[1] == "HasRecentEvent"',
      'missing_tag_provider_false':'has = (tagset != nil && tagset[node[1]] == true)',
      'missing_flag_provider_false':'has = (flags != nil && flags[node[1]] == true)',
      'recent_provider_named_subject':'has = RM_RecentEvents.has?(eid, npc_id)',
      'recent_numeric_suffix_ignored':'eid = $1',
      'recent_exception_becomes_false':'rescue\n            has = false',
    }
    for label,text in anchors.items():
        if text not in runtime:raise ValueError('Exact source branch changed: '+label)
    rows=list(csv.DictReader(io.StringIO(texts[2])));source_rows=[r for r in rows if QUERY.search(r['ConditionsExpr'])]
    if len(source_rows)!=19:raise ValueError('Actual query-bearing row count changed')
    cases=[]
    for row in source_rows:
        expression=row['ConditionsExpr'];refs=list(dict.fromkeys(QUERY.findall(expression)))
        moods=['CALM','OUTBURST','OBSESSED'] if re.search(r'\bMood\b',expression) else [None]
        for mood,values in itertools.product(moods,itertools.product([False,True],repeat=len(refs))):
            queries=[{'function':fn,'argument':arg,'value':value} for (fn,arg),value in zip(refs,values)]
            facts=[] if mood is None else [{'name':'Mood','type':'String','value':mood}]
            cases.append({'id':'source_'+row['VariantID']+'_'+str(len(cases)+1),'category':'actual_variant_expression_known_context','source_variant_ids':[row['VariantID']],'expression':expression,'queries':queries,'facts':facts,'expected':{'complete':True,'satisfied':evaluate(expression,queries,facts)}})
    for function in FUNCTIONS:
        for value,want in itertools.product([False,True],repeat=2):
            expression=f'{function}(KNOWN_QUERY)={str(want).lower()}';queries=[{'function':function,'argument':'KNOWN_QUERY','value':value}]
            cases.append({'id':f'helper_{function}_{int(value)}_{int(want)}','category':'declared_runtime_helper_branch_probe_not_table_row','source_variant_ids':[],'expression':expression,'queries':queries,'facts':[],'expected':{'complete':True,'satisfied':evaluate(expression,queries,[])}})
    good=[{'id':c['id'],**c['expected']} for c in cases];verify_results(cases,good)
    negatives=[]
    for name,actual in [('false_result',[dict(x) for x in good]),('missing_case',good[:-1]),('duplicate_case',good[:-1]+[good[0]])]:
        if name=='false_result':actual[0]['satisfied']=not actual[0]['satisfied']
        try:verify_results(cases,actual)
        except ValueError as e:negatives.append({'id':name,'detected':True,'reason':str(e)})
        else:raise ValueError('Defective result escaped '+name)
    if before!=fingerprints():raise ValueError('Source identity changed during inspection')
    return {'schema_version':1,'kind':'known_named_query_source_protocol','source_sha256':before,'source_stable':True,'variants_identical':True,'actual_variant_rows':len(rows),'query_bearing_variant_rows':len(source_rows),'source_function_counts':{fn:sum(fn+'(' in r['ConditionsExpr'] for r in source_rows) for fn in FUNCTIONS},'actual_source_expressions':[{'variant_id':r['VariantID'],'expression':r['ConditionsExpr']} for r in source_rows],'source_branches':{k:{'literal':v,'first_line':runtime[:runtime.index(v)].count('\n')+1} for k,v in anchors.items()},'cases':cases,'case_count':len(cases),'python_known_subset_passed':len(cases),'result_verifier_negatives':negatives,'strict_destination_differences':['Unknown query/provider is incomplete, not false; query=false cannot authorize it.','Prevalidate every referenced query before short-circuit.','No source numeric-suffix normalization or implicit global/missing-subject fallback as private named authority.','Only declared exact function+argument references; no arbitrary invocation or Ruby coercion.'],'ruby_executed':False,'rgss_executed':False,'rmxp_executed':False,'limits':'Source-shaped known contexts and helper-branch probes evaluated by independent bounded Python, not historical runtime execution, source whole scoring/catalog, people, population findings or approved fiction.'}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path);p.add_argument('--verify-result',type=Path);a=p.parse_args()
    if not a.output and not a.verify_result:p.error('Need --output or --verify-result')
    result=inspect()
    if a.verify_result:
        actual=json.loads(a.verify_result.read_text());verify_results(result['cases'],actual['source_results']);print('PASS: actual C# SAME query-source cases match independent Python')
    if a.output:
        out=a.output.resolve()
        if out==ROOT or ROOT in out.parents or out.exists():p.error('New external output file required')
        out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n');print(f'PASS: {result["case_count"]} known query cases;19actual source rows; no Ruby/RGSS/RMXP')
if __name__=='__main__':main()
