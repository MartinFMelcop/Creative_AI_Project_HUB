extends Node2D
const Combat = preload("res://combat.gd")
const Rehearsal = preload("res://rehearsal.gd")
const Keepsakes = preload("res://keepsakes.gd")
const Errand = preload("res://errand.gd")
const KEEPSAKE_NAMES := {"":"None", "held_line":"Held the Line", "drew_danger":"Drew the Danger"}
var keepsakes = Keepsakes.new()
var profile_path := ""
var normal_run := false
var reward_checked := false
var reward_message := ""
var errand = Errand.new()
var rehearsal = Rehearsal.new()
var game = Combat.new()
var selected := "Guardian"
var taps := {}
var font = ThemeDB.fallback_font
const INK := Color("101b2b")
const PAPER := Color("e9eddf")
const TEAL := Color("5ae0ce")
const AMBER := Color("ffc474")
const RED := Color("ff796f")

func _ready() -> void:
	if profile_path.is_empty(): profile_path=OS.get_environment("CROSSING_PROFILE")
	if profile_path.is_empty(): profile_path="user://crossing-keepsakes.json"
	keepsakes.load_profile(profile_path)
	queue_redraw()

func abandon() -> void:
	errand=Errand.new()
	normal_run=false
	reward_checked=false
	reward_message=""
	rehearsal = Rehearsal.new()
	game = Combat.new()
	game.role = selected
	taps.clear()

func begin_crossing() -> void:
	errand.reset()
	normal_run=true
	reward_checked=false
	reward_message=""
	rehearsal.active = false
	game = Combat.new()
	game.reset(selected)
	taps.clear()

func _notification(what: int) -> void:
	if what==NOTIFICATION_APPLICATION_FOCUS_OUT:
		if rehearsal.active:
			if rehearsal.state=="live" and not rehearsal.paused: rehearsal.toggle_pause()
		elif game.mode=="play": game.mode="paused"
		taps.clear()

func _unhandled_key_input(event: InputEvent) -> void:
	if not event is InputEventKey or not event.pressed or event.echo: return
	var key: int = event.physical_keycode
	if key==KEY_F12: capture()
	if not rehearsal.active and game.mode!="play":
		if key==KEY_C: keepsakes.cycle_equipped()
		elif key==KEY_F5: keepsakes.retry_save()
	if rehearsal.active:
		if key==KEY_ESCAPE: rehearsal.toggle_pause(); taps.clear()
		elif key==KEY_R and (rehearsal.paused or rehearsal.state!="live"): abandon()
		elif key==KEY_ENTER:
			if rehearsal.paused: rehearsal.toggle_pause()
			elif rehearsal.confirm(): begin_crossing()
			if rehearsal.active: game=rehearsal.game
			taps.clear()
		elif key==KEY_T and rehearsal.state!="live": rehearsal.repeat(); game=rehearsal.game; taps.clear()
	else:
		if key==KEY_ENTER:
			if game.mode in ["title","lost","won"]: begin_crossing()
			elif game.mode=="paused": game.mode="play"; taps.clear()
		elif key==KEY_ESCAPE:
			if game.mode=="play": game.mode="paused"
			elif game.mode=="paused": game.mode="play"
			taps.clear()
		elif key==KEY_R and game.mode!="play": abandon()
		elif game.mode=="title":
			if key==KEY_1: selected="Guardian"; game.role=selected
			elif key==KEY_2: selected="Duelist"; game.role=selected
			elif key==KEY_T: rehearsal.start(selected); game=rehearsal.game; taps.clear()
	if game.mode=="play":
		if key==KEY_J: taps.strike=true
		if key==KEY_K: taps.skill_pressed=true
		if key==KEY_SPACE: taps.dodge=true
	queue_redraw()

func key_down(code: int, physical: bool) -> bool:
	return Input.is_physical_key_pressed(code) if physical else Input.is_key_pressed(code)

func vector_keys(left: int, right: int, up: int, down: int, physical: bool=true) -> Vector2:
	return Vector2(float(key_down(right,physical))-float(key_down(left,physical)),float(key_down(down,physical))-float(key_down(up,physical)))

func _physics_process(dt: float) -> void:
	var command: Dictionary=taps.duplicate()
	command.move=vector_keys(KEY_A,KEY_D,KEY_W,KEY_S)
	# Navigation keys carry logical identity; WASD keeps physical keyboard positions.
	command.aim=vector_keys(KEY_LEFT,KEY_RIGHT,KEY_UP,KEY_DOWN,false)
	command.skill=Input.is_physical_key_pressed(KEY_K)
	command.interact=Input.is_physical_key_pressed(KEY_E)
	if rehearsal.active: rehearsal.step(dt,command)
	else: advance_crossing(dt,command)
	taps.clear()
	queue_redraw()

func advance_crossing(dt: float, command: Dictionary) -> void:
	var previous: String=game.mode
	var effective: Dictionary=errand.prepare(game,dt,command) if normal_run else command
	game.step(dt,effective)
	if normal_run: errand.settle(game)
	if previous=="play" and game.mode=="won": settle_crossing()

func settle_crossing() -> void:
	if not normal_run or rehearsal.active or reward_checked or game.mode!="won": return
	reward_checked=true
	if game.courier.x<Combat.FINISH or game.hp<=0 or game.cargo<=0: return
	var signature: bool=game.counters.blocks>0 if game.role=="Guardian" else game.counters.redirects>0
	var id: String="held_line" if game.role=="Guardian" else "drew_danger"
	if not signature:
		reward_message="To earn "+KEEPSAKE_NAMES[id]+", cross with at least one "+("block." if game.role=="Guardian" else "drawn bolt.")
		return
	var fresh: bool=keepsakes.earn(game.role)
	reward_message=("Earned: " if fresh else "Already earned: ")+KEEPSAKE_NAMES[id]+". C to wear / put away."

func draw_keepsake(at: Vector2, id: String, scale_factor: float=1.0) -> void:
	if id.is_empty(): return
	var points: PackedVector2Array
	if id=="held_line":
		points=PackedVector2Array([Vector2(-10,-9),Vector2(10,-9),Vector2(8,5),Vector2(0,12),Vector2(-8,5)])
	else:
		points=PackedVector2Array([Vector2(-12,7),Vector2(-3,-10),Vector2(0,-3),Vector2(10,-12),Vector2(8,2),Vector2(1,10),Vector2(0,3)])
	for i in points.size(): points[i]=at+points[i]*scale_factor
	draw_colored_polygon(points,INK)
	var outline=points.duplicate();outline.append(points[0])
	draw_polyline(outline,PAPER,2*scale_factor)
	if id=="held_line": draw_line(at+Vector2(0,-5)*scale_factor,at+Vector2(0,6)*scale_factor,TEAL,3*scale_factor)
	else: draw_line(at+Vector2(-5,5)*scale_factor,at+Vector2(5,-5)*scale_factor,AMBER,3*scale_factor)

func text(at: Vector2, value: String, size: int=18, color: Color=PAPER) -> void:
	draw_string(font,at,value,HORIZONTAL_ALIGNMENT_LEFT,-1,size,color)

func panel(rect: Rect2, color: Color=Color("1b2d40")) -> void:
	draw_style_box(style(color),rect)

func style(color: Color) -> StyleBoxFlat:
	var box=StyleBoxFlat.new()
	box.bg_color=color
	box.corner_radius_top_left=10
	box.corner_radius_top_right=10
	box.corner_radius_bottom_left=10
	box.corner_radius_bottom_right=10
	return box

func _draw() -> void:
	draw_rect(Rect2(0,0,1152,768),INK)
	draw_rect(Combat.FIELD,Color("172f3b"))
	for x in range(80,1100,55): draw_line(Vector2(x,185),Vector2(x,645),Color("203e49"),1)
	for y in range(200,650,55): draw_line(Vector2(50,y),Vector2(1102,y),Color("203e49"),1)
	draw_rect(Rect2(50,355,1052,70),Color("35454a"))
	draw_line(Vector2(70,390),Vector2(1080,390),Color("718282"),2)
	if errand.active and not rehearsal.active: draw_errand()
	for x in [400,700,1000]:
		draw_line(Vector2(x,350),Vector2(x,430),AMBER if game.courier.x>=x else Color("6c777b"),4)
		text(Vector2(x-35,458),"GATE" if x==1000 else "MARK",14)
	var reviewing: bool=rehearsal.active and rehearsal.state=="review"
	if game.phase=="bolt" or (reviewing and rehearsal.stage==0):
		var width: float=3+game.clock*8
		draw_line(Combat.ENEMY,game.target,Color(1,0.75,0.4,0.25+game.clock*0.5),width)
		draw_arc(game.target,26,0,TAU,24,AMBER,2)
		var label=game.target+Vector2(-50,-76 if game.target.distance_to(game.player)<80 else -38)
		label.y=maxf(200,label.y)
		text(label,"LAST LOCKED LINE" if reviewing else "LOCKED BOLT",14,AMBER)
	if game.phase=="pulse" or (reviewing and rehearsal.stage==1):
		draw_circle(game.pulse,90,Color(1,0.3,0.3,0.18+game.clock*0.22))
		draw_arc(game.pulse,90,0,TAU,48,RED,3)
		text(game.pulse+Vector2(-55,-106),"LAST PULSE" if reviewing else "GROUND PULSE",15,RED)
	# The sentinel's silhouette and name stay separate from the courier's parcel.
	draw_colored_polygon(PackedVector2Array([Combat.ENEMY+Vector2(0,-36),Combat.ENEMY+Vector2(31,5),Combat.ENEMY+Vector2(0,32),Combat.ENEMY+Vector2(-31,5)]),RED)
	text(Combat.ENEMY+Vector2(-42,-50),"SENTINEL",15,RED)
	if game.role=="Duelist": draw_arc(Combat.ENEMY,340,0,TAU,80,Color(1,0.77,0.45,0.18),1)
	if game.opening>0:
		draw_arc(Combat.ENEMY,130,0,TAU,64,TEAL,2)
		text(Combat.ENEMY+Vector2(-53,60),"OPEN %.1fs"%game.opening,19,TEAL)
	draw_circle(game.courier,14,AMBER)
	draw_rect(Rect2(game.courier+Vector2(-11,-10),Vector2(22,18)),Color("756347"),false,2)
	text(game.courier+Vector2(-35,40),"COURIER",14,AMBER)
	var c: Color=TEAL if game.role=="Guardian" else AMBER
	draw_circle(game.player+Vector2(0,7),22,Color(0,0,0,0.35))
	if game.role=="Guardian":
		draw_colored_polygon(PackedVector2Array([game.player+Vector2(-18,-20),game.player+Vector2(18,-20),game.player+Vector2(24,14),game.player+Vector2(0,25),game.player+Vector2(-24,14)]),c)
	else:
		draw_colored_polygon(PackedVector2Array([game.player+Vector2(0,-25),game.player+Vector2(17,17),game.player+Vector2(0,9),game.player+Vector2(-17,17)]),c)
	draw_keepsake(game.player,keepsakes.equipped)
	# Keep the facing cue outside the body so it cannot obscure a worn mark.
	draw_line(game.player+game.facing*26,game.player+game.facing*42,PAPER,3)
	if game.guard:
		var angle: float=game.locked_face.angle()
		draw_arc(game.player,37,angle-0.9,angle+0.9,24,TEAL if game.guards_from(Combat.ENEMY) else AMBER,7)
	if game.step_left>0: draw_line(game.player-game.step_dir*70,game.player,c,8)
	text(game.player+Vector2(-20,47 if game.player.y<245 else -38),"YOU",14,c)
	draw_header()
	panel(Rect2(30,662,1092,86))
	text(Vector2(48,686),"WASD move   •   ARROWS aim   •   J blade   •   K "+("hold guard" if game.role=="Guardian" else "feint bolt")+"   •   SPACE step   •   ESC pause",17)
	text(Vector2(48,718),footer(),17,AMBER)
	if rehearsal.active: rehearsal_overlay()
	elif game.mode!="play": overlay()

func draw_header() -> void:
	draw_rect(Rect2(0,0,1152,174),INK)
	text(Vector2(40,42),"VIRGO DIAMOND / "+("REHEARSAL" if rehearsal.active else "CROSSING DRILL"),25)
	text(Vector2(40,70),("%d / 3  %s  •  "%[rehearsal.stage+1,rehearsal.heading()]+rehearsal.instruction()) if rehearsal.active else (errand.hint() if errand.active else "LOCAL EXPERIMENT  •  Keep the courier alive to the far gate"),16,AMBER)
	text(Vector2(40,110),game.role.to_upper()+"  /  HEALTH "+str(game.hp)+"   COURIER "+str(game.cargo),19)
	draw_rect(Rect2(40,130,300,12),Color("32475a"))
	draw_rect(Rect2(40,130,300*game.energy/100,12),TEAL if game.role=="Guardian" else AMBER)
	text(Vector2(355,142),"POSTURE" if game.role=="Guardian" else "RESOLVE",15)
	var progress: float=(game.courier.x-160)/(1000-160)
	text(Vector2(750,111),("PAUSED" if rehearsal.paused else ("RESPONSE VERIFIED" if rehearsal.passed else rehearsal.state.to_upper())) if rehearsal.active else "CROSSING  %d%%"%roundi(progress*100),19)
	draw_rect(Rect2(750,130,350,12),Color("32475a"))
	draw_rect(Rect2(750,130,350*((rehearsal.stage+int(rehearsal.passed))/3.0 if rehearsal.active else progress),12),AMBER)

	text(Vector2(40,164),"WORN  /  "+KEEPSAKE_NAMES[keepsakes.equipped]+"  •  cosmetic only",14)
	text(Vector2(750,164),"LOCAL SAVE PENDING" if keepsakes.dirty or keepsakes.blocked else "THIS DEVICE'S KEEPSAKES",14,AMBER)

func overlay() -> void:
	draw_rect(Rect2(40,176,1072,473),Color(0.03,0.07,0.12,0.90))
	if game.mode=="title":
		text(Vector2(210,231),"One crossing. Two ways to hold the line.",30)
		text(Vector2(140,266),"Courier keeps moving. At MARK 1, optional medicine falls south of the road.",19)
		panel(Rect2(180,292,380,212),Color("244a50") if selected=="Guardian" else Color("1b2d40"))
		panel(Rect2(590,292,380,212),Color("594730") if selected=="Duelist" else Color("1b2d40"))
		text(Vector2(205,330),"1  GUARDIAN",26,TEAL)
		text(Vector2(205,370),"Stand between bolt and courier.",19)
		text(Vector2(205,400),"Aim at sentinel, hold K to block.",19)
		text(Vector2(205,430),"Guard drains posture; release to recover.",17)
		text(Vector2(205,467),"Cross + block: Held the Line",17,TEAL)
		text(Vector2(615,330),"2  DUELIST",26,AMBER)
		text(Vector2(615,370),"K during a bolt warning draws its aim.",18)
		text(Vector2(615,400),"Move or step away from the locked line.",18)
		text(Vector2(615,430),"Feint within the ring; steps cost resolve.",17)
		text(Vector2(615,467),"Cross + draw: Drew the Danger",17,AMBER)
		text(Vector2(210,543),"Both: leave red ground pulses. Strike only when OPEN and close.",19)
		text(Vector2(210,580),"T  Rehearse as "+selected+"     •     ENTER  Skip to crossing",21,TEAL)
		text(Vector2(210,615),"C  Keepsake: "+KEEPSAKE_NAMES[keepsakes.equipped]+"     /     experimental, cosmetic only",17)
		draw_keepsake(Vector2(1015,602),keepsakes.equipped,1.4)
	elif game.mode=="paused":
		text(Vector2(280,330),"Crossing paused",36)
		text(Vector2(280,385),"ENTER / ESC resume     •     R abandon and choose",22)
		text(Vector2(280,430),("Guard faces the direction locked when K was first held." if game.role=="Guardian" else "K draws an amber bolt only inside the sentinel's ring."),19)
		text(Vector2(280,465),("Release K before turning. Steps move; they grant no immunity." if game.role=="Guardian" else "Leave the drawn line. Steps move; they grant no immunity."),19)
		draw_impact(Vector2(130,530))
		text(Vector2(130,617),"Optional case: hold E nearby to recover, then E near courier to hand over. Neither waits.",17,AMBER)
	else:
		text(Vector2(250,290),"THE COURIER CROSSED" if game.mode=="won" else "THE LINE BROKE",36,TEAL if game.mode=="won" else RED)
		text(Vector2(250,345),game.role+"  /  blocks %d   drawn bolts %d   counters %d"%[game.counters.blocks,game.counters.redirects,game.counters.counters],22)
		text(Vector2(250,390),"Health %d / 5    Courier %d / 3    Crossing %d%%"%[game.hp,game.cargo,roundi((game.courier.x-160)/840*100)],21)
		draw_impact(Vector2(150,435))
		text(Vector2(250,510),"ENTER retry this approach     •     R choose approach",22)
		text(Vector2(150,552),reward_message if game.mode=="won" else "No keepsake earned. Complete a crossing with a block or drawn bolt.",18,TEAL if game.mode=="won" else AMBER)
		text(Vector2(150,585),"C  Wear / put away     •     F5  Retry local save     /     cosmetic only",18)
		text(Vector2(150,622),errand.outcome(),17,AMBER)

func draw_errand() -> void:
	if errand.state=="waiting": return
	if errand.state=="available":
		draw_case(Errand.CASE)
		draw_arc(Errand.CASE,Errand.RADIUS,0,TAU,32,Color(1,0.77,0.45,0.4),1)
		text(Errand.CASE+Vector2(-72,47),"MEDICINE CASE",15,AMBER)
		text(Errand.CASE+Vector2(-74,70),"Hold E  /  optional",15)
	elif errand.state=="carried":
		draw_case(game.player+Vector2(-25,15),0.55)
		draw_arc(game.courier,Errand.HANDOFF_RADIUS,0,TAU,40,Color(0.35,0.88,0.81,0.65),2)
		if not errand.channel: text(game.courier+Vector2(-75,-80),"Hold E to hand over",15,AMBER)
	elif errand.state=="delivered": draw_case(game.courier+Vector2(0,-27),0.55)
	if errand.channel:
		var duration: float=Errand.RECOVER_TIME if errand.state=="available" else Errand.HANDOFF_TIME
		draw_arc(game.player,32,-PI/2,-PI/2+TAU*errand.progress/duration,32,TEAL,4)
		text(game.player+Vector2(-50,-58),"RECOVERING" if errand.state=="available" else "HANDING OVER",14,TEAL)

func draw_case(at: Vector2, scale_factor: float=1.0) -> void:
	draw_rect(Rect2(at-Vector2(15,11)*scale_factor,Vector2(30,22)*scale_factor),INK)
	draw_rect(Rect2(at-Vector2(15,11)*scale_factor,Vector2(30,22)*scale_factor),AMBER,false,2)
	for x in [-8,0,8]:
		draw_line(at+Vector2(x,-6)*scale_factor,at+Vector2(x,6)*scale_factor,TEAL,3*scale_factor)

func footer() -> String:
	if rehearsal.active:
		if rehearsal.paused: return "ENTER / ESC resume  •  R abandon rehearsal"
		if rehearsal.state=="ready": return "ENTER send this trial  •  R choose approach  /  No time passes while you read."
		if rehearsal.state=="review": return ("ENTER "+("start the crossing" if rehearsal.stage==2 else "next exercise") if rehearsal.passed else "ENTER retry this exercise")+"  •  T repeat  •  R choose approach"
	if game.mode!="play" and (keepsakes.dirty or keepsakes.blocked): return keepsakes.status
	if game.mode=="title": return "Win with a block or drawn bolt to earn a keepsake. C chooses what you wear."
	if game.mode=="won": return keepsakes.status
	return game.message

func draw_impact(at: Vector2) -> void:
	if game.last_impact.is_empty(): return
	text(at,"LAST CONTACT  /  "+game.last_impact.explanation,18,AMBER)
	text(at+Vector2(0,32),game.last_impact.tip,18)

func rehearsal_overlay() -> void:
	if rehearsal.state=="live" and not rehearsal.paused: return
	var top: float=500 if game.player.y<350 else 195
	panel(Rect2(80,top,992,116),Color("203548"))
	var label := "READY  /  "+rehearsal.heading()
	if rehearsal.paused: label="REHEARSAL PAUSED"
	elif rehearsal.state=="review": label="RESPONSE VERIFIED" if rehearsal.passed else "TRY THIS RESPONSE AGAIN"
	text(Vector2(100,top+31),label,23,TEAL if rehearsal.passed else AMBER)
	if rehearsal.state=="review":
		if rehearsal.stage==2:
			text(Vector2(100,top+65),"Counter landed inside the opening." if rehearsal.passed else "The opening closed before a close counter landed.",19)
			text(Vector2(100,top+95),"The normal crossing uses the same range, costs and timing." if rehearsal.passed else "Walk into the OPEN ring, release guard, then press J before it closes.",18)
		else:
			text(Vector2(100,top+65),game.last_impact.explanation,19)
			text(Vector2(100,top+95),game.last_impact.tip,18)
	else:
		text(Vector2(100,top+65),rehearsal.instruction(),19)
		text(Vector2(100,top+95),"One real response at a time. Attempts can be repeated; no crossing reward is earned.",18)

func capture() -> void:
	var path := OS.get_environment("CROSSING_CAPTURE")
	if path.is_empty(): return
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(path)
	var file=FileAccess.open(path+".json",FileAccess.WRITE)
	var report=game.snapshot()
	report.last_impact=game.last_impact.duplicate(true)
	report.rehearsal=rehearsal.snapshot()
	report.keepsakes=keepsakes.snapshot()
	report.errand=errand.snapshot()
	file.store_string(JSON.stringify(report,"  ")+"\n")
