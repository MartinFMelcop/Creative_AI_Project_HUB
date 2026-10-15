extends Node2D
## One complete native encounter. Physics bodies own position; combat uses locked telegraphs.

const FIELD := Rect2(80, 175, 1120, 490)
const PLAYER_SPEED := 250.0
const BOSS_MAX := 160.0
const AMBER := Color("eab570")
const TEAL := Color("70dacd")
const RED := Color("ed7f92")
const INK := Color("0d1426")
const WHITE := Color("e5e9ef")
const COURTYARD = preload("res://media/art/courtyard.png")
const RUNNER = preload("res://media/art/veil-runner.png")
const WARDEN = preload("res://media/art/bell-warden.png")
const SoundDirector = preload("res://sound.gd")
const Motion = preload("res://motion.gd")
const Controls = preload("res://controls.gd")
var controls = Controls.new()
const STRIKE_CONTACT := 0.10
const SEAL_CONTACT := 0.075
const PARRY_START := 0.06
const PARRY_END := 0.18
const PARRY_RECOVERY := 0.38
const PARRY_RANGE := 110.0
var player_action := ""
var action_time := 0.0
var action_emitted := false
var action_aim := Vector2.RIGHT
var runner_walk_clock := 0.0
var warden_walk_clock := 0.0
var runner_moving := false
var warden_moving := false
var runner_flipped := false
var sound: Node
var player: CharacterBody2D
var boss: CharacterBody2D
var font: Font
var mode := "title"
var hp := 6
var stamina := 100.0
var boss_hp := BOSS_MAX
var ward := 0.0
var exposed := 0.0
var phase := 1
var boss_stage := "approach"
var pattern := ""
var stage_time := 0.0
var stage_duration := 0.0
var aim := Vector2.LEFT
var attack_origin := Vector2.ZERO
var attack_hit := false
var cycle := 0
var echo_time := -1.0
var echo_origin := Vector2.ZERO
var echo_hit := false
var dash_time := 0.0
var dash_direction := Vector2.RIGHT
var invulnerable := 0.0
var strike_cooldown := 0.0
var seal_cooldown := 0.0
var dash_cooldown := 0.0
var parry_cooldown := 0.0
var swing := 0.0
var damage_flash := 0.0
var boss_flash := 0.0
var elapsed := 0.0
var last_seal := -10.0
var seals: Array[Dictionary] = []
var effects: Array[Dictionary] = []
var feedback := ""
var feedback_time := 0.0
var stats := {}
var paused_from := "fight"
var start_button: Button
var help_button: Button
var help_panel: PanelContainer
var audio_button: Button
var practice_button: Button
var practice_active := false
var practice_round := 0
var practice_completed := 0
var practice_clean_counters := 0
var practice_parried := false
var practice_counter := false
var practice_guard_at := -1.0
var practice_result := ""

func _ready() -> void:
	font = ThemeDB.fallback_font
	_setup_input()
	Input.joy_connection_changed.connect(_controller_connection)
	_build_world()
	_build_ui()
	sound = SoundDirector.new()
	add_child(sound)
	reset_encounter()
	mode = "title"
	_sync_ui()

func _setup_input() -> void:
	controls.setup()

func _input(event: InputEvent) -> void:
	if controls.observe(event) and is_node_ready(): _sync_ui()

func _controller_connection(device: int, connected: bool) -> void:
	if not connected and controls.disconnected(device):
		pause_game()
		feedback = "Controller lost. Enter or reconnect + A resumes."
		feedback_time = 4.0
		_sync_ui()

func _body(radius: float, layer: int, mask: int) -> CharacterBody2D:
	var body := CharacterBody2D.new()
	body.collision_layer = layer
	body.collision_mask = mask
	var shape := CollisionShape2D.new()
	var circle := CircleShape2D.new()
	circle.radius = radius
	shape.shape = circle
	body.add_child(shape)
	add_child(body)
	return body

func _wall(rect: Rect2) -> void:
	var body := StaticBody2D.new()
	body.position = rect.get_center()
	body.collision_layer = 4
	body.collision_mask = 3
	var collision := CollisionShape2D.new()
	var shape := RectangleShape2D.new()
	shape.size = rect.size
	collision.shape = shape
	body.add_child(collision)
	add_child(body)

func _build_world() -> void:
	player = _body(14, 1, 6)
	boss = _body(28, 2, 5)
	_wall(Rect2(50,145,1180,30))
	_wall(Rect2(50,665,1180,30))
	_wall(Rect2(50,175,30,490))
	_wall(Rect2(1200,175,30,490))
	# Two real collision obstacles allow cover and make careless charges punishable.
	_wall(Rect2(365,305,45,110))
	_wall(Rect2(870,425,45,110))

func _build_ui() -> void:
	start_button = Button.new()
	start_button.focus_mode = Control.FOCUS_NONE
	start_button.position = Vector2(500,535)
	start_button.size = Vector2(280,48)
	start_button.add_theme_font_size_override("font_size",20)
	start_button.pressed.connect(_begin_or_resume)
	add_child(start_button)
	practice_button = Button.new()
	practice_button.focus_mode = Control.FOCUS_NONE
	practice_button.position = Vector2(500,590)
	practice_button.size = Vector2(280,42)
	practice_button.add_theme_font_size_override("font_size",18)
	practice_button.pressed.connect(toggle_practice)
	add_child(practice_button)
	help_button = Button.new()
	help_button.focus_mode = Control.FOCUS_NONE
	help_button.text = "Controls / tactics"
	help_button.position = Vector2(1040,725)
	help_button.size = Vector2(180,36)
	help_button.pressed.connect(toggle_tactics)
	add_child(help_button)
	audio_button = Button.new()
	audio_button.focus_mode = Control.FOCUS_NONE
	audio_button.position = Vector2(1040,691)
	audio_button.size = Vector2(180,32)
	audio_button.pressed.connect(toggle_audio)
	add_child(audio_button)
	help_panel = PanelContainer.new()
	help_panel.position = Vector2(235,175)
	help_panel.size = Vector2(810,485)
	var style := StyleBoxFlat.new()
	style.bg_color = INK
	style.border_color = Color("50617b")
	style.set_border_width_all(2)
	style.content_margin_left = 20
	style.content_margin_right = 20
	style.content_margin_top = 18
	style.content_margin_bottom = 18
	help_panel.add_theme_stylebox_override("panel",style)
	var label := Label.new()
	label.text = "MOVE   WASD / arrows · left stick / D-pad\nBLADE   J / X (west) — 12 resolve; locks aim, 100ms preparation.\nContact: guarded 4 / open 24. Finish recovery before attacking again.\nSEAL   K / Y (north) — 34 resolve; 8 damage + 36 ward pressure.\nPARRY   L / LB — 20 resolve; close sweeps only, locked facing.\nGuard is live 60–180ms after pressing; recover until 380ms.\nSuccess: no sweep hit, +8 resolve, 1.2s opening. Cooldown: 0.9s.\nCharge, wave and violet echo cannot be parried. Late guard is vulnerable.\nDODGE   Space / B (east) — 25 resolve; cancels without refund.\nBrief invulnerability, then vulnerable. Columns stop movement.\nPAUSE   Esc / Start · Enter / A (south) begins, resumes or retries.\nTACTICS   F1 / Back · SOUND   M / RB · PRACTICE   P / R3 (menus / exit).\n\nStone columns stop charges and block seals. Amber warnings lock.\nParry within 110px, facing the Warden, or leave the sweep.\nPunish recovery or break the ward with three close seal impacts.\nAt half health attacks accelerate and charges leave a violet echo.\nLeave the echo circle even when the core is open."
	label.add_theme_font_size_override("font_size",16)
	help_panel.add_child(label)
	add_child(help_panel)
	help_panel.hide()

func reset_encounter() -> void:
	practice_active = false
	practice_round = 0
	practice_completed = 0
	practice_clean_counters = 0
	practice_parried = false
	practice_counter = false
	practice_guard_at = -1
	practice_result = ""
	if is_instance_valid(sound): sound.reset()
	player.position = Vector2(300,490)
	boss.position = Vector2(955,345)
	player.velocity = Vector2.ZERO
	boss.velocity = Vector2.ZERO
	hp = 6
	stamina = 100.0
	boss_hp = BOSS_MAX
	ward = 0.0
	exposed = 0.0
	phase = 1
	boss_stage = "approach"
	pattern = ""
	stage_time = 0.0
	stage_duration = 0.7
	cycle = 0
	echo_time = -1.0
	echo_hit = false
	dash_time = 0.0
	invulnerable = 0.0
	strike_cooldown = 0.0
	seal_cooldown = 0.0
	dash_cooldown = 0.0
	parry_cooldown = 0.0
	swing = 0.0
	_clear_player_action()
	runner_walk_clock = 0.0
	warden_walk_clock = 0.0
	runner_moving = false
	warden_moving = false
	runner_flipped = false
	damage_flash = 0.0
	boss_flash = 0.0
	elapsed = 0.0
	last_seal = -10.0
	seals.clear()
	effects.clear()
	feedback = "Read the amber warning. Counter when the Warden opens."
	feedback_time = 3.0
	stats = {"strikes":0,"seals":0,"hits":0,"dodges":0,"breaks":0,"parry_attempts":0,"parries":0,"damage_taken":0,"phase_changes":0,"patterns":[]}

func _begin_or_resume() -> void:
	if mode == "practice_review":
		_next_practice_round()
		return
	if mode == "paused":
		mode = paused_from
	else:
		reset_encounter()
		mode = "fight"
	help_panel.hide()
	_sync_ui()

func toggle_practice() -> void:
	if practice_active:
		reset_encounter()
		mode = "title"
		help_panel.hide()
		_sync_ui()
	elif mode in ["title","victory","defeat"]:
		reset_encounter()
		_next_practice_round()

func _next_practice_round() -> void:
	var previous_round := practice_round
	var previous_completed := practice_completed
	var previous_clean := practice_clean_counters
	reset_encounter()
	practice_active = true
	practice_round = previous_round+1
	practice_completed = previous_completed
	practice_clean_counters = previous_clean
	player.position = Vector2(565,400)
	boss.position = Vector2(650,400)
	mode = "fight"
	_start_pattern() # The same phase-one sweep, collision, guard and recovery clocks.
	feedback = "Practice: L / LB just before contact, then J / X."
	feedback_time = 3
	help_panel.hide()
	_sync_ui()

func _practice_miss_reason() -> String:
	if invulnerable > 0: return "Dodged. Try a close guard instead, then a blade counter."
	if boss.position.distance_to(player.position) > PARRY_RANGE:
		return "Too far to parry. Stay inside the inner 110px arc."
	if practice_guard_at < 0: return "No guard at contact. Press L / LB just before the sweep."
	var age := elapsed-practice_guard_at
	if age < PARRY_START: return "Guard too late. Press earlier, before sweep contact."
	if age >= PARRY_END: return "Guard too early. Wait longer into the amber warning."
	if player_action != "parry": return "Guard cancelled. Keep it through sweep contact."
	return "Guard faced away. Face the Warden when pressing L / LB."

func _finish_practice_round() -> void:
	practice_completed += 1
	if practice_parried and practice_counter and stats.damage_taken == 0:
		practice_clean_counters += 1
		practice_result = "Clean parry + blade counter. Repeat when ready."
	elif practice_parried:
		practice_result = "Parried, no blade counter. Press J / X while the core is teal."
	elif practice_result.is_empty():
		practice_result = "Sweep avoided. Stay close to rehearse the guard timing."
	mode = "practice_review" # Explicit next take; never a trial victory or auto-loop.
	_sync_ui()

func pause_game() -> void:
	if mode == "fight":
		paused_from = mode
		mode = "paused"
		_sync_ui()

func _notification(what: int) -> void:
	if what == NOTIFICATION_WM_WINDOW_FOCUS_OUT and is_node_ready():
		controls.clear_pad()
		pause_game()

func _sync_ui() -> void:
	if is_instance_valid(sound):
		sound.set_suspended(mode == "paused")
		audio_button.text = ("Sound off" if sound.muted else "Sound on")+(" [RB]" if controls.using_gamepad else " [M]")
	start_button.visible = mode != "fight" and not help_panel.visible
	help_button.text = ("Close tactics" if help_panel.visible else "Tactics")+(" [Back]" if controls.using_gamepad else " [F1]")
	practice_button.visible = (practice_active or mode in ["title","victory","defeat"]) and mode != "fight" and not help_panel.visible
	practice_button.text = ("Leave practice" if practice_active else "Sweep practice")+(" [R3]" if controls.using_gamepad else " [P]")
	start_button.text = ("Next sweep" if mode == "practice_review" else "Resume" if mode == "paused" else "Begin trial" if mode == "title" else "Try again")+(" [A / south]" if controls.using_gamepad else " [Enter]")
	queue_redraw()

func toggle_tactics() -> void:
	if mode == "fight": pause_game()
	help_panel.visible = not help_panel.visible
	_sync_ui()

func toggle_audio() -> void:
	sound.toggle_mute()
	_sync_ui()

func _physics_process(delta: float) -> void:
	if controls.pressed("practice") and (practice_active or mode in ["title","victory","defeat"]):
		toggle_practice()
		return
	if controls.pressed("mute"): toggle_audio()
	if controls.pressed("help"): toggle_tactics()
	if controls.pressed("pause"):
		if mode == "fight": pause_game()
		elif mode == "paused": _begin_or_resume()
	if controls.pressed("begin") and mode != "fight": _begin_or_resume()
	if mode == "fight":
		step_fight(delta, controls.movement(), controls.pressed("strike"), controls.pressed("seal"), controls.pressed("dash"), controls.pressed("parry"))
	queue_redraw()

func step_fight(delta: float, move: Vector2, strike: bool, cast_seal: bool, dodge: bool, parry: bool = false) -> void:
	if mode != "fight": return
	elapsed += delta
	stamina = minf(100, stamina + delta * 25)
	invulnerable = maxf(0, invulnerable-delta)
	exposed = maxf(0, exposed-delta)
	strike_cooldown = maxf(0, strike_cooldown-delta)
	seal_cooldown = maxf(0, seal_cooldown-delta)
	dash_cooldown = maxf(0, dash_cooldown-delta)
	parry_cooldown = maxf(0, parry_cooldown-delta)
	damage_flash = maxf(0,damage_flash-delta)
	boss_flash = maxf(0,boss_flash-delta)
	swing = maxf(0,swing-delta)
	feedback_time = maxf(0,feedback_time-delta)
	if elapsed-last_seal > 2.0: ward = maxf(0,ward-delta*18)
	if dodge and dash_cooldown <= 0 and stamina >= 25:
		_clear_player_action() # Cancel pending contact; paid resolve and cooldown stay spent.
		swing = 0
		stamina -= 25
		dash_direction = move.normalized() if move.length() > 0.1 else boss.position.direction_to(player.position)
		dash_time = 0.20
		invulnerable = 0.16
		dash_cooldown = 0.65
		stats.dodges += 1
		sound.cue("dodge",player.position)
	if dash_time > 0:
		dash_time = maxf(0,dash_time-delta)
		player.velocity = dash_direction*620
	else: player.velocity = move.limit_length()*PLAYER_SPEED*(0.65 if not player_action.is_empty() else 1.0)
	var old_player_position := player.position
	player.move_and_slide()
	runner_moving = player.position.distance_to(old_player_position) > 0.1
	if runner_moving:
		runner_walk_clock += player.position.distance_to(old_player_position)/PLAYER_SPEED
		if player_action.is_empty() and swing<=0 and absf(player.velocity.x)>1: runner_flipped = player.velocity.x<0
	_advance_player_action(delta)
	if parry and parry_cooldown <= 0 and stamina >= 20 and dash_time <= 0 and player_action.is_empty():
		stamina -= 20
		parry_cooldown = 0.9
		stats.parry_attempts += 1
		_start_player_action("parry")
		if practice_active: practice_guard_at = elapsed
	elif strike and strike_cooldown <= 0 and stamina >= 12 and dash_time <= 0 and player_action.is_empty():
		stamina -= 12
		strike_cooldown = 0.40
		stats.strikes += 1
		_start_player_action("strike")
	elif cast_seal and seal_cooldown <= 0 and stamina >= 34 and dash_time <= 0 and player_action.is_empty():
		stamina -= 34
		seal_cooldown = 1.10
		stats.seals += 1
		_start_player_action("seal")
	_update_seals(delta)
	var old_boss_position := boss.position
	_update_boss(delta)
	warden_moving = boss.position.distance_to(old_boss_position)>0.1
	if warden_moving: warden_walk_clock += boss.position.distance_to(old_boss_position)/135.0
	_update_echo(delta)
	for effect in effects: effect.life -= delta
	effects = effects.filter(func(e): return e.life > 0)
	if not practice_active:
		if hp <= 0: mode = "defeat"
		elif boss_hp <= 0: mode = "victory"
	if mode in ["victory","defeat"]:
		sound.cue(mode)
		sound.set_phase(false)
		_sync_ui()

func _clear_player_action() -> void:
	player_action = ""
	action_time = 0
	action_emitted = false

func _start_player_action(kind: String) -> void:
	player_action = kind
	action_time = 0
	action_emitted = false
	action_aim = player.position.direction_to(boss.position)
	if action_aim.is_zero_approx(): action_aim = Vector2.LEFT if runner_flipped else Vector2.RIGHT
	if absf(action_aim.x)>0.01: runner_flipped = action_aim.x<0

func _advance_player_action(delta: float) -> void:
	if player_action.is_empty(): return
	action_time += delta
	if player_action == "parry":
		if action_time >= PARRY_RECOVERY:
			_clear_player_action()
			feedback = "Guard spent. Time the next close sweep or dodge."
			feedback_time = 1.5
		return
	var contact := STRIKE_CONTACT if player_action=="strike" else SEAL_CONTACT
	if not action_emitted and action_time+0.000001 >= contact:
		action_emitted = true
		sound.cue(player_action,player.position)
		if player_action=="strike":
			swing = 0.14
			var offset := boss.position-player.position
			if offset.length() <= 103 and (offset.is_zero_approx() or action_aim.dot(offset.normalized()) >= cos(PI/3)):
				var was_open := _boss_open()
				var applied := _damage_boss(24 if was_open else 4)
				if practice_active and practice_parried and was_open and applied > 0: practice_counter = true
				if applied > 0: sound.cue("counter" if was_open else "guard",boss.position)
				_feedback(("COUNTER  +%d"%applied if was_open else "GUARDED  +%d — wait for an opening"%applied) if applied > 0 else "The fracturing ward repels the strike. Regroup.", TEAL)
			else:
				feedback = "Missed. Aim locks when the blade is drawn."
				feedback_time = 1.3
		else:
			seals.append({"position":player.position,"direction":action_aim,"life":0.70})
	if action_time >= (0.32 if player_action=="strike" else 0.30): _clear_player_action()

func _boss_open() -> bool:
	return boss_stage != "transition" and (exposed > 0 or boss_stage == "recover")

func _damage_boss(amount: float) -> float:
	if boss_stage == "transition": return 0
	var applied := minf(amount,boss_hp)
	boss_hp = maxf(0,boss_hp-amount)
	boss_flash = 0.15
	stats.hits += 1
	if boss_hp <= 80 and phase == 1 and boss_hp > 0 and not practice_active:
		phase = 2
		boss_stage = "transition"
		stage_time = 0
		stage_duration = 1.1
		echo_time = -1
		exposed = 0
		ward = 0
		cycle = 1 # Phase two opens with a charge, demonstrating the new echo threat.
		stats.phase_changes += 1
		sound.set_phase(true)
		sound.cue("phase",boss.position)
		_feedback("THE VEIL FRACTURES — phase two: watch for charge echoes", RED)
	return applied

func _feedback(text: String, color: Color) -> void:
	feedback = text
	feedback_time = 2.2
	effects.append({"position":boss.position,"life":0.35,"color":color})

func _update_seals(delta: float) -> void:
	var keep: Array[Dictionary] = []
	for projectile in seals:
		var previous: Vector2 = projectile.position
		projectile.position += projectile.direction * 540 * delta
		projectile.life -= delta
		var hit = PhysicsRayQueryParameters2D.create(previous,projectile.position,6)
		hit.exclude = [player.get_rid()]
		var result := get_world_2d().direct_space_state.intersect_ray(hit)
		if not result.is_empty():
			if result.collider == boss:
				var applied := _damage_boss(8)
				if applied > 0 and boss_stage != "transition": ward = minf(100,ward+36)
				last_seal = elapsed
				if ward >= 100:
					ward = 0
					exposed = 2.4
					stats.breaks += 1
					sound.cue("break",boss.position)
					_feedback("WARD BROKEN — strike while the core is open", TEAL)
			else: _feedback("The seal struck stone. Move out from cover.", AMBER)
		elif projectile.life > 0: keep.append(projectile)
	seals = keep

func _take_hit() -> void:
	if invulnerable > 0 or hp <= 0: return
	hp -= 1
	_clear_player_action()
	swing = 0
	stats.damage_taken += 1
	invulnerable = 0.75
	damage_flash = 0.25
	sound.cue("hurt",player.position)
	feedback = "Hit. Regroup outside the next warning."
	feedback_time = 1.5

func _parry_live() -> bool:
	return player_action == "parry" and action_time + 0.000001 >= PARRY_START and action_time < PARRY_END

func _try_parry_sweep() -> bool:
	# Called only for a real sweep collision. It grants no general invulnerability.
	var offset := boss.position-player.position
	if invulnerable > 0 or not _parry_live() or offset.length() > PARRY_RANGE:
		return false
	if not offset.is_zero_approx() and action_aim.dot(offset.normalized()) < cos(PI/3):
		return false
	_clear_player_action()
	stamina = minf(100,stamina+8)
	stats.parries += 1
	if practice_active: practice_parried = true
	boss_stage = "recover"
	stage_time = 0
	stage_duration = 1.2
	attack_hit = true
	sound.cue("counter",player.position)
	_feedback("PARRY — sweep turned aside. Counter now!",TEAL)
	return true

func _start_pattern() -> void:
	var patterns := ["sweep","charge","wave"]
	pattern = "sweep" if practice_active else patterns[cycle%3]
	cycle += 1
	if not stats.patterns.has(pattern): stats.patterns.append(pattern)
	boss_stage = "windup"
	stage_time = 0
	stage_duration = (0.85 if pattern == "sweep" else 1.0) * (0.80 if phase == 2 else 1.0)
	aim = boss.position.direction_to(player.position)
	attack_origin = boss.position
	attack_hit = false
	sound.cue(pattern,boss.position)

func _update_boss(delta: float) -> void:
	if boss_hp <= 0: return
	stage_time += delta
	boss.velocity = Vector2.ZERO
	if boss_stage == "approach":
		if boss.position.distance_to(player.position) > 145:
			boss.velocity = boss.position.direction_to(player.position)*135
			boss.move_and_slide()
		if stage_time >= stage_duration: _start_pattern()
	elif boss_stage == "windup":
		if stage_time >= stage_duration:
			boss_stage = "active"
			stage_time = 0
			stage_duration = 0.46 if pattern == "charge" else (0.65 if pattern == "wave" else 0.18)
	elif boss_stage == "active":
		if pattern == "charge":
			var previous := boss.position
			boss.velocity = aim*680
			boss.move_and_slide()
			if Geometry2D.get_closest_point_to_segment(player.position,previous,boss.position).distance_to(player.position) < 46 and not attack_hit:
				_take_hit()
				attack_hit = true
		elif pattern == "sweep":
			var to_player := boss.position.direction_to(player.position)
			if player.position.distance_to(boss.position) < 165 and aim.dot(to_player) > cos(PI/3) and not attack_hit:
				if not _try_parry_sweep():
					if practice_active: practice_result = _practice_miss_reason()
					_take_hit()
				attack_hit = true
		else:
			var radius := 30+190*stage_time/stage_duration
			if absf(player.position.distance_to(attack_origin)-radius) < 24 and not attack_hit:
				_take_hit()
				attack_hit = true
		if stage_time >= stage_duration or (pattern == "charge" and boss.get_slide_collision_count() > 0):
			if pattern == "charge" and phase == 2:
				echo_origin = boss.position
				echo_time = 0
				echo_hit = false
				sound.cue("echo",echo_origin)
			boss_stage = "recover"
			stage_time = 0
			stage_duration = 0.90 if phase == 1 else 0.70
	elif boss_stage == "recover" or boss_stage == "transition":
		if stage_time >= stage_duration:
			if practice_active:
				_finish_practice_round()
				return
			boss_stage = "approach"
			stage_time = 0
			stage_duration = 0.80 if phase == 1 else 0.55

func _update_echo(delta: float) -> void:
	if echo_time < 0: return
	echo_time += delta
	if echo_time >= 0.65 and not echo_hit:
		echo_hit = true
		if player.position.distance_to(echo_origin) < 130: _take_hit()
	if echo_time > 0.90: echo_time = -1

func _draw() -> void:
	if not is_node_ready(): return
	draw_rect(Rect2(0,0,1280,800), INK)
	draw_rect(FIELD,Color("151b32"))
	draw_texture_rect(COURTYARD,FIELD,false,Color(0.72,0.78,0.87))
	draw_rect(FIELD,Color("56637b"),false,2)
	for pos in [Vector2(365,305),Vector2(870,425)]:
		# The visible footprint remains the real 45x110 collision rectangle.
		draw_rect(Rect2(pos+Vector2(7,8),Vector2(45,110)),Color(0,0,0,.28))
		draw_rect(Rect2(pos,Vector2(45,110)),Color("35425a"))
		draw_rect(Rect2(pos+Vector2(5,7),Vector2(35,98)),Color("26344b"))
		draw_rect(Rect2(pos,Vector2(45,7)),Color("657082"))
		draw_line(pos+Vector2(4,9),pos+Vector2(4,104),Color("57637b"),2)
		for y in [32,68,95]:
			draw_line(pos+Vector2(6,y),pos+Vector2(38,y+3),Color("172438"),2)
		draw_arc(pos+Vector2(22,46),9,PI,TAU,12,Color("ad956e"),2)
		draw_line(pos+Vector2(14,48),pos+Vector2(30,48),Color("ad956e"),2)
		draw_line(pos+Vector2(22,49),pos+Vector2(22,73),Color("ad956e"),2)
	_draw_warnings()
	_draw_actor(boss.position,false)
	_draw_actor(player.position,true)
	for projectile in seals:
		draw_circle(projectile.position,7,TEAL)
		draw_line(projectile.position-projectile.direction*22,projectile.position,TEAL,3)
	for effect in effects: draw_arc(effect.position,40+(0.35-effect.life)*90,0,TAU,32,Color(effect.color, effect.life/0.35),2)
	if swing > 0:
		var angle := action_aim.angle()
		draw_arc(player.position,90,angle-PI/3,angle+PI/3,24,TEAL,5)
	if player_action == "parry":
		var angle := action_aim.angle()
		var color := TEAL if _parry_live() else AMBER
		draw_arc(player.position,35,angle-PI/3,angle+PI/3,24,color,5 if _parry_live() else 2)
		_text(player.position+Vector2(-45,-75),"PARRY READY" if _parry_live() else "SETTING GUARD" if action_time<PARRY_START else "GUARD SPENT",12,color)
	_draw_hud()
	if mode != "fight": _draw_overlay()

func _draw_warnings() -> void:
	if boss_stage == "windup" or boss_stage == "active":
		var danger := Color(AMBER,0.15 if boss_stage == "windup" else 0.38)
		if pattern == "sweep":
			var points := PackedVector2Array([boss.position])
			for i in range(25): points.append(boss.position+Vector2.from_angle(aim.angle()-PI/3+i*PI/36)*165)
			draw_colored_polygon(points,danger)
			draw_arc(boss.position,165,aim.angle()-PI/3,aim.angle()+PI/3,32,AMBER,3)
			draw_arc(boss.position,PARRY_RANGE,aim.angle()-PI/3,aim.angle()+PI/3,24,Color(TEAL,0.7),2)
		elif pattern == "charge":
			draw_line(attack_origin,attack_origin+aim*315,danger,92)
			draw_line(attack_origin,attack_origin+aim*315,AMBER,2)
		else:
			if boss_stage == "windup": draw_circle(attack_origin,220,danger)
			var radius := 220.0 if boss_stage == "windup" else 30+190*stage_time/stage_duration
			draw_arc(attack_origin,radius,0,TAU,64,AMBER,4)
	if echo_time >= 0:
		draw_circle(echo_origin,130,Color(RED,0.16 if echo_time<0.65 else 0.45))
		draw_arc(echo_origin,130,0,TAU,48,RED,3)
		draw_arc(echo_origin,140,-PI/2,-PI/2+TAU*minf(1,echo_time/0.65),48,RED,3)

func _draw_actor(pos: Vector2, hero: bool) -> void:
	draw_ellipse_shadow(pos)
	if hero:
		if dash_time > 0: draw_circle(pos,28,Color(TEAL,0.25))
		draw_arc(pos,18,0,TAU,24,TEAL,2)
		Motion.draw_actor(self,pos,"runner",Motion.runner_frame(self),runner_flipped,Color(1.5,1.5,1.5) if damage_flash>0 else Color.WHITE)
	else:
		var color := WHITE if boss_flash > 0 else (TEAL if _boss_open() else (RED if phase == 2 else AMBER))
		draw_arc(pos,34,0,TAU,32,color,3)
		var facing := aim if boss_stage in ["windup","active"] else boss.position.direction_to(player.position)
		Motion.draw_actor(self,pos,"warden",Motion.warden_frame(self),facing.x<0,Color(1.5,1.5,1.5) if boss_flash>0 else Color.WHITE)
		# State marker sits above the illustration; color never carries the state alone.
		draw_circle(pos+Vector2(0,-45),5,color)
		if _boss_open():
			draw_arc(pos,46,0,TAU,32,TEAL,3)
			_text(Vector2(pos.x-23,maxf(154,pos.y-65)),"OPEN",12,TEAL)
		elif boss_stage == "transition": _text(Vector2(pos.x-32,maxf(154,pos.y-65)),"FRACTURE",12,RED)
		if exposed > 0: draw_arc(pos,50,0,TAU*exposed/2.4,32,TEAL,3)

func draw_ellipse_shadow(pos: Vector2) -> void:
	draw_set_transform(pos+Vector2(0,22),0,Vector2(1,0.35))
	draw_circle(Vector2.ZERO,28,Color(0,0,0,0.35))
	draw_set_transform(Vector2.ZERO)

func _text(pos: Vector2, text: String, size: int=20, color: Color=WHITE) -> void:
	draw_string(font,pos,text,HORIZONTAL_ALIGNMENT_LEFT,-1,size,color)

func _bar(pos: Vector2, width: float, value: float, maximum: float, color: Color) -> void:
	draw_rect(Rect2(pos,Vector2(width,10)),Color("293449"))
	draw_rect(Rect2(pos,Vector2(width*clampf(value/maximum,0,1),10)),color)

func _draw_hud() -> void:
	# Breathing space accommodates illustrated bodies beyond their floor circles.
	# Hazards still cannot cover the actual HUD, and physics footprints stay fixed.
	draw_rect(Rect2(0,0,1280,140),INK)
	draw_rect(Rect2(0,690,1280,110),INK)
	draw_rect(Rect2(0,140,30,550),INK)
	draw_rect(Rect2(1250,140,30,550),INK)
	draw_rect(FIELD,Color("56637b"),false,2)
	_text(Vector2(80,47),"VEILBREAK",30,WHITE)
	_text(Vector2(80,74),"SWEEP PRACTICE  /  NOT A TRIAL RESULT" if practice_active else "THE BELL WARDEN  /  COURTYARD TRIAL",13,AMBER)
	_text(Vector2(650,47),"WARDEN  /  PHASE %s"%phase,20,AMBER)
	_bar(Vector2(650,62),550,boss_hp,BOSS_MAX,AMBER if phase==1 else RED)
	_bar(Vector2(650,88),550,ward,100,TEAL)
	_text(Vector2(650,118),"Ward pressure %d / 100   |   %s"%[ward,"CORE OPEN" if _boss_open() else "ARMORED"],16,TEAL)
	_text(Vector2(80,112),"Health  %s / 6"%hp,18,RED)
	_bar(Vector2(80,125),200,hp,6,RED)
	_text(Vector2(315,112),"Resolve  %d / 100"%stamina,18,TEAL)
	_bar(Vector2(315,125),255,stamina,100,TEAL)
	var state_label := "Approaching" if boss_stage=="approach" else ("Open for a counter" if boss_stage=="recover" else "Veil fracture" if boss_stage=="transition" else pattern.to_upper()+" / "+boss_stage.to_upper())
	if pattern=="sweep" and boss_stage in ["windup","active"]: state_label = "SWEEP / close parry or dodge"
	if practice_active and boss_stage == "windup": state_label = "Sweep in %.2fs"%maxf(0,stage_duration-stage_time)
	_text(Vector2(80,706),state_label,20,AMBER)
	_text(Vector2(80,742),"Stick / D-pad move   X blade   Y seal   LB parry   B dodge   Start pause" if controls.using_gamepad else "WASD move   J blade   K seal   L parry   Space dodge / cancel   Esc pause",16,Color("aab6cb"))
	if feedback_time > 0: _text(Vector2(420,706),feedback,17,TEAL)

func _draw_overlay() -> void:
	if help_panel.visible: return
	draw_rect(Rect2(220,210,840,450),Color(INK,0.94))
	draw_rect(Rect2(220,210,840,450),Color("50617b"),false,2)
	var title := "Sweep practice: review." if mode=="practice_review" else "Practice paused." if mode=="paused" and practice_active else "The bell has stopped." if mode=="victory" else "The Warden holds the gate." if mode=="defeat" else "Trial paused." if mode=="paused" else "The Bell Warden."
	_text(Vector2(290,279),title,36,WHITE)
	if mode=="title":
		draw_texture_rect(WARDEN,Rect2(260,315,155,190),false)
		_text(Vector2(450,325),"Break the guard. Cross the Veil gate.",22,AMBER)
		_text(Vector2(450,365),"Dodge warnings; L / LB parries close sweeps.",20)
		_text(Vector2(450,401),"Counter an open core; seals build ward pressure.",20)
		_text(Vector2(450,445),"Phase two adds echoes. Leave the violet circle.",20)
	elif mode=="practice_review":
		_text(Vector2(290,335),practice_result,19,TEAL)
		_text(Vector2(290,380),"Round %d  |  Reviewed %d  |  Clean parry + counter %d"%[practice_round,practice_completed,practice_clean_counters],20)
		_text(Vector2(290,420),"This drill repeats one phase-one sweep at real speed and range.",18)
		_text(Vector2(290,460),"No trial victory. P / R3 returns to the title for the full encounter.",18,Color("aab6cb"))
	elif mode=="paused":
		_text(Vector2(290,335),"The encounter is frozen. Resume when you are ready.",22)
	else:
		_text(Vector2(290,335),"Time %.1fs   |   Hits %s   |   Ward breaks %s   |   Dodges %s"%[elapsed,stats.hits,stats.breaks,stats.dodges],20,TEAL)
		_text(Vector2(290,380),"Damage taken %s / 6   |   Both phases share the same fight."%stats.damage_taken,20)
		_text(Vector2(290,420),"Timed guards: %s / %s successful · close sweeps only"%[stats.parries,stats.parry_attempts],18,TEAL)
		_text(Vector2(290,460),"The Veil gate opens. The courtyard falls quiet." if mode=="victory" else "Regroup at the arch. Read the next warning before committing.",18,Color("aab6cb"))
