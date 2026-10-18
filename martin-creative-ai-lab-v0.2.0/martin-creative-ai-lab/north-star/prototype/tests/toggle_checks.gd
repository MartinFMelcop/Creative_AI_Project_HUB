extends RefCounted
const Controls=preload("res://controls.gd")
const Combat=preload("res://combat.gd")
const Errand=preload("res://errand.gd")
const Trial=preload("res://tests/rehearsal_checks.gd")
const Guard=preload("res://tests/guard_checks.gd")
const ErrandPolicy=preload("res://tests/errand_policy.gd")
const Checks=preload("res://tests/controls_checks.gd")

static func tick(node, count: int=1, delta: float=1.0/60.0) -> void:
	for i in count:node._physics_process(delta)

static func press(node, code: int) -> void:
	Trial.key(node,code)
	var up=InputEventKey.new();up.physical_keycode=code;up.pressed=false
	node._unhandled_key_input(up)

static func run(checker) -> Dictionary:
	var node=Checks.scene(checker,"toggles")
	checker.check(not node.bindings.toggle_guard and not node.bindings.toggle_interact,"New session keeps both original hold defaults")
	press(node,KEY_F1);press(node,KEY_H);press(node,KEY_I)
	checker.check(node.controls_open and node.bindings.toggle_guard and node.bindings.toggle_interact,"Settings independently select actual session input alternatives")
	checker.check(not node.bindings.dirty and not FileAccess.file_exists(node.controls_path),"Session modes do not rewrite saved keyboard preferences")
	press(node,KEY_ESCAPE);press(node,KEY_ENTER)
	press(node,KEY_K);tick(node,8)
	checker.check(node.game.guard and node.game.guard_age>0.1 and node.bindings.guard_latched,"A released single press sustains the actual Guardian guard")
	press(node,KEY_R);press(node,KEY_T);press(node,KEY_ENTER);tick(node)
	checker.check(node.game.guard and node.bindings.guard_latched,"Ignored management keys during live play cannot silently cancel guard")
	var energy: float=node.game.energy
	tick(node,12)
	checker.check(node.game.energy<energy and node.game.guard,"Toggle guard pays the unchanged sustained posture drain")
	press(node,KEY_K);tick(node)
	checker.check(not node.game.guard and not node.bindings.guard_latched,"Second press lowers rather than refreshing guard")
	press(node,KEY_K);tick(node)
	var echo=InputEventKey.new();echo.physical_keycode=KEY_K;echo.pressed=true;echo.echo=true
	node._unhandled_key_input(echo);tick(node)
	checker.check(node.game.guard and node.bindings.guard_latched,"Auto-repeat cannot flip a latched action")
	press(node,KEY_ESCAPE)
	checker.check(node.game.mode=="paused" and not node.bindings.guard_latched,"Pause cancels the guard intention immediately")
	press(node,KEY_ENTER);tick(node)
	checker.check(not node.game.guard,"Resume requires another deliberate guard press")
	press(node,KEY_K);tick(node);node._notification(Node.NOTIFICATION_APPLICATION_FOCUS_OUT)
	checker.check(node.game.mode=="paused" and not node.bindings.guard_latched,"Focus loss pauses and clears toggle intent")
	press(node,KEY_ENTER);tick(node);press(node,KEY_K);tick(node);press(node,KEY_F1)
	checker.check(not node.bindings.guard_latched and node.game.mode=="paused","Settings clear a live toggle without advancing play")
	press(node,KEY_ESCAPE);press(node,KEY_ENTER);tick(node)
	checker.check(not node.game.guard,"Closing settings cannot resume a latched guard")
	node.begin_crossing();node.game.courier.x=400;tick(node);node.game.player=Errand.CASE
	node.bindings.toggle_interact=false
	press(node,KEY_K);tick(node);Checks.physical(KEY_E);tick(node,48);Checks.physical(KEY_E,false);tick(node)
	checker.check(node.errand.state=="carried" and not node.bindings.guard_latched and not node.game.guard,"Held interaction also clears toggle guard without a queued re-raise")
	node.bindings.toggle_interact=true
	node.guardian_style="Riposte";node.begin_crossing();press(node,KEY_K);tick(node,23)
	checker.check(node.game.guard_state()=="STALE" and node.bindings.guard_latched,"Riposte still expires while toggle stays raised")
	press(node,KEY_K);tick(node);press(node,KEY_K);tick(node)
	checker.check(node.game.guard_state()=="STARTUP","Re-raising Riposte still pays its original startup")
	node.guardian_style="Steady";node.begin_crossing();node.game.player=Vector2(550,390)
	node.game.phase="bolt";node.game.target=node.game.courier;node.game.clock=.89
	press(node,KEY_K);tick(node,8)
	checker.check(node.game.counters.blocks==1 and node.game.hp==5,"Single-press guard blocks an actual frontal threat")
	node.selected="Duelist";node.begin_crossing();node.game.phase="bolt";node.game.target=node.game.courier
	press(node,KEY_K);tick(node)
	checker.check(node.game.counters.redirects==1 and not node.bindings.guard_latched,"Duelist remains a discrete real draw, never toggle guard")
	node.selected="Guardian";node.begin_crossing();node.game.courier.x=400;tick(node)
	press(node,KEY_E);tick(node)
	checker.check(not node.bindings.interact_latched and node.errand.progress==0,"Out-of-range press cannot arm a future recovery")
	node.game.player=Errand.CASE;tick(node)
	checker.check(node.errand.progress==0,"Walking into range without a new press cannot auto-start")
	press(node,KEY_K);tick(node);press(node,KEY_E);tick(node,12)
	checker.check(node.errand.channel and node.errand.progress>0 and not node.game.guard and not node.bindings.guard_latched,"Eligible recovery clears guard and commits the real model")
	press(node,KEY_E);tick(node)
	checker.check(not node.errand.channel and node.errand.progress==0 and not node.bindings.interact_latched,"Second interaction press cancels partial recovery")
	press(node,KEY_E);tick(node,10);Checks.physical(KEY_W);tick(node);Checks.physical(KEY_W,false)
	checker.check(not node.errand.channel and not node.bindings.interact_latched,"Movement cancels toggle recovery rather than rearming it")
	node.game.player=Errand.CASE;tick(node,50)
	checker.check(node.errand.state=="available" and node.errand.progress==0,"Stopping after movement does not silently restart work")
	press(node,KEY_E);tick(node,12);press(node,KEY_K);tick(node)
	checker.check(not node.bindings.guard_latched and not node.game.guard,"Pressing guard during committed recovery cannot queue a later raise")
	tick(node,35)
	checker.check(node.errand.state=="carried" and not node.bindings.interact_latched,"One released press completes actual 0.8 second recovery then disarms")
	node.game.player=node.game.courier;tick(node,40)
	checker.check(node.errand.state=="carried","Recovered case cannot automatically hand over when entering courier range")
	press(node,KEY_E);tick(node,36)
	checker.check(node.errand.state=="delivered" and not node.bindings.interact_latched,"A separate press completes actual moving-courier handoff then disarms")
	var delivered=node.errand.snapshot()
	press(node,KEY_E);tick(node,10)
	checker.check(node.errand.snapshot()==delivered,"Completed interaction cannot be farmed or rearmed")

	# Mechanical equivalence: same frame intent, different physical sustain schedule.
	var held=Combat.new();held.reset("Guardian","Riposte")
	var toggled=Combat.new();toggled.reset("Guardian","Riposte")
	var adapter=Controls.new();adapter.toggle_guard=true
	var equal:=true
	for frame in 100:
		var raised: bool=frame<20 or (frame>=45 and frame<67)
		var edges: bool=frame in [0,20,45,67]
		held.step(1.0/60.0,{"skill":raised,"aim":Vector2.RIGHT})
		toggled.step(1.0/60.0,adapter.translate({"skill_pressed":edges,"aim":Vector2.RIGHT},toggled))
		equal=equal and held.snapshot()==toggled.snapshot()
	checker.check(equal,"Held and edge-toggle schedules preserve exact model state through Riposte expiry and release")

	node.begin_crossing();node.game.courier.x=400;tick(node);node.game.player=Errand.CASE
	press(node,KEY_E);tick(node,10);press(node,KEY_ESCAPE);press(node,KEY_ENTER);tick(node)
	checker.check(not node.bindings.interact_latched and node.errand.progress==0,"Pause cancels partial toggle interaction instead of resuming unattended")
	press(node,KEY_E);tick(node);node.game.mode="lost";tick(node)
	checker.check(not node.bindings.interact_latched,"Terminal loss disarms pending interaction")
	node.begin_crossing();press(node,KEY_K);tick(node);node.abandon()
	checker.check(not node.bindings.guard_latched and node.bindings.toggle_guard,"Abandon clears activity while preserving the chosen session alternative")
	press(node,KEY_T);press(node,KEY_ENTER);press(node,KEY_K);tick(node,5)
	checker.check(node.game.guard and node.rehearsal.active,"The same single-press guard reaches the real rehearsal consumer")
	press(node,KEY_T);node.abandon()
	checker.check(not node.bindings.guard_latched,"Leaving rehearsal cannot carry an active toggle")
	var mapping=Controls.DEFAULTS.duplicate();mapping.skill=KEY_H;mapping.interact=KEY_F
	node.bindings.apply(mapping);node.begin_crossing();press(node,KEY_H);tick(node)
	checker.check(node.game.guard,"Toggle alternative follows the applied ability binding")
	node.game.courier.x=400;tick(node);node.game.player=Errand.CASE;press(node,KEY_F);tick(node,48)
	checker.check(node.errand.state=="carried","Toggle alternative follows the applied interaction binding")
	checker.check(node.bindings.describe("Hold E. Release K.")=="Press F. Toggle H off.","Hints reflect both input mode and remapped key identity")
	var fresh=Controls.new();fresh.load_profile(node.controls_path)
	checker.check(not fresh.toggle_guard and not fresh.toggle_interact and fresh.keys==mapping,"Fresh process preference object retains keys but resets explicit session alternatives")
	var routes=[]
	for style in ["Steady","Riposte","Duelist"]:
		node.selected="Duelist" if style=="Duelist" else "Guardian"
		node.guardian_style="Riposte" if style=="Riposte" else "Steady"
		node.begin_crossing()
		var guard_before:=false;var interact_before:=false;var skill_presses:=0;var interaction_presses:=0
		for frame in 2400:
			var raw: Dictionary=ErrandPolicy.command(node)
			if node.game.guard_style=="Riposte" and node.game.phase=="bolt" and node.game.clock<.76:raw.skill=false
			var wants_guard: bool=raw.get("skill",false)
			var wants_interact: bool=raw.get("interact",false)
			if node.game.role=="Guardian":
				raw.skill_pressed=wants_guard!=guard_before
				if raw.skill_pressed:skill_presses+=1
			guard_before=wants_guard
			raw.interact_pressed=wants_interact and not interact_before
			if raw.interact_pressed:interaction_presses+=1
			interact_before=wants_interact
			raw.erase("skill");raw.erase("interact")
			node.advance_crossing(1.0/60.0,node.bindings.translate(raw,node.game,node.errand))
			node.bindings.settle_intents(node.game,node.errand)
			if node.game.mode!="play":break
		checker.check(node.game.mode=="won" and node.errand.state=="delivered","No-held-command normal crossing and handoff complete for "+style)
		checker.check(interaction_presses==2,"Recovery and handoff need two discrete starts for "+style)
		routes.append({"style":style,"combat":node.game.snapshot(),"errand":node.errand.snapshot(),"guard_presses":skill_presses,"interaction_presses":interaction_presses})
	var report={"routes":routes,"equivalent_frames":100,"delivered":node.errand.state,"session_only":true}
	node.queue_free()
	return report
