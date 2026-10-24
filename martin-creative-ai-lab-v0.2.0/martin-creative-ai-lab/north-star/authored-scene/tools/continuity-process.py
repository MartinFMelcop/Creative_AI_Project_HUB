#!/usr/bin/env python3
"""Challenge the actual durable authored scene through fresh bounded host processes."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import time
import urllib.error
import urllib.request

ROOT=Path(__file__).resolve().parents[3]
STUDY=ROOT/'north-star/authored-scene'
DLL=STUDY/'Host/bin/Release/net10.0/NorthStar.AuthoredScene.dll'
WEB=STUDY/'web'
SAFE_SURVEY=('skill','skill','walk','skill')
SAFE_DELIVERY=('skill','skill','walk','skill','walk','skill')

class Instrument:
    def __init__(self,dotnet,output):
        self.dotnet=shutil.which(dotnet)
        if not self.dotnet:raise ValueError('Actual SDK executable unavailable')
        self.output=output.resolve()
        if self.output.is_relative_to(ROOT):raise ValueError('Outputs must stay outside maintained sources')
        self.output.mkdir(parents=True,exist_ok=False)
        self.controls=[];self.boundaries=[];self.commands=[];self.processes=[];self.records=[];self.number=0;self.request_number=0
    def check(self,name,condition):
        if not condition:raise AssertionError(name)
        if name in self.controls:raise AssertionError('Duplicate control: '+name)
        self.controls.append(name)
    def request(self,url,body=None):
        data=None if body is None else json.dumps(body).encode()
        req=urllib.request.Request(url+('/state' if body is None else '/command'),data=data,headers={} if body is None else {'Content-Type':'application/json'})
        try:
            with urllib.request.urlopen(req,timeout=4) as response:return response.status,json.loads(response.read())
        except urllib.error.HTTPError as error:return error.code,json.loads(error.read())
    def start(self,mode,path):
        self.number+=1
        with socket.socket() as reserve:reserve.bind(('127.0.0.1',0));port=reserve.getsockname()[1]
        stdout=(self.output/f'host-{self.number}.stdout.txt').open('wb');stderr=(self.output/f'host-{self.number}.stderr.txt').open('wb')
        command=[self.dotnet,str(DLL),'--serve',str(port),str(WEB),'--seconds','120',mode,str(path)]
        process=subprocess.Popen(command,cwd=ROOT,env=dict(os.environ,DOTNET_NOLOGO='1',DOTNET_CLI_TELEMETRY_OPTOUT='1',DOTNET_PROCESSOR_COUNT='2'),stdout=stdout,stderr=stderr)
        row={'process':process,'stdout':stdout,'stderr':stderr,'command':command,'url':f'http://127.0.0.1:{port}','path':str(path),'mode':mode};self.processes.append(row)
        deadline=time.monotonic()+10
        while time.monotonic()<deadline:
            if process.poll() is not None:raise ValueError('Host refused startup: '+(self.output/f'host-{self.number}.stderr.txt').read_text())
            try:
                status,observed=self.request(row['url'])
                if status==200:
                    self.commands.append({'command':command,'observation':'Actual loopback READY and state','exit_code_at_start':None});return row,observed
            except (OSError,ValueError):pass
            time.sleep(.025)
        raise ValueError('Actual host did not become ready')
    def stop(self,row,abrupt=False):
        process=row['process']
        if process.poll() is None:
            process.kill() if abrupt else process.terminate()
            try:process.wait(timeout=3)
            except subprocess.TimeoutExpired:process.kill();process.wait(timeout=3)
        row['stdout'].close();row['stderr'].close()
        self.records.append({'command':row['command'],'owned_process_exit_code':process.returncode,'termination':'owned process kill' if abrupt else 'owned process stop'})
    def state(self,row):
        status,observed=self.request(row['url'])
        if status!=200:raise AssertionError('GET state failed')
        return observed
    @staticmethod
    def continuity_facts(observed):
        return {name:observed['continuity'][name] for name in ('mode','run_id','revision','day','status')}
    def body(self,observed,command,request_id=None):
        self.request_number+=1
        return {'command':command,'request_id':request_id or 'process_'+str(self.request_number),'revision':observed['continuity']['revision'],'run_id':observed['continuity']['run_id']}
    def act(self,row,observed,command,request_id=None):
        body=self.body(observed,command,request_id);status,result=self.request(row['url'],body)
        self.commands.append({'request':body,'http_status':status,'accepted':result.get('accepted')})
        if status!=200 or result.get('accepted') is not True:raise AssertionError('Actual setup action refused: '+command+' '+json.dumps(result))
        if result['continuity']['status']!='saved':raise AssertionError('Accepted action was not saved')
        return result,body
    def sequence(self,row,observed,commands):
        for command in commands:observed,_=self.act(row,observed,command)
        return observed
    def reopen(self,row,observed,label,abrupt=False):
        path=Path(row['path']);before=path.read_bytes();self.stop(row,abrupt);replacement,recovered=self.start('--resume',path)
        self.check(label+': exact saved state recovered',recovered['state']==observed['state'])
        self.check(label+': accepted text and revision recovered',recovered['text']==observed['text'] and self.continuity_facts(recovered)==self.continuity_facts(observed))
        self.check(label+': reopening changes no saved bytes',path.read_bytes()==before)
        self.boundaries.append({'id':label,'termination':'actual owned process kill' if abrupt else 'actual owned process stop','before':observed,'recovered':recovered,'journal_sha256':hashlib.sha256(before).hexdigest()})
        return replacement,recovered
    def reject(self,row,body,label):
        before=self.state(row);path=Path(row['path']);saved=path.read_bytes();status,result=self.request(row['url'],body)
        after=self.state(row)
        self.check(label,status>=400 or result.get('accepted') is False)
        self.check(label+': saved facts and bytes unchanged',after['state']==before['state'] and self.continuity_facts(after)==self.continuity_facts(before) and path.read_bytes()==saved)
        self.commands.append({'rejected_request':body,'http_status':status,'accepted':result.get('accepted')})
        return after
    def reject_start(self,mode,path,label):
        existed=path.exists();before=path.read_bytes() if existed else None
        self.number+=1
        with socket.socket() as reserve:reserve.bind(('127.0.0.1',0));port=reserve.getsockname()[1]
        command=[self.dotnet,str(DLL),'--serve',str(port),str(WEB),'--seconds','5',mode,str(path)]
        result=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=8)
        self.commands.append({'command':command,'exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr,'expected':'refused startup'})
        self.check(label,result.returncode!=0 and 'READY' not in result.stdout)
        self.check(label+': saved bytes preserved',path.read_bytes()==before if existed else not path.exists())
    def run(self):
        complete=False;failure=None
        try:
            path=self.output/'one narrative run.json';row,observed=self.start('--new',path)
            self.check('New durable run is explicitly saved',observed['continuity']['mode']=='local' and observed['continuity']['status']=='saved' and observed['continuity']['revision']==0)
            observed,first_work=self.act(row,observed,'work','first_work')
            observed=self.sequence(row,observed,('survey',)+SAFE_SURVEY+('open','hear'))
            row,observed=self.reopen(row,observed,'heard-offer')
            observed,_=self.act(row,observed,'offer');self.check('Heard private permission permits actual next offer after reopen',observed['state']['conversation']=='terms')
            observed,_=self.act(row,observed,'terms dusk');row,observed=self.reopen(row,observed,'draft-terms')
            observed,_=self.act(row,observed,'confirm');self.check('Draft private permission permits actual confirmation after reopen',observed['state']['guide_location']=='local-preparing' and not observed['state']['delivered'] and not observed['state']['returned'])
            row,observed=self.reopen(row,observed,'preparing')
            observed,_=self.act(row,observed,'depart guided');observed,_=self.act(row,observed,'skill');row,observed=self.reopen(row,observed,'active-guided',True)
            before=observed['state']['encounter'];observed,_=self.act(row,observed,'skill');after=observed['state']['encounter']
            self.check('Recovered encounter executes exactly the next actual beat',after['beat']==before['beat']+1 and after['health']==before['health'] and after['resolve']==before['resolve']-3)
            observed=self.sequence(row,observed,SAFE_DELIVERY[2:]);self.check('Actual completed delivery leaves three local crates unfinished',observed['state']['delivered'] and observed['state']['returned'] and observed['state']['crates']==2 and observed['state']['remaining']==0)
            row,observed=self.reopen(row,observed,'delivered-unfinished-work')
            before=self.state(row);saved=path.read_bytes();status,duplicate=self.request(row['url'],first_work)
            self.check('Accepted request retry after later progress is a no-op',status==200 and duplicate.get('accepted') is True and duplicate['state']==before['state'] and self.continuity_facts(duplicate)==self.continuity_facts(before) and duplicate['continuity']['duplicate'] is True and path.read_bytes()==saved)
            stale=self.body(observed,'work');stale['revision']=0;observed=self.reject(row,stale,'Stale revision refused')
            wrong=self.body(observed,'work');wrong['run_id']='not_this_day';observed=self.reject(row,wrong,'Wrong day identity refused')
            injected=self.body(observed,'work');injected['state']={'delivered':True};observed=self.reject(row,injected,'Client cannot inject delivery state')
            old_id=observed['continuity']['run_id'];old_revision=observed['continuity']['revision'];old_history=json.loads(path.read_text())['entries'];queued=self.body(observed,'work')
            observed,_=self.act(row,observed,'restart');self.check('Explicit new day changes identity and appends accepted revision',observed['continuity']['run_id']!=old_id and observed['continuity']['revision']==old_revision+1 and observed['state']['crates']==0 and observed['state']['shift']==0)
            self.check('New day preserves earlier accepted history',json.loads(path.read_text())['entries'][:-1]==old_history)
            observed=self.reject(row,queued,'Old queued intent refused after new day');observed=self.reject(row,first_work,'Known old request ID refused before duplicate handling')
            row,observed=self.reopen(row,observed,'explicit-new-day');self.stop(row)
            self.reject_start('--new',path,'Create cannot overwrite existing narrative run')
            self.reject_start('--resume',self.output/'missing run.json','Resume cannot silently create missing narrative run')
            corrupt=self.output/'corrupt run.json';corrupt.write_bytes(b'{broken narrative journal')
            self.reject_start('--resume',corrupt,'Corrupt saved narrative cannot silently reset')
            failure_path=self.output/'failed guide run.json';row,observed=self.start('--new',failure_path)
            observed=self.sequence(row,observed,('survey',)+SAFE_SURVEY+('open','hear','offer','terms dusk','confirm','depart guided','wait','wait'))
            self.check('Actual losing encounter leaves Rill unaccounted without delivery or return',observed['state']['status']=='failed' and observed['state']['guide_location']=='unaccounted' and not observed['state']['delivered'] and not observed['state']['returned'])
            row,observed=self.reopen(row,observed,'failed-unaccounted');observed,_=self.act(row,observed,'work')
            self.check('Recovered failed guide remains unavailable during remaining local work',observed['state']['crates']==1 and observed['state']['guide_location']=='unaccounted' and observed['state']['capacity']==1)
            complete=True
            result={'schema_version':1,'complete':True,'passed':len(self.controls),'controls':self.controls,'boundaries':self.boundaries,'scope':'Selected actual trusted-local Linux host-process continuity; no power loss, Windows, Steam, distributed account or human assessment.'}
            (self.output/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':len(self.controls),'process_boundaries':len(self.boundaries),'scope':result['scope']}))
        except Exception as error:failure=str(error);raise
        finally:
            for row in self.processes:
                if row['process'].poll() is None or not row['stdout'].closed or not row['stderr'].closed:self.stop(row)
            (self.output/'execution.json').write_text(json.dumps({'complete':complete,'failure':failure,'controls':self.controls,'boundaries':self.boundaries,'commands':self.commands,'process_exits':self.records},indent=2)+'\n')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--dotnet',default='dotnet');parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    try:Instrument(args.dotnet,args.output).run()
    except (OSError,ValueError,AssertionError,subprocess.SubprocessError) as error:parser.exit(1,'FAIL: '+str(error)+'\n')
