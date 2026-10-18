extends RefCounted
## Original code-drawn actors and event-owned gestures. Never changes combat state.
const Combat = preload("res://combat.gd")
const INK := Color("101b2b")
const PAPER := Color("e9eddf")
const TEAL := Color("5ae0ce")
const AMBER := Color("ffc474")
const RED := Color("ff796f")
var model
var cursor := 0
var last_time := 0.0
var last_player := Vector2.ZERO
var last_strike := 0.0
var stride := 0.0
var moving := false
var action := "idle"
var action_left := 0.0
var action_length := 0.0
var action_dir := Vector2.RIGHT
var contact := ""
var contact_left := 0.0
var contact_at := Vector2.ZERO
var contact_angle := 0.0
var hurt_left := 0.0
var courier_hurt_left := 0.0
var sentinel_left := 0.0

func attach(game) -> void:
	model=game;cursor=game.events.size();last_time=game.elapsed;last_player=game.player
	last_strike=game.strike_cooldown;stride=0;moving=false
	action="idle";action_left=0;action_length=0;contact="";contact_left=0;contact_angle=0
	hurt_left=0;courier_hurt_left=0;sentinel_left=0

func gesture(name: String, duration: float, direction: Vector2) -> void:
	action=name;action_left=duration;action_length=duration;action_dir=direction

func observe(game) -> void:
	if model!=game or game.elapsed<last_time or game.events.size()<cursor:
		attach(game);return
	# Simulation time owns animation. Pause, review and redraw alone cannot age a pose.
	var dt: float=maxf(0,game.elapsed-last_time)
	action_left=maxf(0,action_left-dt);contact_left=maxf(0,contact_left-dt)
	hurt_left=maxf(0,hurt_left-dt);courier_hurt_left=maxf(0,courier_hurt_left-dt);sentinel_left=maxf(0,sentinel_left-dt)
	var distance: float=game.player.distance_to(last_player)
	moving=distance>0.001 if dt>0 else moving
	if dt>0:stride=fmod(stride+distance/26.0,TAU)
	# A blade request can spend resolve but miss. The cooldown edge is acceptance,
	# while only a real counter event receives contact/recoil feedback.
	if game.strike_cooldown>last_strike:
		gesture("blade",0.32,game.facing)
	for i in range(cursor,game.events.size()):
		var kind: String=game.events[i].kind
		if kind=="step":gesture("step",0.20,game.step_dir)
		elif kind=="redirect":gesture("draw",0.36,(Combat.ENEMY-game.player).normalized())
		elif kind=="counter":
			gesture("counter",0.32,(Combat.ENEMY-game.player).normalized());sentinel_left=0.24
		if kind in ["protected","counter","bolt_hit","pulse_hit","courier_hit"]:
			contact=kind;contact_left=0.24;contact_angle=(Combat.ENEMY-game.player).angle()
			contact_at=game.courier if kind=="courier_hit" else (Combat.ENEMY if kind=="counter" else game.player)
			if kind in ["bolt_hit","pulse_hit"]:hurt_left=0.24
			elif kind=="courier_hit":courier_hurt_left=0.24
	last_time=game.elapsed;last_player=game.player;last_strike=game.strike_cooldown;cursor=game.events.size()

func pose(game) -> String:
	if game.step_left>0:return "step"
	if game.guard:return "guard_"+game.guard_state().to_lower()
	if action_left>0:return action
	return "walk" if moving else "idle"

func snapshot(game) -> Dictionary:
	return {"pose":pose(game),"action":action if action_left>0 else "idle",
		"action_left":snappedf(action_left,0.000001),"stride":snappedf(stride,0.000001),
		"contact":contact if contact_left>0 else "","contact_left":snappedf(contact_left,0.000001),"contact_angle":snappedf(contact_angle,0.000001),
		"hurt_left":snappedf(hurt_left,0.000001),"courier_hurt_left":snappedf(courier_hurt_left,0.000001),
		"sentinel_left":snappedf(sentinel_left,0.000001),"cursor":cursor}

static func polygon(canvas, points: Array, color: Color) -> void:
	var shape=PackedVector2Array(points)
	canvas.draw_colored_polygon(shape,color)
	shape.append(shape[0]);canvas.draw_polyline(shape,INK,2.0,true)

func draw_player(canvas, game) -> void:
	var broad: bool=game.role=="Guardian"
	var color: Color=TEAL if broad else AMBER
	var state: String=pose(game)
	var forward: Vector2=game.locked_face if game.guard else game.facing
	var side:=forward.orthogonal()
	var at: Vector2=game.player
	var gait: float=sin(stride)*4 if moving and game.step_left<=0 else 0.0
	if hurt_left>0:at-=forward*(hurt_left/0.24)*4
	canvas.draw_set_transform(at,forward.angle())
	canvas.draw_circle(Vector2(0,7),25,Color(0,0,0,0.28))
	# Feet separate under actual displacement; the Guardian has a wider planted base.
	for sign in [-1,1]:
		canvas.draw_line(Vector2(-8,sign*(12 if broad else 9)),Vector2(-13+gait*sign,sign*(18 if broad else 16)),INK,9,true)
		canvas.draw_line(Vector2(-8,sign*(12 if broad else 9)),Vector2(-13+gait*sign,sign*(18 if broad else 16)),PAPER,3,true)
	if broad:
		polygon(canvas,[Vector2(-22,-19),Vector2(5,-21),Vector2(18,-12),Vector2(18,12),Vector2(5,21),Vector2(-22,19),Vector2(-16,0)],Color("286c70"))
		canvas.draw_line(Vector2(-9,-18),Vector2(3,18),color,5,true)
		for sign in [-1,1]:canvas.draw_circle(Vector2(4,sign*17),7,color)
	else:
		polygon(canvas,[Vector2(-26,-16),Vector2(8,-13),Vector2(14,0),Vector2(8,13),Vector2(-26,16),Vector2(-15,0)],Color("8a6242"))
		canvas.draw_line(Vector2(-18,-11),Vector2(7,-8),color,4,true)
		canvas.draw_line(Vector2(-18,11),Vector2(7,8),color,4,true)
	canvas.draw_circle(Vector2(6,0),9,INK)
	canvas.draw_circle(Vector2(7,0),6,PAPER)
	canvas.draw_line(Vector2(11,-4),Vector2(11,4),color,3,true)
	if broad:
		var shield_x: float=26 if game.guard else 1
		var shield_y: float=0 if game.guard else -23
		var shield_color: Color=RED if state=="guard_stale" else (color if game.guards_from(Combat.ENEMY) else Color("90aca7"))
		var p:=Vector2(shield_x,shield_y)
		polygon(canvas,[p+Vector2(-5,-17),p+Vector2(4,-20),p+Vector2(11,-9),p+Vector2(11,9),p+Vector2(4,20),p+Vector2(-5,17)],shield_color)
		canvas.draw_line(p+Vector2(3,-11),p+Vector2(3,11),PAPER,2,true)
	# Reset before weapon gestures; these use a fixed action direction at acceptance.
	canvas.draw_set_transform(at)
	var weapon_dir: Vector2=action_dir if state in ["blade","counter","draw"] else forward
	var angle: float=weapon_dir.angle()
	if state in ["blade","counter"]:
		var u: float=1-action_left/action_length
		# Instant model contact starts directed at the target, then recovers.
		angle+=0.65*u if state=="counter" else lerpf(-0.9,0.65,clampf(u*1.6,0,1))
	elif state=="draw":angle-=0.9*sin(PI*(1-action_left/action_length))
	var hand: Vector2=Vector2.from_angle(angle)*19+side*12
	var tip: Vector2=hand+Vector2.from_angle(angle)*(30 if broad else 39)
	canvas.draw_line(side*10,hand,color,5,true)
	canvas.draw_line(hand,tip,INK,5,true);canvas.draw_line(hand,tip,PAPER,2,true)
	canvas.draw_line(hand-Vector2.from_angle(angle).orthogonal()*5,hand+Vector2.from_angle(angle).orthogonal()*5,color,3,true)
	if state=="draw":canvas.draw_arc(Vector2.ZERO,31,angle-0.5,angle+0.5,14,AMBER,2,true)
	if state=="step":
		for sign in [-1,1]:canvas.draw_line(-game.step_dir*40+game.step_dir.orthogonal()*sign*12,-game.step_dir*20+game.step_dir.orthogonal()*sign*12,color,2,true)
	canvas.draw_set_transform(Vector2.ZERO)

func draw_courier(canvas, game) -> void:
	var at: Vector2=game.courier
	var stride_y: float=sin(game.elapsed*9)*3 if game.mode!="title" else 0
	canvas.draw_circle(at+Vector2(0,8),19,Color(0,0,0,0.28))
	for sign in [-1,1]:canvas.draw_line(at+Vector2(-4,sign*9),at+Vector2(-12+stride_y*sign,sign*14),INK,6,true)
	polygon(canvas,[at+Vector2(-15,-13),at+Vector2(8,-13),at+Vector2(17,0),at+Vector2(8,13),at+Vector2(-15,13)],Color("756347"))
	canvas.draw_rect(Rect2(at+Vector2(-13,-9),Vector2(14,18)),AMBER,false,2)
	canvas.draw_circle(at+Vector2(10,0),6,PAPER)
	if courier_hurt_left>0:canvas.draw_arc(at,24,-0.8,0.8,12,RED,3,true)

func draw_sentinel(canvas, game) -> void:
	var at: Vector2=Combat.ENEMY
	if sentinel_left>0:at+=(Combat.ENEMY-game.player).normalized()*5*sentinel_left/0.24
	var opened: bool=game.opening>0
	var charging: bool=game.phase in ["bolt","pulse"]
	var color: Color=TEAL if opened else RED
	canvas.draw_circle(at+Vector2(0,12),30,Color(0,0,0,0.3))
	for offset in [Vector2(-29,22),Vector2(29,22),Vector2(0,-32)]:
		canvas.draw_line(at+offset*0.5,at+offset,Color("697b82"),7,true)
		canvas.draw_circle(at+offset,4,PAPER)
	var gap: float=9 if opened else 0
	polygon(canvas,[at+Vector2(-23-gap,-17),at+Vector2(-3-gap,-30),at+Vector2(-3-gap,24),at+Vector2(-23-gap,9)],Color("794c50"))
	polygon(canvas,[at+Vector2(23+gap,-17),at+Vector2(3+gap,-30),at+Vector2(3+gap,24),at+Vector2(23+gap,9)],Color("794c50"))
	canvas.draw_line(at+Vector2(0,-17),at+Vector2(0,13),color,4,true)
	if charging:
		var size: float=6+clampf(game.clock,0,1)*9
		if game.phase=="bolt":
			canvas.draw_line(at+Vector2(-size,0),at+Vector2(size,0),AMBER,3,true)
			canvas.draw_line(at+Vector2(0,-size),at+Vector2(0,size),AMBER,3,true)
		else:canvas.draw_arc(at,size,0,TAU,24,RED,3,true)

func draw_contact(canvas) -> void:
	if contact_left<=0:return
	var size: float=17+(1-contact_left/0.24)*14
	var color: Color=TEAL if contact=="protected" else (PAPER if contact=="counter" else RED)
	# Small local marks, no full-screen flashes, camera shake or random particles.
	if contact=="protected":
		canvas.draw_arc(contact_at,size,contact_angle-0.7,contact_angle+0.7,16,color,3,true)
	elif contact=="counter":
		for angle in [0.0,PI/2,PI,PI*1.5]:
			var direction:=Vector2.from_angle(angle+PI/4)
			canvas.draw_line(contact_at+direction*(size-5),contact_at+direction*(size+3),color,2,true)
	else:
		for sign in [-1,1]:canvas.draw_line(contact_at+Vector2(-size/2,sign*size/2),contact_at+Vector2(size/2,-sign*size/2),color,2,true)
