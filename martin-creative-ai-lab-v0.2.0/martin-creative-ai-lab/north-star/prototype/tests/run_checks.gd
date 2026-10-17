extends SceneTree
const Combat = preload("res://combat.gd")
const Policy = preload("res://tests/policy.gd")
const RehearsalChecks = preload("res://tests/rehearsal_checks.gd")
const KeepsakeChecks = preload("res://tests/keepsake_checks.gd")
var passed := 0
var failed := 0

func check(value: bool, label: String) -> void:
	if value: passed+=1
	else:
		failed+=1
		push_error(label)

func beam(role: String="Guardian"):
	var g=Combat.new()
	g.reset(role)
	g.phase="bolt"
	g.target=g.courier
	g.player=Vector2(550,390)
	return g

func simulate(role: String, active: bool) -> Dictionary:
	var g=Combat.new()
	g.reset(role)
	for i in 2400:
		g.step(1.0/60.0,Policy.command(g) if active else {})
		if g.mode!="play":break
	return g.snapshot()

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var g=beam()
	g.guard=true;g.guard_age=0.1;g.locked_face=Vector2.RIGHT
	g.resolve_threat()
	check(g.hp==5 and g.cargo==3 and g.counters.blocks==1,"Frontal guard protects actual courier beam")
	check(g.energy==78 and g.opening>0,"Protection spends posture and opens response")
	g=beam();g.guard=true;g.guard_age=0.1;g.locked_face=Vector2.LEFT;g.resolve_threat()
	check(g.hp==4 and g.counters.blocks==0,"Rear-facing shield must fail")
	g=beam();g.guard=true;g.guard_age=0.02;g.locked_face=Vector2.RIGHT;g.resolve_threat()
	check(g.hp==4,"Shield startup remains vulnerable")
	g=beam();g.guard=true;g.guard_age=0.1;g.locked_face=Vector2.RIGHT;g.energy=21;g.resolve_threat()
	check(g.hp==4,"Insufficient posture does not create protection")
	g=beam();g.player.y=460;g.resolve_threat()
	check(g.cargo==2,"Standing outside corridor exposes courier")
	g=beam();g.guard=true;g.guard_age=0.1;g.phase="pulse";g.pulse=g.player;g.resolve_threat()
	check(g.hp==4,"Ground pulse bypasses frontal guard")
	g=beam("Duelist");g.step(1.0/60.0,{"skill_pressed":true})
	check(g.redirected and g.counters.redirects==1 and g.target.distance_to(g.player)<1,"Feint changes real locked target")
	check(g.energy<85,"Feint spends finite resolve")
	g.step(1.0/60.0,{"skill_pressed":true})
	check(g.message.contains("already drawn"),"Repeated feint feedback preserves the current threat explanation")
	g.player+=Vector2(0,-100);g.resolve_threat()
	check(g.cargo==3 and g.hp==5 and g.opening>0,"Leaving redirected line protects courier and creates opening")
	g=beam("Duelist");g.energy=0;g.step(1.0/60.0,{"skill_pressed":true,"dodge":true})
	check(g.counters.redirects==0 and g.counters.dodges==0 and g.counters.rejected==2,"Exhausted feint and step fail explicitly")
	g=beam("Duelist");g.step(1.0/60.0,{"dodge":true,"move":Vector2.UP});var after: float=g.energy
	g.step(1.0/60.0,{"dodge":true})
	check(g.counters.dodges==1 and g.energy>=after,"Repeated step cannot bypass cooldown")
	g=beam("Duelist");g.courier=Vector2(650,390);g.target=Vector2(550,390);g.player=Vector2(550,290);g.resolve_threat()
	check(g.cargo==2,"Redirected bolt still hits courier if it crosses the road first")
	g=Combat.new();g.reset("Guardian");g.player.y=600
	for i in 1000:
		g.step(1.0/60.0,{})
		if g.mode!="play":break
	check(g.mode=="lost" and g.hp>0 and g.cargo==0,"Player survival alone does not complete courier objective")
	g=beam();g.mode="paused";var before: Dictionary=g.snapshot();g.step(0.05,{"move":Vector2.RIGHT,"strike":true})
	check(g.snapshot()==before,"Pause freezes resources, courier, clocks and commands")
	g=beam();g.guard=true;g.guard_age=0.1;g.locked_face=Vector2.RIGHT
	for i in 660:g.step(1.0/60.0,{"skill":true})
	check(g.energy<22,"Holding shield cannot sustain protection indefinitely")
	var results: Array[Dictionary]=[]
	for role in ["Guardian","Duelist"]:
		var a: Dictionary=simulate(role,true)
		var b: Dictionary=simulate(role,true)
		check(a==b,role+" complete policy is repeatable")
		check(a.mode=="won",role+" can complete same courier objective")
		check(a.cargo>0 and a.hp>0,role+" preserves courier and player")
		check(a.counters.blocks>0 if role=="Guardian" else a.counters.redirects>0,role+" uses a distinct real response")
		results.append(a)
		var neutral: Dictionary=simulate(role,false)
		check(neutral.mode=="lost",role+" neutral control fails before completion")
		results.append(neutral)
	var scene=load("res://arena.tscn").instantiate()
	root.add_child(scene)
	await process_frame
	scene.set_physics_process(false)
	scene.game.reset("Guardian")
	scene.game.step(1.0/60.0,{"move":Vector2.RIGHT})
	check(scene.game.player.x>550,"Actual playable scene consumes combat model")
	check(scene.game.mode=="play","Configured scene starts selected approach")
	scene.game.reset("Duelist")
	check(scene.game.hp==5 and scene.game.cargo==3 and scene.game.counters.redirects==0,"Retry resets consequences and resources")
	scene._notification(Node.NOTIFICATION_APPLICATION_FOCUS_OUT)
	check(scene.game.mode=="paused","Actual scene pauses on focus loss")
	var event=InputEventKey.new();event.pressed=true;event.physical_keycode=KEY_R
	scene._unhandled_key_input(event)
	check(scene.game.mode=="title" and scene.game.hp==5 and scene.game.cargo==3,"Actual abandon returns to clean selection")
	event.physical_keycode=KEY_2;scene._unhandled_key_input(event)
	check(scene.selected=="Duelist" and scene.game.role=="Duelist","Actual selection updates role and HUD state")
	event.physical_keycode=KEY_ENTER;scene._unhandled_key_input(event)
	check(scene.game.mode=="play" and scene.game.role=="Duelist","Actual Enter starts selected approach")
	scene.game.player=Combat.ENEMY+Vector2(-100,0);scene.game.opening=1.0
	event.physical_keycode=KEY_J;scene._unhandled_key_input(event);scene._physics_process(1.0/60.0)
	check(scene.game.counters.counters==1,"Actual blade input adapter reaches shared consumer")
	var rehearsals: Array[Dictionary]=RehearsalChecks.run(self,scene)
	var keepsakes: Dictionary=KeepsakeChecks.run(self)
	var identities={}
	for name in ["combat.gd","arena.gd","arena.tscn","project.godot","tests/run_checks.gd","tests/policy.gd","rehearsal.gd","tests/rehearsal_checks.gd","keepsakes.gd","tests/keepsake_checks.gd","tests/keepsake_restart.gd"]:
		identities[name]=FileAccess.get_sha256("res://"+name)
	var report={"consumer_hashes":identities,"schema_version":1,"checks":{"passed":passed,"failed":failed},"runtime":Engine.get_version_info().string,"outcomes":results,"rehearsals":rehearsals,"keepsakes":keepsakes}
	var args=OS.get_cmdline_user_args()
	if args.size()==1:
		var file=FileAccess.open(args[0],FileAccess.WRITE)
		file.store_string(JSON.stringify(report,"  ")+"\n")
	print("CROSSING_CHECKS ",JSON.stringify(report))
	quit(1 if failed else 0)
