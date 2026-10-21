extends RefCounted
## Snapshot-only loopback transport. This object never constructs or advances Combat.
const FRAME_LIMIT := 16384
const BUFFER_LIMIT := 65536
const INTERVAL := 0.05
const STALE_AFTER := 0.25
var connection := StreamPeerTCP.new()
var buffer := PackedByteArray()
var status := "closed"
var reason := "Not connected."
var latest: Dictionary = {}
var confirmed: Dictionary = {}
var session := ""
var catalog:Dictionary={}
var prepare_only:=false
var sequence := 0
var position := Vector2.ZERO
var courier_position := Vector2.ZERO
var age := 0.0
var rejected := 0
var snapshots := 0
var deadline := 0
var hello: Dictionary = {}
var hello_sent := false
var next_send_ms := 0
var from_player := Vector2.ZERO
var to_player := Vector2.ZERO
var from_courier := Vector2.ZERO
var to_courier := Vector2.ZERO
var blend_time := INTERVAL

static func integer(value, low: int, high: int) -> bool:
	return typeof(value) in [TYPE_INT, TYPE_FLOAT] and is_finite(float(value)) and float(value)==floor(float(value)) and value>=low and value<=high

static func finite_vector(value) -> bool:
	return value is Array and value.size()==2 and value.all(func(item): return typeof(item) in [TYPE_INT, TYPE_FLOAT] and is_finite(float(item)) and absf(float(item))<=10000)

static func safe_tree(value, depth: int=0) -> bool:
	if depth>8: return false
	if typeof(value)==TYPE_FLOAT: return is_finite(value)
	if value is String: return value.length()<=2048
	if value is Array: return value.size()<=128 and value.all(func(item): return safe_tree(item, depth+1))
	if value is Dictionary:
		if value.size()>64: return false
		for key in value:
			if not key is String or key.length()>64 or not safe_tree(value[key], depth+1): return false
	return true

func fail(message: String) -> void:
	connection.disconnect_from_host()
	buffer.clear()
	if status!="terminal": status="error"; reason=message

func close() -> void:
	connection.disconnect_from_host()
	buffer.clear()
	if status!="terminal": status="closed"; reason="Disconnected. The server world is not paused."

func connect_session(port: int, role: String="Guardian", style: String="Steady", outfit: String="standard", inspect:bool=false) -> bool:
	close()
	latest.clear(); confirmed.clear(); catalog.clear();prepare_only=inspect; session=""; sequence=0; age=0; rejected=0; snapshots=0
	position=Vector2.ZERO; courier_position=Vector2.ZERO; next_send_ms=0; hello_sent=false
	if port<1024 or port>65535 or role not in ["Guardian", "Duelist"] or style not in (["Steady", "Riposte"] if role=="Guardian" else ["none"]) or outfit.is_empty() or outfit.length()>64:
		status="error"; reason="Invalid session choice."; return false
	hello={"v":1,"kind":"hello","role":role,"style":style,"outfit":outfit}
	if inspect:hello={"v":1,"kind":"catalog"}
	connection=StreamPeerTCP.new()
	status="connecting"; reason="Connecting to local authority."
	deadline=Time.get_ticks_msec()+3000
	if connection.connect_to_host("127.0.0.1", port)!=OK:
		fail("Local authority connection failed."); return false
	return true

func start_prepared(role:String,style:String,outfit:String) -> bool:
	if status!="preparing" or not catalog.techniques.has(role):return false
	if not catalog.techniques[role].any(func(row):return row.id==style) or not catalog.outfits.any(func(row):return row.id==outfit):return false
	hello={"v":1,"kind":"hello","role":role,"style":style,"outfit":outfit}
	if not write(hello):return false
	status="joining";reason="Confirming selected preparation.";deadline=Time.get_ticks_msec()+3000
	return true

static func valid_catalog(data:Dictionary) -> bool:
	if data.size()!=4 or not data.get("outfits") is Array or data.outfits.is_empty() or data.outfits.size()>16:return false
	if not data.get("techniques") is Dictionary or data.techniques.size()!=2:return false
	var ids:Array=[]
	for row in data.outfits:
		if not row is Dictionary or row.size()!=5 or not row.get("id") is String or row.id.is_empty() or row.id.length()>64 or row.id in ids:return false
		if not row.get("name") is String or row.name.is_empty() or row.name.length()>80:return false
		if not integer(row.get("health"),1,6) or not finite_number(row.get("movement"),.25,2) or not finite_number(row.get("recovery"),1,100):return false
		ids.append(row.id)
	for role in ["Guardian","Duelist"]:
		var rows=data.techniques.get(role)
		if not rows is Array or rows.size()!=(2 if role=="Guardian" else 1):return false
		var styles:Array=[]
		for row in rows:
			if not row is Dictionary or row.size()!=2 or row.get("id") not in (["Steady","Riposte"] if role=="Guardian" else ["none"]) or row.id in styles:return false
			if not row.get("summary") is String or row.summary.length()>150:return false
			styles.append(row.id)
	return true

func matches_preparation(state:Dictionary) -> bool:
	if not prepare_only:return true
	var actual=state.get("preparation")
	if not actual is Dictionary or actual.size()!=6:return false
	if not integer(actual.get("health"),1,6) or not finite_number(actual.get("movement"),.25,2) or not finite_number(actual.get("recovery"),1,100):return false
	if actual.get("role")!=hello.role or actual.get("style")!=hello.style or actual.get("outfit")!=hello.outfit:return false
	var items:Array=catalog.outfits.filter(func(row):return row.id==hello.outfit)
	if items.size()!=1:return false
	for key in ["health","movement","recovery"]:
		if actual.get(key)!=items[0][key]:return false
	return state.get("role")==hello.role and state.get("guard_style")==hello.style and state.get("health_limit")==actual.health

func write(data: Dictionary) -> bool:
	if connection.get_status()!=StreamPeerTCP.STATUS_CONNECTED: return false
	var bytes: PackedByteArray=(JSON.stringify(data,"",true)+"\n").to_utf8_buffer()
	var sent: Array=connection.put_partial_data(bytes)
	if sent[0]!=OK or sent[1]!=bytes.size():
		fail("Authority transport could not accept an intent."); return false
	return true

func can_send() -> bool:
	return status=="live" and can_send_neutral()

func can_send_neutral() -> bool:
	return status in ["live","stale"] and not session.is_empty() and not latest.is_empty() and Time.get_ticks_msec()>=next_send_ms

func send_neutral() -> bool:
	# The stale path cannot accept caller-supplied movement or paid actions.
	if not can_send_neutral(): return false
	return _transmit({})

func send_intent(input: Dictionary) -> bool:
	if not can_send(): return false
	return _transmit(input)

func _transmit(input: Dictionary) -> bool:
	if not can_send_neutral() or (status=="stale" and not input.is_empty()): return false
	var move=input.get("move",Vector2.ZERO)
	var aim=input.get("aim",Vector2.ZERO)
	if not move is Vector2 or not aim is Vector2 or not move.is_finite() or not aim.is_finite(): return false
	for key in ["guard","feint","step","strike"]:
		if input.has(key) and typeof(input[key])!=TYPE_BOOL: return false
	move=move.limit_length(); aim=aim.limit_length()
	var intent={"v":1,"kind":"input","session":session,"seq":sequence,
		"move":[roundi(move.x*1000),roundi(move.y*1000)],"aim":[roundi(aim.x*1000),roundi(aim.y*1000)],
		"guard":input.get("guard",false),"feint":input.get("feint",false),"step":input.get("step",false),"strike":input.get("strike",false)}
	if not write(intent): return false
	next_send_ms=Time.get_ticks_msec()+50; sequence+=1
	return true

static func finite_number(value, low: float, high: float) -> bool:
	return typeof(value) in [TYPE_INT,TYPE_FLOAT] and is_finite(float(value)) and value>=low and value<=high

static func valid_actions(value) -> bool:
	if not value is Dictionary or value.size()!=5: return false
	for key in ["counter_radius","draw_radius"]:
		if not finite_number(value.get(key),1,1000): return false
	var statuses={"step":["ready","recovering","resolve","terminal"],
		"counter":["ready","silent","guard","stepping","recovering","resolve","range","armored","terminal"],
		"technique":["hold","ground","stepping","resolve","startup","live","stale","ready","silent","bolt","drawn","range","recovering","terminal"]}
	for key in statuses:
		var row=value.get(key)
		if not row is Dictionary or row.size()!=4 or row.get("status") not in statuses[key]: return false
		if not finite_number(row.get("cost"),0,100) or not finite_number(row.get("wait"),0,120) or not finite_number(row.get("drain"),0,100): return false
	return true

func valid_state(data: Dictionary) -> bool:
	if not integer(data.get("tick"),0,2147483647) or not integer(data.get("ack"),-1,2147483647) or typeof(data.get("quarantined"))!=TYPE_BOOL or not data.get("state") is Dictionary: return false
	var state: Dictionary=data.state
	if not valid_actions(state.get("actions")): return false
	if state.get("mode") not in ["play","won","lost"] or state.get("role") not in ["Guardian","Duelist"]: return false
	if not integer(state.get("tick"),0,int(data.tick)) or not integer(state.get("enemy_focus"),0,3): return false
	if not integer(state.get("health_limit"),1,6) or not integer(state.get("hp"),0,int(state.health_limit)) or not integer(state.get("cargo"),0,3): return false
	if not finite_number(state.get("energy"),0,100): return false
	if not state.get("message") is String or state.message.length()>1024 or not state.get("last_impact") is Dictionary: return false
	if state.get("phase") not in ["rest","bolt","pulse","disabled"]: return false
	if state.get("guard_state") not in ["DOWN","STARTUP","LIVE","STALE"] or typeof(state.get("guard"))!=TYPE_BOOL or typeof(state.get("redirected"))!=TYPE_BOOL: return false
	if state.guard!=(state.guard_state!="DOWN"): return false
	if state.get("guard_style") not in (["Steady","Riposte"] if state.role=="Guardian" else ["none"]): return false
	if not state.get("counters") is Dictionary or not integer(state.counters.get("counters"),0,3): return false
	for count in state.counters.values():
		if not integer(count,0,100000): return false
	for key in ["player","courier","facing","locked_face","target","pulse","step_dir"]:
		if not finite_vector(state.get(key)): return false
	for key in ["step_left","strike_cooldown","feint_cooldown","step_cooldown","opening"]:
		if not finite_number(state.get(key),0,120): return false
	# A paid counter deliberately gives the actual model a negative rest clock.
	if not finite_number(state.get("clock"),-2,120): return false
	return true

func receive_message(data: Dictionary) -> void:
	if not safe_tree(data) or not integer(data.get("v"),1,1): fail("Invalid authority message."); return
	if data.get("kind")=="catalog":
		if not prepare_only or status!="connecting" or not catalog.is_empty() or not valid_catalog(data):fail("Invalid preparation catalog.");return
		catalog=data.duplicate(true);status="preparing";reason="Compare server values, then Enter to commit."
	elif data.get("kind")=="welcome":
		if (prepare_only and status!="joining") or not session.is_empty() or not data.get("session") is String or data.session.length()!=32:
			fail("Invalid authority welcome."); return
		session=data.session; reason="Waiting for confirmed world state."
	elif data.get("kind")=="reject":
		if not data.get("reason") is String: fail("Invalid authority rejection."); return
		rejected+=1; reason="Authority rejected intent: "+data.reason
		if session.is_empty(): fail(reason)
	elif data.get("kind")=="state":
		if session.is_empty() or not valid_state(data) or not matches_preparation(data.state): fail("Invalid authority snapshot."); return
		if status=="terminal" and data.state.mode!=confirmed.mode: return
		if not latest.is_empty() and int(data.tick)<=int(latest.tick): return
		var next_player=Vector2(data.state.player[0],data.state.player[1])
		var next_courier=Vector2(data.state.courier[0],data.state.courier[1])
		var snap: bool=latest.is_empty() or status=="stale" or data.state.mode!="play" or data.quarantined or confirmed.get("phase")!=data.state.get("phase")
		from_player=next_player if snap else to_player; from_courier=next_courier if snap else to_courier
		to_player=next_player; to_courier=next_courier; blend_time=INTERVAL if snap else 0.0
		latest=data.duplicate(true); confirmed=latest.state; snapshots+=1; age=0.0
		position=from_player; courier_position=from_courier
		status="terminal" if confirmed.mode in ["won","lost"] else "live"
		reason="Confirmed "+str(confirmed.mode)+"." if status=="terminal" else ("Release action buttons to rearm." if latest.quarantined else "Server-confirmed world; presentation interpolation only.")
	else: fail("Unknown authority message.")

func advance_presentation(delta: float) -> void:
	if not is_finite(delta) or delta<0: return
	if latest.is_empty() or status in ["closed","error","terminal"]: return
	age+=delta
	if age>STALE_AFTER:
		status="stale"; reason="World updates delayed. Inputs blocked; the server is not paused."; return
	blend_time=minf(INTERVAL,blend_time+delta)
	var weight: float=clampf(blend_time/INTERVAL,0,1)
	position=from_player.lerp(to_player,weight)
	courier_position=from_courier.lerp(to_courier,weight)

func poll(delta: float) -> void:
	advance_presentation(delta)
	if status in ["closed","error"]: return
	connection.poll()
	var connected: int=connection.get_status()
	if connected==StreamPeerTCP.STATUS_CONNECTING:
		if Time.get_ticks_msec()>=deadline: fail("Local authority connection timed out.")
		return
	if connected!=StreamPeerTCP.STATUS_CONNECTED:
		if status=="terminal": return
		fail("Authority disconnected. The world cannot be simulated locally."); return
	if not hello_sent:
		hello_sent=write(hello)
		if not hello_sent: return
	var available: int=connection.get_available_bytes()
	if available>BUFFER_LIMIT-buffer.size(): fail("Authority buffer exceeded its limit."); return
	if available>0:
		var received: Array=connection.get_partial_data(available)
		if received[0]!=OK: fail("Authority read failed."); return
		buffer.append_array(received[1])
	for index in 64:
		var end: int=buffer.find(10)
		if end<0: break
		if end==0 or end>FRAME_LIMIT: fail("Authority frame exceeded its limit."); return
		var line: PackedByteArray=buffer.slice(0,end); buffer=buffer.slice(end+1)
		var parser:=JSON.new()
		if parser.parse(line.get_string_from_utf8())!=OK or not parser.data is Dictionary:
			fail("Invalid authority frame."); return
		receive_message(parser.data)
		if status=="error": return
	if buffer.size()>FRAME_LIMIT and buffer.find(10)<0: fail("Unterminated authority frame exceeded its limit.")
	if session.is_empty() and status!="preparing" and Time.get_ticks_msec()>=deadline: fail("Authority welcome timed out.")
