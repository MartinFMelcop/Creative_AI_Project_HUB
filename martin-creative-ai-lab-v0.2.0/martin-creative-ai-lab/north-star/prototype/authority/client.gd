extends SceneTree
## A separate remote policy consumer; never steps or owns a Combat model.
const Policy=preload("res://tests/policy.gd")
var connection:=StreamPeerTCP.new()
var buffer:=""
var session:=""
var sequence:=0
var last_sent:=-1
var observation:Dictionary={}
var report_path:=""
var deadline:=0
var role:="Guardian"
var outfit:="standard"
var terminal_attack:=false
var terminal_confirmed:=false
var finished:=false
var rejections:Array=[]
var snapshots:=0
func send(data:Dictionary) -> void:
	connection.put_data((JSON.stringify(data,"",true)+"\n").to_utf8_buffer())
func quantize(value:Vector2) -> Array:
	return [roundi(value.x*1000),roundi(value.y*1000)]
func _initialize() -> void:
	var args=OS.get_cmdline_user_args()
	if args.size()!=4:quit(2);return
	report_path=args[1];role=args[2];outfit=args[3];deadline=Time.get_ticks_msec()+65000
	if connection.connect_to_host("127.0.0.1",int(args[0]))!=OK:quit(2)
func finish() -> void:
	if finished:return
	finished=true
	var result:Dictionary={"schema_version":1,"role":role,"outfit":outfit,"snapshots":snapshots,
		"state":observation,"rejects":rejections,"terminal_probe_sent":terminal_attack,"terminal_probe_confirmed":terminal_confirmed}
	var file=FileAccess.open(report_path,FileAccess.WRITE);file.store_string(JSON.stringify(result,"  ")+"\n");file.close()
	connection.disconnect_from_host();quit(0 if observation.get("mode","")=="won" and terminal_confirmed else 1)
func receive(data:Dictionary) -> void:
	if finished:return
	if data.kind=="welcome":session=data.session
	elif data.kind=="reject":
		rejections.append(data.reason)
		if terminal_attack and data.reason=="already_started":terminal_confirmed=true
		if session.is_empty():finish()
	elif data.kind=="state":
		snapshots+=1;observation=data.state
		if observation.mode in ["won","lost"]:
			if not terminal_attack:
				terminal_attack=true;send({"v":1,"kind":"hello","role":role,"style":"Steady" if role=="Guardian" else "none","outfit":outfit})
			elif terminal_confirmed:finish()
			return
		if int(data.tick)==last_sent or session.is_empty():return
		last_sent=int(data.tick)
		var state:Dictionary=observation.duplicate(true)
		for key in ["player","target","pulse"]:state[key]=Vector2(state[key][0],state[key][1])
		var input:Dictionary=Policy.command(state)
		# A low-rate remote controller eases toward its target instead of oscillating
		# across the original 3px/4px arrival tolerance between snapshots.
		var destination:Vector2=(Policy.Combat.ENEMY+state.target)*.5 if role=="Guardian" else Policy.Combat.ENEMY+Vector2(-100,-60)
		if input.get("move",Vector2.ZERO)!=Vector2.ZERO and ((role=="Guardian" and state.phase=="bolt") or (role=="Duelist" and state.phase not in ["bolt","pulse"])):
			input.move*=minf(1,state.player.distance_to(destination)/20)
		if data.quarantined:input={}
		send({"v":1,"kind":"input","session":session,"seq":sequence,"move":quantize(input.get("move",Vector2.ZERO)),
			"aim":quantize(input.get("aim",Vector2.RIGHT)),"guard":input.get("skill",false),"feint":input.get("skill_pressed",false),
			"step":input.get("dodge",false),"strike":input.get("strike",false)})
		sequence+=1
func _process(_delta:float) -> bool:
	connection.poll()
	if connection.get_status()==StreamPeerTCP.STATUS_CONNECTED:
		if last_sent<0 and session.is_empty():
			last_sent=0;connection.set_no_delay(true);send({"v":1,"kind":"hello","role":role,"style":"Steady" if role=="Guardian" else "none","outfit":outfit})
		var count:int=connection.get_available_bytes()
		if count>0:buffer+=connection.get_utf8_string(count)
		while buffer.contains("\n"):
			var end:int=buffer.find("\n");var line:String=buffer.substr(0,end);buffer=buffer.substr(end+1)
			var data=JSON.parse_string(line)
			if data is Dictionary:receive(data)
	elif connection.get_status()==StreamPeerTCP.STATUS_ERROR:quit(1)
	if Time.get_ticks_msec()>=deadline:finish()
	return false
