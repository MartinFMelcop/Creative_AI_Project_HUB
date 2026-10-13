extends SceneTree
## Actual engine resources, audio mixer output and native GUI lifecycle.
var arena
var failures: Array[String] = []
var checks := 0
var capture: AudioEffectCapture
var peak := 0.0
var captured_frames := 0

func _initialize() -> void:
	call_deferred("run")

func check(ok: bool, message: String) -> void:
	checks += 1
	if not ok:
		failures.append(message)
		push_error(message)

func wait_audio(seconds: float = 0.25) -> PackedVector2Array:
	capture.clear_buffer()
	await create_timer(seconds).timeout
	var samples := capture.get_buffer(capture.get_frames_available())
	captured_frames += samples.size()
	for sample in samples: peak = maxf(peak,maxf(absf(sample.x),absf(sample.y)))
	return samples

func energy(samples: PackedVector2Array) -> float:
	var result := 0.0
	for sample in samples: result += sample.length_squared()
	return sqrt(result/maxi(1,samples.size()))

func stem_skew() -> float:
	# These getters expose live playback positions. Compare one mixer instant;
	# an audio block between two independent reads is not actual stem drift.
	AudioServer.lock()
	var first: float = arena.sound.tracks[0].get_playback_position()
	var second: float = arena.sound.tracks[1].get_playback_position()
	AudioServer.unlock()
	return absf(first-second)

func screenshot(name: String) -> void:
	var folder := OS.get_environment("VEIL_CAPTURE_DIR")
	if folder.is_empty() or DisplayServer.get_name()=="headless": return
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(folder.path_join(name+".png"))

func run() -> void:
	capture = AudioEffectCapture.new()
	capture.buffer_length = 2
	arena = load("res://arena.tscn").instantiate()
	root.add_child(arena)
	AudioServer.add_bus_effect(0,capture) # Measure after the runtime limiter.
	await process_frame
	await screenshot("title-art")
	check(arena.COURTYARD.get_width()>1000 && arena.WARDEN.get_width()>1000 && arena.RUNNER.get_width()>1000,"Delivered illustrated resources load in the actual scene")
	check(arena.sound.cues.size()==14 && arena.sound.tracks.size()==2,"All fourteen semantic cues and two music streams load")
	check(arena.sound.tracks[0].stream.loop && arena.sound.tracks[1].stream.loop,"Both actual OGG resources loop")
	check(absf(arena.sound.tracks[0].stream.get_length()-24)<.01 && absf(arena.sound.tracks[1].stream.get_length()-24)<.01,"Music transports have the same 24-second length")
	await wait_audio(.3) # Prime the real backend rather than assuming zero latency.
	var music := await wait_audio()
	check(music.size()>100 && energy(music)>.001,"The AudioServer produces actual non-silent music samples")
	check(stem_skew()<.015,"Both stems advance on the same audio transport")
	# A declared real seek must still expose misalignment; never relax the limit.
	arena.sound.tracks[1].seek(arena.sound.tracks[0].get_playback_position()+.1)
	await wait_audio(.2)
	check(stem_skew()>.05,"Atomic sampling still detects a real shifted stream")
	arena.sound.reset()
	await wait_audio(.25)
	check(stem_skew()<.015,"Reset restores actual alignment after the seek fixture")
	# Native input toggles sound without altering the current encounter.
	Input.action_press("mute")
	await physics_frame
	await physics_frame
	Input.action_release("mute")
	await physics_frame
	check(arena.sound.muted && arena.audio_button.text=="Sound off [M]","M changes the native mute control")
	await wait_audio(.3) # Drain output that predates the volume change.
	var muted := await wait_audio()
	check(energy(muted)<.0002,"Muted music output is actually silent within the declared floor")
	var click := InputEventMouseButton.new()
	click.position=arena.audio_button.get_global_rect().get_center()
	click.global_position=click.position
	click.button_index=MOUSE_BUTTON_LEFT
	click.pressed=true
	root.push_input(click,true)
	await process_frame
	click.pressed=false
	root.push_input(click,true)
	await physics_frame
	check(!arena.sound.muted,"Actual Viewport mouse input restores sound")
	arena._begin_or_resume()
	arena.boss_stage="windup"
	arena.stage_duration=100
	# Legal input, not a fabricated media event, triggers each player sound.
	Input.action_press("strike")
	await physics_frame
	await physics_frame
	Input.action_release("strike")
	await wait_audio(.12)
	check(arena.sound.events.has("strike"),"A legal blade input emits its real attack cue")
	await wait_audio(.24)
	Input.action_press("seal")
	await physics_frame
	await physics_frame
	Input.action_release("seal")
	await wait_audio(.10)
	check(arena.sound.events.has("seal"),"A legal seal input emits its real projectile cue")
	Input.action_press("dash")
	await physics_frame
	await physics_frame
	Input.action_release("dash")
	check(arena.sound.events.has("dodge"),"A legal dodge input emits its real movement cue")
	var sound := await wait_audio(.25)
	check(energy(sound)>.001,"Music and native cue players produce actual mixed samples")
	arena.sound.stop()
	await wait_audio(.3)
	arena.sound.cue("wave")
	check(energy(await wait_audio(.45))>.001,"A cue produces non-silent samples with both music streams stopped")
	arena.sound.reset()
	arena.pause_game()
	var paused_position: float = arena.sound.tracks[0].get_playback_position()
	await wait_audio(.16) # Allow the mix thread to flush the previous block.
	var silence := await wait_audio(.16)
	check(arena.sound.suspended && absf(arena.sound.tracks[0].get_playback_position()-paused_position)<.04,"Pause freezes the actual music transport")
	check(energy(silence)<.0002,"Pause silences actual music and cue output")
	arena._begin_or_resume()
	check(energy(await wait_audio())>.001,"Explicit resume restores actual audio output")
	arena._damage_boss(90)
	await wait_audio(1.25)
	check(arena.phase==2 && arena.sound.events.has("phase") && arena.sound.target_mix==1 && arena.sound.mix>.98,"A real phase transition completes the adaptive crossfade")
	await screenshot("fracture-art")
	check(stem_skew()<.015,"Phase transition preserves stem alignment")
	# Deliberate gain stress fixture exercises the limiter, not just quiet files.
	arena.sound.limiter.pre_gain_db = 12
	for i in 8: arena.sound.cue("wave")
	await wait_audio(.6)
	arena.sound.limiter.pre_gain_db = 0
	# Check attack warnings at their real state entry, using boundary fixtures.
	for i in 3:
		arena._start_pattern()
		check(arena.sound.events.back()==arena.pattern,"Pattern entry emits the matching distinct warning")
		await screenshot(arena.pattern+"-art")
	arena.boss_stage="recover"
	arena.exposed=2.4
	await screenshot("open-core-art")
	arena.pause_game()
	# Actual physics bounds; visual review must include the previously cropped wall.
	for name in ["top-edge","bottom-edge"]:
		arena.boss.position=Vector2(1140,203 if name=="top-edge" else 637)
		arena.player.position=Vector2(150,189 if name=="top-edge" else 651)
		await screenshot(name)
	# Signal-only audit ends here; audibility does not establish listening quality.
	check(peak>0.001 && peak<=db_to_linear(-1.5)+.001,"Executed music and eight-voice overlap respect the limiter ceiling")
	arena.sound.toggle_mute()
	arena.reset_encounter()
	check(arena.sound.muted && arena.sound.mix==0 && arena.sound.target_mix==0,"Restart resets music/cues while preserving the chosen mute setting")
	arena.sound.stop()
	OS.delay_msec(150)
	print("PRESENTATION_CHECKS ",JSON.stringify({"checks":checks,"failures":failures,"audio_frames":captured_frames,"measured_peak":peak,"display":DisplayServer.get_name()}))
	quit(0 if failures.is_empty() else 1)
