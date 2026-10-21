extends SceneTree
## Check server advice against real paid actions and contacts, including boundaries.
const Server=preload("../authority/server.gd")
const Model=preload("res://combat.gd")
const View=preload("../authority/view.gd")
var passed:=0
var failures:Array=[]
func check(ok:bool,label:String) -> void:
	if ok:passed+=1
	else:failures.append(label)
func model(role:String="Guardian"):
	var value=Model.new();value.reset(role);return value
func _initialize() -> void:
	for energy in [24.99,25.0,100.0]:
		var game=model();game.energy=energy
		var hint:Dictionary=Server.action_hints(game).step
		game.step(0,{"dodge":true})
		check((hint.status=="ready")==(game.counters.dodges==1),"Step admission agrees at resolve "+str(energy))
		if game.counters.dodges==1:check(is_equal_approx(energy-game.energy,hint.cost),"Step price is actual paid cost")
	var cooling=model();cooling.step_cooldown=.1
	check(Server.action_hints(cooling).step.status=="recovering","Step exposes real recovery")
	cooling.step(0,{"dodge":true});check(cooling.counters.dodges==0,"Recovering step cannot spend again")
	for distance in [129.99,130.0,130.01]:
		var game=model();game.player=Model.ENEMY-Vector2(distance,0);game.opening=1
		var hint:Dictionary=Server.action_hints(game).counter
		game.step(0,{"strike":true})
		check((hint.status=="ready")==(game.counters.counters==1),"Counter guide agrees with actual contact at "+str(distance))
		check((distance<=Server.action_hints(game).counter_radius)==(game.counters.counters==1),"Drawn counter radius matches actual contact")
		check(is_equal_approx(100-game.energy,hint.cost),"A missed counter still pays the advertised cost")
	for state in ["armored","guard","stepping","recovering","resolve","silent","terminal"]:
		var game=model();game.player=Model.ENEMY;game.opening=1
		if state=="armored":game.opening=0
		elif state=="guard":game.guard=true;game.guard_age=.1
		elif state=="stepping":game.step_left=.1
		elif state=="recovering":game.strike_cooldown=.1
		elif state=="resolve":game.energy=11.99
		elif state=="silent":game.enemy_focus=0
		else:game.mode="lost"
		var hint:Dictionary=Server.action_hints(game).counter
		game.step(0,{"strike":true,"skill":state=="guard"})
		check(hint.status==state and game.counters.counters==0,"Counter explains actual unavailable state: "+state)
	for distance in [339.99,340.0,340.01]:
		var game=model("Duelist");game.phase="bolt";game.player=Model.ENEMY-Vector2(distance,0)
		var hint:Dictionary=Server.action_hints(game).technique
		game.step(0,{"skill_pressed":true})
		check((hint.status=="ready")==game.redirected,"Draw guide agrees with actual range at "+str(distance))
		check((distance<=Server.action_hints(game).draw_radius)==game.redirected,"Drawn attraction radius matches actual admission")
		if game.redirected:check(is_equal_approx(100-game.energy,hint.cost),"Draw price is actual paid cost")
	for state in ["bolt","drawn","recovering","resolve","silent"]:
		var game=model("Duelist");game.phase="bolt";game.player=Model.ENEMY
		if state=="bolt":game.phase="pulse"
		elif state=="drawn":game.redirected=true
		elif state=="recovering":game.feint_cooldown=.1
		elif state=="resolve":game.energy=15.99
		else:game.enemy_focus=0;game.phase="disabled"
		var hint:Dictionary=Server.action_hints(game).technique
		var before:int=game.counters.redirects;game.step(0,{"skill_pressed":true})
		check(hint.status==state and game.counters.redirects==before,"Draw explains actual unavailable state: "+state)
	for style in ["Steady","Riposte"]:
		for age in [.059,.06,.3,.301]:
			var game=model();game.guard_style=style;game.guard=true;game.guard_age=age
			var hint:Dictionary=Server.action_hints(game).technique
			check((hint.status=="live")==game.guards_from(Model.ENEMY),style+" advice agrees with actual guard contact window "+str(age))
	var guard=model();guard.guard=true;guard.guard_age=.1
	var hint:Dictionary=Server.action_hints(guard).technique
	guard.phase="bolt";guard.target=guard.player;guard.resolve_threat()
	check(guard.counters.blocks==1 and is_equal_approx(100-guard.energy,hint.cost),"Guard contact price is actual block cost")
	var drain=model();drain.step(.05,{"skill":true})
	check(is_equal_approx((100-drain.energy)/.05,hint.drain),"Held guard drain is actual continuous cost")
	var pulse=model();pulse.phase="pulse";pulse.pulse=pulse.player;pulse.guard=true;pulse.guard_age=.1
	check(Server.action_hints(pulse).technique.status=="ground","Guard advice warns about unblockable ground pulse")
	pulse.resolve_threat();check(pulse.hp<5,"Ground warning corresponds to actual guard failure")
	var pure=model();var before:String=JSON.stringify(pure.snapshot());Server.action_hints(pure)
	check(before==JSON.stringify(pure.snapshot()),"Reading hints does not mutate actual model")
	var view=View.new();view.remote.confirmed={"actions":Server.action_hints(pure)};view.remote.latest={"quarantined":false};view.remote.status="live"
	check(view.action_rows()[1].available and not view.action_rows()[2].available,"UI distinguishes paid step from armored counter")
	for status in ["stale","error","closed","terminal"]:
		view.remote.status=status
		check(view.action_rows().all(func(row):return not row.available and row.caption.contains("BLOCKED")),"UI never advertises active action with transport "+status)
	view.remote.status="live";view.controls.suspend()
	check(view.action_rows().all(func(row):return not row.available),"Suspension masks old ready advice")
	view.controls.resume();view.remote.latest.quarantined=true
	check(view.action_rows().all(func(row):return not row.available and row.caption.contains("REARM")),"Server quarantine masks ready advice")
	view.remote.latest.quarantined=false;view.focused=false
	check(view.action_rows().all(func(row):return not row.available),"Focus loss masks ready advice")
	view.free()
	print(JSON.stringify({"passed":passed,"failed":failures.size(),"failures":failures}))
	quit(0 if failures.is_empty() else 1)
