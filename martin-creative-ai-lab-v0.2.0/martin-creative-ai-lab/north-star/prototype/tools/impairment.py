"""Bounded, byte-preserving loopback TCP frame scheduler for the actual authority.

This is an intervention instrument, not a WAN emulator. Delay begins when a complete
newline frame is received. FIFO survives jitter/batching; no TCP byte loss is faked.
"""
from collections import deque
from contextlib import AbstractContextManager
import math
import selectors
import socket
import threading
import time

PROFILES = {
    'relay_zero': {'delay_ms': 0, 'batch_ms': 0},
    'delay_60': {'delay_ms': 60, 'batch_ms': 0},
    'batch_400': {'delay_ms': 0, 'batch_ms': 400},
}
MAX_FRAME = 16384
MAX_BUFFER = 65536
MAX_QUEUE = 262144
MAX_FRAMES = 128


class Relay(AbstractContextManager):
    def __init__(self, upstream_port, profile='relay_zero', *, lifetime=70):
        if isinstance(upstream_port,bool) or not isinstance(upstream_port,int) or not 1024<=upstream_port<=65535:
            raise ValueError('Invalid upstream loopback port')
        if profile not in PROFILES:raise ValueError('Unknown impairment profile')
        if isinstance(lifetime,bool) or not isinstance(lifetime,(int,float)) or not math.isfinite(lifetime) or not 1<=lifetime<=120:
            raise ValueError('Relay lifetime must be 1..120 seconds')
        self.upstream_port = upstream_port;self.profile = profile;self.lifetime = lifetime
        self.listener = None;self.thread = None;self.stop = threading.Event();self.error = None
        self.stats = {'profile':profile,'configured':dict(PROFILES[profile]),'connected':False,'closed':False,
                      'directions':{name:{'frames_received':0,'frames_forwarded':0,'bytes_received':0,'bytes_forwarded':0,
                      'max_queued_bytes':0,'max_residence_ms':0.0,'min_residence_ms':None,'sum_residence_ms':0.0,
                      'max_lateness_ms':0.0,'max_frames_per_send_turn':0} for name in ('up','down')}}

    def __enter__(self):
        self.listener = socket.socket();self.listener.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        self.listener.bind(('127.0.0.1',0));self.listener.listen(1);self.listener.setblocking(False)
        self.port = self.listener.getsockname()[1]
        self.thread = threading.Thread(target=self._run,name='north-star-impairment',daemon=False);self.thread.start()
        return self

    def __exit__(self, typ, value, traceback):
        self.stop.set()
        if self.thread:self.thread.join(timeout=2)
        if self.thread and self.thread.is_alive():raise RuntimeError('Owned relay thread did not stop')
        if self.error and typ is None:raise ValueError('Impairment relay failed: '+self.error)
        return False

    def due(self, now, direction, previous, origin):
        config = PROFILES[self.profile]
        due = now+config['delay_ms']/1000
        if direction=='down' and config['batch_ms']:
            interval = config['batch_ms']/1000
            due = origin+(math.floor((now-origin)/interval)+1)*interval
        return max(previous,due)

    def _run(self):
        sockets = [];selector = selectors.DefaultSelector();started = time.monotonic();deadline = started+self.lifetime
        try:
            selector.register(self.listener,selectors.EVENT_READ,'accept')
            client = upstream = None
            directions = {}
            while not self.stop.is_set() and time.monotonic()<deadline:
                for key,_ in selector.select(.002):
                    if key.data=='accept':
                        candidate,_ = self.listener.accept()
                        if client is not None:candidate.close();continue
                        client = candidate;client.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1)
                        upstream = socket.create_connection(('127.0.0.1',self.upstream_port),timeout=1)
                        upstream.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1)
                        sockets.extend((client,upstream))
                        for sock in sockets:sock.setblocking(False)
                        directions = {'up':{'source':client,'target':upstream},'down':{'source':upstream,'target':client}}
                        for name,state in directions.items():
                            state.update(buffer=bytearray(),queue=deque(),queued=0,last_due=started,eof=False,shutdown=False)
                            selector.register(state['source'],selectors.EVENT_READ,name)
                        selector.unregister(self.listener);self.listener.close();self.stats['connected']=True
                        continue
                    name = key.data;state = directions[name];stats = self.stats['directions'][name]
                    try:chunk = state['source'].recv(32768)
                    except BlockingIOError:continue
                    if not chunk:
                        if state['buffer']:raise ValueError('EOF inside a newline frame')
                        selector.unregister(state['source']);state['eof']=True;continue
                    stats['bytes_received']+=len(chunk);state['buffer'].extend(chunk)
                    if len(state['buffer'])>MAX_BUFFER:raise ValueError('Frame buffer limit exceeded')
                    while b'\n' in state['buffer']:
                        end = state['buffer'].index(10)+1
                        if end>MAX_FRAME or end==1:raise ValueError('Invalid or oversized relay frame')
                        frame = bytes(state['buffer'][:end]);del state['buffer'][:end]
                        now = time.monotonic();due = self.due(now,name,state['last_due'],started);state['last_due']=due
                        state['queue'].append([due,frame,0,now,False]);state['queued']+=len(frame);stats['frames_received']+=1
                        if state['queued']>MAX_QUEUE or len(state['queue'])>MAX_FRAMES:raise ValueError('Scheduled queue limit exceeded')
                        stats['max_queued_bytes']=max(stats['max_queued_bytes'],state['queued'])
                    if len(state['buffer'])>=MAX_FRAME:raise ValueError('Unterminated relay frame limit exceeded')
                for name,state in directions.items():
                    stats = self.stats['directions'][name];turn = 0
                    while state['queue'] and turn<MAX_FRAMES:
                        item = state['queue'][0];due,frame,offset,received,observed = item
                        now = time.monotonic()
                        if due>now:break
                        try:sent = state['target'].send(memoryview(frame)[offset:])
                        except BlockingIOError:break
                        if not sent:raise ValueError('Relay could not forward bytes')
                        if not observed:
                            residence = (now-received)*1000
                            stats['min_residence_ms']=residence if stats['min_residence_ms'] is None else min(stats['min_residence_ms'],residence)
                            stats['max_residence_ms']=max(stats['max_residence_ms'],residence);stats['sum_residence_ms']+=residence
                            stats['max_lateness_ms']=max(stats['max_lateness_ms'],max(0,now-due)*1000);item[4]=True
                        item[2]+=sent;state['queued']-=sent;stats['bytes_forwarded']+=sent
                        if item[2]==len(frame):state['queue'].popleft();stats['frames_forwarded']+=1;turn+=1
                        else:break
                    stats['max_frames_per_send_turn']=max(stats['max_frames_per_send_turn'],turn)
                    if state['eof'] and not state['queue'] and not state['shutdown']:
                        try:state['target'].shutdown(socket.SHUT_WR)
                        except OSError:pass
                        state['shutdown']=True
                if directions and all(s['eof'] and s['shutdown'] for s in directions.values()):break
            if time.monotonic()>=deadline:raise ValueError('Relay lifetime exceeded')
        except Exception as error:
            self.error=type(error).__name__+": "+str(error)
        finally:
            for sock in sockets:sock.close()
            if self.listener:self.listener.close()
            selector.close();self.stats['closed']=True
