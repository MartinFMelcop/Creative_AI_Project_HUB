#!/usr/bin/env python3
"""Model a bounded source-memory subset and compare the SAME cases with actual C#."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[3]
SOURCE=ROOT/'references/rave-master/snapshots/36af1651271422ae33856e8b5d7b45702215f165/source'
NAMES=['RM_ACT1/DATA/DEV/RGSS/RM_FLAGS_EVENTS_RUNTIME.rb','RM_DIST/RMXP_BASE/ScriptsCustom/RM_FLAGS_EVENTS_RUNTIME.rb','RM_ACT1/DATA/DEV/MEMORY_FLAGS.csv','RM_DIST/RMXP_BASE/Data/RM_CSV/MEMORY_FLAGS.csv','RM_ACT1/DATA/DEV/RECENT_EVENTS.csv','RM_DIST/RMXP_BASE/Data/RM_CSV/RECENT_EVENTS.csv']

def hashes():return {str((SOURCE/n).relative_to(ROOT)):hashlib.sha256((SOURCE/n).read_bytes()).hexdigest() for n in NAMES}
def ttl(s):return None if not s.strip() else int(float(s))
def cases_and_assay():
    for a,b in zip(NAMES[::2],NAMES[1::2]):
        if (SOURCE/a).read_bytes()!=(SOURCE/b).read_bytes():raise ValueError('Preserved variants differ; revisit selected contract')
    text=(SOURCE/NAMES[0]).read_text()
    bindings=['scope = scope || (d ? d["Scope"] : "GLOBAL")','npc_id = npc_id || "NPC_UNKNOWN"','exp > @turn','if npc_id == nil || e["npc"] == nil || e["npc"] == npc_id','n = 1 if n < 1','before != @events.size']
    if not all(x in text for x in bindings):raise ValueError('Source method changed')
    flags=list(csv.DictReader((SOURCE/NAMES[2]).open()));events=list(csv.DictReader((SOURCE/NAMES[4]).open()))
    if len(flags)!=9 or len(events)!=10 or any(r['DefaultValue']!='0' for r in flags):raise ValueError('Actual source definition observations changed')
    cases=[]
    for r in flags:
        fid=r['FlagID'];scope={'GLOBAL':'Global','NPC':'Npc','RELATION':'Relation'}[r['Scope']];t=ttl(r['TTL_Turns']);subject=None if scope=='Global' else 'west'
        ops=[{'op':'any','subject':'west'},{'op':'set','subject':subject,'value':True},{'op':'any','subject':'west'},{'op':'any','subject':'east'},{'op':'any','subject':None}]
        if t is None:ops += [{'op':'tick','count':50},{'op':'any','subject':'west'},{'op':'clear','subject':subject},{'op':'any','subject':'west'}]
        else:ops += [{'op':'tick','count':t-1},{'op':'any','subject':'west'},{'op':'tick','count':1},{'op':'any','subject':'west'}]
        cases.append({'id':fid+'-declared-scope','kind':'flag','definition':{'id':fid,'scope':scope,'ttl':t},'operations':ops})
        cases.append({'id':fid+'-explicit-global-union','kind':'flag','definition':{'id':fid,'scope':scope,'ttl':t},'operations':[{'op':'set','subject':None,'scope':'Global','value':True},{'op':'set','subject':'west','scope':'Npc','value':False},{'op':'any','subject':'west'},{'op':'exact','subject':'west','scope':'Npc'},{'op':'clear','subject':None,'scope':'Global'},{'op':'any','subject':'west'}]})
        cases.append({'id':fid+'-scope-separation','kind':'flag','definition':{'id':fid,'scope':scope,'ttl':t},'operations':[{'op':'set','subject':'west','scope':'Npc','value':True},{'op':'set','subject':'west','scope':'Relation','value':True},{'op':'clear','subject':'west','scope':'Npc'},{'op':'any','subject':'west'},{'op':'exact','subject':'west','scope':'Npc'},{'op':'exact','subject':'west','scope':'Relation'},{'op':'tick','count':0},{'op':'any','subject':'west'}]})
    for r in events:
        eid=r['EventID'];t=ttl(r['TTL_Turns']);definition={'id':eid,'ttl':t}
        cases.append({'id':eid+'-named-expiry','kind':'event','definition':definition,'operations':[{'op':'push','subject':'west'},{'op':'any','subject':'west'},{'op':'any','subject':'east'},{'op':'any','subject':None},{'op':'tick','count':t-1},{'op':'any','subject':'west'},{'op':'tick','count':1},{'op':'any','subject':'west'}]})
        cases.append({'id':eid+'-global-wildcard','kind':'event','definition':definition,'operations':[{'op':'push','subject':None},{'op':'any','subject':'east'},{'op':'exact','subject':'east'},{'op':'clear','subject':'east'},{'op':'any','subject':'east'},{'op':'clear','subject':None},{'op':'any','subject':'east'}]})
        cases.append({'id':eid+'-named-clear','kind':'event','definition':definition,'operations':[{'op':'push','subject':'west'},{'op':'push','subject':'east'},{'op':'clear','subject':'west'},{'op':'any','subject':'west'},{'op':'exact','subject':'east'},{'op':'clear','subject':None},{'op':'any','subject':None}]})
    assay={'schema_version':1,'source_sha256':hashes(),'variants_identical':True,'flag_definitions':len(flags),'event_definitions':len(events),'default_values':sorted({r['DefaultValue'] for r in flags}),'default_value_used_by_helper':False,'actual_flag_ttls':sorted({str(ttl(r['TTL_Turns'])) for r in flags}),'actual_event_ttls':sorted({ttl(r['TTL_Turns']) for r in events}),'source_bindings':bindings,'source_counterexamples':[{'id':'unknown-flag-global-fallback','source_result':'set unknown true with no scope creates a GLOBAL entry','destination_policy':'unknown identity rejects; no global witness grant'},{'id':'missing-named-subject','source_result':'NPC and RELATION writes without subject share NPC_UNKNOWN','destination_policy':'named context required, not silently grouped'},{'id':'unspecified-event-wildcard','source_result':'push known event with npc=nil satisfies has?(id,any_named_npc)','destination_policy':'Any retains explicit source compatibility; Exact excludes global event as named witness evidence'}],'limits':'Independent Python model of inspected source branches with known typed IDs and bounded integers. No Ruby/RGSS/RMXP execution, moral/source fiction, full permissive coercion, persistence, account or human testimony.'}
    return cases,assay

def model(case):
    d=case['definition'];turn=0;flags={};events=[];out=[]
    for op in case['operations']:
        action=op['op'];subject=op.get('subject');scope=op.get('scope',d.get('scope'))
        if action=='tick':turn+=max(1,op['count'])
        elif case['kind']=='flag':
            key=(scope,None if scope=='Global' else subject)
            if action=='set':flags[key]=(op['value'],None if d['ttl'] is None else turn+d['ttl'])
            elif action=='clear':flags.pop(key,None)
            else:
                active=lambda k:k in flags and flags[k][0] and (flags[k][1] is None or flags[k][1]>turn)
                out.append(active(key) if action=='exact' else active(('Global',None)) or subject is not None and (active(('Npc',subject)) or active(('Relation',subject))))
        else:
            if action=='push':events.append((subject,None if d['ttl'] is None else turn+d['ttl']))
            elif action=='clear':events=[e for e in events if not(subject is None or e[0]==subject)]
            else:out.append(any((expiry is None or expiry>turn) and ((owner==subject) if action=='exact' else subject is None or owner is None or owner==subject) for owner,expiry in events))
    return {'id':case['id'],'observations':out,'turn':turn}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--dotnet',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();output=a.output.resolve()
    if output==ROOT or ROOT in output.parents:p.error('New external output required')
    output.mkdir(parents=True,exist_ok=False);before=hashes();cases,assay=cases_and_assay();expected=[model(c) for c in cases]
    (output/'cases.json').write_text(json.dumps(cases,indent=2)+'\n');(output/'python.json').write_text(json.dumps(expected,indent=2)+'\n')
    command=[a.dotnet,str(ROOT/'north-star/memory-study/Checks/bin/Release/net10.0/NorthStar.MemoryChecks.dll'),'--cases',str(output/'cases.json'),str(output/'csharp.json')]
    r=subprocess.run(command,capture_output=True,text=True,timeout=60);(output/'execution.json').write_text(json.dumps({'command':command,'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr},indent=2)+'\n')
    if r.returncode:raise ValueError('Actual C# source-case consumer failed')
    actual=json.loads((output/'csharp.json').read_text())
    if actual!=expected:raise ValueError('SAME source cases differ between Python and C#')
    if hashes()!=before:raise ValueError('Protected source mutated during execution')
    # An isolated wrong result must not pass the same comparison used above.
    forged=json.loads(json.dumps(actual));forged[0]['observations'][0]=not forged[0]['observations'][0]
    if forged==expected:raise ValueError('False result escaped verifier')
    (output/'source-assay.json').write_text(json.dumps(assay,indent=2)+'\n')
    (output/'results.json').write_text(json.dumps({'schema_version':1,'kind':'scoped_memory_source_parity','same_cases':len(cases),'same_queries':sum(len(c['observations']) for c in expected),'exact_agreement':True,'false_result_detected':True,'source_stable':True,'source_sha256':before,'limits':assay['limits']},indent=2)+'\n')
    print('PASS:',len(cases),'SAME Python/C# source cases and false-result detection')
if __name__=='__main__':main()
