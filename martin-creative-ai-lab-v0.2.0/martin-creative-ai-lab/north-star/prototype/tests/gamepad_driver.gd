extends RefCounted
## Synthetic mapped events traverse the actual viewport consumer, not a physical pad.
const Policy=preload("res://tests/policy.gd")
const GatePolicy=preload("res://tests/gate_policy.gd")
var scene
var passed:=0
var failed:=0
var labels:=[]
var journeys:=[]
func check(value: bool,label: String) -> void:
	labels.append(label)
	if value:passed+=1
	else:failed+=1;push_error(label)
func button(id: int,down: bool=true,device: int=0) -> void:
	var event=InputEventJoypadButton.new();event.button_index=id;event.pressed=down;event.device=device
	Input.parse_input_event(event);Input.flush_buffered_events()
func tap(id: int) -> void:button(id);button(id,false)
func axis(id: int,value: float,device: int=0) -> void:
	var event=InputEventJoypadMotion.new();event.axis=id;event.axis_value=value;event.device=device
	Input.parse_input_event(event);Input.flush_buffered_events()
func sticks(move: Vector2=Vector2.ZERO,aim: Vector2=Vector2.ZERO) -> void:
	# Invert the scaled deadzone so a policy's requested direction/speed is exact.
	for pair in [[0,move],[2,aim]]:
		var v:Vector2=pair[1]
		if v.length()>0:v=v.normalized()*(.22+.78*minf(v.length(),1))
		axis(pair[0],v.x);axis(pair[0]+1,v.y)
func policy_step(command: Dictionary) -> void:
	sticks(command.get("move",Vector2.ZERO),command.get("aim",Vector2.ZERO))
	for pair in [[JOY_BUTTON_X,"strike"],[JOY_BUTTON_Y,"skill_pressed"],[JOY_BUTTON_B,"dodge"]]:
		button(pair[0],false)
		if command.get(pair[1],false):button(pair[0])
	button(JOY_BUTTON_Y,command.get("skill",false) or command.get("skill_pressed",false))
	button(JOY_BUTTON_A,command.get("interact",false))
	scene._physics_process(1.0/60)
func neutral() -> void:
	sticks()
	for id in scene.pad.BUTTONS:button(id,false)
func run(target,output: String) -> Dictionary:
	scene=target
	scene.set_physics_process(false)
	axis(0,.1);check(not scene.pad.using_gamepad,"Drift cannot claim the active device")
	button(JOY_BUTTON_GUIDE);check(not scene.pad.using_gamepad,"Unmapped button cannot claim device or dispatch")
	axis(4,1);check(not scene.pad.using_gamepad,"Trigger axis is not interpreted as stick movement")
	tap(JOY_BUTTON_DPAD_RIGHT);check(scene.selected=="Duelist","Mapped right selects Duelist through viewport")
	tap(JOY_BUTTON_DPAD_LEFT);tap(JOY_BUTTON_Y);check(scene.selected=="Guardian" and scene.guardian_style=="Riposte","Mapped left and north select Guardian technique")
	button(JOY_BUTTON_Y);button(JOY_BUTTON_Y)
	check(scene.guardian_style=="Steady","Repeated held button cannot retrigger menu choice")
	button(JOY_BUTTON_Y,false)
	tap(JOY_BUTTON_RIGHT_SHOULDER);check(scene.character_look.active,"Mapped shoulder opens appearance")
	tap(JOY_BUTTON_DPAD_RIGHT);check(scene.character_look.draft.skin==1 and scene.character_look.applied.skin==0,"Appearance navigation edits draft only")
	tap(JOY_BUTTON_B);check(not scene.character_look.active and scene.character_look.applied.skin==0,"East cancels appearance without application")
	tap(JOY_BUTTON_RIGHT_SHOULDER);tap(JOY_BUTTON_DPAD_RIGHT);tap(JOY_BUTTON_A)
	check(scene.character_look.applied.skin==1 and not scene.pad.held(JOY_BUTTON_A),"South applies appearance without interaction leakage")
	tap(JOY_BUTTON_LEFT_SHOULDER);check(scene.workshop.active,"Mapped shoulder opens workshop")
	for i in 100:
		var destination:Vector2=scene.Workshop.STATIONS.riveted-scene.workshop.player
		if destination.length()<10:break
		sticks(destination.normalized());scene._physics_process(1.0/60)
	neutral();check(scene.workshop.near_station()=="riveted","Mapped movement reaches actual fitting station")
	button(JOY_BUTTON_A)
	for i in 65:scene._physics_process(1.0/60)
	check(scene.workshop.outfit=="riveted" and scene.workshop.blank==0,"Held south actually makes and wears paid fitting")
	tap(JOY_BUTTON_START);check(scene.workshop.paused,"Start pauses workshop")
	button(JOY_BUTTON_A,false);tap(JOY_BUTTON_A)
	check(not scene.workshop.paused and not scene.pad.held(JOY_BUTTON_A),"South resumes workshop without leaking held make")
	tap(JOY_BUTTON_X);check(scene.workshop.outfit=="standard" and scene.workshop.blank==1,"West recycles actual fitting and restores blank")
	tap(JOY_BUTTON_B);check(not scene.workshop.active,"Mapped east leaves workshop")
	tap(JOY_BUTTON_LEFT_SHOULDER);tap(JOY_BUTTON_Y)
	check(not scene.workshop.active and scene.game.mode=="play","North deploys workshop into actual crossing")
	tap(JOY_BUTTON_START);tap(JOY_BUTTON_B)

	tap(JOY_BUTTON_X);check(scene.rehearsal.active,"Mapped west opens rehearsal")
	tap(JOY_BUTTON_A);check(scene.rehearsal.state=="live","South starts rehearsal stage")
	tap(JOY_BUTTON_START);check(scene.rehearsal.paused,"Start pauses rehearsal")
	tap(JOY_BUTTON_B);check(not scene.rehearsal.active and scene.game.mode=="title","East deliberately abandons paused rehearsal")
	button(JOY_BUTTON_A);check(scene.game.mode=="play" and not scene.pad.held(JOY_BUTTON_A),"South starts crossing and suppresses held confirmation")
	button(JOY_BUTTON_A,false)
	var start:Vector2=scene.game.player
	axis(0,1);scene._physics_process(.05);check(scene.game.player.x>start.x,"Left stick actually moves the live character")
	axis(0,.61);check(is_equal_approx(scene.pad.movement().length(),.5),"Circular deadzone scales partial analog movement")
	axis(0,0);axis(1,0);tap(JOY_BUTTON_DPAD_RIGHT)
	button(JOY_BUTTON_DPAD_RIGHT);check(scene.pad.movement()==Vector2.RIGHT,"D-pad supplies digital live motion")
	button(JOY_BUTTON_DPAD_RIGHT,false);axis(0,1)
	axis(1,1);check(is_equal_approx(scene.pad.movement().length(),1),"Diagonal movement is bounded")
	sticks(Vector2.ZERO,Vector2.LEFT);check(scene.pad.vector(1).x<-.99,"Right stick supplies independent aim")
	tap(JOY_BUTTON_BACK);var before=scene.game.snapshot();scene._physics_process(.05)
	check(scene.pad_help and scene.game.mode=="paused" and before==scene.game.snapshot(),"Guide freezes the real world and leaves it paused")
	tap(JOY_BUTTON_X);tap(JOY_BUTTON_Y);check(scene.bindings.toggle_guard and scene.bindings.toggle_interact,"Guide changes explicit session toggles")
	tap(JOY_BUTTON_X);tap(JOY_BUTTON_Y);tap(JOY_BUTTON_B)
	check(not scene.pad_help and scene.game.mode=="paused","Closing guide cannot resume play")
	tap(JOY_BUTTON_A);check(scene.game.mode=="play","Explicit south resumes paused crossing")
	axis(0,1);scene.pad_connection(7,false);check(scene.game.mode=="play","Inactive controller disconnect does not pause active play")
	scene.pad_connection(0,false);check(scene.game.mode=="paused" and scene.pad.movement()==Vector2.ZERO,"Active disconnect clears motion and pauses")
	scene.pad_connection(0,true);check(scene.game.mode=="paused","Reconnect cannot silently resume")
	tap(JOY_BUTTON_A);axis(0,1);scene._notification(Node.NOTIFICATION_APPLICATION_FOCUS_OUT)
	check(scene.game.mode=="paused" and scene.pad.movement()==Vector2.ZERO,"Focus loss quarantines held stick")
	tap(JOY_BUTTON_A);check(scene.pad.movement()==Vector2.ZERO,"Resume cannot reactivate an uncentered stick")
	axis(0,0);axis(0,1);check(scene.pad.movement().x>.99,"Centering rearms movement")
	var key=InputEventKey.new();key.keycode=KEY_ESCAPE;key.physical_keycode=KEY_ESCAPE;key.pressed=true
	Input.parse_input_event(key);Input.flush_buffered_events()
	check(not scene.pad.using_gamepad and scene.pad.movement()==Vector2.ZERO,"Keyboard takeover releases retained pad state")
	neutral();scene.abandon()
	for role in ["Guardian","Duelist"]:
		tap(JOY_BUTTON_DPAD_LEFT if role=="Guardian" else JOY_BUTTON_DPAD_RIGHT);tap(JOY_BUTTON_A)
		for i in 4200:
			if scene.game.mode!="play":break
			policy_step(Policy.command(scene.game))
		check(scene.game.mode=="won",role+" completes actual escort using mapped events")
		check(scene.game.counters.blocks>0 if role=="Guardian" else scene.game.counters.redirects>0,role+" uses its distinct mapped response")
		neutral();tap(JOY_BUTTON_RIGHT_SHOULDER)
		check(scene.courier_talk.active,role+" opens actual arrival conversation")
		tap(JOY_BUTTON_DPAD_DOWN);check(scene.courier_talk.draft=="brace" and scene.courier_talk.choice=="",role+" drafts aid without commitment")
		tap(JOY_BUTTON_A);check(scene.courier_talk.choice=="brace",role+" explicitly confirms aid")
		tap(JOY_BUTTON_LEFT_SHOULDER);check(scene.return_gate.active,role+" departs for actual return goal")
		for i in 6000:
			if scene.game.mode!="play":break
			policy_step(GatePolicy.command(scene.return_gate,"quiet"))
		check(scene.game.mode=="won" and scene.return_gate.opened(),role+" completes both catches and return exit through mapped input")
		journeys.append({"role":role,"game":scene.game.snapshot(),"return_gate":scene.return_gate.snapshot()})
		neutral();tap(JOY_BUTTON_B)
	# Prompt conversion remains independent of custom keyboard bindings.
	check(scene.pad.describe("WASD J K E SPACE ESC F1","play")=="LS X Y A B START BACK","Mapped hints cover actual default action positions")
	check(scene.pad.describe("ENTER ESC SPACE TAB","look")=="A B Y L3","Appearance hints use their own modal contract")
	check(scene.pad.describe("ENTER ESC C","workshop_paused")=="A START X","Paused workshop hints expose actual south resume")
	var hashes={}
	for name in ["arena.gd","gamepad.gd","tests/gamepad_checks.gd","tests/gamepad_driver.gd"]:hashes[name]=FileAccess.get_sha256("res://"+name)
	var report={"checks":{"passed":passed,"failed":failed},"labels":labels,"journeys":journeys,"consumer_hashes":hashes,"physical_controller":false}
	var file=FileAccess.open(output,FileAccess.WRITE);file.store_string(JSON.stringify(report,"  ")+"\n")
	scene.sound.silence()
	return report
