extends RefCounted
const Combat = preload("res://combat.gd")
const Rehearsal = preload("res://rehearsal.gd")
const Policy = preload("res://tests/policy.gd")
const ErrandPolicy = preload("res://tests/errand_policy.gd")
const ControlsChecks = preload("res://tests/controls_checks.gd")
const Trial = preload("res://tests/rehearsal_checks.gd")

static func command(game) -> Dictionary:
	var input: Dictionary=Policy.command(game)
	if game.guard_style=="Riposte" and game.phase=="bolt" and game.clock<0.76:input.skill=false
	return input

static func bolt(style: String,start: int):
	var game=Combat.new();game.reset("Guardian",style)
	game.phase="bolt";game.target=game.courier;game.player=Vector2(550,390)
	for tick in 60:game.step(1.0/60.0,{"skill":tick>=start,"aim":Vector2.RIGHT})
	return game

static func route(checker,style: String,naive: bool=false,recover: bool=false) -> Dictionary:
	var scene=ControlsChecks.scene(checker,"guard-route-"+style+str(naive)+str(recover))
	scene.guardian_style=style;scene.begin_crossing()
	for i in 2400:
		var input: Dictionary=ErrandPolicy.command(scene) if recover else (Policy.command(scene.game) if naive else command(scene.game))
		if recover and scene.game.phase=="bolt" and scene.game.clock<0.76:input.skill=false
		scene.advance_crossing(1.0/60.0,input)
		if scene.game.mode!="play":break
	var result={"combat":scene.game.snapshot(),"errand":scene.errand.snapshot(),"marks":scene.keepsakes.snapshot()}
	scene.queue_free()
	return result

static func run(checker) -> Dictionary:
	var boundary=Combat.new();boundary.reset("Guardian","Riposte");boundary.guard=true;boundary.locked_face=Vector2.RIGHT
	for sample in [[0.059,false],[0.06,true],[0.30,true],[0.301,false]]:
		boundary.guard_age=sample[0]
		checker.check(boundary.guards_from(Combat.ENEMY)==sample[1],"Riposte live age boundary "+str(sample[0]))
	boundary.guard_age=0.15;boundary.locked_face=Vector2.LEFT
	checker.check(not boundary.guards_from(Combat.ENEMY),"Timed guard still requires frontal facing")
	boundary.locked_face=Vector2.RIGHT;boundary.energy=21.9
	checker.check(not boundary.guards_from(Combat.ENEMY),"Timed guard still needs the original impact posture")
	boundary.reset("Guardian","unknown")
	checker.check(boundary.guard_style=="Steady","Unknown Guardian technique safely defaults to Steady")
	boundary.reset("Duelist","Riposte")
	checker.check(boundary.guard_style=="none","Duelist cannot borrow a Guardian technique")
	var steady=bolt("Steady",0);var early=bolt("Riposte",0);var timed=bolt("Riposte",45);var late=bolt("Riposte",59)
	checker.check(steady.counters.blocks==1 and steady.hp==5 and steady.opening==1.0,"Sustained Steady guard retains baseline protection and opening")
	checker.check(early.counters.blocks==0 and early.hp==4 and early.last_impact.code=="guard_stale","Early held Riposte guard expires and actually takes the bolt")
	checker.check(timed.counters.blocks==1 and timed.hp==5 and timed.opening==1.6 and timed.last_impact.code=="riposte_blocked","Timed frontal guard buys the actual longer counter opening")
	checker.check(late.hp==4 and late.last_impact.code=="guard_startup","Raising too late still pays the startup exposure")
	var contact={"steady":steady.snapshot(),"early":early.snapshot(),"timed":timed.snapshot(),"late":late.snapshot()}
	for model in [steady,timed]:
		model.player=Combat.ENEMY+Vector2(-100,0)
		for i in 24:model.step(0.05,{})
		model.step(1.0/60.0,{"strike":true})
	checker.check(steady.counters.counters==0 and timed.counters.counters==1,"The extra opening changes a real counter at 1.2s, not only a label")
	var pulse=Combat.new();pulse.reset("Guardian","Riposte");pulse.phase="pulse";pulse.pulse=pulse.player;pulse.clock=0.99
	pulse.step(0.02,{"skill":true})
	checker.check(pulse.hp==4 and pulse.last_impact.code=="pulse_hit","Riposte guard never grants floor immunity")
	var held=bolt("Riposte",0);held.phase="bolt";held.clock=0.2;held.step(0.02,{"skill":false});held.step(0.02,{"skill":true})
	checker.check(held.guard_age<0.06 and held.guard_state()=="STARTUP","Releasing and raising resets age but restores the startup cost")
	held.mode="paused";var age: float=held.guard_age;var before: Dictionary=held.snapshot();held.step(.05,{"skill":true})
	checker.check(held.guard_age==age and held.snapshot()==before,"Pause freezes guard timing and all combat state")

	var scene=ControlsChecks.scene(checker,"guard-ui")
	Trial.key(scene,KEY_TAB)
	checker.check(scene.guardian_style=="Riposte" and scene.game.guard_style=="Riposte","Actual title TAB selects the alternative Guardian technique")
	Trial.key(scene,KEY_ENTER);Trial.key(scene,KEY_TAB)
	checker.check(scene.game.guard_style=="Riposte" and scene.guardian_style=="Riposte","Live TAB cannot switch the selected technique")
	Trial.key(scene,KEY_ESCAPE);Trial.key(scene,KEY_TAB)
	checker.check(scene.game.guard_style=="Riposte","Pause cannot switch technique or reset its timing")
	Trial.key(scene,KEY_R);Trial.key(scene,KEY_T)
	checker.check(scene.rehearsal.game.guard_style=="Riposte" and scene.rehearsal.heading()=="TIMED PROTECTION","Actual rehearsal consumes the selected technique")
	Trial.key(scene,KEY_TAB)
	checker.check(scene.rehearsal.game.guard_style=="Riposte","Rehearsal cannot change technique through title input")
	var r=scene.rehearsal
	r.confirm()
	for tick in 90:
		r.step(1.0/60.0,{"aim":Vector2.RIGHT,"skill":r.game.clock>=0.76})
		if r.state=="review":break
	checker.check(r.passed and r.game.last_impact.code=="riposte_blocked","Timed rehearsal passes only a real eligible block")
	r.repeat();r.confirm()
	for tick in 90:
		r.step(1.0/60.0,{"skill":true,"aim":Vector2.RIGHT})
		if r.state=="review":break
	checker.check(not r.passed and r.game.last_impact.code=="guard_stale","Early held technique fails rehearsal with its actual cause")
	r.repeat()
	checker.check(r.game.guard_style=="Riposte" and r.game.guard_age==0,"Repeating a lesson preserves choice but resets committed state")
	# Complete each real-model exercise using the chosen timing, then start clean play.
	r.confirm()
	for tick in 90:
		r.step(1.0/60.0,{"aim":Vector2.RIGHT,"skill":r.game.clock>=0.76})
		if r.state=="review":break
	r.confirm();r.confirm();Trial.attempt(r,true);r.confirm();r.confirm();Trial.attempt(r,true)
	checker.check(r.stage==2 and r.passed and r.game.guard_style=="Riposte","All three isolated exercises retain the selected technique")
	Trial.key(scene,KEY_ENTER)
	checker.check(not scene.rehearsal.active and scene.game.guard_style=="Riposte" and scene.game.elapsed==0 and scene.game.hp==5,"Rehearsal completion starts a clean crossing with its selected technique")
	Trial.key(scene,KEY_ESCAPE);Trial.key(scene,KEY_R);Trial.key(scene,KEY_2);Trial.key(scene,KEY_ENTER)
	checker.check(scene.game.role=="Duelist" and scene.game.guard_style=="none","Switching approach cannot leak Guardian behavior")
	Trial.key(scene,KEY_ESCAPE);Trial.key(scene,KEY_R);Trial.key(scene,KEY_1);Trial.key(scene,KEY_TAB)
	checker.check(scene.game.guard_style=="Steady" and scene.guardian_style=="Steady","Return to title allows an explicit reversible technique change")
	scene.guardian_style="Riposte";scene.begin_crossing();scene.game.phase="bolt";scene.game.clock=0.76;scene.game.target=scene.game.courier
	var rebound: Dictionary=scene.bindings.keys.duplicate();rebound.skill=KEY_H;scene.bindings.apply(rebound)
	ControlsChecks.physical(KEY_H)
	for i in 5:scene._physics_process(0.05)
	ControlsChecks.physical(KEY_H,false)
	checker.check(scene.game.counters.blocks==1 and scene.bindings.describe("RAISE K NOW")=="RAISE H NOW","The selected timing technique consumes remapped held input and matching cue text")
	scene.queue_free()
	var steady_route=route(checker,"Steady");var riposte_route=route(checker,"Riposte");var naive_route=route(checker,"Riposte",true);var recovery_route=route(checker,"Riposte",false,true)
	checker.check(steady_route.combat.mode=="won" and riposte_route.combat.mode=="won","Both Guardian techniques complete real normal-consumer routes")
	checker.check(naive_route.combat.mode=="lost" and naive_route.combat.counters.blocks==0,"Reusing sustained early-hold timing fails the alternative technique")
	checker.check(riposte_route==route(checker,"Riposte"),"The timed route is deterministic and repeatable")
	checker.check(recovery_route.combat.mode=="won" and recovery_route.errand.state=="delivered","Timed technique still permits an actual voluntary medicine handoff")
	checker.check(riposte_route.marks.earned==steady_route.marks.earned,"Technique choice adds no persistent power or new farming reward")
	return {"contact":contact,"steady_route":steady_route,"riposte_route":riposte_route,"early_hold_route":naive_route,"recovery_route":recovery_route,"long_window_counter":timed.snapshot()}
