extends SceneTree
## Real native joypad events and declared connection notifications; no physical pad is present.
var arena
var failures: Array[String] = []
var checks := 0
var buttons := [JOY_BUTTON_DPAD_LEFT,JOY_BUTTON_DPAD_RIGHT,JOY_BUTTON_DPAD_UP,JOY_BUTTON_DPAD_DOWN,JOY_BUTTON_X,JOY_BUTTON_Y,JOY_BUTTON_B]

func _initialize() -> void: call_deferred("run")

func check(ok: bool,message: String) -> void:
	checks += 1
	if not ok:
		failures.append(message)
		push_error(message)

func frames(n: int) -> void:
	for i in n: await physics_frame

func button(index: int, down: bool) -> void:
	var event := InputEventJoypadButton.new()
	event.device = 0
	event.button_index = index
	event.pressed = down
	Input.parse_input_event(event)
	Input.flush_buffered_events()

func axis(index: int,value: float) -> void:
	var event := InputEventJoypadMotion.new()
	event.device = 0
	event.axis = index
	event.axis_value = value
	Input.parse_input_event(event)
	Input.flush_buffered_events()

func tap(index: int) -> void:
	button(index,true)
	await frames(2)
	button(index,false)
	await frames(2)

func capture(name: String) -> void:
	var folder := OS.get_environment("VEIL_CAPTURE_DIR")
	if folder.is_empty() or DisplayServer.get_name()=="headless": return
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(folder.path_join(name+".png"))

func setup() -> void:
	clear_pad()
	arena.reset_encounter()
	arena.mode="fight"
	arena.boss.position=Vector2(650,400)
	arena.player.position=Vector2(565,400)
	arena.boss_stage="windup"
	arena.stage_duration=100
	arena._sync_ui()

func clear_pad() -> void:
	for index in buttons: button(index,false)
	axis(JOY_AXIS_LEFT_X,0)
	axis(JOY_AXIS_LEFT_Y,0)

func run() -> void:
	arena=load("res://arena.tscn").instantiate()
	root.add_child(arena)
	await frames(4)
	axis(JOY_AXIS_LEFT_X,.1)
	await frames(2)
	check(not arena.controls.using_gamepad,"Stick drift does not change prompts")
	axis(JOY_AXIS_LEFT_X,.6)
	await frames(2)
	check(arena.start_button.text.contains("south"),"Meaningful native pad input changes the begin prompt")
	axis(JOY_AXIS_LEFT_X,0)
	await capture("controller-title")
	await tap(JOY_BUTTON_A)
	check(arena.mode=="fight","South button begins the actual scene")
	setup()
	var start: Vector2=arena.player.position
	axis(JOY_AXIS_LEFT_X,.12)
	await frames(12)
	check(arena.player.position==start,"Circular deadzone prevents drift movement")
	axis(JOY_AXIS_LEFT_X,-.6)
	await frames(12)
	var partial: float=start.x-arena.player.position.x
	axis(JOY_AXIS_LEFT_X,-1)
	start=arena.player.position
	await frames(12)
	var full: float=start.x-arena.player.position.x
	check(partial>5&&partial<full*.8,"Analog movement preserves partial stick strength")
	axis(JOY_AXIS_LEFT_Y,-1)
	await frames(2)
	check(arena.player.velocity.length()<=250.01,"Full diagonal stick input cannot boost speed")
	clear_pad()
	start=arena.player.position
	button(JOY_BUTTON_DPAD_RIGHT,true)
	await frames(12)
	button(JOY_BUTTON_DPAD_RIGHT,false)
	check(arena.player.position.x>start.x,"D-pad moves through native InputMap and physics")
	arena.player.position=Vector2(345,350)
	axis(JOY_AXIS_LEFT_X,1)
	await frames(35)
	axis(JOY_AXIS_LEFT_X,0)
	check(arena.player.position.x<353,"Controller movement respects the collision pillar")
	setup()
	button(JOY_BUTTON_X,true)
	await frames(2)
	check(arena.boss_hp==160,"West button respects blade preparation")
	await frames(10)
	check(arena.boss_hp==156,"West button lands the real guarded contact")
	await frames(45)
	check(arena.stats.strikes==1,"Holding a pad button never repeats or queues attacks")
	button(JOY_BUTTON_X,false)
	setup()
	button(JOY_BUTTON_X,true)
	await frames(2)
	button(JOY_BUTTON_X,false)
	await tap(JOY_BUTTON_B)
	await frames(12)
	check(arena.stats.dodges==1&&arena.boss_hp==160,"East button cancels unfinished contact without refund")
	check(arena.stamina<100,"Cancelled controller action retains its resource cost")
	setup()
	arena.player.position=Vector2(475,400)
	await tap(JOY_BUTTON_Y)
	await frames(25)
	check(arena.stats.seals==1&&arena.boss_hp==152&&arena.ward>0,"North button releases a real ward-pressure projectile")
	await tap(JOY_BUTTON_START)
	var frozen := [arena.elapsed,arena.player.position,arena.stamina,arena.boss_hp]
	axis(JOY_AXIS_LEFT_X,1)
	await frames(20)
	check(arena.mode=="paused"&&frozen==[arena.elapsed,arena.player.position,arena.stamina,arena.boss_hp],"Start freezes gameplay despite held stick input")
	await tap(JOY_BUTTON_BACK)
	check(arena.help_panel.visible&&arena.mode=="paused","Back opens tactics without resuming")
	await capture("controller-tactics")
	await tap(JOY_BUTTON_BACK)
	check(not arena.help_panel.visible&&arena.mode=="paused","Closing tactics keeps explicit resume")
	axis(JOY_AXIS_LEFT_X,0)
	await tap(JOY_BUTTON_A)
	check(arena.mode=="fight","South resumes explicitly")
	await tap(JOY_BUTTON_RIGHT_SHOULDER)
	check(arena.sound.muted&&arena.audio_button.text.contains("RB"),"RB controls sound with matching prompt")
	setup()
	check(arena.sound.muted,"Controller sound preference survives restart")
	axis(JOY_AXIS_LEFT_X,1)
	await frames(2)
	Input.joy_connection_changed.emit(1,false)
	check(arena.mode=="fight","An unrelated device notification does not interrupt this pad")
	Input.action_press("left") # Declared simultaneous keyboard input.
	Input.joy_connection_changed.emit(0,false)
	check(arena.mode=="paused"&&arena.sound.suspended,"Active controller loss pauses gameplay and audio")
	check(Input.is_action_pressed("left")&&!Input.is_action_pressed("pad_right"),"Disconnect clears pad input while retaining keyboard input")
	Input.action_release("left")
	Input.joy_connection_changed.emit(0,true)
	await frames(4)
	check(arena.mode=="paused","Connection alone cannot resume a paused encounter")
	var key := InputEventKey.new()
	key.physical_keycode=KEY_ENTER
	key.pressed=true
	Input.parse_input_event(key)
	await frames(2)
	key.pressed=false
	Input.parse_input_event(key)
	await frames(2)
	start=arena.player.position
	await frames(12)
	check(arena.mode=="fight"&&arena.player.position==start&&!arena.controls.using_gamepad,"Keyboard fallback resumes without stale pad movement")
	axis(JOY_AXIS_LEFT_X,1)
	key.physical_keycode=KEY_W
	key.pressed=true
	Input.parse_input_event(key)
	await frames(2)
	Input.joy_connection_changed.emit(0,false)
	check(arena.mode=="fight"&&Input.is_action_pressed("up"),"Disconnecting the old pad cannot pause an active keyboard player")
	check(not Input.is_action_pressed("pad_right"),"Inactive pad disconnect still clears its held axis")
	key.pressed=false
	Input.parse_input_event(key)
	axis(JOY_AXIS_LEFT_X,-1)
	await frames(2)
	arena._notification(Node.NOTIFICATION_WM_WINDOW_FOCUS_OUT)
	check(arena.mode=="paused"&&!Input.is_action_pressed("pad_left"),"Focus loss clears held pad state and pauses")
	# Complete the real fight using only native D-pad and button events.
	clear_pad()
	arena._begin_or_resume()
	var won := false
	for attempt in 2:
		arena.reset_encounter()
		arena.mode="fight"
		arena._sync_ui()
		for frame in 14000:
			if arena.mode!="fight": break
			bot_input()
			await physics_frame
		clear_pad()
		print("PAD_RUN ",JSON.stringify({"mode":arena.mode,"time":arena.elapsed,"hp":arena.hp,"stats":arena.stats}))
		if arena.mode=="victory":
			won=true
			break
	check(won&&arena.stats.phase_changes==1,"Native controller events complete both phases and victory")
	await capture("controller-victory")
	await tap(JOY_BUTTON_A)
	check(arena.mode=="fight"&&arena.hp==6&&arena.phase==1&&arena.stats.hits==0,"South restarts a completed encounter without old combat state")
	print("CONTROL_CHECKS ",JSON.stringify({"checks":checks,"failures":failures,"physical_gamepad":false,"game_version":ProjectSettings.get_setting("application/config/version")}))
	arena.sound.stop()
	OS.delay_msec(150)
	quit(0 if failures.is_empty() else 1)

func bot_input() -> void:
	for index in buttons: button(index,false)
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
				button(JOY_BUTTON_B,true)
	if arena.echo_time>=0: goal=arena.echo_origin+arena.echo_origin.direction_to(p)*180
	var movement: Vector2=p.direction_to(goal)
	if movement.x< -.18: button(JOY_BUTTON_DPAD_LEFT,true)
	if movement.x>.18: button(JOY_BUTTON_DPAD_RIGHT,true)
	if movement.y< -.18: button(JOY_BUTTON_DPAD_UP,true)
	if movement.y>.18: button(JOY_BUTTON_DPAD_DOWN,true)
	if arena._boss_open()&&distance<102&&arena.strike_cooldown<=0: button(JOY_BUTTON_X,true)
	if distance>110&&distance<330&&arena.seal_cooldown<=0&&arena.stamina>=60: button(JOY_BUTTON_Y,true)
