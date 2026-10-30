#!/usr/bin/env python3
"""Check final CLI help and actual delegated startup; no full route claim."""
import argparse,hashlib,json,os,socket,subprocess,time,urllib.request
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--workspace',type=Path,required=True);p.add_argument('--dotnet',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();root=a.workspace.resolve();source=root/'north-star/field-journey/Host/Program.cs';before=hashlib.sha256(source.read_bytes()).hexdigest();logs=[]
def run(command):
 r=subprocess.run(command,cwd=root,capture_output=True,text=True,timeout=120);logs.append({'command':command,'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr});return r
build=run([a.dotnet,'build',str(root/'north-star/field-journey/Host/NorthStar.FieldJourney.csproj'),'-c','Release']);assert build.returncode==0
app=str(root/'north-star/field-journey/Host/bin/Release/net10.0/NorthStar.FieldJourney.dll');usage=run([a.dotnet,app]);assert usage.returncode==1 and '--policy independent|ordered|single-offer]' in usage.stderr
sock=socket.socket();sock.bind(('127.0.0.1',0));port=sock.getsockname()[1];sock.close();command=[a.dotnet,app,'--serve',str(port),str(root/'north-star/field-journey/web'),'--seconds','10','--policy','single-offer'];child=subprocess.Popen(command,cwd=root,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True);state=None
try:
 for _ in range(100):
  if child.poll() is not None:raise AssertionError('Host exited before observed startup')
  try:
   with urllib.request.urlopen(f'http://127.0.0.1:{port}/state',timeout=1) as response:state=json.load(response)
   break
  except (OSError,ValueError):time.sleep(.05)
 assert state is not None and state['memory']['policy']=='single-offer'
 assert state['memory']['turn']==0 and state['memory']['parts']==4 and state['memory']['coins']==2
 assert all(not b['offer_closed'] and not b['delivered'] for b in state['memory']['benches'])
finally:
 if child.poll() is None:child.terminate()
 out,err=child.communicate(timeout=10);logs.append({'command':command,'exit_code':child.returncode,'stdout':out,'stderr':err,'termination':'Owned probe explicitly stopped after observing startup'})
assert hashlib.sha256(source.read_bytes()).hexdigest()==before
a.output.write_text(json.dumps({'schema_version':1,'checks':{'passed':3,'failed':0},'controls':['Actual final FieldHost build','Invalid invocation advertises all three accepted policies','Actual single-offer child startup preserves original resources and no acquired outputs'],'commands':logs,'source':{'path':str(source.relative_to(root)),'sha256':before},'state':state,'limits':'Post-integrated-run CLI usage-string correction only. Targeted actual build/startup/HTTP observations, not a full single-offer Field route, new Windows/Unity or unchanged final112input gameplay execution.'},indent=2)+'\n');print('PASS: three final Field CLI/startup controls')
