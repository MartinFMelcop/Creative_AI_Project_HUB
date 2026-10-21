extends SceneTree
## Loopback architecture prototype. The shipped single-player scene is unchanged.
const Combat=preload("res://combat.gd")
const STEP:=1.0/60.0
const FRAME_LIMIT:=512
const BUFFER_LIMIT:=4096
const BUTTONS:=["guard","feint","step","strike"]
var listener:=TCPServer.new()
var peer:StreamPeerTCP
var buffer:=PackedByteArray()
var game=Combat.new()
var started:=false
var session:=""
var high_water:=-1
var input_tick:=-100
var server_tick:=0
var active_tick:=0
var held:Dictionary={}
var previous:Dictionary={}
var quarantined:=true
var rejects:Dictionary={}
var accepted:=0
var stale_clears:=0
var disconnected:=false
var terminal_at:=-1
var report_path:=""
var deadline:=0
var port:=0

func integer(value,low:int,high:int) -> bool:
	return typeof(value) in [TYPE_INT,TYPE_FLOAT] and is_finite(float(value)) and float(value)==floor(float(value)) and value>=low and value<=high
func fields(data:Dictionary,names:Array) -> bool:
	return data.size()==names.size() and names.all(func(key):return data.has(key))
func vector(value) -> bool:
	return value is Array and value.size()==2 and integer(value[0],-1000,1000) and integer(value[1],-1000,1000)
func safe_tree(value,depth:int=0) -> bool:
	if depth>4:return false
	if typeof(value)==TYPE_FLOAT:return is_finite(value)
	if value is String:return value.length()<=128
	if value is Array:return value.size()<=16 and value.all(func(item):return safe_tree(item,depth+1))
	if value is Dictionary:
		if value.size()>16:return false
		for item in value.values():
			if not safe_tree(item,depth+1):return false
	return true
func canonical(value):
	if typeof(value)==TYPE_FLOAT and absf(value)<=2147483647 and value==floor(value):return int(value)
	if value is Array:return value.map(func(item):return canonical(item))
	if value is Dictionary:
		var result:Dictionary={}
		for key in value:result[key]=canonical(value[key])
		return result
	return value
func decode(line:PackedByteArray):
	if line.is_empty() or line.size()>FRAME_LIMIT:return null
	for byte in line:
		if byte<32 or byte>126:return null
	var text:String=line.get_string_from_ascii()
	var parser:=JSON.new()
	if parser.parse(text)!=OK or not parser.data is Dictionary or not safe_tree(parser.data):return null
	# Exact canonical ASCII JSON rejects duplicate keys and ambiguous number forms.
	var value:Dictionary=canonical(parser.data)
	if JSON.stringify(value,"",true)!=text:return null
	return value
func send(data:Dictionary) -> void:
	if peer and peer.get_status()==StreamPeerTCP.STATUS_CONNECTED:
		if peer.get_available_bytes()>BUFFER_LIMIT:return
		var bytes:PackedByteArray=(JSON.stringify(data,"",true)+"\n").to_utf8_buffer()
		var sent:Array=peer.put_partial_data(bytes)
		if sent[0]!=OK or sent[1]!=bytes.size():close_peer()
func reject(reason:String) -> void:
	rejects[reason]=rejects.get(reason,0)+1
	send({"v":1,"kind":"reject","reason":reason,"ack":high_water,"tick":server_tick})
func neutral() -> void:
	held.clear();previous.clear();quarantined=true
func close_peer() -> void:
	if peer:peer.disconnect_from_host()
	peer=null;buffer.clear();neutral()
	if started:disconnected=true
func message(data:Dictionary) -> void:
	if not data.get("kind") is String or not integer(data.get("v"),1,1):reject("schema");return
	if data.kind=="hello":
		if started:reject("already_started");return
		if not fields(data,["v","kind","role","style","outfit"]):reject("schema");return
		if not data.role in ["Guardian","Duelist"] or not data.style in (["Steady","Riposte"] if data.role=="Guardian" else ["none"]):reject("choice");return
		if not data.outfit is String or not game.fittings.has(data.outfit):reject("choice");return
		game.reset(data.role,data.style)
		if not game.fit_outfit(data.outfit):reject("choice");return
		started=true;active_tick=server_tick;session=Crypto.new().generate_random_bytes(16).hex_encode()
		send({"v":1,"kind":"welcome","session":session,"tick_hz":60,"stale_ticks":15})
		state();return
	if data.kind!="input" or not fields(data,["v","kind","session","seq","move","aim","guard","feint","step","strike"]):reject("schema");return
	if not started or not data.session is String or data.session!=session:reject("session");return
	if game.mode!="play":reject("terminal");return
	if not integer(data.seq,0,2147483647) or data.seq<=high_water or data.seq>high_water+64:reject("sequence");return
	if not vector(data.move) or not vector(data.aim) or not BUTTONS.all(func(key):return typeof(data[key])==TYPE_BOOL):reject("schema");return
	if input_tick==server_tick:reject("rate");return
	high_water=int(data.seq);input_tick=server_tick;accepted+=1
	if quarantined and BUTTONS.any(func(key):return data[key]):reject("release_required");return
	quarantined=false;held=data.duplicate(true)
func pump() -> void:
	if listener.is_connection_available():
		var candidate:StreamPeerTCP=listener.take_connection()
		if peer or started:
			candidate.put_partial_data((JSON.stringify({"v":1,"kind":"reject","reason":"occupied"})+"\n").to_utf8_buffer());candidate.disconnect_from_host()
		else:peer=candidate;peer.set_no_delay(true)
	if not peer:return
	peer.poll()
	if peer.get_status()!=StreamPeerTCP.STATUS_CONNECTED:close_peer();return
	var available:int=mini(peer.get_available_bytes(),BUFFER_LIMIT-buffer.size())
	if available>0:
		var received:Array=peer.get_data(available)
		if received[0]!=OK:close_peer();return
		buffer.append_array(received[1])
	for index in 16:
		var end:int=buffer.find(10)
		if end<0:break
		var line:PackedByteArray=buffer.slice(0,end);buffer=buffer.slice(end+1)
		var data=decode(line)
		if data==null:reject("frame")
		else:message(data)
	if buffer.size()>FRAME_LIMIT and buffer.find(10)<0:reject("oversize");close_peer()
func command() -> Dictionary:
	if input_tick>=0 and server_tick-input_tick>15 and not held.is_empty():
		neutral();stale_clears+=1
	if quarantined or held.is_empty():return {}
	var move:Vector2=Vector2(held.move[0],held.move[1])/1000
	var aim:Vector2=Vector2(held.aim[0],held.aim[1])/1000
	var result:Dictionary={"move":move.limit_length(),"aim":aim.limit_length(),"skill":held.guard,
		"skill_pressed":held.feint and not previous.get("feint",false),"dodge":held.step and not previous.get("step",false),
		"strike":held.strike and not previous.get("strike",false)}
	previous=held.duplicate();return result
static func action_hints(model) -> Dictionary:
	# Advisory facts at this snapshot, never an admission token for a future input.
	var step_status:String="ready"
	if model.step_cooldown>0:step_status="recovering"
	elif model.energy<25:step_status="resolve"
	var counter_status:String="ready"
	if model.enemy_focus==0:counter_status="silent"
	elif model.guard:counter_status="guard"
	elif model.step_left>0:counter_status="stepping"
	elif model.strike_cooldown>0:counter_status="recovering"
	elif model.energy<12:counter_status="resolve"
	elif model.player.distance_to(Combat.ENEMY)>130:counter_status="range"
	elif model.opening<=0:counter_status="armored"
	var technique_status:String="hold"
	var technique_cost:float=22.0
	var technique_wait:float=0.0
	var drain:float=12.0
	if model.role=="Guardian":
		if model.phase=="pulse":technique_status="ground"
		elif model.step_left>0:technique_status="stepping"
		elif model.energy<22:technique_status="resolve"
		elif model.guard:technique_status=model.guard_state().to_lower()
	else:
		technique_cost=16;drain=0;technique_wait=model.feint_cooldown
		technique_status="ready"
		if model.enemy_focus==0:technique_status="silent"
		elif model.phase!="bolt":technique_status="bolt"
		elif model.redirected:technique_status="drawn"
		elif model.player.distance_to(Combat.ENEMY)>340:technique_status="range"
		elif model.energy<16:technique_status="resolve"
		elif model.feint_cooldown>0:technique_status="recovering"
	if model.mode!="play":step_status="terminal";counter_status="terminal";technique_status="terminal"
	return {"counter_radius":130.0,"draw_radius":340.0,
		"step":{"status":step_status,"cost":25.0,"wait":model.step_cooldown,"drain":0.0},
		"counter":{"status":counter_status,"cost":12.0,"wait":model.strike_cooldown,"drain":0.0},
		"technique":{"status":technique_status,"cost":technique_cost,"wait":technique_wait,"drain":drain}}

func state() -> void:
	if not started:return
	var value:Dictionary=game.snapshot();value.erase("events")
	value.merge({"player":[game.player.x,game.player.y],"target":[game.target.x,game.target.y],"pulse":[game.pulse.x,game.pulse.y],
		"phase":game.phase,"clock":game.clock,"opening":game.opening,"redirected":game.redirected,"guard":game.guard},true)
	# Read-only presentation facts. The client never reconstructs a Combat model.
	value.merge({"courier":[game.courier.x,game.courier.y],"facing":[game.facing.x,game.facing.y],
		"locked_face":[game.locked_face.x,game.locked_face.y],"guard_state":game.guard_state(),
		"step_left":game.step_left,"step_dir":[game.step_dir.x,game.step_dir.y],
		"strike_cooldown":game.strike_cooldown,"feint_cooldown":game.feint_cooldown,
		"step_cooldown":game.step_cooldown,"health_limit":game.health_limit,
		"message":game.message,"last_impact":game.last_impact.duplicate(true),"actions":action_hints(game)},true)
	send({"v":1,"kind":"state","state":value,"ack":high_water,"tick":server_tick,"quarantined":quarantined,
		"accepted":accepted,"rejected":rejects.duplicate(),"stale_clears":stale_clears})
func finish() -> void:
	var identities:Dictionary={}
	for name in ["combat.gd","route.gd","fittings.gd","data/fittings.json","project.godot"]:identities[name]=FileAccess.get_sha256("res://"+name)
	var result:Dictionary={"schema_version":1,"server_ticks":server_tick,"active_ticks":server_tick-active_tick,
		"accepted":accepted,"rejected":rejects,"stale_clears":stale_clears,"disconnected":disconnected,
		"guard":game.guard,"quarantined":quarantined,"position":[game.player.x,game.player.y],
		"model":game.snapshot(),"consumer_hashes":identities}
	var file=FileAccess.open(report_path,FileAccess.WRITE)
	if file==null:quit(2);return
	file.store_string(JSON.stringify(result,"  ")+"\n");file.close();close_peer();listener.stop();quit()
func _initialize() -> void:
	var args=OS.get_cmdline_user_args()
	if args.size()!=3 or not args[0].is_valid_int() or not args[2].is_valid_int():quit(2);return
	port=int(args[0]);report_path=args[1];var seconds:int=int(args[2])
	if port<1024 or port>65535 or seconds<2 or seconds>120:quit(2);return
	if Engine.physics_ticks_per_second!=60 or Engine.time_scale!=1.0:quit(2);return
	if not game.content_errors.is_empty() or listener.listen(port,"127.0.0.1")!=OK:quit(2);return
	deadline=Time.get_ticks_msec()+seconds*1000
	print("AUTHORITY_READY ",port)
func _physics_process(_delta:float) -> bool:
	server_tick+=1;pump()
	if started:
		game.step(STEP,command())
		if server_tick%3==0:state()
		if game.mode in ["won","lost"] and terminal_at<0:terminal_at=server_tick;state()
	if Time.get_ticks_msec()>=deadline or (terminal_at>=0 and server_tick-terminal_at>=120):finish()
	return false
