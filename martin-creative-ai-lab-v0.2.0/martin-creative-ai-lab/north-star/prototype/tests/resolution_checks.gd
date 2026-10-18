extends RefCounted
const Combat=preload("res://combat.gd")
const Guard=preload("res://tests/guard_checks.gd")
const ErrandPolicy=preload("res://tests/errand_policy.gd")
const ControlsChecks=preload("res://tests/controls_checks.gd")
const Trial=preload("res://tests/rehearsal_checks.gd")
const Rehearsal=preload("res://rehearsal.gd")

static func opening(g):
	g.player=Combat.ENEMY+Vector2(-100,0);g.opening=1;g.strike_cooldown=0

static func route(checker,role: String,style: String,policy: String) -> Dictionary:
	var scene=ControlsChecks.scene(checker,"resolution-"+role+style+policy)
	scene.selected=role;scene.guardian_style=style;scene.begin_crossing()
	var disabled_tick := -1
	for i in 2400:
		var command: Dictionary=Guard.command(scene.game)
		if policy=="protect":command.strike=false
		elif policy=="secure_then_recover" and scene.game.sentinel_disabled():command=ErrandPolicy.command(scene)
		scene.advance_crossing(1.0/60.0,command)
		if disabled_tick<0 and scene.game.sentinel_disabled():disabled_tick=roundi(scene.game.elapsed*60)
		if scene.game.mode!="play":break
	var result={"combat":scene.game.snapshot(),"errand":scene.errand.snapshot(),"marks":scene.keepsakes.snapshot(),"disabled_tick":disabled_tick}
	scene.queue_free()
	return result

static func run(checker) -> Dictionary:
	var g=Combat.new();g.reset("Guardian")
	checker.check(g.enemy_focus==3 and not g.sentinel_disabled() and g.courier_speed()==28,"A fresh crossing starts with three active focus plates and walking courier")
	opening(g);g.opening=0;g.step(1.0/60.0,{"strike":true})
	checker.check(g.enemy_focus==3 and g.energy==88,"Paid armor contact cannot remove focus")
	opening(g);g.player=Combat.ENEMY+Vector2(-131,0);g.step(1.0/60.0,{"strike":true})
	checker.check(g.enemy_focus==3,"Out-of-range blade never removes focus")
	opening(g);g.energy=11;g.step(1.0/60.0,{"strike":true})
	checker.check(g.enemy_focus==3 and g.counters.counters==0,"Unfunded request cannot disable a plate")
	g.reset("Guardian");opening(g);g.step(1.0/60.0,{"strike":true,"skill":true})
	checker.check(g.enemy_focus==3,"Guard commitment cannot secretly strike a focus plate")
	g.reset("Duelist");opening(g);g.step(1.0/60.0,{"strike":true,"dodge":true})
	checker.check(g.enemy_focus==3,"Step commitment cannot secretly strike a focus plate")
	g.reset("Guardian");opening(g);g.step(1.0/60.0,{"strike":true})
	checker.check(g.enemy_focus==2 and g.counters.counters==1 and not g.sentinel_disabled(),"One real counter removes exactly one plate")
	checker.check(g.energy==88 and g.opening==0,"Focus damage retains paid strike cost and consumes the real opening")
	g.step(1.0/60.0,{"strike":true})
	checker.check(g.enemy_focus==2,"Repeated input during recovery cannot remove another plate")
	opening(g);g.step(1.0/60.0,{"strike":true})
	checker.check(g.enemy_focus==1 and not g.sentinel_disabled(),"Two counters leave the threat active")
	opening(g);g.phase="bolt";g.target=g.courier;g.clock=.99
	g.step(1.0/60.0,{"strike":true})
	checker.check(g.enemy_focus==0 and g.phase=="disabled" and g.clock==0 and g.opening==0,"Third real counter makes one authoritative disabled transition")
	checker.check(g.hp==5 and g.cargo==3,"Disabling before queued contact actually cancels that threat")
	checker.check(g.mode=="play" and g.courier.x<Combat.FINISH,"Sentinel resolution alone is not escort completion")
	checker.check(g.courier_speed()==56 and g.last_impact.code=="sentinel_disabled","Safe-road consequence is a real speed change and retained explanation")
	var events: Array=g.events.filter(func(e):return e.kind=="sentinel_disabled")
	checker.check(events.size()==1,"The core shutdown event occurs once")
	var x: float=g.courier.x;var cycle: int=g.cycle;var hp: int=g.hp
	for i in 60:g.step(1.0/60.0,{})
	checker.check(absf(g.courier.x-x-56)<.01,"The living courier actually runs 56px in one simulated second")
	checker.check(g.phase=="disabled" and g.cycle==cycle and g.hp==hp,"No bolt or floor wave resumes after shutdown")
	var before: Dictionary=g.snapshot();g.resolve_threat()
	checker.check(g.snapshot()==before,"Even an explicit stale threat callback cannot hurt after shutdown")
	g.mode="paused";before=g.snapshot();g.step(.05,{"strike":true,"skill_pressed":true})
	checker.check(g.snapshot()==before,"Pause freezes the accelerated courier and shutdown state")
	g.mode="play";g.energy=50;g.step(1.0/60.0,{"strike":true})
	checker.check(g.enemy_focus==0 and g.counters.counters==3 and g.energy>50,"Striking a disabled source neither farms counters nor spends strike cost")
	g.role="Duelist";g.step(1.0/60.0,{"skill_pressed":true})
	checker.check(g.counters.redirects==0 and g.message.contains("disabled"),"Draw cannot restart a disabled sentinel")
	var shutdown=g.snapshot()
	g.cargo=0;g.step(1.0/60.0,{})
	checker.check(g.mode=="lost","A disabled sentinel cannot turn a dead courier into success")
	g.reset("Guardian","Riposte")
	checker.check(g.enemy_focus==3 and g.phase=="rest" and g.courier_speed()==28,"Retry restores the real threat and normal pace with the chosen technique")
	var r=Rehearsal.new();r.start("Guardian");r.stage=2;r.prepare("Guardian");r.confirm();r.game.player=Combat.ENEMY+Vector2(-100,0);r.step(1.0/60.0,{"strike":true})
	checker.check(r.passed and r.game.enemy_focus==2 and r.game.courier_speed()==28,"One practice counter does not pretend the full sentinel was disabled")
	r.repeat()
	checker.check(r.game.enemy_focus==3 and r.game.counters.counters==0,"Repeating rehearsal clears partial core damage")
	var scene=ControlsChecks.scene(checker,"resolution-ui");Trial.key(scene,KEY_ENTER)
	scene.game.enemy_focus=1;opening(scene.game);scene.sound.cue("bolt",0);Trial.key(scene,KEY_J);scene._physics_process(1.0/60.0)
	checker.check(scene.game.sentinel_disabled() and scene.game.mode=="play" and scene.actors.sentinel_left>0,"Actual J adapter executes shutdown and its counter presentation")
	checker.check(not scene.sound.voices[0].playing and scene.sound.history[-1].cue=="counter","Shutdown stops the actual threat voice while preserving the accepted counter response")
	checker.check(scene.keepsakes.earned.is_empty() and not scene.reward_checked,"Shutdown before gate does not award a keepsake")
	Trial.key(scene,KEY_ESCAPE);Trial.key(scene,KEY_R);Trial.key(scene,KEY_ENTER)
	checker.check(scene.game.enemy_focus==3 and scene.game.phase=="rest","Actual abandon/restart restores all three focus plates")
	scene.queue_free()
	var routes := {}
	for setup in [["Guardian","Steady"],["Guardian","Riposte"],["Duelist","Steady"]]:
		var id: String=setup[0]+"-"+setup[1]
		var protect: Dictionary=route(checker,setup[0],setup[1],"protect")
		var counter: Dictionary=route(checker,setup[0],setup[1],"counter")
		checker.check(protect.combat.mode=="won" and protect.combat.enemy_focus==3 and protect.combat.counters.counters==0,id+" can complete the unchanged protective goal without attacking")
		checker.check(counter.combat.mode=="won" and counter.combat.enemy_focus==0 and counter.combat.counters.counters==3,id+" executes three actual counters, shutdown and gate completion")
		checker.check(counter.combat.tick<protect.combat.tick,id+" has an observed shorter crossing from the safe-road response")
		checker.check(counter.marks.earned==protect.marks.earned,id+" has no new mandatory kill reward or progression tier")
		routes[id]={"protect":protect,"counter":counter}
	var recovery: Dictionary=route(checker,"Duelist","Steady","secure_then_recover")
	checker.check(recovery.combat.mode=="won" and recovery.errand.state=="delivered" and recovery.disabled_tick>0,"Disabling first can support an actual later medicine recovery and handoff")
	checker.check(recovery==route(checker,"Duelist","Steady","secure_then_recover"),"The complete shutdown-then-handoff route is repeatable")
	return {"shutdown":shutdown,"routes":routes,"secure_then_recover":recovery}
