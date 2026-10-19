extends Node2D
const ReturnGate=preload("res://return_gate.gd")
var return_gate=ReturnGate.new()
const Route = preload("res://route.gd")
const Workshop = preload("res://workshop.gd")
var workshop = Workshop.new()
const Combat = preload("res://combat.gd")
const Rehearsal = preload("res://rehearsal.gd")
const Keepsakes = preload("res://keepsakes.gd")
const Errand = preload("res://errand.gd")
const Sound = preload("res://sound.gd")
const Controls = preload("res://controls.gd")
const Actors = preload("res://actors.gd")
var actors = Actors.new()
const KEEPSAKE_NAMES := {"":"None", "held_line":"Held the Line", "drew_danger":"Drew the Danger"}
var sound = Sound.new()
var keepsakes = Keepsakes.new()
var profile_path := ""
var normal_run := false
var reward_checked := false
var reward_message := ""
var errand = Errand.new()
var bindings = Controls.new()
var controls_path := ""
var controls_open := false
var controls_draft := {}
var controls_row := 0
var controls_listening := false
var controls_message := ""
var drawing_controls := false
var rehearsal = Rehearsal.new()
var game = Combat.new()
var selected := "Guardian"
var guardian_style := "Steady"
var taps := {}
var font = ThemeDB.fallback_font
const INK := Color("101b2b")
const PAPER := Color("e9eddf")
const TEAL := Color("5ae0ce")
const AMBER := Color("ffc474")
const RED := Color("ff796f")

func _ready() -> void:
	add_child(sound)
	if profile_path.is_empty(): profile_path=OS.get_environment("CROSSING_PROFILE")
	if profile_path.is_empty(): profile_path="user://crossing-keepsakes.json"
	keepsakes.load_profile(profile_path)
	if controls_path.is_empty():controls_path=OS.get_environment("CROSSING_CONTROLS")
	if controls_path.is_empty():controls_path="user://crossing-controls.json"
	bindings.load_profile(controls_path)
	actors.attach(game)
	queue_redraw()

func abandon() -> void:
	return_gate=ReturnGate.new()
	bindings.clear_intents()
	errand=Errand.new()
	normal_run=false
	reward_checked=false
	reward_message=""
	rehearsal = Rehearsal.new()
	game = Combat.new()
	game.role = selected
	game.guard_style=guardian_style if selected=="Guardian" else "none"
	actors.attach(game)
	taps.clear()

func begin_crossing() -> void:
	return_gate=ReturnGate.new()
	bindings.clear_intents()
	errand.reset()
	normal_run=true
	reward_checked=false
	reward_message=""
	rehearsal.active = false
	game = Combat.new()
	game.reset(selected,guardian_style)
	game.fit_outfit(workshop.outfit)
	if workshop.active:workshop.leave();bindings.quarantine()
	sound.observe(game,true)
	actors.attach(game)
	taps.clear()

func _notification(what: int) -> void:
	if what==NOTIFICATION_APPLICATION_FOCUS_OUT:
		if return_gate.active:return_gate.suspend()
		if workshop.active:workshop.suspend()
		if rehearsal.active:
			if rehearsal.state=="live" and not rehearsal.paused: rehearsal.toggle_pause()
		elif game.mode=="play": game.mode="paused"
		taps.clear();bindings.quarantine();sound.silence()

func _unhandled_key_input(event: InputEvent) -> void:
	if not event is InputEventKey:return
	if not event.pressed:bindings.release(event);return
	if event.echo:return
	var key: int = event.physical_keycode
	if key==0 or event.keycode in Controls.NAV:key=event.keycode
	if key==KEY_ESCAPE:bindings.clear_intents()
	if key==KEY_F12:capture();return
	if controls_open:
		controls_input(event,key);queue_redraw();return
	if key==KEY_F1:
		open_controls();queue_redraw();return
	if return_gate.active:
		return_gate_input(event,key);sync_sound();queue_redraw();return
	if normal_run and not rehearsal.active and game.mode=="won" and key==KEY_F2:
		begin_return_gate();queue_redraw();return
	if workshop.active:
		workshop_input(key);queue_redraw();return
	if not rehearsal.active and game.mode=="title" and key==KEY_F2:
		workshop.enter();taps.clear();bindings.quarantine();queue_redraw();return
	if not rehearsal.active and game.mode!="play":
		if key==KEY_C: keepsakes.cycle_equipped()
		elif key==KEY_F5: keepsakes.retry_save()
	if rehearsal.active:
		if key==KEY_ESCAPE: rehearsal.toggle_pause(); taps.clear()
		elif key==KEY_R and (rehearsal.paused or rehearsal.state!="live"): abandon()
		elif key==KEY_ENTER:
			if rehearsal.paused or rehearsal.state!="live":bindings.clear_intents()
			if rehearsal.paused: rehearsal.toggle_pause()
			elif rehearsal.confirm(): begin_crossing()
			if rehearsal.active: game=rehearsal.game
			taps.clear()
		elif key==KEY_T and rehearsal.state!="live": bindings.clear_intents();rehearsal.repeat(); game=rehearsal.game; taps.clear()
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
			if key==KEY_1: selected="Guardian"; game.role=selected;game.guard_style=guardian_style
			elif key==KEY_2: selected="Duelist"; game.role=selected;game.guard_style="none"
			elif key==KEY_TAB and selected=="Guardian":
				guardian_style="Riposte" if guardian_style=="Steady" else "Steady"
				game.guard_style=guardian_style
			elif key==KEY_T: rehearsal.start(selected,guardian_style); game=rehearsal.game; taps.clear()
	if game.mode=="play":
		if bindings.matches(event,"strike"): taps.strike=true
		if bindings.matches(event,"skill"): taps.skill_pressed=true
		if bindings.matches(event,"step"): taps.dodge=true
		if bindings.matches(event,"interact"): taps.interact_pressed=true
	sync_sound()
	queue_redraw()

func workshop_input(key: int) -> void:
	if key==KEY_ESCAPE:
		if workshop.paused:workshop.paused=false
		else:workshop.suspend()
		bindings.quarantine()
	elif key==KEY_ENTER:
		if workshop.paused:workshop.paused=false;bindings.quarantine()
		else:begin_crossing()
	elif key==KEY_R:workshop.leave();bindings.quarantine()
	elif key==KEY_C:workshop.recycle();bindings.quarantine()
	taps.clear()

func open_controls() -> void:
	if return_gate.active:return_gate.suspend()
	if workshop.active:workshop.suspend()
	if rehearsal.active:
		if rehearsal.state=="live" and not rehearsal.paused:rehearsal.toggle_pause()
	elif game.mode=="play":game.mode="paused"
	controls_open=true;controls_listening=false;controls_row=0
	controls_draft=bindings.keys.duplicate();controls_message=""
	taps.clear();bindings.quarantine();sound.silence()

func controls_input(event: InputEventKey,key: int) -> void:
	if controls_listening:
		if key==KEY_ESCAPE:
			controls_listening=false;controls_message="Capture cancelled. Draft unchanged.";return
		if event.alt_pressed or event.ctrl_pressed or event.meta_pressed or event.shift_pressed:
			controls_message="Use an unmodified key; combinations are not supported.";return
		var error: String=Controls.assign(controls_draft,Controls.ACTIONS[controls_row],Controls.event_code(event))
		controls_message=error if not error.is_empty() else "Draft changed. S applies; Esc discards unapplied changes."
		if error.is_empty():controls_listening=false
		return
	if key in [KEY_ESCAPE,KEY_F1]:
		controls_open=false;controls_listening=false;taps.clear();bindings.quarantine()
	elif key==KEY_UP:controls_row=posmod(controls_row-1,Controls.ACTIONS.size())
	elif key==KEY_DOWN:controls_row=(controls_row+1)%Controls.ACTIONS.size()
	elif key==KEY_ENTER:controls_listening=true;controls_message="Press a new key. Esc cancels capture."
	elif key==KEY_DELETE:controls_draft=Controls.DEFAULTS.duplicate();controls_message="Defaults in draft. S applies; Esc discards."
	elif key==KEY_F5:sound.set_muted(not sound.muted)
	elif key==KEY_H:
		bindings.toggle_guard=not bindings.toggle_guard;bindings.clear_intents()
		controls_message="Guard input changed for this session; combat timing and costs are unchanged."
	elif key==KEY_I:
		bindings.toggle_interact=not bindings.toggle_interact;bindings.clear_intents()
		controls_message="Interaction input changed for this session; move or press again to cancel."
	elif key==KEY_S:
		bindings.apply(controls_draft);controls_message=bindings.status;taps.clear();bindings.quarantine()

func _physics_process(dt: float) -> void:
	if controls_open:taps.clear();sound.silence();queue_redraw();return
	if workshop.active:
		workshop.step(dt,bindings.vector("move"),bindings.down("interact"))
		taps.clear();queue_redraw();return
	var command: Dictionary=taps.duplicate()
	command.move=bindings.vector("move")
	command.aim=bindings.vector("aim")
	command.skill=bindings.down("skill")
	command.interact=bindings.down("interact")
	if return_gate.active:
		command=return_gate_command(command)
		advance_crossing(dt,command)
		bindings.settle_intents(game)
		if not return_gate.channel:bindings.interact_latched=false;bindings.interaction_state=""
	else:
		command=bindings.translate(command,game,errand if normal_run and not rehearsal.active else null)
		if rehearsal.active: rehearsal.step(dt,command)
		else: advance_crossing(dt,command)
		bindings.settle_intents(game,errand if normal_run and not rehearsal.active else null)
	taps.clear()
	sync_sound()
	queue_redraw()

func sync_sound() -> void:
	var suspended: bool=controls_open or (rehearsal.paused or rehearsal.state=="ready" if rehearsal.active else game.mode in ["title","paused"])
	sound.observe(game,suspended)
	actors.observe(game)

func advance_crossing(dt: float, command: Dictionary) -> void:
	if return_gate.active:
		return_gate.step(dt,command);return
	var previous: String=game.mode
	command=command.duplicate()
	command.route_signal=normal_run and not rehearsal.active and bool(command.get("interact_pressed",false))
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
	if not drawing_controls:value=bindings.describe(value)
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
	if return_gate.active:
		draw_return_gate()
		if controls_open:drawing_controls=true;draw_controls();drawing_controls=false
		return
	if workshop.active:
		draw_workshop()
		if controls_open:drawing_controls=true;draw_controls();drawing_controls=false
		return
	draw_rect(Rect2(0,0,1152,768),INK)
	draw_rect(Combat.FIELD,Color("172f3b"))
	for x in range(80,1100,55): draw_line(Vector2(x,185),Vector2(x,645),Color("203e49"),1)
	for y in range(200,650,55): draw_line(Vector2(50,y),Vector2(1102,y),Color("203e49"),1)
	draw_rect(Rect2(50,355,1052,70),Color("35454a"))
	draw_line(Vector2(70,390),Vector2(1080,390),Color("718282"),2)
	if normal_run and not rehearsal.active: draw_route()
	if errand.active and not rehearsal.active: draw_errand()
	for x in [400,700,1000]:
		draw_line(Vector2(x,350),Vector2(x,430),AMBER if game.courier.x>=x else Color("6c777b"),4)
		text(Vector2(x-35,458),"GATE" if x==1000 else "MARK",14)
	var reviewing: bool=rehearsal.active and rehearsal.state=="review"
	if game.phase=="bolt" or (reviewing and rehearsal.stage==0):
		var width: float=3+game.clock*8
		draw_line(Combat.ENEMY,game.target,Color(1,0.75,0.4,0.25+game.clock*0.5),width)
		draw_arc(game.target,26,0,TAU,24,AMBER,2)
		if game.role=="Guardian" and game.guard_style=="Riposte" and not reviewing:draw_guard_timing()
		var label=game.target+(Vector2(34,-36) if game.target.distance_to(game.player)<80 else Vector2(-50,-38))
		label.x=clampf(label.x,65,940)
		label.y=maxf(200,label.y)
		text(label,"LAST LOCKED LINE" if reviewing else "LOCKED BOLT",14,AMBER)
	if game.phase=="pulse" or (reviewing and rehearsal.stage==1):
		draw_circle(game.pulse,90,Color(1,0.3,0.3,0.18+game.clock*0.22))
		draw_arc(game.pulse,90,0,TAU,48,RED,3)
		text(game.pulse+Vector2(-55,-106),"LAST PULSE" if reviewing else "GROUND PULSE",15,RED)
	actors.draw_sentinel(self,game)
	text(Combat.ENEMY+Vector2(-42,-50),"SENTINEL",15,TEAL if game.sentinel_disabled() else RED)
	text(Combat.ENEMY+Vector2(-70,84),game.sentinel_status(),14,TEAL if game.sentinel_disabled() else AMBER)
	if game.role=="Duelist" and not game.sentinel_disabled(): draw_arc(Combat.ENEMY,340,0,TAU,80,Color(1,0.77,0.45,0.18),1)
	if game.opening>0:
		draw_arc(Combat.ENEMY,130,0,TAU,64,TEAL,2)
		text(Combat.ENEMY+Vector2(-53,60),"OPEN %.1fs"%game.opening,19,TEAL)
	actors.draw_courier(self,game)
	text(game.courier+Vector2(-35,40),"COURIER",14,AMBER)
	var c: Color=TEAL if game.role=="Guardian" else AMBER
	actors.draw_player(self,game)
	draw_keepsake(game.player,keepsakes.equipped)
	# Keep the facing cue outside the body so it cannot obscure a worn mark.
	draw_colored_polygon(PackedVector2Array([game.player+game.facing*43,game.player+game.facing*35+game.facing.orthogonal()*4,game.player+game.facing*35-game.facing.orthogonal()*4]),PAPER)
	if game.guard:
		var angle: float=game.locked_face.angle()
		draw_arc(game.player,37,angle-0.9,angle+0.9,24,TEAL if game.guards_from(Combat.ENEMY) else (RED if game.guard_state()=="STALE" else AMBER),7)
	actors.draw_contact(self)
	text(game.player+Vector2(30 if game.player.x<140 else -65,47 if game.player.y<245 else -38),"YOU",14,c)
	draw_header()
	panel(Rect2(30,662,1092,86))
	text(Vector2(48,686),"WASD move   •   ARROWS aim   •   J blade   •   K "+(("timed guard" if game.guard_style=="Riposte" else ("toggle guard" if bindings.toggle_guard else "hold guard")) if game.role=="Guardian" else "feint bolt")+"   •   SPACE step   •   ESC pause",17)
	text(Vector2(48,718),footer(),17,AMBER)
	if rehearsal.active: rehearsal_overlay()
	elif game.mode!="play": overlay()
	if controls_open:
		drawing_controls=true;draw_controls();drawing_controls=false

func draw_guard_timing() -> void:
	var cue: String="RAISE K NOW" if game.clock>=0.74 and game.clock<=0.90 else ("WAIT TO RAISE" if game.clock<0.74 else "CONTACT NEAR")
	if game.guard_state()=="STALE":cue="STALE / RELEASE K"
	var color: Color=TEAL if cue=="RAISE K NOW" else (RED if game.guard_state()=="STALE" else AMBER)
	draw_arc(Combat.ENEMY,47,-PI/2,-PI/2+TAU*clampf(game.clock,0,1),40,color,3)
	text(Combat.ENEMY+Vector2(-72,-84),cue,15,color)

func draw_header() -> void:
	draw_rect(Rect2(0,0,1152,174),INK)
	text(Vector2(40,42),"VIRGO DIAMOND / "+("REHEARSAL" if rehearsal.active else "CROSSING DRILL"),25)
	text(Vector2(950,41),"F1 Keys / sound",16,AMBER)
	text(Vector2(40,70),("%d / 3  %s  •  "%[rehearsal.stage+1,rehearsal.heading()]+rehearsal.instruction()) if rehearsal.active else (errand.hint() if errand.active else "LOCAL EXPERIMENT  •  Keep the courier alive to the far gate"),16,AMBER)
	text(Vector2(40,110),game.role.to_upper()+(" / "+game.guard_style.to_upper() if game.role=="Guardian" else "")+"  /  HEALTH "+str(game.hp)+" / "+str(game.health_limit)+"   COURIER "+str(game.cargo),19)
	draw_rect(Rect2(40,130,300,12),Color("32475a"))
	draw_rect(Rect2(40,130,300*game.energy/100,12),TEAL if game.role=="Guardian" else AMBER)
	text(Vector2(355,142),"POSTURE" if game.role=="Guardian" else "RESOLVE",15)
	if game.role=="Guardian":text(Vector2(460,142),"GUARD "+game.guard_state()+(" / TOGGLE" if bindings.toggle_guard else ""),14,RED if game.guard_state()=="STALE" else PAPER)
	var progress: float=game.route.progress(game.courier)
	text(Vector2(750,111),("PAUSED" if rehearsal.paused else ("RESPONSE VERIFIED" if rehearsal.passed else rehearsal.state.to_upper())) if rehearsal.active else "CROSSING  %d%%"%roundi(progress*100),19)
	draw_rect(Rect2(750,130,350,12),Color("32475a"))
	draw_rect(Rect2(750,130,350*((rehearsal.stage+int(rehearsal.passed))/3.0 if rehearsal.active else progress),12),AMBER)

	text(Vector2(40,164),"WORN  /  "+KEEPSAKE_NAMES[keepsakes.equipped]+"  •  cosmetic only",14)
	var shown_outfit: String=workshop.outfit if game.mode=="title" else game.outfit
	text(Vector2(505,164),("NEXT / " if game.mode=="title" else "GEAR / ")+("COAT" if shown_outfit=="riveted" else ("WRAP" if shown_outfit=="trail" else "STANDARD")),14,AMBER)
	text(Vector2(750,164),"LOCAL SAVE PENDING" if keepsakes.dirty or keepsakes.blocked else "THIS DEVICE'S KEEPSAKES",14,AMBER)

func overlay() -> void:
	draw_rect(Rect2(40,176,1072,473),Color(0.03,0.07,0.12,0.90))
	if game.mode=="title":
		text(Vector2(210,231),"One crossing. Hold the line or break its source.",30)
		text(Vector2(140,266),"Courier keeps moving. At MARK 1, optional medicine falls south of the road.",19)
		panel(Rect2(180,292,380,212),Color("244a50") if selected=="Guardian" else Color("1b2d40"))
		panel(Rect2(590,292,380,212),Color("594730") if selected=="Duelist" else Color("1b2d40"))
		text(Vector2(205,330),"1  GUARDIAN",26,TEAL)
		text(Vector2(205,365),"TAB  "+guardian_style+" guard",20,TEAL)
		text(Vector2(205,400),"Raise late; early guard expires." if guardian_style=="Riposte" else "Aim at sentinel, hold K to block.",19)
		text(Vector2(205,430),"60-300ms guard; OPEN lasts 1.6s." if guardian_style=="Riposte" else "Sustained guard; OPEN lasts 1.0s.",17)
		text(Vector2(205,467),"Cross + block: Held the Line",17,TEAL)
		text(Vector2(615,330),"2  DUELIST",26,AMBER)
		text(Vector2(615,370),"K during a bolt warning draws its aim.",18)
		text(Vector2(615,400),"Move or step away from the locked line.",18)
		text(Vector2(615,430),"Feint within the ring; steps cost resolve.",17)
		text(Vector2(615,467),"Cross + draw: Drew the Danger",17,AMBER)
		text(Vector2(210,543),"Leave pulses. Three counters stop the sentinel. E at sign chooses route.",17)
		text(Vector2(210,580),"T  Rehearse   •   F2  Workshop   •   ENTER  Crossing",21,TEAL)
		text(Vector2(210,615),"C  Keepsake: "+KEEPSAKE_NAMES[keepsakes.equipped]+"     /     experimental, cosmetic only",17)
		draw_keepsake(Vector2(1015,602),keepsakes.equipped,1.4)
		text(Vector2(150,642),"Sound: high taps = bolt; low pair = floor. F1 opens sound / key controls.",16,AMBER)
	elif game.mode=="paused":
		text(Vector2(280,330),"Crossing paused",36)
		text(Vector2(280,385),"ENTER / ESC resume     •     R abandon and choose",22)
		text(Vector2(280,430),("Guard faces the direction locked when K was raised." if game.role=="Guardian" else "K draws an amber bolt only inside the sentinel's ring."),19)
		text(Vector2(280,465),("Release K before turning. Steps move; they grant no immunity." if game.role=="Guardian" else "Leave the drawn line. Steps move; they grant no immunity."),19)
		draw_impact(Vector2(130,530))
		text(Vector2(130,590),"Route: "+game.route.kind.to_upper()+" / Ridge adds distance and raises a bolt-only filter. Signal locks at MARK 1.",16,TEAL)
		text(Vector2(130,617),"Optional case: hold E nearby to recover, then E near courier to hand over. Neither waits.",17,AMBER)
	else:
		text(Vector2(250,290),"THE COURIER CROSSED" if game.mode=="won" else "THE LINE BROKE",36,TEAL if game.mode=="won" else RED)
		text(Vector2(250,345),game.role+(" / "+game.guard_style if game.role=="Guardian" else "")+"  /  blocks %d   drawn bolts %d   counters %d"%[game.counters.blocks,game.counters.redirects,game.counters.counters],22)
		text(Vector2(250,390),"Health %d / %d    Courier %d / 3    Crossing %d%%"%[game.hp,game.health_limit,game.cargo,roundi(game.route.progress(game.courier)*100)],21)
		draw_impact(Vector2(150,435))
		text(Vector2(250,490),game.sentinel_status()+" / "+game.route.kind.to_upper()+" / filter caught %d bolts"%game.route.covered,16,TEAL if game.sentinel_disabled() else AMBER)
		text(Vector2(250,518),"ENTER retry this approach     •     R choose approach",22)
		text(Vector2(150,552),reward_message if game.mode=="won" else "No keepsake earned. Complete a crossing with a block or drawn bolt.",18,TEAL if game.mode=="won" else AMBER)
		text(Vector2(150,585),"C  Wear / put away     •     F5  Retry local save     /     cosmetic only",18)
		text(Vector2(150,612),errand.outcome(),17,AMBER)
		if game.mode=="won":text(Vector2(150,640),"F2  Continue: open the return gate  /  health carries  /  optional",17,TEAL)

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

func draw_controls() -> void:
	draw_rect(Rect2(40,90,1072,660),INK)
	text(Vector2(85,131),"KEYBOARD CONTROLS  /  "+("CAPTURE KEY" if controls_listening else "DRAFT"),27,TEAL)
	text(Vector2(85,162),"UP / DOWN select  •  ENTER change  •  S apply  •  DELETE defaults  •  ESC close / cancel",18)
	text(Vector2(85,190),"Physical positions / logical arrows. No combos. F5 sound: "+("OFF" if sound.muted else "ON")+" (session)",16,AMBER)
	for index in Controls.ACTIONS.size():
		var y: float=228+index*28
		if index==controls_row:panel(Rect2(75,y-22,1000,28),Color("35505a"))
		text(Vector2(95,y),Controls.LABELS[index],18)
		text(Vector2(650,y),("Press key..." if index==controls_row and controls_listening else bindings.name_for(Controls.ACTIONS[index],controls_draft)),18,TEAL)
	text(Vector2(85,570),"H  Guardian input: "+("PRESS TO TOGGLE" if bindings.toggle_guard else "HOLD")+"   /   I  Interaction: "+("PRESS TO TOGGLE" if bindings.toggle_interact else "HOLD"),17,TEAL)
	text(Vector2(85,596),"Session only. Pause / settings clear active toggles. Duelist K remains one press.",16,AMBER)
	text(Vector2(85,622),"Unapplied changes" if controls_draft!=bindings.keys else "Draft matches active controls",17,AMBER)
	text(Vector2(85,648),controls_message if not controls_message.is_empty() else bindings.status,16)
	text(Vector2(85,682),"Closing does not start or resume play. Resume the attempt explicitly.",16)

func footer() -> String:
	if rehearsal.active:
		if rehearsal.paused: return "ENTER / ESC resume  •  R abandon rehearsal"
		if rehearsal.state=="ready": return "ENTER send this trial  •  R choose approach  /  No time passes while you read."
		if rehearsal.state=="review": return ("ENTER "+("start the crossing" if rehearsal.stage==2 else "next exercise") if rehearsal.passed else "ENTER retry this exercise")+"  •  T repeat  •  R choose approach"
	if game.mode!="play" and (keepsakes.dirty or keepsakes.blocked): return keepsakes.status
	if game.mode=="title": return "F2: make gear with a trade-off. Current: "+Workshop.NAMES[workshop.outfit]+". C cycles cosmetic marks."
	if game.mode=="won": return keepsakes.status
	return game.message

func draw_impact(at: Vector2) -> void:
	if game.last_impact.is_empty(): return
	var explanation:String=game.last_impact.explanation
	var tip:String=game.last_impact.tip
	if return_gate.active:
		explanation=explanation.replace("courier","winch").replace("sentinel","ward")
		tip=tip.replace("courier","winch").replace("sentinel","ward")
	text(at,"LAST CONTACT  /  "+explanation,18,AMBER)
	text(at+Vector2(0,32),tip,18)

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
			text(Vector2(100,top+65),"Counter landed. Three clean counters disable the sentinel." if rehearsal.passed else "The opening closed before a close counter landed.",19)
			text(Vector2(100,top+95),"The normal crossing uses the same range, costs and timing." if rehearsal.passed else "Walk into the OPEN ring, release guard, then press J before it closes.",18)
		else:
			text(Vector2(100,top+65),game.last_impact.explanation,19)
			text(Vector2(100,top+95),game.last_impact.tip,18)
	else:
		text(Vector2(100,top+65),rehearsal.instruction(),19)
		text(Vector2(100,top+95),("Sound: three high taps warn of a bolt. Watch its locked line." if rehearsal.stage==0 else ("Sound: a low rough pair warns of the floor pulse. Leave the marked circle." if rehearsal.stage==1 else "A dry contact sounds only when a close counter lands. No crossing reward here.")),18)

func capture() -> void:
	var path := OS.get_environment("CROSSING_CAPTURE")
	if path.is_empty(): return
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(path)
	var file=FileAccess.open(path+".json",FileAccess.WRITE)
	var report=game.snapshot()
	if return_gate.active:report.return_gate=return_gate.snapshot()
	report.route=game.route.snapshot()
	report.player_position=[game.player.x,game.player.y]
	report.courier_position=[game.courier.x,game.courier.y]
	report.workshop=workshop.snapshot()
	report.actors=actors.snapshot(game)
	report.last_impact=game.last_impact.duplicate(true)
	report.rehearsal=rehearsal.snapshot()
	report.keepsakes=keepsakes.snapshot()
	report.errand=errand.snapshot()
	report.sound=sound.snapshot()
	report.controls={"profile":bindings.snapshot(),"open":controls_open,"draft":controls_draft.duplicate(),"row":controls_row,"listening":controls_listening,"message":controls_message}
	file.store_string(JSON.stringify(report,"  ")+"\n")

func draw_workshop() -> void:
	draw_rect(Rect2(0,0,1152,768),INK)
	text(Vector2(45,48),"VIRGO DIAMOND / ROADSIDE WORKSHOP",28)
	text(Vector2(45,87),"An experimental fitting, not a permanent profession choice. Both approaches can wear either piece.",18,AMBER)
	text(Vector2(45,128),"ONE BLANK  /  %d available     WORN  /  %s"%[workshop.blank,Workshop.NAMES[workshop.outfit]],21,TEAL)
	for id in Workshop.STATIONS:
		var at: Vector2=Workshop.STATIONS[id]
		var heavy: bool=id=="riveted"
		var tint: Color=AMBER if heavy else TEAL
		panel(Rect2(at-Vector2(200,180),Vector2(400,290)),Color("203548"))
		text(at+Vector2(-175,-145),Workshop.NAMES[id].to_upper(),26,tint)
		text(at+Vector2(-175,-113),"6 health  /  200px/s walk" if heavy else "4 health  /  300px/s walk",20)
		text(at+Vector2(-175,-85),"+1 hit; 20% slower movement / step." if heavy else "-1 hit; 20% faster movement / step.",17,tint)
		text(at+Vector2(-175,-61),"Standard: 5 health / 250px/s. No courier bonus.",15)
		draw_rect(Rect2(at-Vector2(46,18),Vector2(92,36)),Color("617986"))
		draw_line(at+Vector2(-30,-20),at+Vector2(25,-20),tint,6)
		draw_arc(at,Workshop.RADIUS,0,TAU,48,tint,2)
		text(at+Vector2(-175,82),"Stand in ring. Hold E 1s: MAKE & WEAR.",17,tint)
		if workshop.target==id:draw_arc(at,54,-PI/2,-PI/2+TAU*workshop.progress/Workshop.MAKE_TIME,48,PAPER,5)
	# The same native actor carries its selected appearance into the actual crossing.
	var preview=Combat.new();preview.role=selected;preview.player=workshop.player
	preview.outfit=workshop.outfit
	actors.draw_player(self,preview)
	draw_keepsake(workshop.player,keepsakes.equipped)
	text(workshop.player+Vector2(-20,48),"YOU",15)
	panel(Rect2(30,650,1092,96))
	text(Vector2(48,679),"WASD move  /  E hold to make  /  C recycle & recover blank  /  R back  /  F1 keys",17)
	text(Vector2(48,710),"PAUSED / ENTER or ESC resumes" if workshop.paused else "ENTER crosses with worn gear. Crafting never starts the threat clock.",19,TEAL)
	text(Vector2(45,620),workshop.message,17,AMBER)

func draw_route() -> void:
	var ridge:bool=game.route.kind=="ridge"
	var color:Color=TEAL if ridge else Color("647a83")
	draw_polyline(PackedVector2Array([Vector2(400,390),Vector2(400,250),Vector2(700,250),Vector2(700,390)]),Color("294a50"),34)
	draw_polyline(PackedVector2Array([Vector2(400,390),Vector2(400,250),Vector2(700,250),Vector2(700,390)]),color,2)
	text(Vector2(425,229),"RIDGE / LONGER WALK",15,color)
	draw_circle(Route.BOARD,Route.SIGNAL_RADIUS,Color(0.2,0.4,0.45,0.25))
	draw_arc(Route.BOARD,Route.SIGNAL_RADIUS,0,TAU,36,color,2)
	draw_rect(Rect2(Route.BOARD-Vector2(16,9),Vector2(32,18)),PAPER)
	draw_line(Route.BOARD,Route.BOARD+Vector2(0,20),PAPER,3)
	text(Vector2(75,210),"ROUTE / "+game.route.kind.to_upper()+"  /  "+("LOCKED AT MARK 1" if game.route.locked else "E AT SIGN TO CHANGE"),16,AMBER)
	text(Vector2(80,320),"SIGN: "+("locked" if game.route.locked else ("E chooses ROAD" if ridge else "E chooses RIDGE + raises filter")),16,AMBER)
	if ridge:
		draw_line(Vector2(Route.SCREEN_X,Route.SCREEN_TOP),Vector2(Route.SCREEN_X,Route.SCREEN_BOTTOM),PAPER if game.route.flash>0 else TEAL,6)
		for y in range(220,366,15):draw_line(Vector2(642,y),Vector2(658,y),TEAL,2)
		text(Vector2(675,280),"BOLT FILTER",14,TEAL)
		text(Vector2(675,302),"People pass; floor hurts.",13)
		if game.route.flash>0:draw_arc(game.route.last_contact,16,0,TAU,24,PAPER,3)

func begin_return_gate() -> bool:
	if not normal_run or rehearsal.active or not return_gate.begin(game,errand.state):return false
	normal_run=false;game=return_gate.game
	taps.clear();bindings.quarantine();sound.observe(game,true);actors.attach(game)
	return true

func return_gate_input(event: InputEventKey,key: int) -> void:
	if key==KEY_ESCAPE:
		return_gate.suspend()
		if game.mode=="play":game.mode="paused"
		elif game.mode=="paused":game.mode="play"
		taps.clear();bindings.quarantine()
	elif key==KEY_ENTER:
		if game.mode=="paused":game.mode="play"
		elif game.mode in ["won","lost"]:
			return_gate.retry();game=return_gate.game;sound.observe(game,true);actors.attach(game)
		taps.clear();bindings.quarantine()
	elif key==KEY_R and game.mode!="play":abandon()
	elif key==KEY_C and game.mode!="play":keepsakes.cycle_equipped()
	elif key==KEY_F5 and game.mode!="play":keepsakes.retry_save()
	elif game.mode=="play":
		if bindings.matches(event,"strike"):taps.strike=true
		if bindings.matches(event,"skill"):taps.skill_pressed=true
		if bindings.matches(event,"step"):taps.dodge=true
		if bindings.matches(event,"interact"):taps.interact_pressed=true

func return_gate_command(command: Dictionary) -> Dictionary:
	var result:Dictionary=bindings.translate(command,game)
	var eligible:bool=return_gate.eligible(command)
	if bindings.toggle_interact:
		if not eligible:bindings.interact_latched=false
		if eligible and command.get("interact_pressed",false):bindings.interact_latched=not bindings.interact_latched
		result.interact=bindings.interact_latched
	if eligible and result.get("interact",false) and bindings.toggle_guard:
		bindings.guard_latched=false;result.skill=false
	return result

func draw_return_gate() -> void:
	draw_rect(Rect2(0,0,1152,768),INK)
	draw_rect(Combat.FIELD,Color("252d3a"))
	for x in range(80,1100,55):draw_line(Vector2(x,185),Vector2(x,645),Color("354051"),1)
	for i in ReturnGate.CATCHES.size():
		var at:Vector2=ReturnGate.CATCHES[i]
		var tint:Color=TEAL if return_gate.raised[i] else AMBER
		draw_line(at,ReturnGate.WINCH,Color("596575"),3)
		draw_arc(at,ReturnGate.RADIUS,0,TAU,32,tint,2)
		draw_rect(Rect2(at-Vector2(18,14),Vector2(36,28)),Color("596575"))
		draw_line(at,at+Vector2(17,-28 if return_gate.raised[i] else 20),tint,6,true)
		text(at+Vector2(-74,-53),("NORTH" if i==0 else "SOUTH")+" CATCH",17,tint)
		text(at+Vector2(-84,61),"RAISED" if return_gate.raised[i] else "Hold E here / 1s",16,tint)
		if return_gate.working==i and return_gate.channel:draw_arc(at,41,-PI/2,-PI/2+TAU*return_gate.progress/ReturnGate.WORK_TIME,40,PAPER,5)
	var winch:Vector2=ReturnGate.WINCH
	draw_circle(winch,29,Color("566675"));draw_arc(winch,22,0,TAU,24,PAPER,4)
	for i in 4:
		var angle:float=i*PI/2
		draw_line(winch,winch+Vector2.from_angle(angle)*21,PAPER,3)
	text(winch+Vector2(-62,58),"WINCH %d / 2"%game.cargo,17,TEAL if game.cargo==2 else RED)
	text(winch+Vector2(-89,82),"Protect this device",14)
	if game.phase=="bolt":
		draw_line(Combat.ENEMY,game.target,Color(1,0.75,0.4,0.25+game.clock*0.5),3+game.clock*8)
		draw_arc(game.target,26,0,TAU,24,AMBER,2)
		text(Vector2(610,200),"LOCKED BOLT / WINCH EXPOSED",16,AMBER)
		if game.role=="Guardian" and game.guard_style=="Riposte":draw_guard_timing()
	if game.phase=="pulse":
		draw_circle(game.pulse,90,Color(1,0.3,0.3,0.3));draw_arc(game.pulse,90,0,TAU,48,RED,3)
		text(game.pulse+Vector2(-65,-104),"GROUND PULSE",16,RED)
	actors.draw_sentinel(self,game)
	text(Combat.ENEMY+Vector2(-49,-50),"GATE WARD",16,RED if not game.sentinel_disabled() else TEAL)
	text(Combat.ENEMY+Vector2(-70,84),game.sentinel_status(),14,TEAL if game.sentinel_disabled() else AMBER)
	if game.opening>0:
		draw_arc(Combat.ENEMY,130,0,TAU,64,TEAL,2)
		text(Combat.ENEMY+Vector2(-50,60),"OPEN %.1fs"%game.opening,18,TEAL)
	if not return_gate.opened():
		for y in range(195,645,25):draw_line(Vector2(1020,y),Vector2(1020,y+18),AMBER,9)
	else:draw_line(Vector2(1020,195),Vector2(1020,235),TEAL,9)
	draw_arc(ReturnGate.EXIT,24,0,TAU,32,TEAL if return_gate.opened() else Color("596575"),3)
	text(Vector2(1010,450),"EXIT" if return_gate.opened() else "LOCKED",16,TEAL if return_gate.opened() else AMBER)
	actors.draw_player(self,game);draw_keepsake(game.player,keepsakes.equipped)
	if game.guard:draw_arc(game.player,37,game.locked_face.angle()-0.9,game.locked_face.angle()+0.9,24,TEAL if game.guards_from(Combat.ENEMY) else AMBER,7)
	actors.draw_contact(self)
	text(game.player+Vector2(-20,-38),"YOU",14,TEAL)
	draw_rect(Rect2(0,0,1152,174),INK)
	text(Vector2(40,42),"VIRGO DIAMOND / THE RETURN GATE",26)
	text(Vector2(950,41),"F1 Keys / sound",16,AMBER)
	text(Vector2(40,72),"Courier safe. Raise BOTH catches, keep the winch intact, then pass the open gate alive.",18,AMBER)
	text(Vector2(40,111),game.role.to_upper()+(" / "+game.guard_style.to_upper() if game.role=="Guardian" else "")+" / HP %d / %d / "%[game.hp,game.health_limit]+Workshop.NAMES[game.outfit],19)
	text(Vector2(750,111),"CATCHES %d / 2"%(int(return_gate.raised[0])+int(return_gate.raised[1])),22,TEAL)
	draw_rect(Rect2(40,130,300,12),Color("32475a"));draw_rect(Rect2(40,130,300*game.energy/100,12),TEAL if game.role=="Guardian" else AMBER)
	text(Vector2(355,142),"POSTURE" if game.role=="Guardian" else "RESOLVE",15)
	if game.role=="Guardian":text(Vector2(460,142),"GUARD "+game.guard_state()+(" / TOGGLE" if bindings.toggle_guard else ""),14,RED if game.guard_state()=="STALE" else PAPER)
	text(Vector2(40,164),"ARRIVAL: %d health / %s route / medicine %s / session checkpoint"%[return_gate.entry.hp,return_gate.entry.route,return_gate.entry.medicine],15,AMBER)
	panel(Rect2(30,662,1092,86))
	text(Vector2(48,687),"WASD move / ARROWS aim / J counter / K guard or feint / SPACE step / E work / ESC pause",17)
	var message:String=game.message.replace("courier safe","winch safe").replace("courier gains time","more time to work").replace("Sentinel focus","Ward focus")
	text(Vector2(48,718),"Working: no guard, blade or step. Moving, release or a hit cancels partial work." if return_gate.channel else message,17,AMBER)
	if game.mode!="play":
		panel(Rect2(90,220,972,365),Color("172535"))
		text(Vector2(125,271),"RETURN GATE PAUSED" if game.mode=="paused" else ("RETURN PASSAGE OPEN" if game.mode=="won" else "RETURN GATE FAILED"),32,TEAL if game.mode=="won" else AMBER)
		text(Vector2(125,318),"Health %d / %d    Winch %d / 2    Catches %d / 2"%[game.hp,game.health_limit,game.cargo,int(return_gate.raised[0])+int(return_gate.raised[1])],21)
		text(Vector2(125,361),"The courier stays safe. This separate ward guards the return mechanism.",19)
		text(Vector2(125,399),"Raise both catches AND cross the exit. Disabling the ward alone does not finish.",18,AMBER)
		draw_impact(Vector2(125,446))
		text(Vector2(125,532),"ENTER / ESC resume   /   R leave" if game.mode=="paused" else "ENTER retry from arrival   /   R leave   /   no extra keepsake",22,TEAL)
		text(Vector2(125,568),"Retry restores the entry checkpoint, not full health. No live outfit or approach swap.",17)
