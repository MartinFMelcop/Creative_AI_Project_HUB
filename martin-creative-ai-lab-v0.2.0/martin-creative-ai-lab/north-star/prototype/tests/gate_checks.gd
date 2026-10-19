extends SceneTree
const Combat=preload("res://combat.gd")
const Gate=preload("res://return_gate.gd")
const Arena=preload("res://arena.gd")
const Policy=preload("res://tests/policy.gd")
const GatePolicy=preload("res://tests/gate_policy.gd")
var passed:=0
var failed:=0
var journeys:=[]
func check(value: bool,label: String) -> void:
	if value:passed+=1
	else:failed+=1;push_error(label)
func arrival(role: String="Guardian", outfit: String="standard"):
	var source=Combat.new();source.reset(role);source.fit_outfit(outfit)
	source.hp=3;source.energy=44;source.courier.x=1000;source.mode="won"
	return source
func room():
	var value=Gate.new();value.begin(arrival(),"carried");return value
func hold(value, index: int, count: int=60) -> void:
	value.game.player=Gate.CATCHES[index]
	for i in count:value.step(1.0/60,{"interact":true})
func key(code: int) -> InputEventKey:
	var event=InputEventKey.new();event.physical_keycode=code;event.keycode=code;event.pressed=true;return event
func _initialize() -> void:call_deferred("run")
func run() -> void:
	var source=Combat.new();source.reset("Guardian")
	var r=Gate.new()
	check(not r.begin(source,"available") and not r.active,"live crossing cannot continue")
	source.mode="lost";check(not r.begin(source,"available"),"loss cannot continue")
	source.mode="won";check(not r.begin(source,"available"),"label alone is not arrival")
	source=arrival("Guardian","riveted");var unchanged=source.snapshot()
	check(r.begin(source,"delivered"),"real arrival prerequisites accepted")
	check(source.snapshot()==unchanged,"source outcome remains preserved")
	check(r.game.hp==3 and r.game.health_limit==6 and r.game.outfit=="riveted" and r.game.movement_scale==0.8,"actual health and fitting carry without healing")
	check(r.game.energy==44 and r.entry.medicine=="delivered","entry resource and medicine fact carried")
	check(not r.begin(arrival("Duelist"),"available") and r.entry.role=="Guardian","cannot replace active checkpoint")
	for i in 60:r.step(1.0/60,{})
	check(r.game.courier==Gate.WINCH and r.game.mode=="play","protected device is stationary; no automatic escort win")
	check(not r.game.signal_route("ridge"),"old route board cannot alter room")
	var exposed=room();exposed.game.player=Vector2(330,270)
	for i in 170:exposed.step(1.0/60,{})
	check(exposed.game.cargo==1,"normal ward bolt actually reaches stationary winch")
	for i in 180:
		if exposed.game.mode!="play":break
		exposed.step(1.0/60,{})
	check(exposed.game.mode=="lost" and exposed.game.cargo==0,"ignoring device protection breaks winch under normal timed threats")
	r.game.player=Gate.EXIT;r.step(0,{})
	check(r.game.player.x==1000 and r.game.mode=="play","closed bars actually stop early exit")
	r=room();r.step(0.05,{"interact":true})
	check(r.progress==0 and not r.channel,"out of range cannot queue work")
	r.game.player=Gate.CATCHES[0]
	for i in 30:r.step(1.0/60,{"interact":true,"skill":true,"strike":true,"dodge":true})
	check(r.channel and is_equal_approx(r.progress,0.5) and not r.raised[0],"real uninterrupted work time required")
	check(not r.game.guard and r.game.counters.dodges==0 and r.game.counters.counters==0,"working excludes guard step and blade")
	r.step(0.01,{"interact":true,"move":Vector2.RIGHT})
	check(r.progress==0 and not r.channel,"movement cancels partial work")
	r.game.player=Gate.CATCHES[0];r.step(0.05,{"interact":true});r.step(0.01,{})
	check(r.progress==0,"release cancels partial work")
	r=room();r.game.player=Gate.CATCHES[0];r.game.step_left=0.1;r.step(0.05,{"interact":true})
	check(r.progress==0,"active step cannot start work")
	r=room();r.game.player=Gate.CATCHES[0];r.progress=0.99;r.working=0
	r.game.phase="bolt";r.game.clock=0.99;r.game.target=r.game.player
	r.step(0.02,{"interact":true})
	check(r.game.hp==2 and r.progress==0 and not r.raised[0],"same-frame hit defeats work completion")
	r=room();hold(r,0)
	check(r.raised==[true,false] and r.events.size()==1,"first actual catch raised once")
	hold(r,0,30);check(r.events.size()==1,"held completed catch cannot farm events")
	hold(r,1)
	check(r.opened() and r.game.mode=="play","both catches open bars but do not award arrival")
	r.game.enemy_focus=0;r.step(0.05,{})
	check(r.game.mode=="play","ward shutdown alone cannot finish objective")
	r.game.player=Vector2(1000,390)
	for i in 20:r.step(0.02,{"move":Vector2.RIGHT})
	check(r.game.mode=="won" and r.game.player.x>=1040 and r.events[-1].action=="return_opened","actual movement through open exit completes")
	var terminal=r.snapshot();r.step(0.05,{"interact":true})
	check(r.snapshot()==terminal,"terminal room cannot accumulate work")
	r.retry();check(r.game.hp==3 and r.game.energy==44 and r.raised==[false,false] and r.events.is_empty(),"retry restores entry only and clears work")
	r.game.player=Gate.CATCHES[0];r.step(0.05,{"interact":true});r.suspend();r.game.mode="paused"
	var frozen=r.snapshot();r.step(0.05,{"interact":true})
	check(r.snapshot()==frozen and not r.channel and r.progress==0,"pause/focus suspension cannot advance or retain partial intent")
	r=room();r.raised=[true,true];r.game.player=Gate.EXIT;r.game.hp=0;r.step(0.01,{})
	check(r.game.mode=="lost","survival owns success even at exit")
	r=room();r.game.cargo=0;r.step(0.01,{})
	check(r.game.mode=="lost","broken winch loses")
	r=room()
	for i in 900:
		if r.game.mode!="play":break
		r.step(1.0/60,{})
	check(r.game.mode=="lost" and not r.opened(),"inaction cannot complete the second goal")
	var a=Arena.new();root.add_child(a);a.set_physics_process(false);a.begin_crossing()
	a.game.mode="lost";a._unhandled_key_input(key(KEY_F2));check(not a.return_gate.active,"native result adapter rejects failed crossing")
	a.game=arrival();a._unhandled_key_input(key(KEY_F2))
	check(a.return_gate.active and a.game==a.return_gate.game and not a.normal_run,"actual F2 result key starts second consumer state")
	a.game.player=Gate.CATCHES[0];a.bindings.toggle_interact=true;a.bindings.toggle_guard=true;a.bindings.guard_latched=true
	a.bindings.keys.interact=KEY_F;a.bindings.refresh_labels();a._unhandled_key_input(key(KEY_F))
	var input:Dictionary=a.return_gate_command(a.taps)
	check(input.interact and not input.skill and not a.bindings.guard_latched,"remapped interaction edge starts work and disarms guard intent")
	a.advance_crossing(0.05,input);a.taps.clear()
	check(a.return_gate.progress>0,"actual scene consumes work command")
	a._unhandled_key_input(key(KEY_ESCAPE));var paused=a.return_gate.snapshot()
	a.advance_crossing(0.05,{"interact":true})
	check(a.return_gate.snapshot()==paused and not a.bindings.interact_latched,"native pause freezes and clears toggles")
	a.open_controls();check(a.controls_open and not a.return_gate.channel,"settings cannot preserve hidden work")
	a.controls_open=false;a.game.mode="lost";a._unhandled_key_input(key(KEY_ENTER))
	check(a.game==a.return_gate.game and a.game.hp==3 and a.game.mode=="play","native retry rebinds checkpoint model")
	a.game.mode="paused";a._unhandled_key_input(key(KEY_R));check(not a.return_gate.active and a.game.mode=="title","abandon clears continuation")
	a.free()
	for role in ["Guardian","Duelist"]:
		for strategy in ["work","quiet"]:
			a=Arena.new();root.add_child(a);a.set_physics_process(false);a.selected=role;a.begin_crossing()
			for i in 4200:
				if a.game.mode!="play":break
				# First contact is deliberately unprotected: real damage, not a stat fixture.
				a.advance_crossing(1.0/60,{} if i<170 else Policy.command(a.game))
			check(a.game.mode=="won" and a.game.hp<a.game.health_limit,"actual wounded crossing reaches continuation: "+role+strategy)
			var first=a.game.snapshot();var earned=a.keepsakes.earned.duplicate()
			check(a.begin_return_gate(),"actual normal outcome starts room")
			check(a.game.hp==first.hp,"full journey carries measured health")
			for i in 6000:
				if a.game.mode!="play":break
				a.advance_crossing(1.0/60,GatePolicy.command(a.return_gate,strategy))
			check(a.game.mode=="won","complete two-stage journey: "+role+strategy)
			check(a.keepsakes.earned==earned,"second objective grants no duplicate crossing mark")
			check(a.return_gate.opened() and a.game.player.x>=1040,"complete journey really raised catches and crossed exit")
			check(a.game.sentinel_disabled()==(strategy=="quiet"),"both working under threat and optional shutdown complete")
			journeys.append({"role":role,"strategy":strategy,"crossing":first,"return_gate":a.return_gate.snapshot()})
			a.free()
	var hashes={}
	for name in ["return_gate.gd","combat.gd","arena.gd","tests/gate_policy.gd","tests/gate_checks.gd"]:hashes[name]=FileAccess.get_sha256("res://"+name)
	var report={"checks":{"passed":passed,"failed":failed},"consumer_hashes":hashes,"journeys":journeys}
	var args=OS.get_cmdline_user_args()
	if args.size()==1:
		var file=FileAccess.open(args[0],FileAccess.WRITE);file.store_string(JSON.stringify(report,"  ")+"\n")
	print("GATE_CHECKS ",passed," passed / ",failed," failed");quit(1 if failed else 0)
