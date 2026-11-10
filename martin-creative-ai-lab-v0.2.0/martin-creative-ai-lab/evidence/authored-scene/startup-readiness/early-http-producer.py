import subprocess,socket,time,json,os,urllib.request,threading
from pathlib import Path
out=Path(__file__).with_name('early-http');out.mkdir(exist_ok=False)
base=Path('/workspace/work/gate-equipment/martin-creative-ai-lab-v0.2.0/martin-creative-ai-lab/north-star/authored-scene')
rows=[]
for i in range(12):
 with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
 cmd=['/workspace/work/runtime/dotnet/dotnet',str(base/'Host/bin/Release/net10.0/NorthStar.AuthoredScene.dll'),'--serve',str(port),str(base/'web'),'--seconds','2','--new',str(out/f'run-{i}.json')]
 env=dict(os.environ,DOTNET_PROCESSOR_COUNT='2',DOTNET_STARTUP_HOOKS=str(Path(__file__).parent/'bin/Release/net10.0/Hook.dll'))
 with (out/f'host-{i}.out').open('w') as so,(out/f'host-{i}.err').open('w') as se:
  proc=subprocess.Popen(cmd,stdout=so,stderr=se,env=env);stop=threading.Event()
  def poke():
   while not stop.is_set():
    try:
     with urllib.request.urlopen(f'http://127.0.0.1:{port}/state',timeout=.1) as r:r.read()
    except Exception:pass
  threads=[threading.Thread(target=poke) for _ in range(2)]
  for t in threads:t.start()
  proc.wait(timeout=6);stop.set()
  for t in threads:t.join()
 rows.append({'command':cmd,'exit_code':proc.returncode,'stdout':(out/f'host-{i}.out').read_text(),'stderr':(out/f'host-{i}.err').read_text()})
 (out/'commands.json').write_text(json.dumps(rows,indent=2))
 if proc.returncode:print(json.dumps(rows[-1],indent=2));break
print('attempts',len(rows),'failures',sum(r['exit_code']!=0 for r in rows))
