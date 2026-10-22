#!/usr/bin/env python3
"""Independent PNG geometry and real isolated Godot motion-source assay."""
import argparse
import binascii
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import zlib
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
ORIGIN=ROOT/'projects/veil-arena'
PATHS=['media/art/runner-motion.png','media/art/warden-motion.png','media/motion-catalog.json','media/provenance.json','tools/build_motion_catalog.gd','motion.gd']

def png_alpha(path):
 data=Path(path).read_bytes()
 if data[:8]!=b'\x89PNG\r\n\x1a\n':raise ValueError('PNG signature')
 at=8;compressed=bytearray();header=None;ended=False
 while at<len(data):
  length=struct.unpack('>I',data[at:at+4])[0];kind=data[at+4:at+8];body=data[at+8:at+8+length];crc=data[at+8+length:at+12+length]
  if len(body)!=length or len(crc)!=4 or binascii.crc32(kind+body)&0xffffffff!=struct.unpack('>I',crc)[0]:raise ValueError('PNG chunk CRC/length')
  if kind==b'IHDR':header=struct.unpack('>IIBBBBB',body)
  if kind==b'IDAT':compressed.extend(body)
  at+=12+length
  if kind==b'IEND':ended=True;break
 if not ended or at!=len(data) or header is None:raise ValueError('Incomplete PNG')
 w,h,depth,color,compression,filtering,interlace=header
 if (depth,color,compression,filtering,interlace)!=(8,6,0,0,0):raise ValueError('Requires noninterlaced RGBA8')
 raw=zlib.decompress(compressed);stride=w*4
 if len(raw)!=(stride+1)*h:raise ValueError('PNG scanline size')
 previous=bytearray(stride);alpha=[]
 for y in range(h):
  start=y*(stride+1);mode=raw[start];row=bytearray(raw[start+1:start+1+stride])
  if mode>4:raise ValueError('PNG filter')
  for x in range(stride):
   a=row[x-4] if x>=4 else 0;b=previous[x];c=previous[x-4] if x>=4 else 0
   if mode==1:prediction=a
   elif mode==2:prediction=b
   elif mode==3:prediction=(a+b)//2
   elif mode==4:
    p=a+b-c;dist=[abs(p-a),abs(p-b),abs(p-c)];prediction=[a,b,c][dist.index(min(dist))]
   else:prediction=0
   row[x]=(row[x]+prediction)&255
  alpha.append(bytes(row[3::4]));previous=row
 return w,h,alpha

def derive(w,h,alpha,native_float=True):
 frames=[];maxheight=0
 for row in range(4):
  for col in range(4):
   # Positive nearest-integer matches Godot roundi, including half values.
   edges=lambda n,size:(n*size*2+4)//8
   x,y=edges(col,w),edges(row,h);right,bottom=edges(col+1,w),edges(row+1,h)
   points=[(xx-x,yy-y) for yy in range(y,bottom) for xx in range(x,right) if (struct.unpack('>f',struct.pack('>f',alpha[yy][xx]/255.0))[0]>32.0/255.0 if native_float else alpha[yy][xx]>32)]
   if not points:raise ValueError('Empty atlas frame')
   lowx=min(p[0] for p in points);lowy=min(p[1] for p in points);highx=max(p[0] for p in points);highy=max(p[1] for p in points)
   if min(lowx,lowy,right-x-highx-1,bottom-y-highy-1)<2:raise ValueError('Atlas gutter')
   feet=[p[0] for p in points if p[1]>=max(lowy,highy-12)]
   pivot=[round(sum(feet)/len(feet)+1e-10,2),highy+1]
   frames.append({'region':[x,y,right-x,bottom-y],'opaque_bounds':[lowx,lowy,highx+1,highy+1],'pivot':pivot})
   maxheight=max(maxheight,highy-lowy+1)
 return frames,maxheight

def registration(pivot,scale,flipped,anchor=(320,240)):
 sign=-1 if flipped else 1
 # Destination origin plus pivot, with horizontal mirror around the same anchor.
 origin=(anchor[0]-sign*pivot[0]*scale,anchor[1]-pivot[1]*scale)
 return [round(origin[0]+sign*pivot[0]*scale,8),round(origin[1]+pivot[1]*scale,8)]

def invoke(command,cwd):
 p=subprocess.run(command,cwd=cwd,capture_output=True,text=True,timeout=120)
 if p.returncode:raise ValueError('Environment/native execution failed: '+(p.stdout+p.stderr)[-2500:])
 return p.stdout

def fingerprints():
 paths=[ORIGIN/p for p in PATHS]+[HERE/'run.py',HERE/'native.gd']
 return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}

def run(output,godot='godot',compare=None):
 output=Path(output).resolve()
 if output==ROOT or ROOT in output.parents:raise ValueError('Output must be outside maintained sources')
 identities=fingerprints();catalog=json.loads((ORIGIN/'media/motion-catalog.json').read_text());observations=[];negatives=[]
 for actor,spec in catalog['actors'].items():
  p=ORIGIN/spec['texture'];w,h,alpha=png_alpha(p);frames,maxheight=derive(w,h,alpha)
  if [w,h]!=spec['size'] or hashlib.sha256(p.read_bytes()).hexdigest()!=spec['sha256'] or frames!=spec['frames']:raise ValueError('Independent pixel-derived catalog mismatch')
  if abs(spec['scale']-round((66 if actor=='runner' else 84)/maxheight,6))>1e-9:raise ValueError('Independent scale mismatch')
  naive,_=derive(w,h,alpha,native_float=False)
  threshold_diff=[i for i,(a,b) in enumerate(zip(naive,frames)) if a['pivot']!=b['pivot']]
  wrongcrop=[];wrongpivot=[]
  for i,f in enumerate(frames):
   for scale in [spec['scale'],0.5,1.0,2.0]:
    for flipped in [False,True]:
     if registration(f['pivot'],scale,flipped)!=[320,240]:raise ValueError('Mirror/scale anchor drift')
   fixed=[(i%4)*313,(i//4)*313,313,313]
   if fixed!=f['region']:wrongcrop.append(i)
   if f['pivot']!=frames[0]['pivot']:wrongpivot.append(i)
  if not wrongcrop or not wrongpivot:raise ValueError('Negative policy not distinguished')
  observations.append({'actor':actor,'size':[w,h],'frames':len(frames),'max_opaque_height':maxheight,'scale':spec['scale'],'registration_checks':len(frames)*8})
  negatives.append({'actor':actor,'policy':'integer_alpha_greater_than_32','detected_frames':threshold_diff,'classification':'float32 channel versus integer threshold; retained source semantic difference'})
  negatives.extend([{'actor':actor,'policy':'fixed_313_cells','detected_frames':wrongcrop,'classification':'expected policy mismatch; not environment failure'}, {'actor':actor,'policy':'constant_first_frame_pivot','detected_frames':wrongpivot,'classification':'expected policy mismatch; not environment failure'}])
 with tempfile.TemporaryDirectory(prefix='visual-origin-') as temp:
  stage=Path(temp)
  for name in PATHS:
   dest=stage/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ORIGIN/name,dest)
  (stage/'project.godot').write_text('[application]\nconfig/name="Isolated visual source assay"\n[rendering]\nrenderer/rendering_method="gl_compatibility"\n')
  shutil.copyfile(HERE/'native.gd',stage/'native.gd')
  version=invoke([godot,'--version'],stage).strip()
  invoke([godot,'--headless','--path',str(stage),'--editor','--import','--quit'],stage)
  invoke([godot,'--headless','--path',str(stage),'--script','tools/build_motion_catalog.gd'],stage)
  if json.loads((stage/'media/motion-catalog.json').read_text())!=catalog:raise ValueError('Actual isolated producer differs')
  p=stage/'motion.gd';p.write_text(p.read_text().replace('canvas: Node2D','canvas'))
  native=invoke([godot,'--headless','--path',str(stage),'--script','native.gd'],stage)
  marker=[line for line in native.splitlines() if line.startswith('VISUAL_NATIVE ')]
  if len(marker)!=1:raise ValueError('Native result missing')
  controls=json.loads(marker[0].removeprefix('VISUAL_NATIVE '))
  p=stage/'motion.gd';text=p.read_text();old='position+Vector2(0,22)'
  if text.count(old)!=1:raise ValueError('Wrong-anchor mutation target changed')
  p.write_text(text.replace(old,'position+Vector2(0,23)'))
  mutant=subprocess.run([godot,'--headless','--path',str(stage),'--script','native.gd'],cwd=stage,capture_output=True,text=True,timeout=120)
  if mutant.returncode!=1 or 'WRONG_ANCHOR_DETECTED' not in mutant.stdout:raise ValueError('Wrong-anchor mutant escaped or environment failed')
 if fingerprints()!=identities:raise ValueError('Source identities changed during execution')
 result={'schema_version':1,'kind':'visual_source_registration_study','identities':identities,'runtime':{'godot':version},'origin':observations,'negative_policies':negatives,'native':controls,'native_instrumentation':'Only staged canvas: Node2D parameter annotation is removed to permit a RefCounted draw-call recorder. Actual selector and draw arithmetic execute; renderer I/O is observed, not rasterized. Destination browser must establish actual rendering separately.','source_mutants':[{'policy':'wrong_vertical_anchor_23_instead_of_22','detected':True,'classification':'actual isolated native draw-transform failure'}],'limits':'Pixel geometry, native source selection/draw transform and isolated producer execution only. Foot pivot is an alpha-derived registration convention, not anatomical ground truth. No human silhouette recognition, visual quality, accessibility, final art/canon, exclusive rights, Unity, Windows or Steam validation.'}
 if compare and json.loads(Path(compare).read_text())!=result:raise ValueError('Exact identities/results differ')
 output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',required=True,type=Path);p.add_argument('--compare',type=Path);p.add_argument('--godot',default='godot');a=p.parse_args()
 try:r=run(a.output,a.godot,a.compare)
 except (OSError,ValueError,KeyError,subprocess.SubprocessError) as e:p.exit(1,'FAIL: '+str(e)+'\n')
 print('PASS: 32 real atlas cells, 256 registration checks, actual producer/native controls and detected anchor mutant')
