extends Node2D
const Model=preload("model.gd")
const Catalog=preload("catalog.gd")
const INK=Color("101b2b")
const PAPER=Color("e9eddf")
const TEAL=Color("5ae0ce")
const AMBER=Color("ffc474")
const RED=Color("ff796f")
var catalog_path:=Catalog.PATH
var model
var choices:Array=["none"]
var choice:=0
var held:Dictionary={}
var edges:Dictionary={}
var paused:=false
var focused:=true
var captures:=0
var font=ThemeDB.fallback_font
func _ready() -> void:
	DisplayServer.window_set_title("Virgo Diamond — Ability Bench")
	model=Model.new(catalog_path)
	if model.catalog.ok:choices.append_array(model.catalog.items.keys())
func _notification(what:int) -> void:
	if what in [NOTIFICATION_APPLICATION_FOCUS_OUT,NOTIFICATION_WM_WINDOW_FOCUS_OUT]:
		focused=false
		if model!=null and model.game.mode=="play":paused=true
		held.clear();edges.clear()
	elif what in [NOTIFICATION_APPLICATION_FOCUS_IN,NOTIFICATION_WM_WINDOW_FOCUS_IN]:focused=true
func _input(event:InputEvent) -> void:
	if not event is InputEventKey:return
	var code=event.keycode
	if not event.pressed:held.erase(code);return
	if event.echo:return
	if code==KEY_Q:get_tree().quit();return
	if code==KEY_F12:capture.call_deferred();return
	if model==null:return
	if code==KEY_ESCAPE:
		if focused:paused=not paused
		held.clear();edges.clear();return
	if model.game.mode=="title":
		if code==KEY_TAB:choice=(choice+1)%choices.size();model.prepare(choices[choice])
		elif code==KEY_ENTER:model.begin();paused=false;held.clear();edges.clear()
		return
	if model.game.mode in ["won","lost"] and code==KEY_ENTER:
		model=Model.new(catalog_path);model.prepare(choices[choice]);held.clear();edges.clear();return
	if paused or not focused:return
	held[code]=true
	if code==KEY_E:edges.rush=true
	elif code==KEY_SPACE:edges.dodge=true
	elif code==KEY_J:edges.strike=true
func _physics_process(delta:float) -> void:
	if model!=null and not paused and focused:
		var command=edges.duplicate();edges.clear()
		command.move=Vector2(int(held.has(KEY_D))-int(held.has(KEY_A)),int(held.has(KEY_S))-int(held.has(KEY_W)))
		command.aim=(get_global_mouse_position()-model.game.player).normalized()
		command.skill=held.has(KEY_K)
		model.step(delta,command)
	queue_redraw()
func label(at:Vector2,value:String,size:int=18,color:Color=PAPER) -> void:
	draw_string(font,at,value,HORIZONTAL_ALIGNMENT_LEFT,-1,size,color)
func _draw() -> void:
	draw_rect(Rect2(0,0,1152,768),INK)
	label(Vector2(38,42),"ABILITY BENCH / COMMITTED RUSH",27,TEAL)
	label(Vector2(38,73),"Experimental Guardian behavior • source-only developer consumer • not final class canon",17)
	if model==null:return
	if not model.catalog.ok:
		label(Vector2(38,140),model.catalog.error,22,RED);return
	var g=model.game
	if g.mode=="title":
		label(Vector2(38,125),"Choose one rush, or keep the unchanged crossing baseline.",23)
		var y:=192
		for id in choices:
			var selected=id==choices[choice]
			draw_rect(Rect2(32,y-32,1088,100),Color("244b53") if selected else Color("172a3d"))
			if id=="none":
				label(Vector2(52,y),"> BASELINE / no added ability" if selected else "BASELINE / no added ability",22)
				label(Vector2(52,y+34),"The existing paid step, guard and counter remain available.")
			else:
				var row:Dictionary=model.catalog.items[id]
				label(Vector2(52,y),(" > " if selected else "")+row.name.to_upper(),22)
				label(Vector2(52,y+34),"%.0f resolve • %.0fpx travel • %.2fs locked + %.2fs recovery • %.2fs cooldown"%[row.cost,row.speed*row.travel,row.travel,row.recovery,row.cooldown])
			y+=119
		label(Vector2(38,590),"Tab: compare    Enter: commit once    Q: close",22,TEAL)
		label(Vector2(38,630),"Rush locks its aim; threats keep advancing. It grants no immunity or automatic counter.")
		label(Vector2(38,662),"After arrival, walking recovers resolve; guard, step and strike wait for recovery.")
		label(Vector2(38,704),"Choices stay locked through the crossing. Retry is available after a terminal result.")
		return
	label(Vector2(38,112),"%s / %s    HP %d    Cargo %d    Resolve %.1f"%[model.selected.to_upper(),model.status(),g.hp,g.cargo,g.energy],23)
	label(Vector2(38,143),"WASD move / mouse aim / K guard / J counter / Space step / E rush / Esc pause",17)
	draw_rect(Model.Combat.FIELD,Color("1a3040"))
	draw_line(Vector2(130,390),Vector2(1040,390),Color("60716f"),3)
	draw_line(Vector2(1000,190),Vector2(1000,640),TEAL,4)
	if g.phase=="bolt":draw_line(Model.Combat.ENEMY,g.target,AMBER,4)
	if g.phase=="pulse":draw_arc(g.pulse,90,0,TAU,64,RED,4)
	draw_circle(Model.Combat.ENEMY,23,RED)
	label(Model.Combat.ENEMY+Vector2(-90,-42),g.sentinel_status(),15)
	draw_circle(g.courier,15,AMBER)
	if model.travel_left>0:
		draw_line(g.player,g.player+model.direction*float(model.catalog.items[model.selected].speed)*model.travel_left,TEAL,8)
	if g.opening>0:draw_arc(Model.Combat.ENEMY,130,0,TAU,64,TEAL,2)
	draw_circle(g.player,18,TEAL)
	draw_line(g.player,g.player+g.facing*33,PAPER,3)
	if g.guard:draw_arc(g.player,30,g.locked_face.angle()-.9,g.locked_face.angle()+.9,24,PAPER,4)
	label(Vector2(38,675),model.reason,17,TEAL)
	label(Vector2(38,705),g.message,17)
	label(Vector2(38,739),"Travel %.2f / recovery %.2f / cooldown %.2f   %s"%[model.travel_left,model.recovery_left,model.cooldown,"PAUSED — Esc resumes" if paused else ("Enter: return to preparation" if g.mode in ["won","lost"] else "World live; rush grants no immunity")],17,AMBER)
func observation() -> Dictionary:
	return {"capture":captures,"selected":model.selected,"status":model.status(),"paused":paused,"player":[model.game.player.x,model.game.player.y],"starts":model.starts,"refusals":model.refusals,"travel":model.travel_left,"recovery":model.recovery_left,"cooldown":model.cooldown,"combat":model.game.snapshot()}
func capture() -> void:
	var path=OS.get_environment("NORTH_STAR_ABILITY_CAPTURE")
	if path.is_empty():return
	await RenderingServer.frame_post_draw
	captures+=1
	get_viewport().get_texture().get_image().save_png(path+".png")
	var file=FileAccess.open(path+".json",FileAccess.WRITE)
	if file:file.store_string(JSON.stringify(observation(),"  ")+"\n")
