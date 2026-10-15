extends SceneTree
## Real shared combat code with scripted inputs; this is not human learning evidence.
var arena
var failures: Array[String] = []
var checks := 0

func _initialize() -> void: call_deferred("run")

func check(ok: bool, message: String) -> void:
	checks += 1
	if not ok:
		failures.append(message)
		push_error(message)

func capture(name: String) -> void:
	var folder := OS.get_environment("VEIL_CAPTURE_DIR")
	if folder.is_empty() or DisplayServer.get_name()=="headless": return
	arena.queue_redraw()
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(folder.path_join(name+".png"))

func take(guard_at: float = -1, counter: bool = false) -> void:
	var pressed := false
	for i in 400:
		if arena.mode != "fight": return
		var guard: bool = not pressed and guard_at >= 0 and arena.elapsed >= guard_at
		if guard: pressed = true
		var strike: bool = counter and arena.practice_parried and not arena.practice_counter and arena.player_action.is_empty()
		arena.step_fight(1.0/60,Vector2.ZERO,strike,false,false,guard)
	check(false,"A practice take must finish rather than run indefinitely")

func key(code: Key, down: bool) -> void:
	var event := InputEventKey.new()
	event.physical_keycode = code
	event.pressed = down
	Input.parse_input_event(event)
	Input.flush_buffered_events()

func pad(down: bool) -> void:
	var event := InputEventJoypadButton.new()
	event.device = 0
	event.button_index = JOY_BUTTON_RIGHT_STICK
	event.pressed = down
	Input.parse_input_event(event)
	Input.flush_buffered_events()

func run() -> void:
	arena = load("res://arena.tscn").instantiate()
	root.add_child(arena)
	await physics_frame
	await physics_frame
	arena.set_physics_process(false)
	check(arena.mode=="title" and not arena.practice_active,"Startup remains the ordinary trial title")
	check(arena.practice_button.visible and arena.practice_button.text.contains("Sweep practice"),"Native title offers a distinct practice choice")
	arena.practice_button.pressed.emit()
	check(arena.mode=="fight" and arena.practice_active and arena.practice_round==1,"Mouse practice choice starts a separate first take")
	check(arena.pattern=="sweep" and arena.boss_stage=="windup" and arena.stage_duration==0.85,"Practice uses the actual phase-one 850ms sweep windup")
	check(arena.player.position.distance_to(arena.boss.position)==85 and arena.hp==6 and arena.stamina==100,"Take starts inside real guard/blade range with full resources")
	check(not arena.practice_button.visible,"Mouse leave button does not cover active combat")
	await capture("practice-windup")
	take()
	check(arena.mode=="practice_review" and arena.hp==5 and arena.stats.damage_taken==1,"An unguarded sweep genuinely damages the player and stops for review")
	check(arena.practice_result.contains("No guard") and arena.practice_completed==1 and arena.practice_clean_counters==0,"No-guard feedback and take counts reflect actual collisions")
	check(arena.practice_button.visible and arena.start_button.text.contains("Next sweep"),"Review offers deliberate retry and exit")
	var frozen: float = arena.elapsed
	arena.step_fight(10,Vector2.RIGHT,true,true,true,true)
	check(arena.elapsed==frozen and arena.mode=="practice_review","Review cannot auto-loop or spend combat input")
	await capture("practice-missed")
	arena._begin_or_resume()
	check(arena.practice_round==2 and arena.practice_completed==1 and arena.hp==6 and arena.stats.damage_taken==0,"Retry clears combat state while retaining session take count")
	take(0.05)
	check(arena.practice_result.contains("too early") and arena.stats.parry_attempts==1 and arena.stats.parries==0,"Early committed guard costs its attempt and reports pressing too soon")
	arena._begin_or_resume()
	take(0.85)
	check(arena.practice_result.contains("too late") and arena.hp==5,"Late guard remains vulnerable and reports pressing earlier")
	arena._begin_or_resume()
	arena.player.position = Vector2(525,400)
	take(0.75)
	check(arena.practice_result.contains("Too far") and arena.hp==5,"Live guard outside 110px cannot falsely succeed")
	arena._begin_or_resume()
	take(0.75)
	check(arena.practice_parried and not arena.practice_counter and arena.stats.parries==1 and arena.hp==6,"A real timed guard cancels the sweep without automatic damage")
	check(arena.practice_result.contains("no blade counter") and arena.boss_hp==arena.BOSS_MAX,"Guard-only review asks for the missing counter")
	arena._begin_or_resume()
	take(0.75,true)
	check(arena.practice_parried and arena.practice_counter and arena.hp==6,"Normal blade contact completes the parry/counter take")
	check(arena.boss_hp==arena.BOSS_MAX-24 and arena.stats.strikes==1,"Counter applies the actual 24 open-core damage")
	check(arena.practice_clean_counters==1 and arena.practice_completed==6,"Only the actual clean parry/counter is counted")
	check(arena.mode!="victory" and arena.phase==1 and arena.stats.phase_changes==0,"Practice never claims trial completion or advances phases")
	await capture("practice-clean")
	arena._begin_or_resume()
	check(arena.parry_cooldown==0 and arena.player_action.is_empty() and arena.seals.is_empty() and arena.echo_time<0,"Retry removes old cooldowns, commitments, seals and echoes")
	arena.step_fight(0.3,Vector2.ZERO,false,false,false)
	arena.pause_game()
	var paused_time: float = arena.elapsed
	arena.step_fight(1,Vector2.ZERO,false,false,false,true)
	check(arena.mode=="paused" and arena.elapsed==paused_time,"Pause freezes the drill and its guard clock")
	arena.toggle_tactics()
	check(arena.help_panel.visible,"Tactics remain available during practice pause")
	arena._begin_or_resume()
	check(arena.practice_active and arena.elapsed==paused_time and arena.practice_round==7,"Resume does not restart the take")
	arena.player.position = Vector2(100,200)
	take()
	check(arena.practice_result.contains("Sweep avoided") and arena.stats.parries==0,"Avoiding contact is distinguished from a successful parry")
	arena.toggle_practice()
	check(arena.mode=="title" and not arena.practice_active and arena.practice_completed==0,"Leaving practice returns to a clean ordinary title")
	arena._begin_or_resume()
	check(not arena.practice_active and arena.mode=="fight" and arena.stats.parries==0,"Full trial starts without practice progress or rewards")
	arena.toggle_practice()
	check(not arena.practice_active and arena.mode=="fight","Practice cannot replace an active trial through its title-only entry")

	arena.pause_game()
	arena.toggle_practice()
	check(arena.mode=="paused" and not arena.practice_active and not arena.practice_button.visible,"Paused trial cannot be discarded by the practice shortcut or menu")

	# Exercise native input events rather than invoking the mode methods alone.
	arena.reset_encounter()
	arena.mode = "title"
	arena.set_physics_process(true)
	key(KEY_P,true)
	await physics_frame
	await physics_frame
	key(KEY_P,false)
	check(arena.practice_active,"Keyboard P starts the native drill")
	key(KEY_P,true)
	await physics_frame
	await physics_frame
	key(KEY_P,false)
	check(arena.mode=="title" and not arena.practice_active,"Keyboard P exits an active drill explicitly")
	pad(true)
	await physics_frame
	await physics_frame
	pad(false)
	check(arena.practice_active and arena.controls.using_gamepad,"Mapped R3 starts practice and switches native prompts")
	arena._controller_connection(0,false)
	check(arena.mode=="paused" and arena.practice_active,"Active-controller loss pauses the drill")
	arena.set_physics_process(false)
	print("PRACTICE_CHECKS ",JSON.stringify({"checks":checks,"failures":failures,"scope":"native shared combat and synthetic input; not human learning"}))
	arena.sound.stop()
	OS.delay_msec(150) # Let the audio thread release queued playback resources.
	arena.queue_free()
	await process_frame
	await process_frame
	quit(0 if failures.is_empty() else 1)
