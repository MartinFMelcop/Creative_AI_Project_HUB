#!/usr/bin/env python3
"""Route unchanged C# verification contracts from their current input dependencies.

This is conservative routing, not MSBuild evaluation or a correctness/Unity claim.
Unsupported graph syntax, absent/deleted inputs, unknown executable contracts, routing
changes and full/manual/empty scopes select every retained suite. Integrity is separate.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import ci_scope

ROOT=Path(__file__).resolve().parents[1]
WORKSPACE=ci_scope.WORKSPACE
SUITES=('progression','crafting','loadout','recovery','narrative','input_timing','intake','field',
        'presentation','audio','authored_scene','tooling','reputation','combat','availability','recipient')
BROWSER=frozenset(SUITES)-{'progression','crafting','loadout','recovery','narrative'}
CS='north-star/csharp/'
PROJECT_ROOTS={
 'progression':(CS+'Checks/NorthStar.Checks.csproj',CS+'Crossing/NorthStar.Crossing.csproj'),
 'crafting':(CS+'ForgeChecks/NorthStar.ForgeChecks.csproj',),
 'loadout':(CS+'LoadoutChecks/NorthStar.LoadoutChecks.csproj',),
 'recovery':(CS+'RecoveryChecks/NorthStar.RecoveryChecks.csproj',),
 'narrative':(CS+'NarrativeChecks/NorthStar.NarrativeChecks.csproj',),
 'input_timing':(CS+'InteractionChecks/NorthStar.InteractionChecks.csproj',),
 'intake':('north-star/intake/Checks/NorthStar.IntakeChecks.csproj',),
 'field':tuple('north-star/'+p for p in ('field-journey/PreparationChecks/NorthStar.PreparationChecks.csproj','field-journey/SamplingChecks/NorthStar.FieldSamplingChecks.csproj','field-journey/PresentationChecks/NorthStar.FieldPresentationChecks.csproj','field-journey/Checks/NorthStar.FieldChecks.csproj','memory-study/ConditionsChecks/NorthStar.ConditionsChecks.csproj','memory-study/ServiceChecks/NorthStar.ConditionServiceChecks.csproj','memory-study/Checks/NorthStar.MemoryChecks.csproj')),
 'presentation':(CS+'PresentationChecks/NorthStar.PresentationChecks.csproj',),
 'audio':(CS+'AudioChecks/NorthStar.AudioChecks.csproj',),
 'authored_scene':('north-star/authored-scene/Checks/NorthStar.AuthoredSceneChecks.csproj','north-star/authored-scene/JournalChecks/NorthStar.JournalChecks.csproj'),
 'tooling':('north-star/tooling-study/Checks/NorthStar.ToolingChecks.csproj','north-star/tooling-study/ConsumerChecks/NorthStar.ToolingConsumerChecks.csproj'),
 'reputation':('north-star/reputation-study/Checks/NorthStar.ReputationChecks.csproj','north-star/reputation-study/ConsumerChecks/NorthStar.ReputationConsumerChecks.csproj'),
 'combat':('north-star/combat-study/Checks/NorthStar.CombatChecks.csproj','north-star/combat-study/TrialChecks/NorthStar.TrialChecks.csproj','north-star/combat-study/PassiveChecks/NorthStar.PassiveChecks.csproj'),
 'availability':('north-star/availability-study/Checks/NorthStar.AvailabilityChecks.csproj','north-star/availability-study/JourneyChecks/NorthStar.JourneyChecks.csproj'),
 'recipient':('north-star/authored-scene/Host/NorthStar.AuthoredScene.csproj',),
}
# Explicit runtime, scripts, protocols, source assays and recorded comparisons outside
# ProjectReference. Directory entries end with '/'; other entries are exact files.
EXTRA={
 'progression':('labs/rpg-systems/','evidence/rpg-progression/'),
 'crafting':('labs/economy-simulation/','evidence/economy-crafting/','projects/eclipse-fair/Core/Game.cs','projects/eclipse-fair/Cli/Journal.cs'),
 'loadout':('labs/world-gameplay/run.py','labs/world-gameplay/test_instrument.py','evidence/world-loadout/'),
 'recovery':('labs/networking-persistence/','evidence/persistent-expedition/','projects/cinderwatch/Core/Journal.cs','projects/eclipse-fair/Cli/Journal.cs','projects/realtime-integration-lab/rooms-store.cjs','projects/realtime-integration-lab/rooms-actions.cjs','projects/realtime-integration-lab/rooms-backup.cjs'),
 'narrative':('labs/narrative-continuity/run.py','labs/narrative-continuity/test_instrument.py','evidence/narrative-continuity/','projects/lich-cistern/story.en.md','projects/lich-cistern/SOURCE_COMPARISON.md','projects/waystone-dialogue/browser/dist/deferred-request.js','projects/waystone-dialogue/browser/tests/deferred-request.test.mjs',CS+'Narrative/SCENE.md'),
 'input_timing':('labs/input-timing/','evidence/input-timing/',CS+'InputTiming/',CS+'Interaction/','projects/tokyo80s/dist/core.js','projects/tokyo80s/dist/rehearsal.js','projects/tokyo80s/dist/review.js','north-star/prototype/return_gate.gd','north-star/prototype/controls.gd'),
 'intake':('north-star/intake/','evidence/intake/'),
 'field':('north-star/field-journey/','north-star/intake/','north-star/memory-study/','labs/narrative-continuity/memory/','labs/world-gameplay/dialogue-conditions/','evidence/preparation-authoring/','evidence/field-sampling/','evidence/field-presentation/','evidence/field-journey/','evidence/dialogue-conditions/','evidence/memory-study/'),
 'presentation':('labs/visual-animation/','evidence/visual-animation/',CS+'Presentation/'),
 'audio':('labs/audio-music/','evidence/audio-music/',CS+'Audio/',CS+'Presentation/'),
 'authored_scene':('north-star/authored-scene/','evidence/authored-scene/','evidence/request-continuity/',CS+'Narrative/SCENE.md'),
 'tooling':('north-star/tooling-study/','labs/economy-simulation/tooling/','evidence/tooling-study/'),
 'reputation':('north-star/reputation-study/','labs/narrative-continuity/reputation/','evidence/reputation-study/'),
 'combat':('north-star/combat-study/','labs/combat-response/status/','labs/combat-response/passives/','evidence/combat-status/','evidence/passive-response/'),
 'availability':('north-star/availability-study/','labs/world-gameplay/availability/','evidence/npc-availability/','evidence/repair-hauling/'),
 'recipient':('delivery/authored-scene/','evidence/recipient-delivery/','evidence/request-continuity/','north-star/authored-scene/Host/','north-star/authored-scene/web/','north-star/authored-scene/README.md'),
}
WRAPPER_COVERAGE={'field':('preparation-verify.py','sampling-verify.py','conditions-verify.py','memory-verify','presentation-verify.py','field-verify')}
# These current source-binding assays deliberately fingerprint the whole C# tree,
# even files not compiled by their domain. Preserve that existing exact-compare gate.
WHOLE_CSHARP_BINDINGS=('progression','crafting','loadout','recovery')
SHARED_FILES={'north-star/csharp/global.json','tools/ci_scope.py','tools/csharp_scope.py','tools/test_ci_scope.py','tools/test_csharp_scope.py','tools/test_csharp_workflow.py'}
BUILD_NAMES={'global.json','Directory.Build.props','Directory.Build.targets','Directory.Packages.props','NuGet.Config','nuget.config'}
PROPERTIES={'TargetFramework','LangVersion','OutputType','Nullable','TreatWarningsAsErrors','Deterministic','ImplicitUsings'}
SKIP={'bin','obj','.git','__pycache__','node_modules'}


def validate_contracts(project_roots=PROJECT_ROOTS,extra=EXTRA,coverage=WRAPPER_COVERAGE):
    if set(project_roots)!=set(SUITES) or set(extra)!=set(SUITES):raise ValueError('Suite contract keys differ from fixed retained suites')
    if any(not project_roots[k] or not extra[k] for k in SUITES):raise ValueError('Every suite needs project and runtime contracts')
    if coverage!=WRAPPER_COVERAGE or set(coverage)!= {'field'} or len(coverage['field'])!=6:raise ValueError('Atomic wrapper coverage differs')
    # Important non-project runtime dependencies must not disappear during refactoring.
    for suite,anchor in [('field','north-star/field-journey/'),('field','north-star/memory-study/'),('recipient','delivery/authored-scene/'),('recovery','projects/realtime-integration-lab/rooms-backup.cjs')]:
        if anchor not in extra[suite]:raise ValueError('Required runtime dependency missing: '+anchor)


def regular(root,path):
    path=path.absolute()
    if not path.is_relative_to(root):raise ValueError('Dependency escapes maintained root')
    if any(p.is_symlink() for p in (path,*path.parents) if p.is_relative_to(root)) or not path.is_file():raise ValueError('Missing, linked or nonregular dependency: '+str(path))
    resolved=path.resolve()
    if not resolved.is_relative_to(root):raise ValueError('Dependency resolves outside maintained root')
    return resolved


def project_inputs(root,seeds):
    root=Path(root).resolve();pending=[root/name for name in seeds];seen=set();files=set();edges=[];linked=[];identities={}
    while pending:
        project=regular(root,pending.pop())
        if project in seen:continue
        seen.add(project);files.add(project)
        identities[project.relative_to(root).as_posix()]=hashlib.sha256(project.read_bytes()).hexdigest()
        for parent in (project.parent,*project.parent.parents):
            if parent==root.parent:break
            for name in BUILD_NAMES-{'global.json'}:
                if (parent/name).exists():raise ValueError('Inherited build configuration needs reviewed graph support: '+name)
        tree=ET.parse(project)
        if tree.getroot().attrib!={'Sdk':'Microsoft.NET.Sdk'}:raise ValueError('Unsupported project SDK or attributes')
        for item in tree.iter():
            tag=item.tag.split('}')[-1]
            if 'Condition' in item.attrib:raise ValueError('Conditional MSBuild input is unsupported')
            if tag in ('Project','PropertyGroup','ItemGroup'):
                if tag!='Project' and item.attrib:raise ValueError('Unsupported MSBuild group attributes')
            elif tag in PROPERTIES:
                if item.attrib or list(item):raise ValueError('Unsupported build property')
            elif tag in ('ProjectReference','Compile','Content','None','EmbeddedResource'):
                allowed={'Include','Link','CopyToOutputDirectory','CopyToPublishDirectory'}
                if not item.attrib.get('Include') or set(item.attrib)-allowed:raise ValueError('Unsupported MSBuild input attributes')
                value=item.attrib['Include']
                if any(c in value for c in ('$',';','\\','?','[')) or '**' in value:raise ValueError('Dynamic/glob MSBuild dependency unsupported')
                if '*' in value:
                    if tag!='EmbeddedResource' or value!='../Domain/*.cs':raise ValueError('Unreviewed explicit wildcard')
                    candidates=sorted(project.parent.glob(value))
                    if not candidates:raise ValueError('Empty explicit source glob')
                else:candidates=[project.parent/value]
                for candidate in candidates:
                    target=regular(root,candidate);files.add(target)
                    pair=[project.relative_to(root).as_posix(),target.relative_to(root).as_posix()]
                    if tag=='ProjectReference':pending.append(target);edges.append(pair)
                    else:linked.append({'kind':tag,'from':pair[0],'input':pair[1]})
            else:raise ValueError('Unsupported MSBuild element: '+tag)
        for path in project.parent.rglob('*.cs'):
            if not SKIP.intersection(path.relative_to(root).parts):files.add(regular(root,path))
    return {'inputs':sorted(p.relative_to(root).as_posix() for p in files),'projects':identities,'project_edges':sorted(edges),'linked_inputs':sorted(linked,key=lambda x:(x['from'],x['input']))}


def matches(name,entries):return any(name.startswith(p) if p.endswith('/') else name==p for p in entries)


def plan(paths,full=False,root=ROOT):
    root=Path(root).resolve();paths=[ci_scope.normalized_path(p) for p in paths];reasons=[];selected=set();graph={};fallback=False
    def broad(reason):
        nonlocal fallback
        fallback=True;selected.update(SUITES);reasons.append({'path':None,'reason':reason,'suites':list(SUITES)})
    if full or not paths:broad('Explicit full/manual/empty scope')
    try:
        validate_contracts()
        graph={key:project_inputs(root,PROJECT_ROOTS[key]) for key in SUITES}
    except (OSError,ValueError,ET.ParseError) as error:broad('Unresolved build graph: '+str(error))
    if not fallback:
        for path in paths:
            if path.startswith(('.github/workflows/','.github/actions/')):broad('Workflow/action changed');break
            if not path.startswith(WORKSPACE):
                if 'north_star_csharp' in ci_scope.affected(path):broad('Unknown/shared repository contract');break
                continue
            name=path[len(WORKSPACE):]
            if name in SHARED_FILES or Path(name).name in BUILD_NAMES:broad('Shared SDK/build/routing contract changed');break
            owners=set(k for k in SUITES if name in graph[k]['inputs'] or matches(name,EXTRA[k]))
            if name.startswith(CS) and Path(name).suffix in {'.cs','.csproj','.json','.props','.asmdef'}:owners.update(WHOLE_CSHARP_BINDINGS)
            if name in {'projects/realtime-integration-lab/package.json','projects/realtime-integration-lab/package-lock.json'}:owners.update(BROWSER)
            if name.startswith('references/rave-master/'):
                # Multiple literal source assays consume different variants. Broad is
                # deliberate until their static/runtime edges have individual support.
                broad('Shared protected-source collection changed');break
            if not owners:
                if 'north_star_csharp' in ci_scope.affected(path):broad('Unclassified C# or shared contract: '+name);break
                continue
            target=root/name
            if not target.is_file() or target.is_symlink():broad('Changed dependency deleted/missing/linked: '+name);break
            # New source projects are not silently assigned by an application prefix.
            if target.suffix in {'.cs','.csproj'} and not any(name in item['inputs'] for item in graph.values()) and not any(name==entry for entries in EXTRA.values() for entry in entries):broad('Unresolved executable source/project: '+name);break
            selected.update(owners);reasons.append({'path':path,'reason':'Current project/runtime/source-binding dependency','suites':[s for s in SUITES if s in owners]})
    enabled={s:s in selected for s in SUITES}
    return {'schema_version':1,'selected':enabled,'suites':[s for s in SUITES if enabled[s]],'browser':bool(selected&BROWSER),'required':bool(selected),'full_fallback':fallback,'changed_paths':paths,'reasons':reasons,'graph':graph,'wrapper_coverage':WRAPPER_COVERAGE,'limits':'Conservative routing of unchanged verification bodies; no test execution, performance, Unity/Windows or human claim.'}


def classify(paths,full=False,root=ROOT):return plan(paths,full,root)['selected']


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);source=p.add_mutually_exclusive_group();source.add_argument('--path',action='append');source.add_argument('--base');source.add_argument('--full',action='store_true');p.add_argument('--head');p.add_argument('--output',type=Path);p.add_argument('--report',type=Path);a=p.parse_args(argv)
    try:
        if a.head and not a.base:raise ValueError('--head requires --base')
        paths=a.path or []
        if a.base and not (len(a.base) in (40,64) and set(a.base)=={'0'}):
            repo=ci_scope.git_output(ROOT,'rev-parse','--show-toplevel').decode().strip();paths=ci_scope.changed_paths(repo,a.base,a.head or 'HEAD')
        result=plan(paths,a.full)
        if a.output:
            with a.output.open('a') as f:
                f.write(''.join(f'{s}={str(result["selected"][s]).lower()}\n' for s in SUITES));f.write('suites='+json.dumps(result['suites'],separators=(',',':'))+'\n');f.write('browser='+str(result['browser']).lower()+'\nrequired='+str(result['required']).lower()+'\n')
        if a.report:a.report.write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({k:v for k,v in result.items() if k!='graph'},sort_keys=True));return 0
    except (OSError,ValueError) as error:p.exit(1,'FAIL: '+str(error)+'\n')
if __name__=='__main__':raise SystemExit(main())
