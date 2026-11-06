import json,hashlib,shutil
from pathlib import Path
r=Path.cwd();o=r/'evidence/field-gate';base=Path('/workspace/work/gate-final-review');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def copy(src,dst):
 dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
shutil.copytree(base/'execution',o/'execution',dirs_exist_ok=True)
for folder,src in [('superseded-layout',Path('/workspace/work/gate-science/integrated-initial')),('initial-syntax',Path('/workspace/work/gate-science/syntax-initial'))]:
 shutil.copytree(src,o/folder,dirs_exist_ok=True)
for name in ['initial-native-producer.cs','initial-native.log','msb4166.log','native-final.log','native-retry.log']:
 copy(Path('/workspace/work/gate-engineering')/name,o/'initial-native'/name)
for name in ['initial-index.html','initial-test-csharp-scope.py']:
 copy(base/name,o/'review-preimages'/name)
copy(Path('/workspace/work/gate-cycle/routing-final.log'),o/'initial-routing/error.log')
copy(Path('/workspace/work/gate-cycle/initial-godot-dependency-plan.json'),o/'initial-routing/missing-field-plan.json')
copy(Path('/workspace/work/gate-cycle/withdrawal-regression/withdrawal-failure.json'),o/'initial-withdrawal/failure.json')
copy(Path('/workspace/work/current-next-ci/baseline.json'),o/'continuity/baseline-ci.json')
copy(Path('/workspace/work/current-next-ci/authority.json'),o/'continuity/authority.json')
for name,filename in [('keyboard','keyboard-browser.json'),('withdrawal','withdrawal-browser.json')]:copy(base/name/filename,o/(name+'-regression.json'))
# Only summaries/commands for unchanged nested methods are public; full originals stay in external output.
for name in ['maximal','focused']:
 for filename in ['verification.json','commands.json','native.json']:
  p=base/name/filename
  if p.exists():copy(p,o/'regressions'/name/filename)

if (base/'source-launch/browser.json').exists():copy(base/'source-launch/browser.json',o/'source-launch.json')
copy(base/'affected-commands.json',o/'affected-commands.json')
copy(base/'routing.log',o/'routing-final.log')
inv=[]
for folder in [Path('/workspace/work/gate-cycle/maximal-field-regression'),base/'maximal',base/'focused',base/'source-launch']:
 for p in sorted(folder.rglob('*')):
  if p.is_file():inv.append({'external_path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)})
(o/'external-output-inventory.json').write_text(json.dumps(inv,indent=2)+'\n')
v=json.loads((o/'execution/verification.json').read_text());assert all(sha(r/p)==h for p,h in v['source_sha256'].items())
target='evidence/field-gate/RUN.json';catp=r/'labs/origins.json';cat=json.loads(catp.read_text());cons={'north-star/field-journey/Gate/Gate.cs','north-star/field-journey/Host/Room.cs'}
for row in cat['consumption']:
 if 'north-star/field-journey/Host/Room.cs' in row.get('consumer_paths',[]):cons.update(row['consumer_paths']);row['evidence'].insert(0,target)
for row in cat['labs']:
 if 'north-star/field-journey/Host/Room.cs' in row.get('consumer_paths',[]):cons.update(row['consumer_paths']);row['evidence'].append(target)
sources=sorted(set(v['source_sha256'])|cons)
run={'schema_version':1,'kind':'destination_execution','baseline_commit':'23bd920c128ea4d528a8f844a63ac652aa4306a0','capability_ids':[],'consumer_paths':sorted(cons),'runtime':'SDK10.0.401/Linux; Node24.19.0/Chromium154; C#8/netstandard2.1 Gate with existing .NET10 host','scope':'Original paid post-Crossing gate in the same FieldJourney; previous children freeze at explicit entry. Selected Godot contracts redesigned as discrete paid actions, not timing equivalence.','checks':{'passed':len(v['native']),'failed':0},'commands':json.loads((o/'execution/commands.json').read_text()),'source_artifacts':[{'local_path':p,'size_bytes':(r/p).stat().st_size,'sha256':sha(r/p)} for p in sources],'result_artifacts':[{'local_path':str(p.relative_to(r)),'size_bytes':p.stat().st_size,'sha256':sha(p)} for p in [o/'execution/native.json',o/'execution/browser/gate-browser.json',o/'execution/verification.json',o/'regressions/maximal/verification.json',o/'regressions/focused/verification.json',o/'keyboard-regression.json',o/'withdrawal-regression.json',o/'source-launch.json'] if p.exists()],'source_inputs_stable':len(v['source_sha256']),'native_controls':len(v['native']),'browser_controls':len(v['chromium']),'http_controls':len(v['http']),'negative_controls':v['negative_controls'],'policies':'Native direct/grounded each9beats; browser direct9, grounded11 including paid release/rework and delayed-response controls. Direct5HP/7resolve/1integrity; grounded9HP/5resolve/2integrity. Inaction breaks mechanism at beat11 with5HP alive. No optimality/balance claim.','retained_failures':['Initial7HP exit-death fixture actually survived at1HP; corrected5HP fixture without rule change.','MSB4166 with unavailable indicated diagnostic directory; one unchanged retry passed, cause unknown.','Initial browser syntax refusal retained.','Initial withdrawal source-stability rejection after concurrent producer change; exact failure retained, stable rerun passed.','Initial new source routing omitted Field; corrected four exact dependencies preserve prior input_timing selection. New routing test initially queried absent RUN.json and correctly hit conservative full fallback; existing README path now tests the intended prefix.','Initial maximum wrapper interrupted without final verification; retained external output inventory is not acceptance.','Earlier valid execution/captures superseded after actor/label overlap correction; final source-stable instruments and regressions reexecuted.'],'limitations':['No fresh source Godot/RGSS/RMXP execution or continuous-time equivalence. New integrity3, named movement, costs, brace and no-retry rules are disclosed original policies.','Current gate health and frozen child health are distinct phases; no home return, sample delivery, XP, heal, refund or new save/package.','Software controls overlap outcomes; no participants, population estimates, balance, human agency/accessibility, physical device, Unity/Windows Player/Steam or commercial clearance.'],'strategic_unit':'ONE North Star production-domain unit, second consecutive after focused workflow. UI/instruments/CI/regressions support it, not additional units.','specialists':'Independent Engineering/Scientific/Creative analyses and coordinated implementation. Agents unavailable at final resumption; primary completed source review, visual correction, final executions and publication sequentially. No human validation.'}
(o/'RUN.json').write_text(json.dumps(run,indent=2)+'\n')
for row in cat['labs']+cat['consumption']:
 if target in row.get('evidence',[]):row['evidence_sha256'][target]=sha(o/'RUN.json')
catp.write_text(json.dumps(cat,indent=2,ensure_ascii=False)+'\n')
p=r/'showcase/portfolio.json';j=json.loads(p.read_text())
for x in j['source_experiments']:
 if x['id']=='field-journey':x['evidence_path']=target;x['evidence_sha256']=sha(o/'RUN.json')
p.write_text(json.dumps(j,indent=2)+'\n')
print('Integrated actual gate execution and current existing consumer bindings; no new consumption decision.')
