extends SceneTree
## Executes the actual scene and PhysicsServer. Scripted play is not a human playtest.
var arena
var failures: Array[String] = []
var checks := 0
var captures := ""
var captured := {}

func _initialize() -> void:
	call_deferred("run")

func check(ok: bool, message: String) -> void:
	checks += 1
	if not ok:
		failures.append(message)
		push_error(message)

func wait_frames(n: int) -> void:
	for i in n: await physics_frame

func press(action: String) -> void:
	Input.action_press(action)
	await wait_frames(2)
	Input.action_release(action)
	await wait_frames(2)

func capture(name: String) -> void:
	if captures.is_empty() or DisplayServer.get_name() == "headless" or captured.has(name): return
	captured[name]=true
	await RenderingServer.frame_post_draw
	var image := root.get_texture().get_image()
	check(image.get_width()==1280, "Native framebuffer has the expected width")
	image.save_png(captures.path_join(name+".png"))

func run() -> void:
	captures = OS.get_environment("VEIL_CAPTURE_DIR")
	arena = load("res://arena.tscn").instantiate()
	root.add_child(arena)
	await wait_frames(4)
	await capture("title")
	await press("begin")
	check(arena.mode=="fight", "Enter starts the actual encounter")
	var position: Vector2 = arena.player.position
	Input.action_press("left")
	await wait_frames(90)
	Input.action_release("left")
	check(arena.player.position.x>=93 && arena.player.position.x<position.x, "Physics walls bound native player movement")
	arena.player.position=Vector2(345,350)
	Input.action_press("right")
	await wait_frames(40)
	Input.action_release("right")
	check(arena.player.position.x<353,"The pillar is a real collision obstacle")
	arena.pause_game()
	var frozen := [arena.elapsed,arena.player.position,arena.stamina,arena.boss_hp]
	await wait_frames(20)
	check(frozen==[arena.elapsed,arena.player.position,arena.stamina,arena.boss_hp],"Pause freezes combat, movement and regeneration")
	await capture("paused")
	await press("begin")
	check(arena.mode=="fight","Explicit Enter resumes")
	var click := InputEventMouseButton.new()
	click.position=Vector2(1110,742)
	click.global_position=click.position
	click.button_index=MOUSE_BUTTON_LEFT
	click.pressed=true
	root.push_input(click,true)
	await wait_frames(2)
	click.pressed=false
	root.push_input(click,true)
	await wait_frames(2)
	check(arena.mode=="paused"&&arena.help_panel.visible,"Native GUI mouse input opens tactics and pauses")
	await capture("tactics")
	await press("begin")
	check(arena.mode=="fight"&&!arena.help_panel.visible,"Resume dismisses the tactics panel")
	await press("help")
	check(arena.mode=="paused"&&arena.help_panel.visible,"F1 exposes tactics without a mouse")
	await press("help")
	check(arena.mode=="paused"&&!arena.help_panel.visible,"Closing tactics preserves explicit resume")
	await press("begin")
	arena._notification(Node.NOTIFICATION_WM_WINDOW_FOCUS_OUT)
	check(arena.mode=="paused","Native focus-loss notification pauses")
	arena._begin_or_resume()
	# Boundary fixtures still run the actual attack and projectile code.
	arena.reset_encounter()
	arena.boss.position=Vector2(650,400)
	arena.player.position=Vector2(565,400)
	arena.boss_stage="windup"
	arena.stage_duration=100
	await press("strike")
	check(arena.boss_hp==156,"Armored blade chips exactly 4")
	arena.strike_cooldown=0
	arena.boss_stage="recover"
	await press("strike")
	check(arena.boss_hp==132,"Recovery counter applies exactly 24")
	arena.stamina=0
	arena.strike_cooldown=0
	var health: float=arena.boss_hp
	await press("strike")
	check(arena.boss_hp==health,"Insufficient resolve cannot buy an attack")
	arena.reset_encounter()
	arena.boss.position=Vector2(650,400)
	arena.player.position=Vector2(475,400)
	arena.boss_stage="windup"
	arena.stage_duration=100
	for i in 3:
		await press("seal")
		await wait_frames(67)
	check(arena.stats.breaks==1 && arena.exposed>0,"Three real projectile impacts break the ward")
	check(arena.boss_hp==136,"Seal impacts apply actual damage")
	await capture("ward-broken")
	arena._damage_boss(60)
	check(arena.phase==2&&arena.boss_stage=="transition","Half-health enters the real second phase")
	var transition_hp: float=arena.boss_hp
	arena._damage_boss(24)
	check(arena.boss_hp==transition_hp,"Transition cannot be burst-skipped")
	await wait_frames(72)
	check(arena.boss_stage=="approach"||arena.boss_stage=="windup","Second phase resumes into combat")
	# Actual unmoving play must lose; no result is injected.
	arena.reset_encounter()
	arena.player.position=Vector2(600,450)
	arena.boss.position=Vector2(725,450)
	for i in 10000:
		await physics_frame
		if arena.mode!="fight": break
	check(arena.mode=="defeat"&&arena.hp==0,"An idle player loses through actual boss attacks")
	await capture("defeat")
	await press("begin")
	check(arena.hp==6&&arena.boss_hp==160&&arena.seals.is_empty()&&arena.phase==1,"Restart resets the complete encounter")
	# Integrated strategy: position outside locked warnings, counter recovery,
	# use seals when separated, and respect the second-phase echo.
	var won := false
	for attempt in 2:
		arena.reset_encounter()
		arena.mode="fight"
		arena._sync_ui()
		for frame in 14000:
			if arena.mode!="fight": break
			bot_input(frame)
			if frame%240==0 and arena.boss_stage=="windup": await capture("warning")
			if arena.phase==2&&arena.echo_time>=0&&arena.echo_time<0.3: await capture("phase-two-echo")
			await physics_frame
		clear_inputs()
		print("SCRIPTED_RUN ",JSON.stringify({"mode":arena.mode,"time":arena.elapsed,"boss_hp":arena.boss_hp,"hp":arena.hp,"stats":arena.stats}))
		if arena.mode=="victory":
			won=true
			break
	check(won,"Scripted legal input completes the whole fight")
	check(arena.stats.phase_changes==1,"Complete fight encounters one second phase")
	await capture("result")
	print("ENCOUNTER_CHECKS ",JSON.stringify({"checks":checks,"failures":failures}))
	quit(0 if failures.is_empty() else 1)

func clear_inputs() -> void:
	for action in ["left","right","up","down","strike","seal","dash"]: Input.action_release(action)

func bot_input(frame: int) -> void:
	clear_inputs()
	var p: Vector2=arena.player.position
	var b: Vector2=arena.boss.position
	var away: Vector2=b.direction_to(p)
	var goal: Vector2=b+away*78
	var distance:=p.distance_to(b)
	if arena.boss_stage=="windup"||arena.boss_stage=="active":
		if arena.pattern=="sweep": goal=b-arena.aim*105
		elif arena.pattern=="charge":
			var side: Vector2=arena.aim.orthogonal()
			goal=b+side*205
			if not Rect2(120,215,1040,410).has_point(goal): goal=b-side*205
		else:
			goal=b+away*280
			if arena.boss_stage=="active"&&absf(distance-(30+190*arena.stage_time/arena.stage_duration))<65&&arena.dash_cooldown<=0:
				goal=b
				Input.action_press("dash")
	if arena.echo_time>=0:
		goal=arena.echo_origin+arena.echo_origin.direction_to(p)*180
	var movement: Vector2=p.direction_to(goal)
	if movement.x< -0.18: Input.action_press("left")
	if movement.x>0.18: Input.action_press("right")
	if movement.y< -0.18: Input.action_press("up")
	if movement.y>0.18: Input.action_press("down")
	if arena._boss_open()&&distance<102&&arena.strike_cooldown<=0: Input.action_press("strike")
	if distance>110&&distance<330&&arena.seal_cooldown<=0&&arena.stamina>=60: Input.action_press("seal")
