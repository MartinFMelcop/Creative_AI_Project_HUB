#!/usr/bin/env python3
"""Inventory accessible origin sources and packages without executing reference code.

Classification is a discovery aid, not a maturity or rights verdict. Individual file
identities remain in the maintained manifest; ordered tree hashes bind this summary.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile, BadZipFile

ROOT=Path(__file__).resolve().parents[1]
LABS=dict(zip((f'P{i:02}' for i in range(1,12)),(
    'economy-simulation','ai-evaluation','input-timing','narrative-continuity',
    'rpg-systems','combat-response','visual-animation','audio-music',
    'build-operations','world-gameplay','networking-persistence')))
EXTRA_ROOTS={'P04':['references/literature/lich'], 'P10':['references/rave-master']}
SOURCE_SUFFIXES={'.cs','.gd','.rb','.py','.js','.cjs','.mjs','.ts','.html','.css'}
ASSET_SUFFIXES={'.png','.jpg','.jpeg','.svg','.wav','.ogg','.mp3','.flac','.ttf','.otf','.epub','.pdf'}


def digest_stream(stream):
    h=hashlib.sha256()
    while chunk:=stream.read(1024*1024):h.update(chunk)
    return h.hexdigest()


def digest(path):
    with path.open('rb') as stream:return digest_stream(stream)


def tracked_files(root):
    result=subprocess.run(['git','ls-files','--cached','--others','--exclude-standard','-z','--','.'],cwd=root,capture_output=True,check=True)
    return sorted({name.decode() for name in result.stdout.split(b'\0') if name})


def classify(name):
    p=Path(name);parts={part.lower() for part in p.parts};lower=p.name.lower()
    if p.suffix.lower() in {'.zip','.pck'}:return 'distribution_or_preservation_package'
    if 'third-party' in parts or 'license' in lower or 'copyright' in lower:return 'rights_and_attribution'
    if name.startswith('evidence/'):return 'recorded_evidence'
    if 'tests' in parts or 'checks' in parts or lower.startswith(('test_','test.','tests.')) or lower.endswith(('_checks.gd','checks.cs')):return 'tests_and_controls'
    if 'tools' in parts or lower.startswith(('check_','verify_','render_','export_')):return 'production_or_verification_tool'
    if p.suffix.lower() in SOURCE_SUFFIXES:return 'implementation'
    if p.suffix.lower() in ASSET_SUFFIXES:return 'creative_or_runtime_asset'
    if p.suffix.lower() in {'.csv','.json','.jsonl','.tscn','.tres'}:return 'data_and_contracts'
    return 'documentation_configuration_or_other'


def selected(name, roots):
    return any(name==base or name.startswith(base.rstrip('/')+'/') for base in roots)


def read_origins(root):
    data=json.loads((root/'registry/projects.json').read_text())
    rows=[row for row in data['projects'] if row.get('id') in LABS]
    if len(rows)!=11 or {row['id'] for row in rows}!=set(LABS):raise ValueError('Require the eleven unique P01-P11 origin identities')
    return sorted(rows,key=lambda row:row['id'])


def summarize(root, names):
    classes=Counter();size=0;identity=hashlib.sha256()
    for name in sorted(names):
        path=root/name
        if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(root.resolve()):raise ValueError('Missing or linked source: '+name)
        blob=digest(path);length=path.stat().st_size
        classes[classify(name)]+=1;size+=length
        identity.update(f'{name}\0{length}\0{blob}\n'.encode())
    return {'files':len(names),'bytes':size,'classification':dict(sorted(classes.items())), 'tree_sha256':identity.hexdigest()}


def package_audit(root,names):
    packages=[];payloads=defaultdict(list);whole=defaultdict(list)
    for name in sorted(n for n in names if Path(n).suffix.lower() in {'.zip','.pck'}):
        path=root/name;record={'path':name,'bytes':path.stat().st_size,'sha256':digest(path)}
        whole[record['sha256']].append(name)
        if path.suffix.lower()=='.zip':
            try:
                with ZipFile(path) as archive:
                    entries=[entry for entry in archive.infolist() if not entry.is_dir()]
                    record['members']=len(entries);record['uncompressed_bytes']=sum(entry.file_size for entry in entries)
                    for entry in entries:
                        with archive.open(entry) as stream:blob=digest_stream(stream)
                        payloads[(entry.file_size,blob)].append({'package':name,'member':entry.filename})
            except BadZipFile as error:raise ValueError('Unreadable ZIP: '+name) from error
        packages.append(record)
    repeated=[{'bytes':length,'sha256':blob,'copies':members} for (length,blob),members in sorted(payloads.items(),reverse=True) if len(members)>1 and length>=1024*1024]
    return {'package_count':len(packages),'tracked_blob_bytes':sum(p['bytes'] for p in packages),
            'zip_uncompressed_bytes':sum(p.get('uncompressed_bytes',0) for p in packages),
            'packages':packages,'identical_whole_packages':[paths for paths in whole.values() if len(paths)>1],
            'repeated_payloads_over_1_mib':repeated,
            'limits':'No package is declared removable. Identical embedded runtimes do not make version-specific source, saves, PCKs or notices redundant; no extraction or execution occurred.'}


def preserved_archive_sources(root):
    metadata=json.loads((root/'registry/legacy_sources.json').read_text())
    archive_path=root/metadata['source_archive']['path']
    if digest(archive_path)!=metadata['source_archive']['sha256']:raise ValueError('Pinned legacy archive changed')
    result=[]
    with ZipFile(archive_path) as archive:
        for source in metadata['sources']:
            prefix=source['archive_prefix']+'/'
            members=sorted((entry for entry in archive.infolist() if entry.filename.startswith(prefix) and not entry.is_dir()),key=lambda entry:entry.filename)
            if len(members)!=source['preserved_file_count']:raise ValueError('Preserved archive source count differs')
            identity=hashlib.sha256();classes=Counter()
            for entry in members:
                with archive.open(entry) as stream:blob=digest_stream(stream)
                identity.update(f'{entry.filename}\0{entry.file_size}\0{blob}\n'.encode())
                classes[classify(entry.filename)]+=1
            result.append({'origin':source['project_id'],'legacy_source':source['id'],
                           'archive':metadata['source_archive']['path'],'prefix':prefix,
                           'members':len(members),'bytes':sum(entry.file_size for entry in members),
                           'classification':dict(sorted(classes.items())),'tree_sha256':identity.hexdigest(),
                           'limits':'Pinned selected extracts, not complete historical repository/runtime. Rave members overlap its readable snapshot; do not double-count unique knowledge.'})
    return result


def inventory(root=ROOT,names=None):
    root=Path(root).resolve();names=tracked_files(root) if names is None else sorted(set(names))
    projects=read_origins(root);origins=[];union=set()
    for row in projects:
        roots=sorted(set(([row['working_path']] if row.get('working_path') else [])+row.get('working_paths',[])+EXTRA_ROOTS.get(row['id'],[])))
        evidence=sorted(set(row.get('evidence',[])))
        for name in roots+evidence:
            if not (root/name).exists():raise ValueError('Missing declared origin input: '+name)
        files=[name for name in names if selected(name,roots) or name in evidence]
        union.update(files)
        origins.append({'origin':row['id'],'laboratory':LABS[row['id']],'roots':roots,'evidence_paths':evidence,
                        'inventory':summarize(root,files),
                        'availability':'available' if roots else 'no_historical_case_supplied',
                        'limits':'Inventory and inspected source availability do not establish destination integration or newly executed origin behavior.'})
    shared={name:[row['origin'] for row in origins if selected(name,row['roots']) or name in row['evidence_paths']] for name in sorted(union)}
    shared={name:ids for name,ids in shared.items() if len(ids)>1}
    return {'schema_version':1,'kind':'accessible_origin_inventory','origins':origins,
            'unique_available_sources':summarize(root,union),'shared_source_files':len(shared),
            'overlap_policy':'A shared source is counted once in unique_available_sources; per-origin counts intentionally overlap, never measure effort.',
            'individual_hash_authority':'MANIFEST.sha256','preserved_archive_sources':preserved_archive_sources(root),'packages':package_audit(root,names),
            'reproduce':'python3 tools/inventory_origins.py --check labs/source-inventory.json; use --files for the complete classified per-file listing.',
            'limits':'Broad inventory reads every selected file for classification/hash and ZIP members for payload identity, not all semantic content. See labs/legacy-audit.md for material source inspection. Unavailable historical payloads and third-party rights remain bounded by references/catalog.json.'},shared


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path);parser.add_argument('--check',type=Path);parser.add_argument('--files',action='store_true');args=parser.parse_args()
    try:
        result,shared=inventory()
        if args.files:
            selected_origins=result['origins'];records=[]
            for name in tracked_files(ROOT):
                owners=[row['origin'] for row in selected_origins if selected(name,row['roots']) or name in row['evidence_paths']]
                if owners:records.append({'path':name,'classification':classify(name),'origins':owners,'bytes':(ROOT/name).stat().st_size,'sha256':digest(ROOT/name)})
            result['file_inventory']=records
        if args.check and json.loads(args.check.read_text())!=result:raise ValueError('Origin inventory differs; inspect changed inputs before regeneration')
        if args.output:args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
        elif not args.check:print(json.dumps(result,indent=2,sort_keys=True))
        print(f"PASS: {len(result['origins'])} origins, {result['unique_available_sources']['files']} unique accessible files, {result['packages']['package_count']} ZIP/PCK packages",file=sys.stderr)
    except (OSError,ValueError,KeyError,subprocess.SubprocessError) as error:parser.exit(1,f'FAIL: {error}\n')

if __name__=='__main__':main()
