extends SceneTree
const Workshop=preload("res://workshop.gd")
const Combat=preload("res://combat.gd")
const Arena=preload("res://arena.gd")
const Policy=preload("res://tests/policy.gd")
var passed:=0
var failed:=0
var routes:=[]
func check(value: bool, label: String) -> void:
	if value:passed+=1
	else:failed+=1;push_error(label)
func key(scene, code: int) -> void:
	var event=InputEventKey.new();event.keycode=code;event.physical_keycode=code;event.pressed=true
	scene._unhandled_key_input(event)
func make(shop, id: String) -> void:
	shop.step(0.0,Vector2.ZERO,false)
	shop.player=shop.stations[id]
	for i in 60:shop.step(1.0/60,Vector2.ZERO,true)
func _initialize() -> void:call_deferred("run")
func run() -> void:
	var w=Workshop.new()
	w.step(0.05,Vector2.RIGHT,true)
	check(w.player==Vector2(575,540) and w.blank==1,"inactive cannot move/craft")
	check(not w.recycle(),"inactive cannot refund")
	w.enter();w.step(0.05,Vector2.ZERO,true)
	check(w.outfit=="standard" and w.progress==0,"range is required")
	w.player=w.stations.riveted
	w.step(0.05,Vector2.ZERO,true)
	check(is_equal_approx(w.progress,0.05),"actual elapsed craft progress")
	w.step(0.05,Vector2.RIGHT,true)
	check(w.progress==0,"movement cancels")
	w.step(0.05,Vector2.ZERO,true);w.step(0.05,Vector2.ZERO,false)
	check(w.progress==0,"release cancels")
	w.step(0.05,Vector2.ZERO,true);w.suspend()
	var frozen=w.snapshot();w.step(0.05,Vector2.LEFT,true)
	check(w.snapshot()==frozen and w.progress==0,"suspend cancels then freezes")
	check(not w.recycle(),"paused cannot recycle")
	w.paused=false;w.player=w.stations.riveted
	for i in 59:w.step(1.0/60,Vector2.ZERO,true)
	check(w.outfit=="standard" and w.blank==1,"incomplete work spends nothing")
	w.step(1.0/60,Vector2.ZERO,true)
	check(w.outfit=="riveted" and w.blank==0 and w.made==1,"one complete make consumes once")
	for i in 20:w.step(1.0/60,Vector2.ZERO,true)
	check(w.message.begins_with("Made and worn"),"held completion retains positive feedback")
	make(w,"trail")
	check(w.outfit=="riveted" and w.made==1 and w.blank==0,"no second output from same blank")
	check(w.recycle() and w.blank==1 and w.outfit=="standard","explicit undo refunds exactly one")
	check(not w.recycle() and w.blank==1,"cannot duplicate refunds")
	w.step(0.05,Vector2.ZERO,true)
	check(w.blank==1 and w.progress==0,"recycling requires release before new work")
	make(w,"trail");w.leave();w.enter()
	check(w.outfit=="trail" and w.blank==0,"workshop reentry retains session fitting")
	w.leave();check(not w.recycle(),"live-run object cannot undo a fitting")
	for role in ["Guardian","Duelist"]:
		for id in ["standard","riveted","trail"]:
			var g=Combat.new();g.reset(role)
			check(not g.fit_outfit("unknown"),"unknown equipment rejected")
			check(g.fit_outfit(id),"both approaches accept fitting")
			var hp:int=6 if id=="riveted" else (4 if id=="trail" else 5)
			var speed:float=200.0 if id=="riveted" else (300.0 if id=="trail" else 250.0)
			check(g.hp==hp and g.health_limit==hp,"actual health trade-off")
			check(not g.fit_outfit("standard"),"start fitting cannot heal/swap twice")
			var x:float=g.player.x
			g.step(0.05,{"move":Vector2.RIGHT})
			check(is_equal_approx(g.player.x-x,speed*0.05),"actual movement trade-off")
			check(not g.fit_outfit("standard"),"live swap rejected")
			check(g.energy==100 and g.cargo==3,"no free resource or courier bonus")
			g.phase="pulse";g.pulse=g.player;g.resolve_threat()
			check(g.hp==hp-1,"gear does not erase pulse damage")
			for i in hp-1:g.resolve_threat()
			g.step(0.0,{})
			check(g.mode=="lost" and g.hp==0 and g.counters.player_hits==hp,"distinct real hit budget still ends in defeat")
			g.reset(role);g.fit_outfit(id)
			var start:Vector2=g.player
			g.step(0.05,{"move":Vector2.RIGHT,"dodge":true})
			check(is_equal_approx(g.player.x-start.x,(620.0 if role=="Duelist" else 470.0)*0.05*speed/250.0),"paid step has actual fitting mobility")
			g.reset(role)
			check(g.outfit=="standard" and g.hp==5 and g.movement_scale==1.0,"model reset has no hidden gear carry")
			g.fit_outfit(id)
			for i in 2400:
				if g.mode!="play":break
				g.step(1.0/60,Policy.command(g))
			check(g.mode=="won" and g.hp>0 and g.cargo>0,"complete feasible fitting route "+role+"/"+id)
			routes.append({"role":role,"outfit":id,"result":g.snapshot()})
	var a=Arena.new();root.add_child(a);a.set_physics_process(false)
	key(a,KEY_F2)
	check(a.workshop.active and a.game.mode=="title","real scene opens workshop without threat time")
	make(a.workshop,"riveted");key(a,KEY_ENTER)
	check(not a.workshop.active and a.game.outfit=="riveted" and a.game.hp==6,"real scene consumes crafted piece")
	key(a,KEY_F2);key(a,KEY_C)
	check(not a.workshop.active and a.game.outfit=="riveted","live controls cannot craft/refund")
	key(a,KEY_ESCAPE);key(a,KEY_F2)
	check(not a.workshop.active,"paused crossing cannot open workshop")
	key(a,KEY_R);key(a,KEY_F2);key(a,KEY_C)
	check(a.workshop.outfit=="standard" and a.workshop.blank==1,"actual title reentry supports undo")
	a.workshop.player=a.workshop.stations.trail;a.workshop.step(0.05,Vector2.ZERO,true)
	a._notification(Node.NOTIFICATION_APPLICATION_FOCUS_OUT)
	check(a.workshop.paused and a.workshop.progress==0,"focus loss cancels work")
	key(a,KEY_ENTER);check(not a.workshop.paused and a.workshop.active,"resume never silently departs")
	a.open_controls();check(a.workshop.paused,"settings suspend fitting")
	a.controls_open=false;key(a,KEY_ENTER);key(a,KEY_R);key(a,KEY_T)
	check(a.rehearsal.active and a.game.outfit=="standard","isolated rehearsal remains standard")
	a.free()
	var hashes={}
	for name in ["workshop.gd","combat.gd","arena.gd","actors.gd","tests/workshop_checks.gd","tests/policy.gd"]:hashes[name]=FileAccess.get_sha256("res://"+name)
	var report={"checks":{"passed":passed,"failed":failed},"consumer_hashes":hashes,"routes":routes,"workshop":w.snapshot()}
	var args=OS.get_cmdline_user_args()
	if args.size()==1:
		var file=FileAccess.open(args[0],FileAccess.WRITE);file.store_string(JSON.stringify(report,"  ")+"\n")
	print("WORKSHOP_CHECKS ",passed," passed; ",failed," failed")
	quit(1 if failed else 0)
