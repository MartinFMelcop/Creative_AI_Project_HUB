extends RefCounted
## Fixed functional policies are not independent player observations.
const Gate=preload("res://return_gate.gd")
const Combat=preload("res://combat.gd")
const Policy=preload("res://tests/policy.gd")
const GatePolicy=preload("res://tests/gate_policy.gd")
var labels:Array[String]=[]
var failures:Array[String]=[]
func check(value:bool,label:String) -> void:
	labels.append(label)
	if not value:failures.append(label)
func room(aid:String=""):
	var source=Combat.new();source.reset("Guardian");source.mode="won";source.courier.x=1000
	var r=Gate.new();r.begin(source,"carried",aid);r.game.player=Gate.GROUND;return r
func hold(r, ticks:int=90) -> void:
	for i in ticks:r.step(1.0/60,{"interact":true,"skill":true,"strike":true,"dodge":true})
func key(scene,code:int) -> void:
	var e=InputEventKey.new();e.keycode=code;e.physical_keycode=code;e.pressed=true;scene._unhandled_key_input(e)
func command(r) -> Dictionary:
	if r.game.sentinel_disabled():return GatePolicy.command(r,"work")
	var offset:Vector2=Gate.GROUND-r.game.player
	return {"move":offset.normalized() if offset.length()>20 else Vector2.ZERO,"interact":offset.length()<=20}
func run(scene,output:String) -> Dictionary:
	var r=room();hold(r,89)
	check(not r.grounded and r.game.cargo==2 and r.progress>1.4,"Full uninterrupted time required before spending")
	check(not r.game.guard and r.game.counters.dodges==0 and r.game.counters.counters==0,"Grounding excludes guard, blade and step")
	hold(r,1)
	check(r.grounded and r.game.cargo==1 and r.game.sentinel_disabled(),"One integrity grounds ward after 1.5 seconds")
	check(r.game.mode=="play" and not r.opened(),"Shutdown cannot substitute for catches and exit")
	check(r.events.size()==1 and r.events[0].action=="ward_grounded" and r.game.counters.counters==0,"Grounding reports truthful event without fake counters")
	check(r.game.phase=="disabled" and r.game.opening==0 and not r.game.redirected,"Grounding clears pending attacks and openings")
	hold(r,180);check(r.game.cargo==1 and r.events.size()==1,"Holding completed lever cannot spend twice or farm events")
	r.retry();check(not r.grounded and r.game.cargo==2 and r.events.is_empty() and r.progress==0,"Retry clears route and restores immutable checkpoint")
	r=room("brace");hold(r);check(r.grounded and r.game.cargo==2,"Brace margin survives the same explicit cost")
	r.retry();check(r.game.cargo==3 and not r.grounded,"Brace retry cannot stack integrity")
	r=room();r.game.cargo=1;hold(r);check(not r.grounded and r.progress==0 and r.game.cargo==1,"One integrity denies suicidal grounding")
	r=room();r.game.enemy_focus=0;hold(r);check(not r.grounded and r.game.cargo==2,"Counter-disabled ward cannot charge lever cost")
	r=room();r.game.player+=Vector2(33,0);r.step(.05,{"interact":true});check(r.progress==0,"Outside radius cannot queue work")
	r=room();r.game.step_left=.1;r.step(.05,{"interact":true});check(r.progress==0,"Active step denies work")
	r=room();hold(r,20);r.step(.01,{"move":Vector2.LEFT,"interact":true});check(r.progress==0 and not r.channel,"Movement cancels progress")
	r=room();hold(r,20);r.step(.01,{});check(r.progress==0,"Release cancels progress")
	r=room();hold(r,20);r.suspend();r.game.mode="paused";var frozen:Dictionary=r.snapshot();hold(r)
	check(r.snapshot()==frozen and r.progress==0,"Pause cannot retain or advance hidden work")
	r=room();r.progress=1.49;r.working=Gate.GROUND_INDEX;r.game.phase="bolt";r.game.clock=.99;r.game.target=Gate.WINCH
	r.step(.02,{"interact":true});check(not r.grounded and r.game.cargo==1 and r.progress==0,"Same-frame winch hit defeats grounding completion")
	r=room();r.progress=1.49;r.working=Gate.GROUND_INDEX;r.game.phase="bolt";r.game.clock=.99;r.game.target=Gate.GROUND
	r.step(.02,{"interact":true});check(not r.grounded and r.game.hp==4 and r.progress==0,"Same-frame personal hit defeats completion")
	r=room();r.game.hp=0;hold(r);check(not r.grounded and r.game.mode=="lost" and r.game.cargo==2,"Death cannot complete or spend")
	# Consume remapped/toggled interaction through the actual scene adapter.
	scene.abandon();scene.begin_crossing();scene.game.mode="won";scene.game.courier.x=1000;scene.begin_return_gate()
	scene.game.player=Gate.GROUND;scene.bindings.toggle_interact=true;scene.bindings.toggle_guard=true;scene.bindings.guard_latched=true
	scene.bindings.keys.interact=KEY_F;scene.bindings.refresh_labels();key(scene,KEY_F)
	var input:Dictionary=scene.return_gate_command(scene.taps)
	check(input.interact and not input.skill and not scene.bindings.guard_latched,"Remapped toggle starts grounding and releases guard")
	scene.advance_crossing(.05,input);scene.taps.clear();check(scene.return_gate.progress>0,"Scene consumes grounding command")
	key(scene,KEY_ESCAPE);check(scene.game.mode=="paused" and scene.return_gate.progress==0 and not scene.bindings.interact_latched,"Native pause clears grounding and interaction latch")
	scene.game.mode="play";scene.return_gate.game.mode="play";scene.bindings.interact_latched=true
	scene.return_gate.step(.05,{"interact":true});scene._notification(MainLoop.NOTIFICATION_APPLICATION_FOCUS_OUT)
	check(scene.return_gate.progress==0 and not scene.bindings.interact_latched,"Focus loss clears grounding intent")
	scene.bindings.toggle_interact=false;scene.bindings.toggle_guard=false;scene.bindings.keys=scene.bindings.DEFAULTS.duplicate();scene.bindings.refresh_labels()
	var journeys:Array=[]
	for outfit in ["standard","riveted","trail","field_sash"]:
		for role in ["Guardian","Duelist"]:
			scene.abandon();scene.workshop=scene.Workshop.new();scene.selected=role;scene.begin_crossing()
			if outfit!="standard":scene.game.mode="title";scene.game.fit_outfit(outfit);scene.game.mode="play"
			for tick in 4200:
				if scene.game.mode!="play":break
				scene.advance_crossing(1.0/60,Policy.command(scene.game))
			check(scene.game.mode=="won","Actual escort completes: "+role+"/"+outfit)
			var entry_hp:int=scene.game.hp;var earned:Array=scene.keepsakes.earned.duplicate()
			check(scene.begin_return_gate() and scene.game.hp==entry_hp,"Real arrival carries health: "+outfit)
			for tick in 6000:
				if scene.game.mode!="play":break
				scene.advance_crossing(1.0/60,command(scene.return_gate))
			check(scene.game.mode=="won" and scene.return_gate.grounded and scene.return_gate.opened(),"Grounded return completes both catches and exit: "+role+"/"+outfit)
			check(scene.game.cargo==1 and scene.game.counters.counters==0 and scene.keepsakes.earned==earned,"Cost paid, no fake counters or duplicate reward: "+role+"/"+outfit)
			journeys.append({"role":role,"outfit":outfit,"entry_hp":entry_hp,"return_gate":scene.return_gate.snapshot()})
	var hashes:Dictionary={}
	for name in ["arena.gd","return_gate.gd","combat.gd","tests/grounding_driver.gd"]:hashes[name]=FileAccess.get_sha256("res://"+name)
	var report:Dictionary={"schema_version":1,"checks":{"passed":labels.size()-failures.size(),"failed":failures.size()},"labels":labels,"failures":failures,"journeys":journeys,"consumer_hashes":hashes}
	var file=FileAccess.open(output,FileAccess.WRITE);file.store_string(JSON.stringify(report,"  ")+"\n");file.close()
	print("GROUNDING_CHECKS ",report.checks)
	return report
