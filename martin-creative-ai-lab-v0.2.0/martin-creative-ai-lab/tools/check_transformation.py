#!/usr/bin/env python3
"""Validate current laboratory/consumption claims and execution boundaries.

This checks identities and recorded contracts. It does not run instruments or prove
that an authored result is true; relevant instrument execution remains a CI duty.
Historical schema-1 origin inventories are not current transformation authority.
"""
import argparse
from datetime import date
import hashlib
import json
from pathlib import Path, PurePosixPath
import re

ROOT=Path(__file__).resolve().parents[1]
ORIGINS={f'P{i:02d}' for i in range(1,12)}
LAB_IDS=('economy-simulation','ai-evaluation','input-timing','narrative-continuity',
         'rpg-systems','combat-response','visual-animation','audio-music',
         'build-operations','world-gameplay','networking-persistence')
CODE={'.py','.cs','.gd','.js','.mjs','.cjs','.ts','.cpp','.c','.rs'}


def require(condition,message):
    if not condition:raise ValueError(message)


def text(row,key,label):
    require(isinstance(row.get(key),str) and bool(row[key].strip()),f'{label}: missing {key}')
    return row[key]


def strings(row,key,label,required=True):
    value=row.get(key,[])
    require(isinstance(value,list) and (bool(value) or not required)
            and all(isinstance(item,str) and item.strip() for item in value),f'{label}: invalid {key}')
    require(len(value)==len(set(value)),f'{label}: duplicate {key}')
    return value


def local(root,value,label,directory=None):
    require(isinstance(value,str) and value and '\\' not in value and '\0' not in value,f'{label}: invalid local path')
    path=PurePosixPath(value)
    require(not path.is_absolute() and '..' not in path.parts and path.as_posix()==value
            and not re.match(r'^[A-Za-z][A-Za-z0-9+.-]*:',value),f'{label}: noncanonical local path')
    destination=root/Path(value)
    require(not any((root/Path(*path.parts[:i])).is_symlink() for i in range(1,len(path.parts)+1)),f'{label}: linked path')
    require(destination.resolve().is_relative_to(root.resolve()),f'{label}: path escapes root')
    require((destination.is_file() or destination.is_dir()) if directory is None else
            destination.is_dir() if directory else destination.is_file(),f'{label}: missing local target {value}')
    return destination


def paths(root,row,key,label,required=True,code=False):
    values=strings(row,key,label,required)
    for value in values:
        target=local(root,value,f'{label}: {key}',False if code else None)
        if code:require(target.suffix in CODE,f'{label}: {key} requires actual consumer code')
    return values


def evidence(root,row,label,required=True):
    values=strings(row,'evidence',label,required)
    bindings=row.get('evidence_sha256',{})
    require(isinstance(bindings,dict),f'{label}: invalid evidence_sha256')
    require(set(bindings)==set(values),f'{label}: evidence hashes must cover every evidence path exactly')
    json_results=0
    for value in values:
        target=local(root,value,f'{label}: evidence',False)
        digest=bindings[value]
        require(isinstance(digest,str) and re.fullmatch('[0-9a-f]{64}',digest),f'{label}: invalid evidence hash')
        require(hashlib.sha256(target.read_bytes()).hexdigest()==digest,f'{label}: evidence hash mismatch {value}')
        if target.suffix=='.json':
            try:result=json.loads(target.read_text())
            except (ValueError,OSError) as exc:raise ValueError(f'{label}: invalid JSON evidence {value}: {exc}') from exc
            require(isinstance(result,dict) and bool(result),f'{label}: empty or non-object execution evidence')
            json_results+=1
    require(not required or json_results>0,f'{label}: execution requires nonempty JSON evidence, not documentation alone')
    return values


def integrated_consumers(root,row,consumers,label):
    """Reuse the destination-execution binding instead of unrelated result files."""
    for value in row['evidence']:
        target=root/value
        if target.suffix!='.json':continue
        record=json.loads(target.read_text())
        if not isinstance(record,dict) or record.get('kind')!='destination_execution':continue
        declared=record.get('consumer_paths')
        if not isinstance(declared,list) or not all(isinstance(name,str) for name in declared):continue
        if not set(consumers)<=set(declared):continue
        controls=record.get('checks');commands=record.get('commands');sources=record.get('source_artifacts')
        if not (isinstance(controls,dict) and type(controls.get('passed')) is int and controls['passed']>0
                and type(controls.get('failed')) is int and controls['failed']==0):continue
        if not (isinstance(commands,list) and commands and all(isinstance(command,dict)
                and isinstance(command.get('command'),list) and command['command']
                and all(isinstance(part,str) and part for part in command['command'])
                and type(command.get('exit_code')) is int and command['exit_code']==0 for command in commands)):continue
        if not isinstance(sources,list) or not all(isinstance(item,dict) for item in sources):continue
        artifacts={item.get('local_path'):item for item in sources if isinstance(item.get('local_path'),str)}
        if not set(consumers)<=set(artifacts):continue
        for name in consumers:
            source=local(root,name,f'{label}: bound source',False);artifact=artifacts[name]
            require(type(artifact.get('size_bytes')) is int and artifact['size_bytes']==source.stat().st_size
                    and artifact.get('sha256')==hashlib.sha256(source.read_bytes()).hexdigest(),
                    f'{label}: integrated consumer source hash mismatch')
        return
    raise ValueError(f'{label}: integration requires successful destination execution bound to actual consumer bytes')


def execution_boundary(root,direction,key):
    status=direction.get(key)
    require(status in ('not_executed','executed'),f'direction: invalid {key}')
    if status=='not_executed':return
    runtime_key='unity' if key=='unity_execution' else 'windows'
    records=direction.get('execution_evidence',[])
    require(isinstance(records,list) and records,f'direction: {key} needs actual runtime evidence')
    matching=[]
    for record in records:
        require(isinstance(record,dict),f'direction: invalid execution evidence')
        path=local(root,record.get('path'),f'direction: {key} evidence',False)
        require(path.suffix=='.json',f'direction: {key} needs JSON runtime evidence')
        require(hashlib.sha256(path.read_bytes()).hexdigest()==record.get('sha256'),f'direction: runtime evidence hash mismatch')
        try:run=json.loads(path.read_text())
        except (OSError,ValueError) as exc:raise ValueError(f'direction: invalid runtime evidence: {exc}') from exc
        require(isinstance(run,dict),f'direction: invalid runtime evidence object')
        if record.get('runtime')==runtime_key:matching.append(run)
    require(matching,f'direction: {key} needs its own runtime evidence')
    def passed(run):
        controls=run.get('checks')
        return (isinstance(controls,dict) and type(controls.get('failed')) is int and controls['failed']==0
                and type(controls.get('passed')) is int and controls['passed']>0)
    if runtime_key=='unity':
        require(any(run.get('runtime')=='Unity Editor' and run.get('executed') is True
                    and isinstance(run.get('editor_version'),str) and run['editor_version'].strip()
                    and passed(run)
                    for run in matching), 'direction: unexecuted Unity scaffolding is not a playable runtime')
    else:
        require(any(run.get('platform')=='Windows' and run.get('executed') is True
                    and isinstance(run.get('artifact_sha256'),str) and re.fullmatch('[0-9a-f]{64}',run['artifact_sha256'])
                    and passed(run)
                    for run in matching), 'direction: cross-compilation is not Windows execution')


def check(root=ROOT,data=None):
    root=Path(root).resolve()
    if data is None:
        try:data=json.loads((root/'labs/origins.json').read_text())
        except (OSError,ValueError) as exc:raise ValueError(f'transformation: cannot read origins: {exc}') from exc
    require(isinstance(data,dict) and type(data.get('schema_version')) is int and data['schema_version']==2,
            'transformation: current authority requires origins schema_version 2')
    try:date.fromisoformat(data.get('updated_at',''))
    except (ValueError,TypeError) as exc:raise ValueError('transformation: invalid updated_at') from exc
    require(isinstance(data.get('baseline_commit'),str) and re.fullmatch('[0-9a-f]{40}',data['baseline_commit']),
            'transformation: invalid baseline_commit')
    text(data,'scope','transformation')
    require(data.get('allocation')=={'legacy_labs':47,'north_star':40,'repository':13}
            and all(type(value) is int for value in data['allocation'].values()),
            'transformation: allocation must preserve 47/40/13 targets')
    direction=data.get('direction');require(isinstance(direction,dict),'transformation: missing direction')
    require(direction.get('stack')=='Unity/C#' and direction.get('player_platform')=='Windows'
            and direction.get('distribution')=='Steam','transformation: selected direction must be Unity/C#, Windows, Steam')
    for key in ('unity_execution','windows_execution'):execution_boundary(root,direction,key)
    require(isinstance(direction.get('execution_evidence'),list),'direction: invalid execution_evidence')
    program=root/'north-star/capabilities.json'
    if program.is_file():
        try:capabilities=json.loads(program.read_text())
        except (OSError,ValueError) as exc:raise ValueError(f'transformation: invalid North Star metadata: {exc}') from exc
        require(isinstance(capabilities,dict),'transformation: North Star metadata must be an object')
        require(capabilities.get('engine_selection') in ('Unity','Unity/C#'),
                'transformation: North Star engine selection conflicts with current direction')
    origins=data.get('origins')
    require(isinstance(origins,list) and all(isinstance(row,dict) for row in origins),'transformation: invalid origins')
    require(len(origins)==11 and all(isinstance(row.get('id'),str) for row in origins) and {row.get('id') for row in origins}==ORIGINS,
            'transformation: exactly P01–P11 origins are required')
    for row in origins:
        label='origin '+row['id']
        paths(root,row,'source_paths',label,False)
        for value in strings(row,'execution_evidence',label,False):
            local(root,value,f'{label}: execution_evidence',False)
        text(row,'extraction_next',label)
    labs=data.get('labs')
    require(isinstance(labs,list) and all(isinstance(row,dict) for row in labs),'transformation: invalid labs')
    require(len(labs)==11 and all(isinstance(row.get('id'),str) for row in labs) and {row.get('id') for row in labs}==set(LAB_IDS),
            'transformation: eleven named laboratory destinations are mandatory')
    owners=[];operational=0
    for row in labs:
        label='lab '+row['id'];owner=row.get('owner_origin');owners.append(owner)
        require(isinstance(owner,str) and owner in ORIGINS,f'{label}: invalid owner_origin')
        require(owner==f'P{LAB_IDS.index(row["id"])+1:02d}',f'{label}: owner_origin must match its mandatory origin destination')
        refs=strings(row,'origin_projects',label)
        require(owner in refs and set(refs)<=ORIGINS,f'{label}: invalid origin_projects')
        for field in ('domain','question','validity_boundary','next_objective'):text(row,field,label)
        paths(root,row,'source_paths',label)
        paths(root,row,'consumer_paths',label,False,True)
        status=row.get('status')
        require(status in ('incomplete','operational'),f'{label}: invalid maturity status')
        if status=='incomplete':
            require(not row.get('instrument') and not row.get('evidence') and not row.get('evidence_sha256'),
                    f'{label}: incomplete destination cannot claim an instrument or execution')
            continue
        operational+=1
        path=local(root,row.get('path'),f'{label}: path',True)
        require(path.is_relative_to(root/'labs'),f'{label}: operational path must belong to labs')
        instrument=local(root,row.get('instrument'),f'{label}: instrument',False)
        require(instrument.suffix in CODE and instrument.is_relative_to(path),f'{label}: instrument must be actual code within its lab')
        strings(row,'controls',label)
        paths(root,row,'consumer_paths',label,True,True)
        evidence(root,row,label)
    require(set(owners)==ORIGINS and len(set(owners))==11,'transformation: each origin must own exactly one destination')
    consumptions=data.get('consumption')
    require(isinstance(consumptions,list),'transformation: missing consumption decisions')
    seen=set();totals={'INTEGRATED':0,'REJECTED':0,'UNRESOLVED':0}
    for row in consumptions:
        require(isinstance(row,dict),'transformation: invalid consumption record')
        key=text(row,'id','consumption');label='consumption '+key
        require(key not in seen,f'{label}: duplicate id');seen.add(key)
        require(isinstance(row.get('laboratory_id'),str) and row['laboratory_id'] in LAB_IDS,f'{label}: unknown laboratory')
        require(set(strings(row,'origin_projects',label))<=ORIGINS,f'{label}: unknown origin')
        paths(root,row,'source_paths',label)
        text(row,'decision',label)
        status=row.get('status');require(isinstance(status,str) and status in totals,f'{label}: invalid terminal state');totals[status]+=1
        if status=='UNRESOLVED':
            text(row,'next_action',label)
            require(row.get('consumed',False) is False,f'{label}: unresolved work cannot be called consumed')
            if row.get('evidence'):evidence(root,row,label,False)
        else:
            evidence(root,row,label)
            if status=='INTEGRATED':
                consumers=paths(root,row,'consumer_paths',label,True,True)
                integrated_consumers(root,row,consumers,label)
    return {'laboratories':len(labs),'operational':operational,'incomplete':len(labs)-operational,'consumption':totals}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,default=ROOT);args=parser.parse_args()
    try:result=check(args.root)
    except (OSError,ValueError,TypeError,KeyError) as exc:parser.exit(1,f'FAIL: {exc}\n')
    print('PASS: '+json.dumps(result,sort_keys=True)+'; documentary identities, not fresh runtime execution')

if __name__=='__main__':main()
