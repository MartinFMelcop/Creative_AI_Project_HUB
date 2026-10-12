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

func _ready() -> void:
	font = ThemeDB.fallback_font
	_setup_input()
	_build_world()
	_build_ui()
	reset_encounter()
	mode = "title"
	_sync_ui()

func _setup_input() -> void:
	var keys := {"left":[KEY_A,KEY_LEFT],"right":[KEY_D,KEY_RIGHT],"up":[KEY_W,KEY_UP],"down":[KEY_S,KEY_DOWN],"strike":[KEY_J],"seal":[KEY_K],"dash":[KEY_SPACE],"begin":[KEY_ENTER],"pause":[KEY_ESCAPE],"help":[KEY_F1]}
	for action in keys:
		if not InputMap.has_action(action): InputMap.add_action(action)
		for key in keys[action]:
			var event := InputEventKey.new()
			event.physical_keycode = key
			InputMap.action_add_event(action, event)

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
	help_button = Button.new()
	help_button.focus_mode = Control.FOCUS_NONE
	help_button.text = "Controls / tactics"
	help_button.position = Vector2(1040,725)
	help_button.size = Vector2(180,36)
	help_button.pressed.connect(toggle_tactics)
	add_child(help_button)
	help_panel = PanelContainer.new()
	help_panel.position = Vector2(275,215)
	help_panel.size = Vector2(730,285)
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
	label.text = "MOVE   WASD / arrows\nSTRIKE   J — 12 resolve; short range. Guarded: 4 / open: 24 damage.\nSEAL   K — 34 resolve; projectile, 8 damage + 36 ward pressure.\nDODGE   Space — 25 resolve; brief invulnerability, then vulnerable.\nPAUSE   Esc — focus loss also pauses. Enter resumes.\n\nStone columns stop charges and block seals. Amber shapes lock.
Step outside a sweep; cross a wave\nwith a well-timed dodge. Punish recovery or break the ward with seals.\nAt half health the Warden attacks faster and charges leave an echo.\nThe violet echo gives a separate warning — leave its circle."
	label.add_theme_font_size_override("font_size",18)
	help_panel.add_child(label)
	add_child(help_panel)
	help_panel.hide()

func reset_encounter() -> void:
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
	swing = 0.0
	damage_flash = 0.0
	boss_flash = 0.0
	elapsed = 0.0
	last_seal = -10.0
	seals.clear()
	effects.clear()
	feedback = "Read the amber warning. Counter when the Warden opens."
	feedback_time = 3.0
	stats = {"strikes":0,"seals":0,"hits":0,"dodges":0,"breaks":0,"damage_taken":0,"phase_changes":0,"patterns":[]}

func _begin_or_resume() -> void:
	if mode == "paused":
		mode = paused_from
	else:
		reset_encounter()
		mode = "fight"
	help_panel.hide()
	_sync_ui()

func pause_game() -> void:
	if mode == "fight":
		paused_from = mode
		mode = "paused"
		_sync_ui()

func _notification(what: int) -> void:
	if what == NOTIFICATION_WM_WINDOW_FOCUS_OUT and is_node_ready(): pause_game()

func _sync_ui() -> void:
	start_button.visible = mode != "fight" and not help_panel.visible
	help_button.text = "Close tactics [F1]" if help_panel.visible else "Tactics [F1]"
	start_button.text = "Resume  [Enter]" if mode == "paused" else ("Begin trial  [Enter]" if mode == "title" else "Try again  [Enter]")
	queue_redraw()

func toggle_tactics() -> void:
	if mode == "fight": pause_game()
	help_panel.visible = not help_panel.visible
	_sync_ui()

func _physics_process(delta: float) -> void:
	if Input.is_action_just_pressed("help"): toggle_tactics()
	if Input.is_action_just_pressed("pause"):
		if mode == "fight": pause_game()
		elif mode == "paused": _begin_or_resume()
	if Input.is_action_just_pressed("begin") and mode != "fight": _begin_or_resume()
	if mode == "fight":
		step_fight(delta, Input.get_vector("left","right","up","down"), Input.is_action_just_pressed("strike"), Input.is_action_just_pressed("seal"), Input.is_action_just_pressed("dash"))
	queue_redraw()

func step_fight(delta: float, move: Vector2, strike: bool, cast_seal: bool, dodge: bool) -> void:
	if mode != "fight": return
	elapsed += delta
	stamina = minf(100, stamina + delta * 25)
	invulnerable = maxf(0, invulnerable-delta)
	exposed = maxf(0, exposed-delta)
	strike_cooldown = maxf(0, strike_cooldown-delta)
	seal_cooldown = maxf(0, seal_cooldown-delta)
	dash_cooldown = maxf(0, dash_cooldown-delta)
	damage_flash = maxf(0,damage_flash-delta)
	boss_flash = maxf(0,boss_flash-delta)
	swing = maxf(0,swing-delta)
	feedback_time = maxf(0,feedback_time-delta)
	if elapsed-last_seal > 2.0: ward = maxf(0,ward-delta*18)
	if dodge and dash_cooldown <= 0 and stamina >= 25:
		stamina -= 25
		dash_direction = move.normalized() if move.length() > 0.1 else boss.position.direction_to(player.position)
		dash_time = 0.20
		invulnerable = 0.16
		dash_cooldown = 0.65
		stats.dodges += 1
	if dash_time > 0:
		dash_time -= delta
		player.velocity = dash_direction*620
	else: player.velocity = move.limit_length()*PLAYER_SPEED
	player.move_and_slide()
	if strike and strike_cooldown <= 0 and stamina >= 12 and dash_time <= 0:
		stamina -= 12
		strike_cooldown = 0.40
		swing = 0.16
		stats.strikes += 1
		if player.position.distance_to(boss.position) <= 103:
			var was_open := _boss_open()
			var applied := _damage_boss(24 if was_open else 4)
			_feedback(("COUNTER  +%d"%applied if was_open else "GUARDED  +%d — wait for an opening"%applied) if applied > 0 else "The fracturing ward repels the strike. Regroup.", TEAL)
	if cast_seal and seal_cooldown <= 0 and stamina >= 34 and dash_time <= 0:
		stamina -= 34
		seal_cooldown = 1.10
		stats.seals += 1
		seals.append({"position":player.position,"direction":player.position.direction_to(boss.position),"life":0.70})
	_update_seals(delta)
	_update_boss(delta)
	_update_echo(delta)
	for effect in effects: effect.life -= delta
	effects = effects.filter(func(e): return e.life > 0)
	if hp <= 0: mode = "defeat"
	elif boss_hp <= 0: mode = "victory"
	if mode != "fight": _sync_ui()

func _boss_open() -> bool:
	return boss_stage != "transition" and (exposed > 0 or boss_stage == "recover")

func _damage_boss(amount: float) -> float:
	if boss_stage == "transition": return 0
	var applied := minf(amount,boss_hp)
	boss_hp = maxf(0,boss_hp-amount)
	boss_flash = 0.15
	stats.hits += 1
	if boss_hp <= 80 and phase == 1 and boss_hp > 0:
		phase = 2
		boss_stage = "transition"
		stage_time = 0
		stage_duration = 1.1
		echo_time = -1
		exposed = 0
		ward = 0
		cycle = 1 # Phase two opens with a charge, demonstrating the new echo threat.
		stats.phase_changes += 1
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
					_feedback("WARD BROKEN — strike while the core is open", TEAL)
			else: _feedback("The seal struck stone. Move out from cover.", AMBER)
		elif projectile.life > 0: keep.append(projectile)
	seals = keep

func _take_hit() -> void:
	if invulnerable > 0 or hp <= 0: return
	hp -= 1
	stats.damage_taken += 1
	invulnerable = 0.75
	damage_flash = 0.25
	feedback = "Hit. Regroup outside the next warning."
	feedback_time = 1.5

func _start_pattern() -> void:
	var patterns := ["sweep","charge","wave"]
	pattern = patterns[cycle%3]
	cycle += 1
	if not stats.patterns.has(pattern): stats.patterns.append(pattern)
	boss_stage = "windup"
	stage_time = 0
	stage_duration = (0.85 if pattern == "sweep" else 1.0) * (0.80 if phase == 2 else 1.0)
	aim = boss.position.direction_to(player.position)
	attack_origin = boss.position
	attack_hit = false

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
			boss_stage = "recover"
			stage_time = 0
			stage_duration = 0.90 if phase == 1 else 0.70
	elif boss_stage == "recover" or boss_stage == "transition":
		if stage_time >= stage_duration:
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
	for x in range(80,1201,56): draw_line(Vector2(x,175),Vector2(x,665),Color("202941"),1)
	for y in range(175,666,49): draw_line(Vector2(80,y),Vector2(1200,y),Color("202941"),1)
	draw_rect(FIELD,Color("56637b"),false,2)
	for pos in [Vector2(365,305),Vector2(870,425)]:
		draw_rect(Rect2(pos,Vector2(45,110)),Color("35425a"))
		draw_rect(Rect2(pos+Vector2(6,6),Vector2(33,98)),Color("1d293e"))
		draw_line(pos+Vector2(22,12),pos+Vector2(22,98),AMBER,2)
	_draw_warnings()
	_draw_actor(boss.position,false)
	_draw_actor(player.position,true)
	for projectile in seals:
		draw_circle(projectile.position,7,TEAL)
		draw_line(projectile.position-projectile.direction*22,projectile.position,TEAL,3)
	for effect in effects: draw_arc(effect.position,40+(0.35-effect.life)*90,0,TAU,32,Color(effect.color, effect.life/0.35),2)
	if swing > 0:
		var angle := player.position.direction_to(boss.position).angle()
		draw_arc(player.position,90,angle-PI/3,angle+PI/3,24,TEAL,5)
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
		var color := WHITE if damage_flash > 0 else TEAL
		if dash_time > 0: draw_circle(pos,28,Color(TEAL,0.25))
		draw_colored_polygon(PackedVector2Array([pos+Vector2(-15,10),pos+Vector2(0,22),pos+Vector2(15,10),pos+Vector2(7,-8),pos+Vector2(-7,-8)]),Color("426b87"))
		draw_circle(pos-Vector2(0,7),10,color)
		draw_line(pos+Vector2(12,0),pos+Vector2(21,-17),WHITE,3)
	else:
		var color := WHITE if boss_flash > 0 else (TEAL if _boss_open() else (RED if phase == 2 else AMBER))
		draw_circle(pos,31,Color("4c3e5a"))
		draw_colored_polygon(PackedVector2Array([pos+Vector2(-37,8),pos+Vector2(-23,-25),pos+Vector2(23,-25),pos+Vector2(37,8),pos+Vector2(15,32),pos+Vector2(-15,32)]),Color("384257"))
		draw_line(pos+Vector2(-21,-20),pos+Vector2(-32,-43),color,5)
		draw_line(pos+Vector2(21,-20),pos+Vector2(32,-43),color,5)
		draw_circle(pos,13,color)
		draw_line(pos+Vector2(-7,-6),pos+Vector2(7,6),INK,2)
		if exposed > 0: draw_arc(pos,42,0,TAU*exposed/2.4,32,TEAL,3)

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
	# Keep arena hazards out of the interface even when a wave reaches a wall.
	draw_rect(Rect2(0,0,1280,174),INK)
	draw_rect(Rect2(0,666,1280,134),INK)
	draw_rect(Rect2(0,174,79,492),INK)
	draw_rect(Rect2(1201,174,79,492),INK)
	draw_rect(FIELD,Color("56637b"),false,2)
	_text(Vector2(80,47),"VEILBREAK",30,WHITE)
	_text(Vector2(80,74),"THE BELL WARDEN  /  COURTYARD TRIAL",13,AMBER)
	_text(Vector2(650,47),"WARDEN  /  PHASE %s"%phase,20,AMBER)
	_bar(Vector2(650,62),550,boss_hp,BOSS_MAX,AMBER if phase==1 else RED)
	_bar(Vector2(650,88),550,ward,100,TEAL)
	_text(Vector2(650,118),"Ward pressure %d / 100   |   %s"%[ward,"CORE OPEN" if _boss_open() else "ARMORED"],16,TEAL)
	_text(Vector2(80,112),"Health  %s / 6"%hp,18,RED)
	_bar(Vector2(80,125),200,hp,6,RED)
	_text(Vector2(315,112),"Resolve  %d / 100"%stamina,18,TEAL)
	_bar(Vector2(315,125),255,stamina,100,TEAL)
	var state_label := "Approaching" if boss_stage=="approach" else ("Open for a counter" if boss_stage=="recover" else "Veil fracture" if boss_stage=="transition" else pattern.to_upper()+" / "+boss_stage.to_upper())
	_text(Vector2(80,706),state_label,20,AMBER)
	_text(Vector2(80,742),"WASD move    J strike    K seal    Space dodge    Esc pause",16,Color("aab6cb"))
	if feedback_time > 0: _text(Vector2(420,706),feedback,17,TEAL)

func _draw_overlay() -> void:
	draw_rect(Rect2(220,210,840,385),Color(INK,0.94))
	draw_rect(Rect2(220,210,840,385),Color("50617b"),false,2)
	if help_panel.visible: return
	var title := "The bell has stopped." if mode=="victory" else "The Warden holds the gate." if mode=="defeat" else "Trial paused." if mode=="paused" else "The Bell Warden."
	_text(Vector2(290,279),title,36,WHITE)
	if mode=="title":
		_text(Vector2(290,325),"Break the Warden's guard and cross the Veil gate.",22,AMBER)
		_text(Vector2(290,365),"Warnings lock before impact. Dodge, then punish recovery.",20)
		_text(Vector2(290,401),"Seals pressure the ward; blade counters exploit the open core.",20)
		_text(Vector2(290,445),"At half health, charges leave a second threat. Watch the echo.",20)
	elif mode=="paused":
		_text(Vector2(290,335),"The encounter is frozen. Resume when you are ready.",22)
	else:
		_text(Vector2(290,335),"Time %.1fs   |   Hits %s   |   Ward breaks %s   |   Dodges %s"%[elapsed,stats.hits,stats.breaks,stats.dodges],20,TEAL)
		_text(Vector2(290,380),"Damage taken %s / 6   |   Both phases share the same fight."%stats.damage_taken,20)
		_text(Vector2(290,425),"The Veil gate opens. The courtyard falls quiet." if mode=="victory" else "Regroup at the arch. Read the next warning before committing.",18,Color("aab6cb"))
