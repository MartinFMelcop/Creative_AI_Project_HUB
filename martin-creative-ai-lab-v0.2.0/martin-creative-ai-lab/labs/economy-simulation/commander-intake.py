#!/usr/bin/env python3
"""Inspect supplied research archives without importing or executing their code."""
from __future__ import annotations
import argparse, collections, hashlib, io, json, pathlib, re, stat, zipfile

def digest(data): return hashlib.sha256(data).hexdigest()

def inspect_archive(path):
    raw=path.read_bytes(); members={}; rows=[]
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if len(z.infolist())>10000: raise ValueError('Archive member bound exceeded')
        total=0
        for info in z.infolist():
            name=info.filename; p=pathlib.PurePosixPath(name); mode=info.external_attr>>16
            if not name or name.startswith('/') or '\\' in name or ':' in name or any(x in ('..','.') for x in name.split('/')):
                raise ValueError('Unsafe archive path: '+name)
            if name in members or any(x['path'].casefold()==name.casefold() for x in rows): raise ValueError('Duplicate archive path: '+name)
            if stat.S_ISLNK(mode) or stat.S_IFMT(mode) not in (0,stat.S_IFREG,stat.S_IFDIR): raise ValueError('Unexpected archive link or special file: '+name)
            total+=info.file_size
            if info.file_size>32*1024*1024 or total>64*1024*1024: raise ValueError('Archive size bound exceeded')
            data=z.read(info); members[name]=data
            rows.append({'path':name,'bytes':len(data),'sha256':digest(data),'directory':info.is_dir()})
        if z.testzip() is not None: raise ValueError('ZIP CRC mismatch')
    return {'archive':path.name,'bytes':len(raw),'sha256':digest(raw),'member_count':len(rows),'uncompressed_bytes':total,'members':rows},members

def inspect(engine,transfer):
    ei,em=inspect_archive(engine);ti,tm=inspect_archive(transfer)
    prefix='CommanderSIM_v16_Current/'
    def e(name): return em[prefix+name]
    man=json.loads(e('manifest.json')); checks=[]
    for name,expected in man['current_source_hashes_sha256'].items():
        actual=digest(e(name));assert actual==expected, name;checks.append({'path':name,'sha256':actual})
    assert digest(e(man['raw_run_path']))==man['raw_run_sha256']
    commanders=[['Dralnu, Lich Lord'],['Palladia-Mors, the Ruiner'],["Be\'lakor, the Dark Master"],['Livio, Oathsworn Sentinel','Ikra Shidiqi, the Usurper']]
    decknames=sorted(n for n in em if n.startswith(prefix+'decks/'))
    assert len(decknames)==4
    deckrows=[]
    allcmd=sum(commanders,[])
    for idx,name in enumerate(decknames):
        cards=[]
        for line in em[name].decode('utf-8-sig').splitlines():
            count,card=line.split(' ',1);assert count.isdigit() and int(count)>0;cards.extend([card]*int(count))
        assert len(cards)==100
        assert [c for c in cards if c in allcmd]==commanders[idx]
        d=man['decks'][idx];assert digest(em[name])==d['sha256'] and d['card_count']==100 and d['commanders']==commanders[idx]
        deckrows.append({'path':name,'cards':len(cards),'commanders':commanders[idx],'sha256':digest(em[name]),'protected_comparative_reference':idx==3})
    im=json.loads(tm['release/INTEGRATION_MANIFEST_v10.json'])
    for name,entry in im['files'].items(): assert len(tm[name])==entry['bytes'] and digest(tm[name])==entry['sha256'],name
    sums=[]
    for line in tm['release/SHA256SUMS'].decode().splitlines():
        expected,name=line.split('  ',1);assert digest(tm[name])==expected,name;sums.append(name)
    raw=json.loads(e(man['raw_run_path']));kpi=json.loads(e('reports/current_kpis.json'));scenarios=json.loads(e('reports/bounded_combo_scenarios.json'))
    assert raw['metadata']['total_four_player_games']==sum(p['games'] for p in raw['phases'])==30000
    assert raw['metadata']['paired_trials']==15000
    assert sum(sum(row) for row in raw['paired_outcomes'])==15000
    assert scenarios['count']==len(scenarios['scenarios'])==6
    assert man['oracle_complete_games']==kpi['complete_rules_verified_games']==0
    assert kpi['surrogate_four_player_games']==30000 and kpi['bounded_scenarios_not_games']==6
    for phase in raw['phases']:
        assert sum(p['wins'] for p in phase['wins'])+phase['unresolved_surrogate']==phase['games']
        assert sum(phase['round_histogram'])==phase['games']
    return {'schema_version':1,'label':'OBSERVED_SOURCE','scope':'Archive content and declared report consistency; no code executed by this tool','archives':[ei,ti], 'manifest_checks':{'engine_source_entries':checks,'engine_raw_run':man['raw_run_sha256'],'transfer_manifest_entries':len(im['files']),'transfer_checksum_entries':len(sums)},'decks':deckrows,'recorded_claims':{'label':'RECORDED_EXECUTION','surrogate_episodes':30000,'paired_policy_trials':15000,'bounded_scenarios_not_games':6,'fully_verified_complete_commander_games':0,'note':'Recorded aggregate consistency is not independent regeneration or full Magic validity.'},'rights':'User-supplied research preserved with original notices; no general license or commercial/IP clearance inferred.'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--engine-archive',type=pathlib.Path,required=True);p.add_argument('--transfer-archive',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args()
    result=inspect(a.engine_archive,a.transfer_archive)
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':'pass','archive_members':[x['member_count'] for x in result['archives']],'decks':[x['cards'] for x in result['decks']],'recorded_claims':result['recorded_claims']}))
if __name__=='__main__': main()
