extends Node2D
## Read-only remote presentation. No Combat model, local costs or local success.
const Remote=preload("remote.gd")
const Intent=preload("intent.gd")
const INK=Color("101b2b")
const PAPER=Color("e9eddf")
const TEAL=Color("5ae0ce")
const AMBER=Color("ffc474")
const RED=Color("ff796f")
const ENEMY=Vector2(790,390)
const PULSE_RADIUS:=90.0
const OUTFITS=["standard","riveted","trail","field_sash"]
var remote=Remote.new()
var controls=Intent.new()
var port:=47620
var selected:="Guardian"
var style:="Steady"
var outfit:=0
var started:=false
var focused:=true
var clock:=0.0
var previous_status:=""
var font=ThemeDB.fallback_font
var captures:=0

func _ready() -> void:
	DisplayServer.window_set_title("Virgo Diamond — Remote Crossing")
	queue_redraw()
func connect_session() -> void:
	if started:return
	started=true
	remote.connect_session(port,selected,style if selected=="Guardian" else "none",OUTFITS[outfit])
func suspend_controls() -> void:
	controls.suspend()
	if remote.status=="live":remote.send_intent({})
func _notification(what:int) -> void:
	if what in [NOTIFICATION_APPLICATION_FOCUS_OUT,NOTIFICATION_WM_WINDOW_FOCUS_OUT]:
		focused=false;suspend_controls()
	elif what in [NOTIFICATION_APPLICATION_FOCUS_IN,NOTIFICATION_WM_WINDOW_FOCUS_IN]:focused=true
	elif what==NOTIFICATION_WM_CLOSE_REQUEST:
		remote.close();get_tree().quit()
func _input(event:InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		var key:int=event.keycode
		if key==KEY_Q:remote.close();get_tree().quit();return
		if key==KEY_F12:capture.call_deferred();return
		if not started:
			if key==KEY_F2:selected="Duelist" if selected=="Guardian" else "Guardian"
			elif key==KEY_TAB:style="Riposte" if style=="Steady" else "Steady"
			elif key==KEY_C:outfit=(outfit+1)%OUTFITS.size()
			elif key==KEY_ENTER:connect_session()
			queue_redraw();return
		if key==KEY_ESCAPE:
			if controls.suspended and focused:controls.resume()
			else:suspend_controls()
			queue_redraw();return
	controls.receive(event)
func _process(delta:float) -> void:
	if focused and controls.suspended:reconcile_releases()
	remote.poll(delta)
	if remote.status=="stale" and previous_status!="stale":suspend_controls()
	previous_status=remote.status
	clock+=delta
	if clock>=.05:
		clock=0
		if remote.can_send():
			var direction:Vector2=get_global_mouse_position()-remote.position
			# Release a server quarantine before consuming a queued local press.
			if remote.latest.quarantined:
				if not controls.suspended:controls.resume()
				remote.send_intent({})
			else:remote.send_intent(controls.command(direction.normalized()))
	queue_redraw()
func reconcile_releases() -> void:
	# Focus can hide release events. Only remove absent controls; never synthesize
	# a press or rearm from polling, including keys still held outside this window.
	for code in controls.held.keys():
		if code<0:
			if not Input.is_mouse_button_pressed(-code):
				var event=InputEventMouseButton.new();event.button_index=-code;controls.receive(event)
		elif not Input.is_physical_key_pressed(code) and not Input.is_key_pressed(code):
			var event=InputEventKey.new();event.keycode=code;event.physical_keycode=code;controls.receive(event)
func text(at:Vector2,value:String,size:int=18,color:Color=PAPER) -> void:
	draw_string(font,at,value,HORIZONTAL_ALIGNMENT_LEFT,-1,size,color)
func vec(value:Array) -> Vector2:return Vector2(value[0],value[1])
func panel(rect:Rect2) -> void:
	draw_style_box(style_box(),rect)
func style_box() -> StyleBoxFlat:
	var box=StyleBoxFlat.new();box.bg_color=Color("1c2c3b");box.border_color=Color("3f5a65")
	box.set_border_width_all(1);box.set_corner_radius_all(12);return box
func _draw() -> void:
	draw_rect(Rect2(0,0,1152,768),INK)
	var state:Dictionary=remote.confirmed
	if not state.is_empty():
		draw_world(state,TEAL if state.role=="Guardian" else AMBER)
		# Clip telegraphs/avatars to the field without covering them with UI panels.
		for rect in [Rect2(0,0,1152,185),Rect2(0,645,1152,123),Rect2(0,185,50,460),Rect2(1102,185,50,460)]:draw_rect(rect,INK)
	text(Vector2(50,42),"VIRGO DIAMOND",24,TEAL)
	text(Vector2(50,70),"REMOTE CROSSING  /  developer experiment",16)
	text(Vector2(700,40),"Protect the courier. Reach the far gate.",20)
	if state.is_empty():
		panel(Rect2(210,200,732,345))
		text(Vector2(245,247),"One crossing, one server-owned session",26)
		text(Vector2(245,292),"F2  Approach: "+selected+"     Tab  Guardian: "+style,20)
		text(Vector2(245,329),"C  Outfit: "+OUTFITS[outfit],20)
		text(Vector2(245,377),"Enter  Connect to the local server",22,TEAL)
		text(Vector2(245,418),"Each choice keeps its real costs. Preparation locks on entry.",17)
		text(Vector2(245,457),"Q  Close     |     "+(remote.reason if started else "Start the documented loopback server first."),16,AMBER)
	else:
		var accent:Color=TEAL if state.role=="Guardian" else AMBER
		panel(Rect2(50,91,1052,76))
		text(Vector2(70,118),state.role+" / "+state.get("guard_style","none"),19,accent)
		text(Vector2(70,147),"Health %d / %d   Cargo %d"%[state.hp,state.health_limit,state.cargo],18)
		text(Vector2(370,118),"Resolve  %d / 100"%state.energy,19)
		draw_rect(Rect2(370,132,220,9),INK);draw_rect(Rect2(370,132,220*state.energy/100.0,9),accent)
		text(Vector2(650,118),"Confirmed  %.1fs"%(state.tick/60.0),19)
		text(Vector2(650,147),"Counters %d / 3"%state.counters.counters,17)
		text(Vector2(888,118),remote.status.to_upper(),20,TEAL if remote.status=="live" else AMBER)
		text(Vector2(888,147),"Snapshot age %.2fs"%remote.age,16)
		var info:String=state.message
		text(Vector2(55,676),info.left(114),17,AMBER)
		text(Vector2(55,710),"WASD / arrows move    Mouse aims    K / right mouse guard    J draw    Space step    L / left mouse counter",16)
		text(Vector2(55,740),"Esc suspend / resume controls (world continues)    Q close    |    Confirmed costs; positions interpolate, never predict.",15)
		if state.mode in ["won","lost"]:
			panel(Rect2(250,250,652,235))
			text(Vector2(286,299),"CROSSING COMPLETE" if state.mode=="won" else "CROSSING LOST",29,accent if state.mode=="won" else RED)
			text(Vector2(286,343),"Server confirmed: health %d, cargo %d."%[state.hp,state.cargo],21)
			text(Vector2(286,386),"This result stays visible after the server closes.",18)
			text(Vector2(286,438),"Q  Close. A new attempt needs a new server process.",17,AMBER)
		elif controls.suspended or controls.quarantined or remote.status!="live":
			# Keep the ongoing world and threat geometry visible during suspension.
			panel(Rect2(50,653,1052,102))
			var heading:String="CONTROLS SUSPENDED — WORLD CONTINUES" if controls.suspended else "RELEASE HELD CONTROLS TO REARM"
			text(Vector2(70,681),heading if remote.status=="live" else "UPDATES STOPPED — LAST CONFIRMED WORLD",21,AMBER)
			var recovery:String="Release held controls, return focus, then Esc to resume.   Q closes." if controls.suspended else "Release all held controls, then make a fresh press. The world continues."
			text(Vector2(70,710),recovery if remote.status=="live" else remote.reason.left(104),17)
			text(Vector2(70,738),"No movement or paid action is queued. Positions and resources above come from the server.",16)
func draw_world(state:Dictionary,accent:Color) -> void:
	draw_rect(Rect2(50,185,1052,460),Color("203c43"))
	for x in range(100,1100,100):draw_line(Vector2(x,185),Vector2(x,645),Color("28464b"),1)
	draw_line(Vector2(140,390),Vector2(1020,390),Color("69755d"),38)
	for x in [400,680,1000]:
		draw_line(Vector2(x,365),Vector2(x,415),PAPER,2)
	text(Vector2(950,448),"FAR GATE",15)
	draw_line(Vector2(1010,333),Vector2(1010,390),TEAL,4)
	draw_colored_polygon(PackedVector2Array([Vector2(1010,334),Vector2(1040,345),Vector2(1010,358)]),TEAL)
	if state.enemy_focus>0:
		if state.phase=="bolt":
			var target:Vector2=vec(state.target)
			draw_line(ENEMY,target,AMBER,3,true);draw_arc(target,24,0,TAU,32,AMBER,2,true)
		elif state.phase=="pulse":
			var target:Vector2=vec(state.pulse)
			draw_circle(target,PULSE_RADIUS,Color(1,.35,.3,.12));draw_arc(target,PULSE_RADIUS,0,TAU,48,RED,3,true)
		draw_circle(ENEMY,29,Color("794c50"));draw_line(ENEMY-Vector2(0,20),ENEMY+Vector2(0,20),TEAL if state.opening>0 else RED,5)
		for i in 3:draw_circle(ENEMY+Vector2(-16+i*16,42),4,PAPER if i<state.enemy_focus else INK)
		text(ENEMY+Vector2(-65,-44),"OPEN %.1fs"%state.opening if state.opening>0 else str(state.phase).to_upper(),18,TEAL if state.opening>0 else AMBER)
	else:
		draw_line(ENEMY-Vector2(22,20),ENEMY+Vector2(22,20),PAPER,5);text(ENEMY+Vector2(-70,-40),"WARD SILENT",18,TEAL)
	var courier:Vector2=remote.courier_position
	draw_circle(courier+Vector2(0,10),24,Color(0,0,0,.25))
	draw_colored_polygon(PackedVector2Array([courier+Vector2(-20,0),courier+Vector2(0,-15),courier+Vector2(20,0),courier+Vector2(0,15)]),AMBER)
	draw_rect(Rect2(courier-Vector2(7,9),Vector2(14,18)),INK,false,2)
	text(courier+Vector2(-33,38),"COURIER",13)
	var player:Vector2=remote.position
	var face:Vector2=vec(state.locked_face if state.guard else state.facing)
	draw_set_transform(player,face.angle())
	draw_circle(Vector2(0,10),26,Color(0,0,0,.25))
	if state.role=="Guardian":
		draw_colored_polygon(PackedVector2Array([Vector2(-22,-19),Vector2(12,-19),Vector2(20,0),Vector2(12,19),Vector2(-22,19)]),accent)
		var shield:Vector2=Vector2(28,0) if state.guard else Vector2(0,-26)
		draw_line(shield-Vector2(0,18),shield+Vector2(0,18),PAPER if state.guard_state!="STALE" else RED,7,true)
	else:
		draw_colored_polygon(PackedVector2Array([Vector2(-25,-14),Vector2(14,0),Vector2(-25,14),Vector2(-15,0)]),accent)
		draw_line(Vector2(12,14),Vector2(48,14),PAPER,4,true)
	draw_circle(Vector2(6,0),7,INK);draw_line(Vector2(9,-3),Vector2(9,3),PAPER,2)
	if state.guard:draw_arc(Vector2.ZERO,37,-.7,.7,18,accent,3,true)
	if state.step_left>0:draw_line(Vector2(-55,-12),Vector2(-30,-12),PAPER,3)
	draw_set_transform(Vector2.ZERO)
	text(player+Vector2(-14,51),"YOU",14,accent)
	text(Vector2(68,210),"Server state: "+str(state.phase)+"  |  Guard: "+str(state.guard_state),15)
func observation() -> Dictionary:
	return {"status":remote.status,"reason":remote.reason,"age":remote.age,"confirmed":remote.confirmed.duplicate(true),
		"position":[remote.position.x,remote.position.y],"courier_position":[remote.courier_position.x,remote.courier_position.y],
		"suspended":controls.suspended,"quarantined":controls.quarantined,"focused":focused}
func capture() -> void:
	var prefix:String=OS.get_environment("NORTH_STAR_REMOTE_CAPTURE")
	if prefix.is_empty():return
	await RenderingServer.frame_post_draw
	captures+=1
	get_viewport().get_texture().get_image().save_png(prefix+".png")
	var data:Dictionary=observation();data.capture=captures
	var file=FileAccess.open(prefix+".json",FileAccess.WRITE)
	if file:file.store_string(JSON.stringify(data,"  ")+"\n");file.close()
