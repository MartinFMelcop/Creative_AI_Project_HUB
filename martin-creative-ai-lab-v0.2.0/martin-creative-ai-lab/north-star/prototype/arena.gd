extends Node2D
const Combat = preload("res://combat.gd")
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
	queue_redraw()

func _notification(what: int) -> void:
	if what==NOTIFICATION_APPLICATION_FOCUS_OUT and game.mode=="play":
		game.mode="paused"
		taps.clear()

func _unhandled_key_input(event: InputEvent) -> void:
	if not event is InputEventKey or not event.pressed or event.echo: return
	if event.physical_keycode==KEY_F12:
		capture()
	if event.physical_keycode==KEY_ENTER:
		if game.mode in ["title","lost","won"]: game.reset(selected)
		elif game.mode=="paused": game.mode="play"
	if event.physical_keycode==KEY_ESCAPE:
		if game.mode=="play": game.mode="paused"
		elif game.mode=="paused": game.mode="play"
	if event.physical_keycode==KEY_R and game.mode!="play":
		game=Combat.new()
		game.role=selected
		taps.clear()
	if game.mode=="title":
		if event.physical_keycode==KEY_1: selected="Guardian";game.role=selected
		if event.physical_keycode==KEY_2: selected="Duelist";game.role=selected
	if event.physical_keycode==KEY_J: taps.strike=true
	if event.physical_keycode==KEY_K: taps.skill_pressed=true
	if event.physical_keycode==KEY_SPACE: taps.dodge=true
	queue_redraw()

func vector_keys(left: int, right: int, up: int, down: int) -> Vector2:
	return Vector2(float(Input.is_physical_key_pressed(right))-float(Input.is_physical_key_pressed(left)),float(Input.is_physical_key_pressed(down))-float(Input.is_physical_key_pressed(up)))

func _physics_process(dt: float) -> void:
	var command: Dictionary=taps.duplicate()
	command.move=vector_keys(KEY_A,KEY_D,KEY_W,KEY_S)
	command.aim=vector_keys(KEY_LEFT,KEY_RIGHT,KEY_UP,KEY_DOWN)
	command.skill=Input.is_physical_key_pressed(KEY_K)
	game.step(dt,command)
	taps.clear()
	queue_redraw()

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
	for x in [400,700,1000]:
		draw_line(Vector2(x,350),Vector2(x,430),AMBER if game.courier.x>=x else Color("6c777b"),4)
		text(Vector2(x-35,458),"GATE" if x==1000 else "MARK",14)
	if game.phase=="bolt":
		var width: float=3+game.clock*8
		draw_line(Combat.ENEMY,game.target,Color(1,0.75,0.4,0.25+game.clock*0.5),width)
		draw_arc(game.target,26,0,TAU,24,AMBER,2)
		text(game.target+Vector2(-50,-38),"LOCKED BOLT",14,AMBER)
	if game.phase=="pulse":
		draw_circle(game.pulse,90,Color(1,0.3,0.3,0.18+game.clock*0.22))
		draw_arc(game.pulse,90,0,TAU,48,RED,3)
		text(game.pulse+Vector2(-55,-106),"GROUND PULSE",15,RED)
	# The sentinel's silhouette and name stay separate from the courier's parcel.
	draw_colored_polygon(PackedVector2Array([Combat.ENEMY+Vector2(0,-36),Combat.ENEMY+Vector2(31,5),Combat.ENEMY+Vector2(0,32),Combat.ENEMY+Vector2(-31,5)]),RED)
	text(Combat.ENEMY+Vector2(-42,-50),"SENTINEL",15,RED)
	if game.role=="Duelist": draw_arc(Combat.ENEMY,340,0,TAU,80,Color(1,0.77,0.45,0.18),1)
	if game.opening>0: text(Combat.ENEMY+Vector2(-27,60),"OPEN",19,TEAL)
	draw_circle(game.courier,14,AMBER)
	draw_rect(Rect2(game.courier+Vector2(-11,-10),Vector2(22,18)),Color("756347"),false,2)
	text(game.courier+Vector2(-35,40),"COURIER",14,AMBER)
	var c: Color=TEAL if game.role=="Guardian" else AMBER
	draw_circle(game.player+Vector2(0,7),22,Color(0,0,0,0.35))
	if game.role=="Guardian":
		draw_colored_polygon(PackedVector2Array([game.player+Vector2(-18,-20),game.player+Vector2(18,-20),game.player+Vector2(24,14),game.player+Vector2(0,25),game.player+Vector2(-24,14)]),c)
	else:
		draw_colored_polygon(PackedVector2Array([game.player+Vector2(0,-25),game.player+Vector2(17,17),game.player+Vector2(0,9),game.player+Vector2(-17,17)]),c)
	draw_line(game.player,game.player+game.facing*38,PAPER,3)
	if game.guard:
		var angle: float=game.locked_face.angle()
		draw_arc(game.player,37,angle-0.9,angle+0.9,24,TEAL if game.guards_from(Combat.ENEMY) else AMBER,7)
	if game.step_left>0: draw_line(game.player-game.step_dir*70,game.player,c,8)
	text(game.player+Vector2(-20,47 if game.player.y<245 else -38),"YOU",14,c)
	draw_header()
	panel(Rect2(30,662,1092,86))
	text(Vector2(48,686),"WASD move   •   ARROWS aim   •   J blade   •   K "+("hold guard" if game.role=="Guardian" else "feint bolt")+"   •   SPACE step   •   ESC pause",17)
	text(Vector2(48,718),game.message,17,AMBER if game.message_left>0 else PAPER)
	if game.mode!="play": overlay()

func draw_header() -> void:
	draw_rect(Rect2(0,0,1152,174),INK)
	text(Vector2(40,42),"VIRGO DIAMOND / CROSSING DRILL",25)
	text(Vector2(40,70),"LOCAL EXPERIMENT  •  Keep the courier alive to the far gate",16,AMBER)
	text(Vector2(40,110),game.role.to_upper()+"  /  HEALTH "+str(game.hp)+"   COURIER "+str(game.cargo),19)
	draw_rect(Rect2(40,130,300,12),Color("32475a"))
	draw_rect(Rect2(40,130,300*game.energy/100,12),TEAL if game.role=="Guardian" else AMBER)
	text(Vector2(355,142),"POSTURE" if game.role=="Guardian" else "RESOLVE",15)
	var progress: float=(game.courier.x-160)/(1000-160)
	text(Vector2(750,111),"CROSSING  %d%%"%roundi(progress*100),19)
	draw_rect(Rect2(750,130,350,12),Color("32475a"))
	draw_rect(Rect2(750,130,350*progress,12),AMBER)

func overlay() -> void:
	draw_rect(Rect2(40,176,1072,473),Color(0.03,0.07,0.12,0.90))
	if game.mode=="title":
		text(Vector2(210,231),"One crossing. Two ways to hold the line.",30)
		text(Vector2(210,266),"The courier keeps moving. Three impacts lose the crossing.",19)
		panel(Rect2(180,292,380,212),Color("244a50") if selected=="Guardian" else Color("1b2d40"))
		panel(Rect2(590,292,380,212),Color("594730") if selected=="Duelist" else Color("1b2d40"))
		text(Vector2(205,330),"1  GUARDIAN",26,TEAL)
		text(Vector2(205,370),"Stand between bolt and courier.",19)
		text(Vector2(205,400),"Aim at sentinel, hold K to block.",19)
		text(Vector2(205,430),"Guard drains posture; release to recover.",17)
		text(Vector2(205,467),"Slow protection • reachable counters",17,TEAL)
		text(Vector2(615,330),"2  DUELIST",26,AMBER)
		text(Vector2(615,370),"K during a bolt warning draws its aim.",18)
		text(Vector2(615,400),"Move or step away from the locked line.",18)
		text(Vector2(615,430),"Feint within the ring; steps cost resolve.",17)
		text(Vector2(615,467),"Risky redirection • faster movement step",17,AMBER)
		text(Vector2(210,543),"Both: leave red ground pulses. Strike only when OPEN and close.",19)
		text(Vector2(210,585),"ENTER  Begin as "+selected+"     /     experimental approaches, not final classes",19,TEAL)
	elif game.mode=="paused":
		text(Vector2(280,330),"Crossing paused",36)
		text(Vector2(280,385),"ENTER / ESC resume     •     R abandon and choose",22)
		text(Vector2(280,430),"Guard faces the direction locked when K was first held.",19)
		text(Vector2(280,465),"Release K before turning. Steps move; they grant no immunity.",19)
	else:
		text(Vector2(250,290),"THE COURIER CROSSED" if game.mode=="won" else "THE LINE BROKE",36,TEAL if game.mode=="won" else RED)
		text(Vector2(250,345),game.role+"  /  blocks %d   drawn bolts %d   counters %d"%[game.counters.blocks,game.counters.redirects,game.counters.counters],22)
		text(Vector2(250,390),"Health %d / 5    Courier %d / 3    Crossing %d%%"%[game.hp,game.cargo,roundi((game.courier.x-160)/840*100)],21)
		text(Vector2(250,440),"Crossing token: "+("Held the line" if game.role=="Guardian" else "Drew the danger") if game.mode=="won" else "Review the impact feedback and try the other approach.",20,AMBER)
		text(Vector2(250,510),"ENTER retry this approach     •     R choose approach",22)
		text(Vector2(250,552),"Result lasts for this session.",18)

func capture() -> void:
	var path := OS.get_environment("CROSSING_CAPTURE")
	if path.is_empty(): return
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(path)
	var file=FileAccess.open(path+".json",FileAccess.WRITE)
	file.store_string(JSON.stringify(game.snapshot(),"  ")+"\n")
