extends SceneTree
## Native collision/input checks and a scripted policy, not a human playtest.
var arena
var failures: Array[String] = []
var checks := 0

func _initialize() -> void: call_deferred("run")

func check(ok: bool, message: String) -> void:
	checks += 1
	if not ok:
		failures.append(message)
		push_error(message)

func setup(distance: float = 85) -> void:
	arena.reset_encounter()
	arena.mode = "fight"
	arena.player.position = Vector2(650-distance,400)
	arena.boss.position = Vector2(650,400)
	arena.boss_stage = "windup"
	arena.pattern = "sweep"
	arena.aim = Vector2.LEFT
	arena.attack_origin = arena.boss.position
	arena.stage_duration = 100
	arena.attack_hit = false
	arena._sync_ui()

func guard() -> void:
	arena.step_fight(.001,Vector2.ZERO,false,false,false,true)

func sweep(time: float) -> void:
	arena.action_time = time
	arena.boss_stage = "active"
	arena.stage_time = 0
	arena.stage_duration = .18
	arena.step_fight(.001,Vector2.ZERO,false,false,false)

func capture(name: String) -> void:
	var folder := OS.get_environment("VEIL_CAPTURE_DIR")
	if folder.is_empty() or DisplayServer.get_name()=="headless": return
	arena.queue_redraw()
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(folder.path_join(name+".png"))

func frames(n: int) -> void:
	for i in n: await physics_frame

func key(code: Key,down: bool) -> void:
	var event := InputEventKey.new()
	event.physical_keycode = code
	event.pressed = down
	Input.parse_input_event(event)
	Input.flush_buffered_events()

func pad(down: bool) -> void:
	var event := InputEventJoypadButton.new()
	event.device = 0
	event.button_index = JOY_BUTTON_LEFT_SHOULDER
	event.pressed = down
	Input.parse_input_event(event)
	Input.flush_buffered_events()

func run() -> void:
	arena = load("res://arena.tscn").instantiate()
	root.add_child(arena)
	await frames(4)
	arena.set_physics_process(false)
	setup()
	guard()
	check(arena.stats.parry_attempts==1 and arena.stamina==80 and arena.parry_cooldown==.9,"Guard pays 20 resolve and commits its cooldown")
	check(arena.player_action=="parry" and not arena._parry_live() and arena.invulnerable==0,"Guard starts vulnerable without instant blocking")
	arena.step_fight(.059,Vector2.ZERO,false,false,false)
	check(not arena._parry_live(),"The first 59ms are startup, not a live guard")
	arena.step_fight(.001,Vector2.ZERO,false,false,false)
	check(arena._parry_live() and arena.Motion.runner_frame(arena)==4,"Guard opens at 60ms with the held blade pose")
	await capture("parry-ready")
	sweep(.06)
	check(arena.hp==6 and arena.stats.parries==1 and arena.boss_hp==160,"Actual close sweep collision is turned aside without free boss damage")
	check(arena.boss_stage=="recover" and arena.stage_duration==1.2 and arena.invulnerable==0,"Parry creates a 1.2s opening without invulnerability")
	check(arena.stamina>89 and arena.stamina<90 and arena.sound.events.has("counter"),"Success recovers exactly eight resolve beside normal regeneration and uses the existing counter cue")
	check(arena.player_action.is_empty() and arena.attack_hit,"Successful guard releases control and consumes this sweep once")
	await capture("parry-counter")
	arena.step_fight(.01,Vector2.ZERO,true,false,false)
	arena.step_fight(.101,Vector2.ZERO,false,false,false)
	check(arena.boss_hp==136 and arena.stats.parries==1,"Player must land a real blade counter for the 24 damage reward")
	for time in [.058,.178,.18]:
		setup();guard();sweep(time)
		check(arena.hp==(6 if time==.178 else 5),"Real sweep tests guard clock boundary "+str(time+.001))
	setup(110);guard();sweep(.09)
	check(arena.stats.parries==1,"110px is inside the close parry range")
	setup(111);guard();sweep(.09)
	check(arena.hp==5 and arena.stats.parries==0,"A sweep at 111px still hits; its outer reach is not parry range")
	setup();guard()
	arena.boss.position=Vector2(480,400);arena.aim=Vector2.RIGHT
	sweep(.09)
	check(arena.hp==5 and arena.stats.parries==0,"A locked guard cannot block a sweep behind its facing")
	setup();guard();arena.invulnerable=.3;sweep(.09)
	check(arena.stats.parries==0 and arena.hp==6,"Existing hurt protection cannot farm parry rewards")
	# These hazards use their actual collision paths; none calls the sweep parry.
	setup(45);guard();arena.action_time=.08
	arena.pattern="charge";arena.boss_stage="active";arena.stage_duration=.46
	arena.step_fight(.01,Vector2.ZERO,false,false,false)
	check(arena.hp==5 and arena.stats.parries==0,"A close charge hits through a live guard")
	setup(110);guard();arena.action_time=.08
	arena.pattern="wave";arena.boss_stage="active";arena.stage_time=.27;arena.stage_duration=.65
	arena.step_fight(.001,Vector2.ZERO,false,false,false)
	check(arena.hp==5 and arena.stats.parries==0,"Expanding wave collision hits through a live guard")
	setup();guard();arena.action_time=.08
	arena.echo_time=.649;arena.echo_origin=arena.player.position
	arena.step_fight(.002,Vector2.ZERO,false,false,false)
	check(arena.hp==5 and arena.stats.parries==0,"Violet echo hits through a live guard")
	setup();guard();arena.echo_time=.649;arena.echo_origin=arena.player.position
	sweep(.09)
	check(arena.stats.parries==1 and arena.hp==5,"Parrying a sweep does not protect against a simultaneous echo")
	setup();guard();arena.step_fight(.181,Vector2.ZERO,false,false,false)
	check(not arena._parry_live() and arena.player_action=="parry" and arena.Motion.runner_frame(arena)==7,"A missed guard visibly recovers and remains committed")
	arena.step_fight(.02,Vector2.ZERO,true,true,false,true)
	check(arena.stats.parry_attempts==1 and arena.stats.strikes==0 and arena.stats.seals==0,"Recovery and cooldown prevent queued attack or guard replacement")
	arena.step_fight(.18,Vector2.ZERO,false,false,false)
	check(arena.player_action.is_empty() and arena.stats.parries==0,"Missed guard ends without a reward or phantom cast")
	setup();arena.stamina=0;guard()
	check(arena.stats.parry_attempts==0 and arena.parry_cooldown==0,"Insufficient resolve cannot buy a guard")
	setup();arena.step_fight(.001,Vector2.ZERO,true,true,false,true)
	check(arena.stats.parry_attempts==1 and arena.stats.strikes==0 and arena.stats.seals==0,"Simultaneous legal inputs select the defensive commitment")
	setup();guard();arena.step_fight(.01,Vector2.LEFT,false,false,true)
	check(arena.player_action.is_empty() and arena.stats.dodges==1 and arena.stamina<56,"Dodge cancels guard without refunding either cost")
	setup();guard();arena.action_time=.08;arena.pause_game()
	var frozen := [arena.action_time,arena.parry_cooldown,arena.boss_stage,arena.stamina]
	arena.step_fight(.5,Vector2.RIGHT,true,true,true,true)
	check(frozen==[arena.action_time,arena.parry_cooldown,arena.boss_stage,arena.stamina],"Pause freezes guard clock, resource and cooldown")
	arena._begin_or_resume();sweep(.09)
	check(arena.stats.parries==1,"Explicit resume continues a committed guard")
	arena.reset_encounter()
	check(arena.parry_cooldown==0 and arena.player_action.is_empty() and arena.stats.parries==0 and arena.stats.parry_attempts==0,"Restart clears guard commitments, rewards and results")
	# Real keyboard and mapped shoulder events still require a fresh press.
	setup();arena.set_physics_process(true);key(KEY_L,true);await frames(3)
	check(arena.stats.parry_attempts==1,"Physical L mapping reaches the actual native combat loop")
	await frames(65)
	check(arena.stats.parry_attempts==1,"Held L does not repeat after recovery/cooldown")
	key(KEY_L,false);await frames(2);pad(true);await frames(3)
	check(arena.stats.parry_attempts==2 and arena.controls.using_gamepad,"Mapped LB starts a new guard and changes native prompts")
	await frames(65)
	check(arena.stats.parry_attempts==2,"Held LB does not repeat after recovery/cooldown")
	pad(false);await frames(2)
	arena.set_physics_process(false);setup();guard();arena.action_time=.1;arena.queue_redraw()
	await capture("parry-gamepad")
	arena.toggle_tactics();await capture("parry-tactics")
	check(arena.help_panel.get_rect().end.y<690,"Guard rules and tactics remain inside the native viewport")
	# One full legal-input policy chooses close parries, dodges other hazards and
	# lands its counters through normal aim/contact. Nothing injects a win or HP.
	arena.mode="title";arena._begin_or_resume();arena.set_physics_process(true)
	var parry_phases: Array[int] = []
	for i in 16000:
		if arena.mode!="fight": break
		policy()
		await physics_frame
		if arena.stats.parries>parry_phases.size(): parry_phases.append(arena.phase)
	clear_inputs()
	check(arena.mode=="victory" and arena.stats.phase_changes==1 and parry_phases==[1,2],"Timed-guard policy completes the encounter with a parry in each phase")
	check(arena.stats.parries>=2 and arena.stats.hits>0,"Complete policy earns multiple parries and lands actual damage")
	await capture("parry-victory")
	print("PARRY_RUN ",JSON.stringify({"mode":arena.mode,"time":arena.elapsed,"hp":arena.hp,"stats":arena.stats,"parry_phases":parry_phases,"input":"scripted native actions; no physical controller"}))
	print("PARRY_CHECKS ",JSON.stringify({"checks":checks,"failures":failures}))
	arena.sound.stop();OS.delay_msec(150)
	quit(0 if failures.is_empty() else 1)

func clear_inputs() -> void:
	for action in ["left","right","up","down","strike","seal","dash","parry"]: Input.action_release(action)

func policy() -> void:
	# Hold a requested action until the native loop consumes it; toggling every
	# physics signal can continually renew just-pressed timestamps before dispatch.
	var requested: Array[String] = []
	var p: Vector2=arena.player.position
	var b: Vector2=arena.boss.position
	var away: Vector2=b.direction_to(p)
	var distance := p.distance_to(b)
	var goal: Vector2=b+away*78
	if arena.boss_stage in ["windup","active"]:
		if arena.pattern=="sweep":
			goal=b+arena.aim*78
			if arena.boss_stage=="windup" and arena.stage_duration-arena.stage_time<=.14 and distance<=100 and arena.parry_cooldown<=0:
				requested.append("parry")
		elif arena.pattern=="charge":
			var side: Vector2=arena.aim.orthogonal()
			goal=b+side*205
			if not Rect2(120,215,1040,410).has_point(goal): goal=b-side*205
		else:
			goal=b+away*280
			if arena.boss_stage=="active" and absf(distance-(30+190*arena.stage_time/arena.stage_duration))<65 and arena.dash_cooldown<=0:
				goal=b;requested.append("dash")
	if arena.echo_time>=0: goal=arena.echo_origin+arena.echo_origin.direction_to(p)*180
	var movement: Vector2=p.direction_to(goal) if p.distance_to(goal)>8 else Vector2.ZERO
	if movement.x<-.18: requested.append("left")
	if movement.x>.18: requested.append("right")
	if movement.y<-.18: requested.append("up")
	if movement.y>.18: requested.append("down")
	# Deliberately wait for each phase's close sweep before dealing blade damage.
	# This demonstrates the guard in both tempos rather than a speedrun.
	if arena._boss_open() and distance<102 and arena.strike_cooldown<=0 and arena.stats.parries>=arena.phase: requested.append("strike")
	# Commit to the close counter route before adding ranged pressure. The opening
	# sweep can begin out of reach while the Warden is still crossing the courtyard.
	if arena.stats.parries>=2 and arena.pattern!="sweep" and distance>110 and distance<330 and arena.seal_cooldown<=0 and arena.stamina>=60: requested.append("seal")
	for action in ["left","right","up","down","strike","seal","dash","parry"]:
		if not requested.has(action): Input.action_release(action)
		elif not Input.is_action_pressed(action): Input.action_press(action)
