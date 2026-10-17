extends RefCounted
const Combat = preload("res://combat.gd")
const Rehearsal = preload("res://rehearsal.gd")

static func action(r, tick: int) -> Dictionary:
	if r.stage==0:
		if r.game.role=="Guardian": return {"aim":Vector2.RIGHT,"skill":true}
		return {"skill_pressed":tick==0,"move":Vector2.UP if tick>0 else Vector2.ZERO}
	if r.stage==1: return {"move":Vector2.UP}
	return {"move":Vector2.RIGHT} if r.game.player.distance_to(Combat.ENEMY)>125 else {"strike":true}

static func attempt(r, successful: bool) -> void:
	for tick in 90:
		r.step(1.0/60.0,action(r,tick) if successful else {})
		if r.state=="review": break

static func key(scene, code: int) -> void:
	var event=InputEventKey.new()
	event.pressed=true
	event.physical_keycode=code
	scene._unhandled_key_input(event)

static func run(checker, scene) -> Array[Dictionary]:
	var outcomes: Array[Dictionary]=[]
	for role in ["Guardian","Duelist"]:
		var r=Rehearsal.new()
		r.start(role)
		var before: Dictionary=r.game.snapshot()
		r.step(0.05,{"strike":true,"skill":true,"move":Vector2.RIGHT})
		checker.check(r.game.snapshot()==before and r.state=="ready",role+" waits for explicit start without queued simulation")
		for exercise in 3:
			r.confirm()
			attempt(r,true)
			checker.check(r.state=="review" and r.passed and r.game.hp==5 and r.game.cargo==3,role+" exercise "+str(exercise)+" needs a real successful response")
			before=r.game.snapshot()
			r.step(0.05,{"strike":true,"move":Vector2.DOWN})
			checker.check(r.game.snapshot()==before,role+" result freezes for reading")
			if exercise<2: r.confirm()
		outcomes.append({"role":role,"results":r.results.duplicate(true)})
		checker.check(r.confirm() and not r.active,role+" can finish rehearsal only after all exercises")
	var r=Rehearsal.new()
	r.start("Guardian");r.confirm()
	for i in 65: r.step(1.0/60.0,{"skill":true,"aim":Vector2.LEFT})
	checker.check(not r.passed and r.game.last_impact.code=="guard_wrong_facing","Facing failure is explained, never marked rehearsed")
	r.confirm()
	checker.check(r.stage==0 and r.state=="ready" and r.game.hp==5 and r.game.energy==100,"Failed exercise retries cleanly without advancement")
	r.start("Duelist");r.confirm();attempt(r,false)
	checker.check(not r.passed and r.game.last_impact.code=="courier_first_contact","Avoiding personal damage without drawing does not pass")
	r.confirm();r.confirm()
	for i in 65: r.step(1.0/60.0,{"skill_pressed":i==0})
	checker.check(not r.passed and r.game.hp==4 and r.game.counters.redirects==1,"Drawing without leaving the line still fails")
	r.stage=1;r.prepare("Guardian");r.confirm()
	for i in 65: r.step(1.0/60.0,{"skill":true})
	checker.check(not r.passed and r.game.last_impact.code=="pulse_hit","Holding guard in a pulse never passes")
	r.stage=2;r.prepare("Guardian");r.confirm()
	for i in 65: r.step(1.0/60.0,{"strike":i==0})
	checker.check(not r.passed and r.game.counters.counters==0,"Out-of-range blade and timeout do not pass the opening")
	# Retained diagnosis is separate from transient text, including terminal loss.
	var g=Combat.new();g.reset("Guardian");g.phase="bolt";g.target=g.courier
	g.guard=true;g.guard_age=0.01;g.locked_face=Vector2.RIGHT;g.resolve_threat()
	checker.check(g.last_impact.code=="guard_startup","Contact distinguishes startup failure")
	g.guard_age=0.2;g.energy=21;g.resolve_threat()
	checker.check(g.last_impact.code=="guard_insufficient_posture","Contact distinguishes insufficient impact posture")
	g.guard=false;g.resolve_threat();g.note("Next warning or final loss")
	checker.check(g.last_impact.code=="guard_not_held","Transient warnings cannot erase the last diagnosis")
	g.reset("Duelist")
	checker.check(g.last_impact.is_empty(),"Fresh crossing clears old contact feedback")
	key(scene,KEY_ESCAPE);key(scene,KEY_R);key(scene,KEY_2);key(scene,KEY_T)
	checker.check(scene.rehearsal.active and scene.game==scene.rehearsal.game and scene.rehearsal.state=="ready","Actual T input opens the selected shared-model rehearsal")
	key(scene,KEY_K);key(scene,KEY_ENTER);scene._physics_process(1.0/60.0)
	checker.check(scene.game.counters.redirects==0 and scene.taps.is_empty(),"Ready-screen skill presses are not buffered into the trial")
	scene._notification(Node.NOTIFICATION_APPLICATION_FOCUS_OUT)
	before_scene_pause(checker,scene)
	key(scene,KEY_ENTER)
	checker.check(not scene.rehearsal.paused and scene.rehearsal.state=="live","Enter resumes the same rehearsal trial")
	key(scene,KEY_ESCAPE);key(scene,KEY_R)
	checker.check(not scene.rehearsal.active and scene.game.mode=="title","Abandon leaves no active rehearsal")
	key(scene,KEY_ENTER)
	checker.check(scene.game.mode=="play" and scene.game.hp==5 and scene.game.energy==100 and scene.game.elapsed==0,"Skipping rehearsal starts a normal unmodified crossing")
	# Exercise completion through the actual scene adapter, then start without carryover.
	key(scene,KEY_ESCAPE);key(scene,KEY_R);key(scene,KEY_T)
	for exercise in 3:
		key(scene,KEY_ENTER)
		attempt(scene.rehearsal,true)
		key(scene,KEY_ENTER)
		if scene.rehearsal.active: scene.game=scene.rehearsal.game
	checker.check(not scene.rehearsal.active and scene.game.mode=="play" and scene.game.elapsed==0 and scene.game.courier.x==160 and scene.game.last_impact.is_empty(),"Actual completion starts a clean crossing without rehearsed advantage")
	var arrow=InputEventKey.new()
	arrow.keycode=KEY_LEFT;arrow.pressed=true
	Input.parse_input_event(arrow)
	Input.flush_buffered_events()
	scene._physics_process(1.0/60.0)
	checker.check(scene.game.facing==Vector2.LEFT,"Logical navigation arrows reach actual scene aiming without a physical code")
	var released=arrow.duplicate()
	released.pressed=false;Input.parse_input_event(released);Input.flush_buffered_events()
	return outcomes

static func before_scene_pause(checker,scene) -> void:
	var before: Dictionary=scene.game.snapshot()
	scene._physics_process(0.05)
	checker.check(scene.rehearsal.paused and scene.game.snapshot()==before,"Focus loss freezes rehearsal clock, courier and resources")
