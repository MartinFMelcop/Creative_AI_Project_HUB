extends SceneTree
## Controlled main-thread delay diagnoses stale seek targets; no physical audio claim.
var arena
func _initialize(): call_deferred("run")
func observe() -> Array:
	AudioServer.lock()
	var a: float=arena.sound.tracks[0].get_playback_position()
	var b: float=arena.sound.tracks[1].get_playback_position()
	AudioServer.unlock()
	return [a,b,absf(a-b)]
func run():
	arena=load("res://arena.tscn").instantiate()
	root.add_child(arena)
	arena.set_physics_process(false)
	await create_timer(.3).timeout
	var start=observe()
	var before_delay=Time.get_ticks_usec()
	var target: float=arena.sound.tracks[0].get_playback_position()+.1
	OS.delay_msec(100)
	var unlocked_gap_ms=(Time.get_ticks_usec()-before_delay)/1000.0
	arena.sound.tracks[1].seek(target)
	await create_timer(.2).timeout
	# The unlocked result is diagnostic: scheduler oversleep may change its magnitude.
	# It must not become an exact wall-clock timing gate.
	var unlocked=observe()
	arena.sound.reset()
	await create_timer(.25).timeout
	AudioServer.lock()
	target=arena.sound.tracks[0].get_playback_position()+.1
	OS.delay_msec(100)
	arena.sound.tracks[1].seek(target)
	AudioServer.unlock()
	await create_timer(.2).timeout
	var locked=observe()
	arena.sound.reset()
	await create_timer(.2).timeout
	var restored=observe()
	var failures: Array[String]=[]
	if start[2]>=.015: failures.append("Initial transports were not aligned within15ms")
	if locked[2]<=.05: failures.append("Atomic injection did not preserve an actual shift above50ms")
	if restored[2]>=.015: failures.append("Reset did not restore alignment within15ms")
	print("AUDIO_SEEK_INJECTION_CHECKS ",JSON.stringify({"checks":3,"failures":failures,"restored":restored,"requested_gap_ms":100,"unlocked_gap_ms":unlocked_gap_ms,"baseline":start,"unlocked":unlocked,"locked":locked,"threshold":.05,"unlocked_detected":unlocked[2]>.05,"locked_detected":locked[2]>.05}))
	arena.sound.stop()
	OS.delay_msec(150)
	quit(0 if failures.is_empty() else 1)
