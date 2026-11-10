import subprocess,socket,time,json,os,urllib.request,threading,hashlib,importlib.util
from pathlib import Path
base=Path('/workspace/work/gate-assist/startup-hook-probe');out=base/'ready-http';out.mkdir(exist_ok=False)
scene=Path('/workspace/work/gate-equipment/martin-creative-ai-lab-v0.2.0/martin-creative-ai-lab/north-star/authored-scene');dll=scene/'Host/bin/Release/net10.0/NorthStar.AuthoredScene.dll';hook=base/'bin/Release/net10.0/Hook.dll'
helper=Path('/workspace/work/authored-startup/martin-creative-ai-lab-v0.2.0/martin-creative-ai-lab/north-star/authored-scene/tools/continuity-process.py');spec=importlib.util.spec_from_file_location('actual_continuity_ready',helper);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);instrument=module.Instrument.__new__(module.Instrument)
rows=[];journal=out/'one actual journal.json';identity=hashlib.sha256(dll.read_bytes()).hexdigest();original=None
for i in range(4):
 with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
 mode='--new' if i==0 else '--resume';before=journal.read_bytes() if journal.exists() else None
 cmd=['/workspace/work/runtime/dotnet/dotnet',str(dll),'--serve',str(port),str(scene/'web'),'--seconds','2',mode,str(journal)]
 env=dict(os.environ,DOTNET_PROCESSOR_COUNT='2',DOTNET_STARTUP_HOOKS=str(hook));so_path=out/f'host-{i}.out';se_path=out/f'host-{i}.err';url=f'http://127.0.0.1:{port}';start=time.monotonic()
 with so_path.open('wb') as so,se_path.open('wb') as se:
  proc=subprocess.Popen(cmd,stdout=so,stderr=se,env=env);stop=threading.Event();ready=threading.Event();http=[];ready_at=None
  def poke(worker):
   ready.wait(timeout=4)
   while ready.is_set() and not stop.is_set():
    began=time.monotonic();record={'worker':worker,'started_after_process_seconds':began-start,'ready_observed_before_request':ready_at is not None and began>=ready_at}
    try:
     with urllib.request.urlopen(url+'/state',timeout=.1) as r:
      body=json.loads(r.read());record.update(status=r.status,sequence=body.get('sequence'),run_id=body.get('continuity',{}).get('run_id'))
    except Exception as e:record.update(error_type=type(e).__name__,error=str(e))
    http.append(record)
  threads=[threading.Thread(target=poke,args=(n,)) for n in range(2)]
  for t in threads:t.start()
  failure=None
  try:
   instrument.wait_ready({'process':proc,'url':url,'stdout_path':so_path,'stderr_path':se_path},time.monotonic()+5)
   ready_at=time.monotonic();ready.set();proc.wait(timeout=6)
  except Exception as e:
   failure=f'{type(e).__name__}: {e}'
   if proc.poll() is None:proc.kill();proc.wait(timeout=3)
  finally:
   stop.set();ready.set()
   for t in threads:t.join(timeout=2)
 data=journal.read_bytes() if journal.exists() else None
 if i==0:original=data
 successful=[r for r in http if r.get('status')==200]
 row={'command':cmd,'exit_code':proc.returncode,'stdout':so_path.read_text(),'stderr':se_path.read_text(),'failure':failure,'ready_observed_after_process_seconds':None if ready_at is None else ready_at-start,'http_threads':2,'http_attempts':len(http),'http_success':len(successful),'all_requests_after_matching_ready':all(r['ready_observed_before_request'] for r in http),'http_outcomes':http,'journal_sha256_after':None if data is None else hashlib.sha256(data).hexdigest(),'resume_bytes_unchanged':None if mode=='--new' else data==before,'all_journal_bytes_equal_original':data==original};rows.append(row);(out/'commands.json').write_text(json.dumps(rows,indent=2)+'\n')
 print(i,mode,'exit',row['exit_code'],'HTTP',len(successful),'afterREADY',row['all_requests_after_matching_ready'],'resumeUnchanged',row['resume_bytes_unchanged'])
 if proc.returncode or failure or not successful or not row['all_requests_after_matching_ready'] or data!=original:break
summary={'actual_processes':len(rows),'ready_and_successful_http_each':all(r['ready_observed_after_process_seconds'] is not None and r['http_success']>0 for r in rows),'exit_zero_each':all(r['exit_code']==0 for r in rows),'all_http_after_matching_ready':all(r['all_requests_after_matching_ready'] for r in rows),'all_resume_journal_bytes_unchanged':all(r['resume_bytes_unchanged'] is not False for r in rows),'host_sha256_before':identity,'host_sha256_after':hashlib.sha256(dll.read_bytes()).hexdigest(),'hook_sha256':hashlib.sha256(hook.read_bytes()).hexdigest(),'actual_ready_helper':str(helper),'ready_helper_sha256':hashlib.sha256(helper.read_bytes()).hexdigest(),'rules_identity':None if original is None else json.loads(original)['rules_id'],'limits':'Four bounded processes; deliberately stressed loopback GET. Observer present in both early and READY-first probes; no general runtime/server fix inferred.'};(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
