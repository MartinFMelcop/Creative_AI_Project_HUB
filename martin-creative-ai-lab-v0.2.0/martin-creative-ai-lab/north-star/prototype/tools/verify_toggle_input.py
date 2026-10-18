#!/usr/bin/env python3
"""Bounded source/PCK XTest input journeys in the actual Godot window.

Requires Xorg dummy driver and libX11/libXtst. Synthetic OS input is not a human
accessibility study. Fixture medicine geometry is explicit; guard uses rehearsal.
"""
import argparse
import ctypes as C
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
ROOT=Path(__file__).resolve().parents[1]

X=C.CDLL('libX11.so.6');T=C.CDLL('libXtst.so.6')
X.XOpenDisplay.argtypes=[C.c_char_p];X.XOpenDisplay.restype=C.c_void_p
X.XStringToKeysym.argtypes=[C.c_char_p];X.XStringToKeysym.restype=C.c_ulong
X.XKeysymToKeycode.argtypes=[C.c_void_p,C.c_ulong];X.XKeysymToKeycode.restype=C.c_uint
X.XSync.argtypes=[C.c_void_p,C.c_int];X.XSetInputFocus.argtypes=[C.c_void_p,C.c_ulong,C.c_int,C.c_ulong]
X.XCloseDisplay.argtypes=[C.c_void_p]
T.XTestFakeKeyEvent.argtypes=[C.c_void_p,C.c_uint,C.c_int,C.c_ulong]
X.XDefaultRootWindow.argtypes=[C.c_void_p];X.XDefaultRootWindow.restype=C.c_ulong
X.XQueryTree.argtypes=[C.c_void_p,C.c_ulong,C.POINTER(C.c_ulong),C.POINTER(C.c_ulong),C.POINTER(C.POINTER(C.c_ulong)),C.POINTER(C.c_uint)]
X.XFetchName.argtypes=[C.c_void_p,C.c_ulong,C.POINTER(C.c_char_p)]
X.XFree.argtypes=[C.c_void_p]
def window(display):
 root=C.c_ulong();parent=C.c_ulong();children=C.POINTER(C.c_ulong)();count=C.c_uint()
 X.XQueryTree(display,X.XDefaultRootWindow(display),C.byref(root),C.byref(parent),C.byref(children),C.byref(count))
 found=None
 for i in range(count.value):
  name=C.c_char_p()
  if X.XFetchName(display,children[i],C.byref(name)) and name.value:
   if b'Virgo Diamond' in name.value:found=children[i]
   X.XFree(name)
 if children:X.XFree(children)
 return found
def verify(output):
 output.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory(prefix='crossing-toggle-') as directory:
  scratch=Path(directory);env=os.environ.copy()
  for name in ('CROSSING_PROFILE','CROSSING_CONTROLS','CROSSING_CAPTURE'):env.pop(name,None)
  env.update({k:str(scratch/k) for k in ('XDG_DATA_HOME','XDG_CONFIG_HOME','XDG_CACHE_HOME')})
  display=next((n for n in range(110,130) if not Path(f'/tmp/.X11-unix/X{n}').exists() and not Path(f'/tmp/.X{n}-lock').exists()),None)
  if display is None:raise ValueError('No unused local display')
  env['DISPLAY']=f':{display}'
  server=game=d=None;records={};deadline=time.monotonic()+150
  with (scratch/'engine.log').open('w') as log:
   try:
    server=subprocess.Popen(['Xorg',env['DISPLAY'],'-config',str(ROOT/'tests/dummy-display.conf'),'-logfile',str(scratch/'Xorg.log'),'-noreset','-nolisten','tcp'],env=env,stdout=log,stderr=log)
    for _ in range(40):
     d=X.XOpenDisplay(env['DISPLAY'].encode())
     if d:break
     time.sleep(.05)
    if not d:raise ValueError('Owned Xorg unavailable')
    for delivery in ('source','pack'):
     capture=scratch/(delivery+'.png');env['CROSSING_CAPTURE']=str(capture)
     env['CROSSING_PROFILE']=str(scratch/(delivery+'-marks.json'));env['CROSSING_CONTROLS']=str(scratch/(delivery+'-keys.json'))
     base=['godot','--path',str(ROOT)] if delivery=='source' else ['godot','--main-pack',str(ROOT/'dist/crossing-drill.pck')]
     def launch(fixture=False):
      nonlocal game
      if game:
       game.terminate();game.wait(timeout=3)
       for _ in range(60):
        X.XSync(d,0)
        if window(d) is None:break
        time.sleep(.05)
      game=subprocess.Popen(base+['--audio-driver','Dummy']+(['--script','res://tests/toggle_fixture.gd'] if fixture else []),env=env,stdout=log,stderr=log)
      target=None
      for _ in range(300):
       target=window(d)
       if target:break
       if game.poll() is not None:raise ValueError('Godot stopped before its window appeared')
       time.sleep(.05)
      if not target:raise ValueError('Actual consumer window missing: '+(scratch/'engine.log').read_text()[-1800:])
      X.XSetInputFocus(d,target,1,0);X.XSync(d,0);time.sleep(.3)
     def key(name,on=True):
      if time.monotonic()>deadline:raise ValueError('Owned journey exceeded 150 second bound')
      code=X.XKeysymToKeycode(d,X.XStringToKeysym(name.encode()))
      if not code:raise ValueError('Unavailable XTest key '+name)
      T.XTestFakeKeyEvent(d,code,on,0);X.XSync(d,0)
     def tap(name):
      key(name);time.sleep(.06);key(name,False);time.sleep(.06)
     def shot(name):
      record=Path(str(capture)+'.json');prior=record.stat().st_mtime_ns if record.exists() else 0
      tap('F12')
      for _ in range(100):
       if record.exists() and record.stat().st_mtime_ns!=prior:
        try:
         result=json.loads(record.read_text());shutil.copyfile(capture,output/(delivery+'-'+name+'.png'));return result
        except json.JSONDecodeError:pass
       time.sleep(.03)
      raise ValueError('Consumer did not acknowledge capture input at '+delivery+'/'+name+': '+(scratch/'engine.log').read_text()[-1000:])
     launch();tap('F1');tap('h');tap('i');settings=shot('settings')
     assert settings['controls']['profile']['toggle_guard'] and settings['controls']['profile']['toggle_interact'], delivery+': failed consumer invariant at instrument line 97'
     tap('Escape');tap('t');tap('Return');tap('k')
     raised=shot('raised');assert raised['controls']['profile']['guard_latched'], delivery+': released guard press was not received'
     for _ in range(15):
      block=shot('block')
      if block['rehearsal']['state']=='review':break
      time.sleep(.06)
     assert block['rehearsal']['passed'] and block['counters']['blocks']==1, delivery+': failed consumer invariant at instrument line 104'
     assert not block['controls']['profile']['guard_latched'], delivery+': failed consumer invariant at instrument line 105'
     launch(True);fresh=shot('fresh-session')
     assert not fresh['controls']['profile']['toggle_guard'] and not fresh['controls']['profile']['toggle_interact'], delivery+': failed consumer invariant at instrument line 107'
     tap('F1');tap('i');tap('Escape');tap('Return');tap('e');time.sleep(.85)
     recovery_samples=[]
     for _ in range(15):
      recovered=shot('recovered')
      recovery_samples.append({'tick':recovered['tick'],'errand':recovered['errand'],'intent':recovered['controls']['profile']['interact_latched']})
      if recovered['errand']['state']=='carried':break
      if not recovered['controls']['profile']['interact_latched']:raise ValueError(delivery+': consumer did not retain the received recovery press')
      time.sleep(.1)
     assert recovered['errand']['state']=='carried' and not recovered['controls']['profile']['interact_latched'], delivery+': actual recovery did not finish/disarm within bounded observations'
     tap('Escape');paused=shot('paused')
     assert paused['mode']=='paused' and not paused['controls']['profile']['guard_latched'] and not paused['controls']['profile']['interact_latched'], delivery+': failed consumer invariant at instrument line 118'
     records[delivery]={'settings':settings,'raised':raised,'block':block,'fresh':fresh,'recovered':recovered,'paused':paused,'recovery_samples':recovery_samples}
     game.terminate();game.wait(timeout=3);game=None
   finally:
    if d:X.XCloseDisplay(d)
    for child in (game,server):
     if child:
      child.terminate()
      try:child.wait(timeout=3)
      except subprocess.TimeoutExpired:child.kill();child.wait()
  logtext=(scratch/'engine.log').read_text()
  if any(e in logtext for e in ('SCRIPT ERROR:','Parse Error:','ERROR:')):raise ValueError(logtext[-2000:])
  result={'kind':'synthetic_os_input','deliveries':records,'scope':'Actual source/PCK settings, released single-press rehearsal block, fresh-session reset and prepared case recovery. Wall-clock ticks may differ. No participant, navigated case route or hardware latency claim.'}
  (output/'keyboard.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
  print('PASS: source/PCK actual XTest single-press guard, case recovery, settings and fresh-session reset')
  return result

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
 try:verify(args.output)
 except (AssertionError,OSError,ValueError,subprocess.TimeoutExpired) as error:parser.exit(1,f'FAIL: {error}\n')
