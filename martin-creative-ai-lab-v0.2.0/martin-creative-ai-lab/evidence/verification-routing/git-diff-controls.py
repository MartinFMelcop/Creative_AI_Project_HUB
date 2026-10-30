#!/usr/bin/env python3
"""Exercise the reused real Git diff through final C# selection in an isolated tree."""
import importlib.util,json,shutil,subprocess,sys,tempfile
from pathlib import Path
root=Path(sys.argv[1]).resolve();output=Path(sys.argv[2]).resolve();sys.path.insert(0,str(root/'tools'));import csharp_scope as scope
records=[]
def command(repo,*args):
 r=subprocess.run(['git','-C',str(repo),*args],capture_output=True,text=True,timeout=30);records.append({'arguments':list(args),'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr});assert r.returncode==0;return r.stdout.strip()
with tempfile.TemporaryDirectory(prefix='routing-git-') as folder:
 repo=Path(folder);workspace=repo/scope.WORKSPACE
 original=scope.plan([],full=True)
 for name in {n for g in original['graph'].values() for n in g['inputs']}|{'north-star/field-journey/preparations.json'}:
  target=workspace/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(root/name,target)
 command(repo,'init','-q');command(repo,'add','.');command(repo,'-c','user.name=Routing control','-c','user.email=routing@example.invalid','commit','-qm','Baseline graph')
 base=command(repo,'rev-parse','HEAD');old=workspace/'north-star/field-journey/preparations.json';new=old.with_name('renamed-preparations.json');old.rename(new)
 removed=workspace/'north-star/reputation-study/Rules/Standing.cs';removed.unlink();added=workspace/'shared/new-contract.py';added.parent.mkdir();added.write_text('# declared new contract\n')
 command(repo,'add','-A');command(repo,'-c','user.name=Routing control','-c','user.email=routing@example.invalid','commit','-qm','Rename remove and add')
 paths=scope.ci_scope.changed_paths(repo,base,'HEAD');expected={str(p.relative_to(repo)) for p in [old,new,removed,added]};assert set(paths)==expected,(paths,expected)
 plan=scope.plan(paths,root=workspace);assert plan['full_fallback'] and all(plan['selected'].values())
 empty=scope.plan(scope.ci_scope.changed_paths(repo,'HEAD','HEAD'),root=workspace);assert all(empty['selected'].values())
 try:scope.ci_scope.changed_paths(repo,'--all','HEAD')
 except ValueError:invalid=True
 else:raise AssertionError('Invalid revision accepted')
 output.write_text(json.dumps({'schema_version':1,'git_commands':records,'actual_changed_paths':paths,'rename_detection':'disabled deliberately; old and new paths both retained','all16_on_deleted_unknown_graph':True,'empty_diff_all16':True,'invalid_revision_refused':invalid,'graph_input_copy':'Exact current declared graph sources copied to isolated temporary repository; no maintained file edited','limits':'Git/parser/selection controls only, no gameplay/CI execution or benchmark.'},indent=2)+'\n')
print('PASS: real Git addition deletion rename empty and invalid-ref routing controls')
