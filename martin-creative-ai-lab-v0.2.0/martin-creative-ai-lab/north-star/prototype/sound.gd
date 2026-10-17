extends Node
## Original short procedural cues; a read-only observer never changes Combat.
const RATE := 22050
const NAMES := ["bolt","pulse","block","draw","counter","hurt","won","lost"]
const LENGTHS := {"bolt":0.30,"pulse":0.38,"block":0.28,"draw":0.24,"counter":0.16,"hurt":0.24,"won":0.60,"lost":0.56}
static var cache := {}
var voices: Array[AudioStreamPlayer] = []
var muted := false
var model
var phase := "rest"
var mode := "title"
var cursor := 0
var history: Array[Dictionary] = []

static func stream_for(name: String) -> AudioStreamWAV:
	if cache.has(name):return cache[name]
	if name not in NAMES:return null
	var length: float=LENGTHS[name]
	var frames: int=roundi(length*RATE)
	var pcm=PackedByteArray();pcm.resize(frames*2)
	for i in frames:
		var t: float=float(i)/RATE
		var u: float=t/length
		var envelope: float=minf(1,t/0.008)*pow(1-u,2)
		var value := 0.0
		match name:
			"bolt":
				# Three rising narrow-band taps; no implied directional information.
				var tap: int=mini(2,int(t/0.1))
				var local: float=fmod(t,0.1)
				value=sin(TAU*(440+tap*110)*local)*minf(1,local/0.006)*maxf(0,1-local/0.075)
			"pulse":
				# Low rough falling pair, distinct in rhythm and register from the bolt.
				var local: float=fmod(t,0.19)
				value=(sin(TAU*(150*local-90*local*local))+0.25*sin(TAU*310*local))*minf(1,local/0.008)*maxf(0,1-local/0.16)
			"block":value=(sin(TAU*430*t)+0.45*sin(TAU*1091*t))*exp(-9*t)
			"draw":value=(sin(TAU*(1350*t-1800*t*t))+0.3*sin(TAU*2039*t))*sin(PI*u)
			"counter":value=(sin(TAU*1800*t)+0.5*sin(TAU*310*t))*exp(-24*t)
			"hurt":value=(sin(TAU*(120*t-80*t*t))+0.3*sin(TAU*697*t))*exp(-15*t)
			"won","lost":
				var note: int=mini(2,int(u*3))
				var pitches=[146.8324,184.9972,220.0] if name=="won" else [146.8324,130.8128,110.0]
				var local: float=fmod(t,length/3)
				value=(sin(TAU*pitches[note]*local)+0.2*sin(TAU*pitches[note]*2*local))*minf(1,local/0.008)*minf(1,(length/3-local)/0.012)
		var sample: int=roundi(clampf(value*envelope*0.28,-0.9,0.9)*32767)
		pcm.encode_s16(i*2,sample)
	var stream=AudioStreamWAV.new()
	stream.format=AudioStreamWAV.FORMAT_16_BITS;stream.mix_rate=RATE;stream.stereo=false;stream.data=pcm
	cache[name]=stream
	return stream

func _ready() -> void:
	for name in NAMES:stream_for(name)
	# One threat voice and one response voice bound overlap without touching Master.
	for i in 2:
		var voice=AudioStreamPlayer.new();voice.volume_db=-6
		add_child(voice);voices.append(voice)

func silence() -> void:
	for voice in voices:
		voice.stop()

func set_muted(value: bool) -> void:
	muted=value
	if muted:silence()

func cue(name: String,tick: int) -> void:
	if muted:return
	var channel: int=0 if name in ["bolt","pulse"] else 1
	var voice=voices[channel]
	voice.stop();voice.stream=stream_for(name);voice.play()
	history.append({"cue":name,"tick":tick})
	if history.size()>64:history.pop_front()

func observe(game, suspended: bool=false) -> void:
	if model!=game:
		silence();model=game;phase="rest" if game.elapsed==0 else game.phase;mode=game.mode;cursor=game.events.size();history.clear()
	if suspended:
		silence();phase="rest" if game.elapsed==0 else game.phase;mode=game.mode;cursor=game.events.size();return
	# Consume event history even while muted: unmute never replays stale threats/hits.
	if game.phase!=phase and game.phase in ["bolt","pulse"] and game.mode=="play":cue(game.phase,roundi(game.elapsed*60))
	for i in range(cursor,game.events.size()):
		var event: Dictionary=game.events[i]
		var name: String={"protected":"block","redirect":"draw","counter":"counter","pulse_hit":"hurt","bolt_hit":"hurt","courier_hit":"hurt"}.get(event.kind,"")
		if not name.is_empty():cue(name,event.tick)
	if game.mode!=mode and game.mode in ["won","lost"]:
		voices[0].stop();cue(game.mode,roundi(game.elapsed*60))
	phase=game.phase;mode=game.mode;cursor=game.events.size()

func snapshot() -> Dictionary:
	return {"muted":muted,"events":history.duplicate(true),"voice_limit":2}

func _exit_tree() -> void:
	silence()
	for voice in voices:voice.stream=null
	model=null
	cache.clear()
