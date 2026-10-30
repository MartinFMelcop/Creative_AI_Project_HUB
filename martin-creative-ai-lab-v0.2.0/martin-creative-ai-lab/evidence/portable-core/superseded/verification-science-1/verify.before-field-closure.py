#!/usr/bin/env python3
"""Execute bounded compatibility checks against the existing gameplay owners."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from xml.sax.saxutils import escape

ROOT=Path(__file__).resolve().parents[3]
CORE=ROOT/'north-star/csharp'
NAMES=('Crossing','Forge','Loadout')
ALL=('Domain',)+NAMES
CHECKS={'Crossing':('Checks','NorthStar.Checks'),'Forge':('ForgeChecks','NorthStar.ForgeChecks'),'Loadout':('LoadoutChecks','NorthStar.LoadoutChecks')}

PE_SOURCE = r'''using System;
using System.IO;
using System.Linq;
using System.Reflection.Metadata;
using System.Reflection.PortableExecutable;
using System.Text.Json;
var rows = args.Select(path => {
 using var stream=File.OpenRead(path);using var pe=new PEReader(stream);var reader=pe.GetMetadataReader();string? target=null;
 foreach(var handle in reader.GetAssemblyDefinition().GetCustomAttributes()) {
  var attribute=reader.GetCustomAttribute(handle);if(attribute.Constructor.Kind!=HandleKind.MemberReference)continue;
  var constructor=reader.GetMemberReference((MemberReferenceHandle)attribute.Constructor);if(constructor.Parent.Kind!=HandleKind.TypeReference)continue;
  var type=reader.GetTypeReference((TypeReferenceHandle)constructor.Parent);
  if(reader.GetString(type.Namespace)=="System.Runtime.Versioning"&&reader.GetString(type.Name)=="TargetFrameworkAttribute") {
   var blob=reader.GetBlobReader(attribute.Value);if(blob.ReadUInt16()!=1)throw new InvalidDataException("Invalid attribute prolog");target=blob.ReadSerializedString();
  }
 }
 return new {path,target_framework=target,assembly_references=reader.AssemblyReferences.Select(h=>reader.GetString(reader.GetAssemblyReference(h).Name)).ToArray()};
}).ToArray();Console.WriteLine(JsonSerializer.Serialize(rows));
'''

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def project(name):return CORE/name/('NorthStar.'+name+'.csproj')
def dll(name,tfm):return CORE/name/'bin/Release'/tfm/('NorthStar.'+name+'.dll')
def identities():
    paths=[p for folder in (CORE,ROOT/'north-star/intake') for p in folder.rglob('*') if p.is_file() and p.suffix in ('.cs','.csproj') and not {'bin','obj'}.intersection(p.relative_to(folder).parts)]
    paths+=list(Path(__file__).parent.glob('*'))
    return {str(p.relative_to(ROOT)):sha(p) for p in sorted(paths) if p.is_file()}

def verify_report(report):
    if report.get('source_before')!=report.get('source_after'):raise ValueError('Source stability failure')
    rows=report.get('parity',[])
    expected={n+':demo' for n in NAMES}|{n+':native' for n in NAMES}
    if {r.get('id') for r in rows}!=expected or len(rows)!=6:raise ValueError('Exact six comparisons required')
    for row in rows:
        files=row['files']
        if len(files)!=(3 if row['id'].endswith(':demo') else 2):raise ValueError('Missing execution category')
        data=[]
        for item in files:
            path=Path(item['path'])
            if sha(path)!=item['sha256']:raise ValueError('Actual result identity mismatch')
            data.append(path.read_bytes())
        if any(d!=data[0] for d in data[1:]):raise ValueError('Actual result bytes differ')
    for row in report.get('consumer_copied_assemblies',[]):
        if sha(row['copied_path'])!=row['portable_sha256'] or sha(row['portable_path'])!=row['portable_sha256']:raise ValueError('Actual portable consumer binding mismatch')
    if {(r['consumer'],r['name']) for r in report.get('consumer_copied_assemblies',[])}!={(c,n) for c in ('Intake','Field') for n in ALL}:raise ValueError('Incomplete actual assembly check')
    for path,digest in report.get('baseline_inputs',{}).items():
        if sha(path)!=digest:raise ValueError('Baseline input changed')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--dotnet',required=True);p.add_argument('--baseline',type=Path,default=ROOT/'evidence/portable-core/baseline');p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    out=a.output.resolve();baseline=a.baseline.resolve()
    if out==ROOT or ROOT in out.parents:p.error('New external output required')
    out.mkdir(parents=True,exist_ok=False);dotnet=shutil.which(a.dotnet) or a.dotnet;before=identities();baseline_before={str(x):sha(x) for x in sorted(baseline.glob('*.json'))};commands=[];controls=[];evaluations={}
    def run(args,required=True):
        r=subprocess.run([str(x) for x in args],cwd=ROOT,capture_output=True,text=True,timeout=300)
        commands.append({'command':[str(x) for x in args],'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
        (out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
        if required and r.returncode:raise RuntimeError('Actual command failed: '+' '.join(str(x) for x in args[:4]))
        return r
    def check(name,value):
        if not value:raise AssertionError(name)
        controls.append(name)
    def evaluated(path,portable=False):
        args=[dotnet,'msbuild',path,'-nologo','-getProperty:TargetFramework,TargetFrameworks,OutputType,LangVersion','-getItem:Compile,ProjectReference']
        if portable:args+=['-p:TargetFramework=netstandard2.1']
        return json.loads(run(args).stdout)
    def validate_graph(path,seen=None):
        seen=set() if seen is None else seen;path=path.resolve()
        if path in seen:return
        seen.add(path);outer=evaluated(path);props=outer['Properties'];supported=(props.get('TargetFrameworks') or props.get('TargetFramework','')).split(';')
        if 'netstandard2.1' not in supported:raise ValueError('Project does not declare portable target: '+str(path))
        data=evaluated(path,True);v=data['Properties'];items=data['Items'];lang=v['LangVersion']
        if v['TargetFramework']!='netstandard2.1' or v['OutputType']!='Library' or lang not in ('8','8.0'):raise ValueError('Portable target/compiler/output contract violated')
        sources=[Path(x['FullPath']) for x in items.get('Compile',[])]
        if not sources or any(x.name=='Program.cs' or 'System.Text.Json' in x.read_text() for x in sources):raise ValueError('Portable input includes transport/entrypoint or no owner')
        for ref in items.get('ProjectReference',[]):validate_graph(Path(ref['FullPath']),seen)
        evaluations[str(path)]={'properties':v,'compile':[str(x) for x in sources],'project_references':items.get('ProjectReference',[])}
    def consumer(label,source):
        folder=out/label;folder.mkdir();path=folder/(label+'.csproj')
        refs=''.join('<Reference Include="NorthStar.'+n+'"><HintPath>'+escape(str(dll(n,'netstandard2.1')))+'</HintPath><Private>true</Private></Reference>' for n in ALL)
        path.write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net10.0</TargetFramework><EnableDefaultCompileItems>false</EnableDefaultCompileItems><Nullable>enable</Nullable><TreatWarningsAsErrors>true</TreatWarningsAsErrors><Deterministic>true</Deterministic></PropertyGroup><ItemGroup><Compile Include="'+escape(str(source))+'" />'+refs+'</ItemGroup></Project>\n')
        run([dotnet,'build',path,'-c','Release']);return folder/'bin/Release/net10.0'/(label+'.dll')
    parity=[]
    try:
        check('Pinned actual SDK10.0.401',run([dotnet,'--version']).stdout.strip()=='10.0.401')
        owner_baseline=json.loads((baseline/'owner-cli-source-baseline.json').read_text())
        check('Exact previous owner and CLI sources',all(sha(ROOT/n)==h for n,h in owner_baseline.items()))
        for n in NAMES:run([dotnet,'build',project(n),'-c','Release']);validate_graph(project(n))
        check('All three actual portable dependency closures satisfy C#8/netstandard2.1 library contract',all(str(project(n)) in evaluations for n in NAMES))
        for n in NAMES:
            current=out/(n.lower()+'-current.json');portable=out/(n.lower()+'-portable.json');old=baseline/(n.lower()+'-baseline.json')
            run([dotnet,dll(n,'net10.0'),'--demo',current]);adapter=consumer(n+'PortableCli',CORE/n/'Program.cs');run([dotnet,adapter,'--demo',portable])
            files=[{'path':str(x),'sha256':sha(x)} for x in (old,current,portable)]
            check(n+' baseline/net10/portable CLI exact outcome bytes',len({x['sha256'] for x in files})==1)
            parity.append({'id':n+':demo','files':files})
            checkdir,assembly=CHECKS[n];normal=out/(n.lower()+'-native-normal.json');ported=out/(n.lower()+'-native-portable.json')
            run([dotnet,'build',CORE/checkdir/(assembly+'.csproj'),'-c','Release']);run([dotnet,CORE/checkdir/'bin/Release/net10.0'/(assembly+'.dll'),'native',normal])
            adapter=consumer(n+'PortableChecks',CORE/checkdir/'Program.cs');run([dotnet,adapter,'native',ported])
            check(n+' existing native controls exact output bytes',normal.read_bytes()==ported.read_bytes())
            parity.append({'id':n+':native','files':[{'path':str(x),'sha256':sha(x)} for x in (normal,ported)]})
        copied=[]
        for host,label in (('intake','Intake'),('field-journey','Field')):
            application=ROOT/('north-star/'+host+'/Host/NorthStar.'+('Intake' if label=='Intake' else 'FieldJourney')+'.csproj')
            run([dotnet,'build',application,'-c','Release']);evaluations[str(application)]=evaluated(application)
            for n in ALL:
                path=application.parent/'bin/Release/net10.0'/('NorthStar.'+n+'.dll')
                check(label+' actual copied '+n+' DLL is portable output',sha(path)==sha(dll(n,'netstandard2.1')))
                copied.append({'consumer':label,'name':n,'copied_path':str(path),'portable_path':str(dll(n,'netstandard2.1')),'portable_sha256':sha(path)})
        probe=out/'MetadataProbe';probe.mkdir();(probe/'Program.cs').write_text(PE_SOURCE)
        (probe/'MetadataProbe.csproj').write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net10.0</TargetFramework><Nullable>enable</Nullable><TreatWarningsAsErrors>true</TreatWarningsAsErrors></PropertyGroup></Project>\n')
        run([dotnet,'build',probe/'MetadataProbe.csproj','-c','Release'])
        metadata=json.loads(run([dotnet,probe/'bin/Release/net10.0/MetadataProbe.dll']+[r['copied_path'] for r in copied]+[str(dll(n,'net10.0')) for n in NAMES]).stdout)
        check('Actual copied PE metadata declares netstandard2.1 without JSON transport dependency',all(x['target_framework']=='.NETStandard,Version=v2.1' and 'System.Text.Json' not in x['assembly_references'] for x in metadata[:8]))
        check('Retained CLI PE metadata declares actual net10 executable target',all(x['target_framework']=='.NETCoreApp,Version=v10.0' for x in metadata[8:]))
        negative=out/'negative-projects';negative.mkdir();(negative/'Program.cs').write_text('public class Contaminated {}\n')
        bad=negative/'Bad.csproj';bad.write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>netstandard2.1</TargetFramework><LangVersion>8.0</LangVersion></PropertyGroup></Project>\n')
        try:validate_graph(bad)
        except ValueError as e:controls.append('Actual evaluated Program.cs contamination rejected');(out/'negative-program.json').write_text(json.dumps({'detected':True,'reason':str(e)},indent=2)+'\n')
        else:raise AssertionError('Program contamination escaped')
        only=negative/'OnlyNet10.csproj';only.write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net10.0</TargetFramework><OutputType>Exe</OutputType><EnableDefaultCompileItems>false</EnableDefaultCompileItems></PropertyGroup></Project>\n')
        (negative/'Owner.cs').write_text('public class Owner {}\n');bad.write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>netstandard2.1</TargetFramework><LangVersion>8.0</LangVersion><EnableDefaultCompileItems>false</EnableDefaultCompileItems></PropertyGroup><ItemGroup><Compile Include="Owner.cs"/><ProjectReference Include="OnlyNet10.csproj"/></ItemGroup></Project>\n')
        try:validate_graph(bad)
        except ValueError as e:controls.append('Actual evaluated executable net10 dependency rejected');(out/'negative-reference.json').write_text(json.dumps({'detected':True,'reason':str(e)},indent=2)+'\n')
        else:raise AssertionError('Executable dependency escaped')
        report={'schema_version':1,'kind':'actual_portable_owner_compatibility','source_before':before,'source_after':identities(),'parity':parity,'consumer_copied_assemblies':copied,'baseline_inputs':baseline_before,'evaluated_projects':evaluations,'actual_pe_metadata':metadata,'limits':'Trusted-local software compatibility, not Unity Editor/runtime, Windows/Steam, save migration, binary identity promise or independent human evidence.'}
        verify_report(report);check('Source closure stable during execution',before==report['source_after'])
        forged=copy.deepcopy(report);forged['parity'][0]['files'][1]['sha256']='0'*64
        try:verify_report(forged)
        except ValueError as e:controls.append('Forged passing parity result identity rejected');(out/'negative-result.json').write_text(json.dumps({'detected':True,'reason':str(e),'forged':forged},indent=2)+'\n')
        else:raise AssertionError('Forged parity escaped')
        changed=copy.deepcopy(report);actual=json.loads(Path(changed['parity'][0]['files'][1]['path']).read_text());actual['crossing']['health']+=1
        wrong=out/'mutated-gameplay-result.json';wrong.write_text(json.dumps(actual,indent=2)+'\n')
        changed['parity'][0]['files'][1]={'path':str(wrong),'sha256':sha(wrong)}
        try:verify_report(changed)
        except ValueError as e:controls.append('Changed actual health with truthful new hash rejected');(out/'negative-gameplay-result.json').write_text(json.dumps({'detected':True,'reason':str(e),'mutated_file':str(wrong),'sha256':sha(wrong)},indent=2)+'\n')
        else:raise AssertionError('Altered gameplay result escaped')
        report['checks']={'passed':len(controls),'failed':0};report['controls']=controls
        (out/'results.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS: '+str(len(controls))+' portable compatibility controls; six exact comparisons')
    finally:(out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
if __name__=='__main__':main()
