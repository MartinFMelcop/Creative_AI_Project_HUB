extends SceneTree
## Synthetic native input drives the actual view; the authority owns every outcome.
const View=preload("../authority/view.gd")
const ENEMY:=Vector2(790,390)
var view
var port:=0
var role:="Guardian"
var output:=""
var deadline:=0
var terminal_at:=-1
var terminal_tick:=-1
var terminal_mode:=""
var last_tick:=-1
var last_strike:=-100
var bolt_used:=false
var pressed:Dictionary={}
var input_events:=0
var finished:=false
var capture_prefix:=""
var retained_capture_at:=-1
func key(code:int,down:bool) -> void:
	if pressed.has(code)==down:return
	if down:pressed[code]=true
	else:pressed.erase(code)
	var event:=InputEventKey.new();event.keycode=code;event.physical_keycode=code;event.pressed=down
	Input.parse_input_event(event);input_events+=1
func tap(code:int) -> void:
	key(code,true);key(code,false)
func release() -> void:
	for code in pressed.keys():key(code,false)
func _initialize() -> void:
	var args=OS.get_cmdline_user_args()
	if args.size()!=3 or not args[0].is_valid_int() or args[1] not in ["Guardian","Duelist"]:quit(2);return
	port=int(args[0]);role=args[1];output=args[2];deadline=Time.get_ticks_msec()+65000
	capture_prefix=OS.get_environment("NORTH_STAR_REMOTE_CAPTURE")
	view=View.new();view.port=port;view.selected=role;root.add_child.call_deferred(view)
	call_deferred("start")
func start() -> void:
	root.content_scale_size=Vector2i(1152,768)
	root.size=Vector2i(1152,768)
	await process_frame
	var motion:=InputEventMouseMotion.new();motion.position=ENEMY;motion.global_position=ENEMY
	Input.parse_input_event(motion);input_events+=1
	tap(KEY_ENTER)
func capture(suffix:String) -> void:
	if capture_prefix.is_empty() or DisplayServer.get_name()=="headless":return
	OS.set_environment("NORTH_STAR_REMOTE_CAPTURE",capture_prefix+suffix)
	view.capture()
func finish(success:bool,reason:String) -> void:
	if finished:return
	finished=true;release()
	var observation:Dictionary=view.observation()
	var report:Dictionary={"schema_version":1,"role":role,"success":success,"reason":reason,"input_events":input_events,
		"observation":observation,"snapshots":view.remote.snapshots,"terminal_tick":terminal_tick,
		"authority_closed":view.remote.connection.get_status()!=StreamPeerTCP.STATUS_CONNECTED,
		"limits":"Synthetic Input.parse_input_event drives the actual view. No independent player, physical device, latency or capacity claim."}
	var file=FileAccess.open(output,FileAccess.WRITE)
	if not file:quit(2);return
	file.store_string(JSON.stringify(report,"  ")+"\n");file.close()
	view.remote.close();quit(0 if success else 1)
func _process(_delta:float) -> bool:
	if finished or view==null:return false
	var now:int=Time.get_ticks_msec()
	if now>=deadline:finish(false,"Remote input journey timed out.");return false
	var state:Dictionary=view.remote.confirmed
	if state.is_empty():
		if view.remote.status=="preparing":tap(KEY_ENTER)
		if view.remote.status=="error":finish(false,view.remote.reason)
		return false
	if state.mode in ["won","lost"]:
		release()
		if terminal_at<0:
			terminal_at=now;terminal_tick=int(state.tick);terminal_mode=state.mode
			capture("-terminal")
		if now-terminal_at>=2500 and view.remote.connection.get_status()!=StreamPeerTCP.STATUS_CONNECTED:
			if retained_capture_at<0:
				retained_capture_at=now;capture("-retained");return false
			# Let the asynchronous viewport capture finish before owned process shutdown.
			if now-retained_capture_at<100:return false
			var retained:bool=view.remote.status=="terminal" and state.mode==terminal_mode and int(state.tick)==terminal_tick
			finish(retained and state.role==role and state.mode=="won" and state.hp>0 and state.cargo>0,"Confirmed terminal state retained after actual authority closure.")
		elif now-terminal_at>5000:finish(false,"Authority did not close after terminal grace.")
		return false
	if view.remote.status=="error":finish(false,view.remote.reason);return false
	if int(view.remote.latest.tick)==last_tick:return false
	last_tick=int(view.remote.latest.tick)
	if view.controls.suspended:
		release();tap(KEY_ESCAPE);return false
	if view.remote.latest.quarantined or view.controls.quarantined:
		release();return false
	var player:=Vector2(state.player[0],state.player[1])
	var move:=Vector2.ZERO
	var guard:=false
	var strike:=false
	if state.phase!="bolt":bolt_used=false
	if role=="Guardian":
		if state.phase=="bolt":
			var destination:Vector2=(ENEMY+Vector2(state.target[0],state.target[1]))*.5
			if player.distance_to(destination)<=18:guard=true
			else:
				var offset:Vector2=destination-player
				move=Vector2(signf(offset.x) if absf(offset.x)>10 else 0,signf(offset.y) if absf(offset.y)>10 else 0)
		elif state.phase=="pulse" and player.distance_to(Vector2(state.pulse[0],state.pulse[1]))<110:move=Vector2.UP
		elif state.opening>0 and player.distance_to(ENEMY)<=130 and state.strike_cooldown<=0:strike=true
	else:
		if state.phase=="bolt":
			move=Vector2.UP
			if not bolt_used:
				bolt_used=true
				if not state.redirected:tap(KEY_J)
				tap(KEY_SPACE)
		elif state.phase=="pulse" and player.distance_to(Vector2(state.pulse[0],state.pulse[1]))<110:move=Vector2.LEFT
		else:
			var offset:Vector2=ENEMY+Vector2(-100,-60)-player
			move=Vector2(signf(offset.x) if absf(offset.x)>6 else 0,signf(offset.y) if absf(offset.y)>6 else 0)
			if state.opening>0 and player.distance_to(ENEMY)<=130 and state.strike_cooldown<=0:strike=true
	key(KEY_W,move.y<0);key(KEY_S,move.y>0);key(KEY_A,move.x<0);key(KEY_D,move.x>0);key(KEY_K,guard)
	if strike and int(state.tick)-last_strike>=30:
		last_strike=int(state.tick);tap(KEY_L)
	return false
