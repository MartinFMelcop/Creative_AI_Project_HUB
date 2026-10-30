#!/usr/bin/env python3
"""Inspect preserved response requirements and reject false actual-consumer results."""
import argparse,copy,csv,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
SOURCE='references/rave-master/snapshots/36af1651271422ae33856e8b5d7b45702215f165/source/RM_CORE/DATA/CORE/REGRAS_DE_COMBATE.csv'
def verify(x):
    if x.get('checks')!={'passed':60,'failed':0}:raise ValueError('Declared actual native control set differs')
    for name,wanted in {'cast':{'round':0,'hp':100,'enemyHp':96,'charges':1},'released':{'round':1,'hp':71,'enemyHp':96,'charges':1},'winning':{'round':3,'hp':33,'enemyHp':0,'charges':0,'outcome':'secured'},'yielding':{'round':4,'hp':0,'enemyHp':24,'charges':1,'outcome':'defeated'},'heated':{'round':3,'enemyHp':52,'charges':0}}.items():
        if any(x.get(name,{}).get(k)!=v for k,v in wanted.items()):raise ValueError('Actual gameplay result differs: '+name)
    if x['cast']['pending']!={'ward':True,'items':2} or x['cast']['resolution']!=[]:raise ValueError('Pending cast fabricated resolution')
    if x['released']['resolution']!=['Ward:applied','CommittedStrike:cancelled']:raise ValueError('Countered resolution order differs')
    if x['winning']['resolution']!=['BreakWard:applied','Ward:cancelled','CommittedStrike:applied']:raise ValueError('Paid LIFO order differs')
def main():
    p=argparse.ArgumentParser();p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.resolve().is_relative_to(ROOT) or a.output.exists():p.error('New external result file required')
    rows={r['RuleID']:r for r in csv.DictReader((ROOT/SOURCE).open())};selected=[rows[k] for k in ['STK-001','STK-002','STK-007','CST-001']]
    x=json.loads(a.native.read_text());verify(x);negatives=[]
    for name in ['false-refund','premature-hit','fifo-order']:
        bad=copy.deepcopy(x)
        if name=='false-refund':bad['released']['charges']=2
        elif name=='premature-hit':bad['cast']['enemyHp']=48
        else:bad['winning']['resolution'].reverse()
        try:verify(bad)
        except ValueError as e:negatives.append({'id':name,'detected':True,'reason':str(e)})
        else:raise ValueError('False actual result escaped')
    a.output.write_text(json.dumps({'schema_version':1,'kind':'observed_requirement_and_actual_result_assay','evidence_category':'OBSERVED_SOURCE','source':SOURCE,'source_sha256':hashlib.sha256((ROOT/SOURCE).read_bytes()).hexdigest(),'selected_rows':selected,'native_sha256':hashlib.sha256(a.native.read_bytes()).hexdigest(),'negatives':negatives,'limits':'Preserved requirements inspected, not Ruby/RMXP engine execution or recovered numeric skill. Native consumer uses disclosed original parameters; no claim of full stack/trigger/initiative.'},indent=2,ensure_ascii=False)+'\n');print('PASS: four observed requirements, actual outcome checks and three false-result negatives')
if __name__=='__main__':main()
