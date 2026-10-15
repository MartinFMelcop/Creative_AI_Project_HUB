extends Node
## Two aligned transports, semantic one-shots and explicit mute/pause lifecycle.
const QUIET = preload("res://media/audio/courtyard.ogg")
const FRACTURE = preload("res://media/audio/fracture.ogg")
const CUE_NAMES = ["sweep","charge","wave","strike","seal","guard","counter","break","hurt","dodge","phase","echo","victory","defeat"]
var tracks: Array[AudioStreamPlayer] = []
var voices: Array[AudioStreamPlayer2D] = []
var cues := {}
var voice_cursor := 0
var mix := 0.0
var target_mix := 0.0
var muted := false
var suspended := false
var events: Array[String] = []
var limiter: AudioEffectHardLimiter

func _ready() -> void:
	limiter = AudioEffectHardLimiter.new()
	limiter.ceiling_db = -1.5
	limiter.release = 0.05
	AudioServer.add_bus_effect(0,limiter)
	for resource in [QUIET, FRACTURE]:
		var track := AudioStreamPlayer.new()
		var stream: AudioStreamOggVorbis = resource.duplicate()
		stream.loop = true
		track.stream = stream
		add_child(track)
		tracks.append(track)
	for name in CUE_NAMES: cues[name] = load("res://media/audio/%s.wav" % name)
	for i in 8:
		var voice := AudioStreamPlayer2D.new()
		voice.volume_db = -8
		voice.max_distance = 1800
		voice.attenuation = 0.25
		voice.panning_strength = 0.6
		add_child(voice)
		voices.append(voice)
	_apply_levels()
	# Start both on the same AudioServer block; do not restart at the phase change.
	AudioServer.lock()
	for track in tracks: track.play()
	AudioServer.unlock()

func _process(delta: float) -> void:
	if suspended: return
	mix = move_toward(mix, target_mix, delta / 1.1)
	_apply_levels()

func _apply_levels() -> void:
	if tracks.is_empty(): return
	# Equal-power crossfade; the quiet bed stays audible at either endpoint.
	tracks[0].volume_db = -80 if muted else linear_to_db(maxf(0.0001,cos(mix*PI/2)*0.32))
	tracks[1].volume_db = -80 if muted else linear_to_db(maxf(0.0001,sin(mix*PI/2)*0.32))
	for voice in voices: voice.volume_db = -80 if muted else -8

func cue(name: String, at: Vector2 = Vector2(640,400)) -> void:
	if suspended or not cues.has(name): return
	# Bounded audit window supports execution checks without an ever-growing log.
	events.append(name)
	if events.size() > 64: events.pop_front()
	if muted: return
	var voice := voices[voice_cursor]
	voice_cursor = (voice_cursor+1)%voices.size()
	voice.position = at
	voice.stream = cues[name]
	voice.play()

func set_phase(second: bool) -> void:
	target_mix = 1.0 if second else 0.0

func set_suspended(value: bool) -> void:
	suspended = value
	for track in tracks: track.stream_paused = value
	for voice in voices: voice.stream_paused = value

func toggle_mute() -> void:
	muted = not muted
	_apply_levels()

func reset() -> void:
	set_suspended(false)
	mix = 0
	target_mix = 0
	events.clear()
	for voice in voices: voice.stop()
	# Reset both stems in one mixer instant, even during repeated practice takes.
	AudioServer.lock()
	for track in tracks:
		track.stop()
		track.play()
	AudioServer.unlock()
	_apply_levels()

func stop() -> void:
	for track in tracks:
		track.stop()
	for voice in voices:
		voice.stop()

func _exit_tree() -> void:
	stop()
	for index in range(AudioServer.get_bus_effect_count(0)-1,-1,-1):
		if AudioServer.get_bus_effect(0,index)==limiter: AudioServer.remove_bus_effect(0,index)
