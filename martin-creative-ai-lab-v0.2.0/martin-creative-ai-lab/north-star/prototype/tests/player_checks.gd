extends RefCounted
## Opt-in verification of the actual release scene, not an alternate game model.
const Policy=preload("res://tests/policy.gd")
const GatePolicy=preload("res://tests/gate_policy.gd")
const LOOK:={"skin":2,"hair":1,"dye":1}
var labels:Array[String]=[]
var failures:Array[String]=[]
func check(value: bool,label: String) -> void:
	labels.append(label)
	if not value:failures.append(label);push_error(label)
func key(scene,code: int) -> void:
	var event=InputEventKey.new();event.pressed=true;event.keycode=code;event.physical_keycode=code
	scene._unhandled_key_input(event)
func run(scene,output: String,read_only: bool) -> bool:
	var journeys:Array=[]
	check(scene.game.mode=="title" and scene.game.snapshot().tick==0,"Default scene starts a fresh selection")
	if read_only:
		check(scene.character_look.applied==LOOK,"New release process retains the applied free look")
		check(scene.keepsakes.earned==["held_line","drew_danger"] and scene.keepsakes.equipped=="","New release process retains earned marks without auto-wear")
	else:
		check(scene.keepsakes.earned.is_empty() and scene.keepsakes.look.is_empty(),"Controlled release profile starts empty")
		for code in [KEY_F3,KEY_RIGHT,KEY_RIGHT,KEY_DOWN,KEY_RIGHT,KEY_DOWN,KEY_RIGHT,KEY_ENTER]:key(scene,code)
		check(scene.character_look.applied==LOOK and not scene.keepsakes.dirty,"Actual editor applies and saves in the release runtime")
		var prior=FileAccess.get_file_as_bytes(scene.profile_path)
		for code in [KEY_F3,KEY_RIGHT,KEY_ESCAPE]:key(scene,code)
		check(FileAccess.get_file_as_bytes(scene.profile_path)==prior and scene.character_look.applied==LOOK,"Release cancellation preserves profile bytes and applied look")
		for role in ["Guardian","Duelist"]:
			scene.selected=role;scene.begin_crossing()
			for i in 4200:
				if scene.game.mode!="play":break
				scene.advance_crossing(1.0/60,Policy.command(scene.game))
			check(scene.game.mode=="won" and scene.game.cargo>0,"Actual release escort completes: "+role)
			var escort=scene.game.snapshot()
			key(scene,KEY_F4);key(scene,KEY_2);key(scene,KEY_ENTER)
			check(scene.courier_talk.choice=="brace","Confirmed release conversation selects one winch brace: "+role)
			check(scene.begin_return_gate() and scene.game.cargo==3,"Real release arrival enters the braced second goal: "+role)
			for i in 6000:
				if scene.game.mode!="play":break
				scene.advance_crossing(1.0/60,GatePolicy.command(scene.return_gate,"work"))
			check(scene.game.mode=="won" and scene.game.cargo>0,"Actual braced return completes: "+role)
			check(scene.character_look.applied==LOOK,"Applied look survives both release goals: "+role)
			journeys.append({"role":role,"escort":escort,"return_gate":scene.return_gate.snapshot()})
			scene.abandon()
		check(scene.keepsakes.earned==["held_line","drew_danger"] and scene.keepsakes.equipped=="","Release journeys earn both marks without auto-wear")
	var identity={}
	if FileAccess.file_exists("res://runtime_identity.json"):
		var expected=JSON.parse_string(FileAccess.get_file_as_string("res://runtime_identity.json"))
		for name in expected.sources:
			identity[name]=FileAccess.get_sha256("res://"+name)
			check(identity[name]==expected.sources[name],"Release embedded source identity: "+name)
	var report={"schema_version":1,"checks":{"passed":labels.size()-failures.size(),"failed":failures.size()},"labels":labels,"failures":failures,
		"read_only":read_only,"journeys":journeys,"look":scene.character_look.applied.duplicate(),"profile":scene.keepsakes.snapshot(),"mode":scene.game.mode,"tick":scene.game.snapshot().tick,"sources":identity}
	var file=FileAccess.open(output,FileAccess.WRITE)
	if file==null:push_error("Cannot write release verification result");return false
	file.store_string(JSON.stringify(report,"  ")+"\n");file.close()
	print("PLAYER_CHECKS ",report.checks.passed," passed / ",report.checks.failed," failed")
	return failures.is_empty()
