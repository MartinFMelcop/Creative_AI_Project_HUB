extends SceneTree
## Driver-locked observations across real mixer time; no physical listening claim.
var arena
var failures: Array[String] = []
var checks := 0

func _initialize() -> void: call_deferred("run")

func check(ok: bool, message: String) -> void:
	checks += 1
	if not ok:
		failures.append(message)
		push_error(message)

func skew() -> float:
	AudioServer.lock()
	var first: float = arena.sound.tracks[0].get_playback_position()
	var second: float = arena.sound.tracks[1].get_playback_position()
	AudioServer.unlock()
	return absf(first-second)

func run() -> void:
	arena = load("res://arena.tscn").instantiate()
	root.add_child(arena)
	arena.set_physics_process(false)
	await create_timer(.15).timeout
	var worst := 0.0
	var samples: Array[float] = []
	for i in 64:
		arena.sound.reset()
		await create_timer(.045).timeout
		var value := skew()
		samples.append(value)
		worst = maxf(worst,value)
	check(worst<.015,"Repeated take resets keep both real transports aligned within 15ms")
	arena.sound.tracks[1].seek(arena.sound.tracks[0].get_playback_position()+.1)
	await create_timer(.15).timeout
	check(skew()>.05,"Atomic reset audit still detects an actual shifted music stem")
	arena.sound.reset()
	await create_timer(.15).timeout
	check(skew()<.015,"The same reset recovers from the real seek fixture")
	print("AUDIO_RESET_CHECKS ",JSON.stringify({"checks":checks,"failures":failures,"resets":64,"worst_skew":worst,"samples":samples}))
	arena.sound.stop()
	OS.delay_msec(150)
	quit(0 if failures.is_empty() else 1)
