extends RefCounted
const Combat = preload("res://combat.gd")
const Errand = preload("res://errand.gd")
const Route = preload("res://tests/errand_policy.gd")
const Policy = preload("res://tests/policy.gd")
const Scenes = preload("res://tests/keepsake_checks.gd")
const Trial = preload("res://tests/rehearsal_checks.gd")

static func tick(g,e,dt: float,command: Dictionary) -> void:
	g.step(dt,e.prepare(g,dt,command));e.settle(g)

static func journey(tree,role: String,recover: bool) -> Dictionary:
	var scene=Scenes.fresh_scene(tree,"errand-"+role+str(recover))
	scene.selected=role;scene.begin_crossing()
	for i in 2400:
		scene.advance_crossing(1.0/60.0,Route.command(scene) if recover else Policy.command(scene.game))
		if scene.game.mode!="play":break
	var report={"combat":scene.game.snapshot(),"errand":scene.errand.snapshot(),"marks":scene.keepsakes.snapshot()}
	scene.queue_free()
	return report

static func run(checker) -> Array[Dictionary]:
	var g=Combat.new();g.reset("Guardian")
	var e=Errand.new()
	var before: Dictionary=e.snapshot()
	e.prepare(g,0.05,{"interact":true})
	checker.check(e.snapshot()==before,"Rehearsal/inactive errand cannot acquire a case")
	e.reset();g.player=Errand.CASE
	for i in 20:tick(g,e,0.05,{"interact":true})
	checker.check(e.state=="waiting","Case cannot be collected before the actual first marker")
	g.courier.x=400;g.phase="rest";g.clock=0
	tick(g,e,0.05,{"interact":true,"skill":true,"strike":true,"dodge":true})
	checker.check(e.state=="available" and e.progress>0 and not g.guard and g.counters.dodges==0 and g.counters.counters==0,"Real recovery commitment prevents simultaneous guard, step and strike")
	checker.check(g.courier.x>400 and g.clock>0,"Recovering never pauses courier or threat clock")
	tick(g,e,0.05,{})
	checker.check(e.progress==0 and not e.channel,"Releasing E cancels partial progress")
	tick(g,e,0.05,{"interact":true});tick(g,e,0.05,{"interact":true,"move":Vector2.UP})
	checker.check(e.progress==0 and g.player.y<Errand.CASE.y,"Movement cancels recovery and immediately remains available")
	g.player=Errand.CASE;tick(g,e,0.05,{"interact":true});g.mode="paused"
	before=e.snapshot();var paused: Dictionary=g.snapshot()
	tick(g,e,0.05,{"interact":true})
	checker.check(e.snapshot()==before and g.snapshot()==paused,"Pause freezes partial interaction and all combat state")
	g.mode="play";g.player=Errand.CASE+Vector2(100,0);tick(g,e,0.05,{"interact":true,"dodge":true})
	checker.check(e.progress==0 and g.counters.dodges==1,"Out-of-range E cannot collect remotely or suppress combat")
	g.player=Errand.CASE;g.step_left=0;g.phase="rest";g.clock=0
	for i in 16:tick(g,e,0.05,{"interact":true})
	checker.check(e.state=="carried","Actual uninterrupted nearby recovery creates a carried case")
	for i in 20:tick(g,e,0.05,{"interact":true})
	checker.check(e.state=="carried","Carried case cannot be handed over from afar")
	g.player=g.courier+Vector2(10,0);g.phase="rest";g.clock=0
	for i in 12:tick(g,e,0.05,{"interact":true})
	checker.check(e.state=="delivered","Nearby held handoff delivers to the actually moving courier")
	before=e.snapshot();tick(g,e,0.05,{"interact":true})
	checker.check(e.snapshot()==before,"Completed handoff cannot be repeated")
	# Controlled terminal fixtures isolate outcome ownership from full route feasibility.
	e.reset();e.state="carried";g.mode="won";g.courier.x=1000;e.settle(g)
	checker.check(e.state=="carried" and e.finished and e.outcome().contains("not delivered"),"A carried case at gate is never reported delivered")
	before=e.snapshot();e.prepare(g,0.05,{"interact":true})
	checker.check(e.snapshot()==before,"Terminal input cannot complete an unearned handoff")
	e.reset();e.state="delivered";g.mode="lost";e.settle(g)
	checker.check(e.outcome().contains("failed"),"A handoff before defeat does not claim arrival at gate")
	e.reset();g.reset("Guardian");g.courier.x=400;g.player=Errand.CASE
	e.prepare(g,4,{"interact":true})
	checker.check(is_equal_approx(e.progress,0.05),"Long frame cannot skip interaction duration")
	g.step_left=0.1;e.prepare(g,0.05,{"interact":true})
	checker.check(not e.channel and e.progress==0,"An already committed step must finish before interaction can begin")
	# A real pulse lands during commitment; E is neither immunity nor simulation pause.
	e.reset();g.reset("Guardian");g.courier.x=400;g.player=Errand.CASE;g.phase="pulse";g.pulse=g.player;g.clock=0.99
	tick(g,e,1.0/60.0,{"interact":true})
	checker.check(g.hp==4 and g.last_impact.code=="pulse_hit","Greedy recovery remains vulnerable to the actual threat")
	var result: Array[Dictionary]=[]
	for role in ["Guardian","Duelist"]:
		var direct: Dictionary=journey(checker,role,false)
		var recovered: Dictionary=journey(checker,role,true)
		checker.check(direct.combat.mode=="won" and direct.errand.state=="available",role+" direct escort remains a successful voluntary choice")
		checker.check(direct.combat==checker.simulate(role,true),role+" direct scene preserves the complete original combat outcome")
		checker.check(recovered.combat.mode=="won" and recovered.errand.state=="delivered",role+" actual recovery route reaches gate with delivered case")
		checker.check(recovered==journey(checker,role,true),role+" complete recovery route is repeatable")
		checker.check(recovered.marks.earned.size()==1 and direct.marks.earned==recovered.marks.earned,role+" optional medicine creates no extra persistent mark or power")
		result.append({"role":role,"direct":direct,"recovered":recovered})
	var scene=Scenes.fresh_scene(checker,"errand-input");Trial.key(scene,KEY_ENTER)
	scene.game.courier.x=400;scene.game.player=Errand.CASE
	var event=InputEventKey.new();event.physical_keycode=KEY_E;event.keycode=KEY_E;event.pressed=true
	Input.parse_input_event(event);Input.flush_buffered_events();scene._physics_process(1.0/60.0)
	checker.check(scene.errand.progress>0,"Actual held E input adapter begins nearby recovery")
	var released=event.duplicate()
	released.pressed=false;Input.parse_input_event(released);Input.flush_buffered_events();scene._physics_process(1.0/60.0)
	checker.check(scene.errand.progress==0,"Actual E release cancels recovery without buffered completion")
	scene.abandon();Trial.key(scene,KEY_T)
	checker.check(not scene.errand.active,"Abandon/rehearsal discards session errand without granting anything")
	scene.queue_free()
	return result
