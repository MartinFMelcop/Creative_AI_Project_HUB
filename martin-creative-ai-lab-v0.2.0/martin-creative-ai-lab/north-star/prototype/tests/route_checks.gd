extends SceneTree
const Combat=preload("res://combat.gd")
const Route=preload("res://route.gd")
const Arena=preload("res://arena.gd")
const Policy=preload("res://tests/policy.gd")
var passed:=0
var failed:=0
var routes:=[]
func check(value: bool, label: String) -> void:
	if value:passed+=1
	else:failed+=1;push_error(label)
static func command(g, choice: String) -> Dictionary:
	if choice=="ridge" and g.route.kind=="road":
		if g.player.distance_to(Route.BOARD)>24:return {"move":(Route.BOARD-g.player).normalized()}
		return {"route_signal":true}
	return Policy.command(g)
func beam():
	var g=Combat.new();g.reset("Guardian");g.route.choose("ridge",g.courier)
	g.phase="bolt";g.target=Vector2(400,250);g.courier=Vector2(400,250);g.player=Vector2(500,300)
	return g
func _initialize() -> void:call_deferred("run")
func run() -> void:
	var r=Route.new()
	check(r.kind=="road" and not r.locked,"default road")
	check(not r.choose("teleport",Vector2(160,390)),"invalid choice rejects")
	check(r.choose("ridge",Vector2(160,390)),"explicit choice before fork")
	var before=r.snapshot();var future:Vector2=r.predict(Vector2(399,390),29)
	check(future.is_equal_approx(Vector2(400,362)) and r.snapshot()==before,"prediction crosses corner without changing state")
	var at:Vector2=r.advance(Vector2(399,390),29,0.01)
	check(at.is_equal_approx(future) and r.locked,"actual movement spends budget around corner and locks")
	check(r.progress(at)>240.0/1120.0,"vertical travel advances displayed progress")
	check(not r.choose("road",at),"cannot replan after first marker")
	r=Route.new();r.choose("ridge",Vector2(160,390))
	check(r.advance(Vector2(160,390),1120,0)==Vector2(1000,390),"full route is 1120px")
	check(r.progress(Vector2(1000,390))==1.0,"arrival progress is complete")
	r=Route.new();r.choose("ridge",Vector2(160,390))
	var single:Vector2=r.predict(Vector2(160,390),1119)
	at=Vector2(160,390)
	for i in 1119:at=r.advance(at,1,0)
	check(at.is_equal_approx(single) and at.x<1000,"step subdivision preserves distance and no premature arrival")
	r=Route.new();check(r.advance(Vector2(160,390),840,0)==Vector2(1000,390),"road remains 840px")
	check(not r.choose("ridge",Vector2(400,390)),"exact fork boundary rejects")
	check(r.cover_distance(Combat.ENEMY,Vector2(400,250))<0,"road has no cover")
	r=Route.new();r.choose("ridge",Vector2(160,390))
	check(r.cover_distance(Combat.ENEMY,Vector2(400,250))>0,"ridge screen intersects finite ray")
	check(r.cover_distance(Combat.ENEMY,Vector2(700,250))<0,"screen behind endpoint cannot block")
	check(r.cover_distance(Combat.ENEMY,Vector2(400,390))<0,"road-height ray misses upper screen")
	check(r.cover_distance(Combat.ENEMY,Vector2(790,200))<0,"parallel ray has no invented contact")
	var g=beam();g.resolve_threat()
	check(g.hp==5 and g.cargo==3 and g.route.covered==1,"screen prevents damage behind it")
	check(g.counters.blocks==0 and g.opening==0,"cover grants no personal block or free counter")
	check(g.last_impact.code=="cover_blocked","cover owns distinct causal feedback")
	g=beam();g.player=Combat.ENEMY.lerp(g.target,0.2);g.resolve_threat()
	check(g.hp==4 and g.route.covered==0,"nearer player takes contact before screen")
	g=beam();g.courier=Combat.ENEMY.lerp(g.target,0.2);g.resolve_threat()
	check(g.cargo==2 and g.route.covered==0,"nearer courier takes contact before screen")
	g=beam();g.player=Combat.ENEMY.lerp(g.target,0.2)
	g.guard=true;g.guard_age=0.1;g.locked_face=(Combat.ENEMY-g.player).normalized();g.resolve_threat()
	check(g.counters.blocks==1 and g.route.covered==0 and g.opening>0,"nearer live guard keeps personal ownership")
	g=beam();g.phase="pulse";g.pulse=g.player;g.resolve_threat()
	check(g.hp==4 and g.route.covered==0,"screen never protects floor")
	g=Combat.new();g.reset("Guardian")
	check(not g.signal_route("ridge"),"range required for signal")
	g.player=Route.BOARD;g.mode="paused";check(not g.signal_route("ridge"),"paused cannot signal")
	var frozen=g.snapshot();g.step(0.05,{"route_signal":true})
	check(g.snapshot()==frozen,"paused signal cannot queue or advance time")
	g.mode="play";check(g.signal_route("ridge"),"model accepts actual nearby signal")
	check(g.signal_route("road"),"choice reversible before commitment")
	g.courier.x=400;check(not g.signal_route("ridge"),"locked signal cannot alter route")
	g.reset("Guardian");check(g.route.kind=="road" and g.route.covered==0,"new attempt resets route")
	for role in ["Guardian","Duelist"]:
		for choice in ["road","ridge"]:
			g=Combat.new();g.reset(role)
			var visited:=false
			for i in 4200:
				if g.mode!="play":break
				g.step(1.0/60,command(g,choice))
				if g.courier.y<300:visited=true
			check(g.mode=="won" and g.hp>0 and g.cargo>0,"complete route "+role+"/"+choice)
			check(visited==(choice=="ridge"),"courier really used selected path")
			routes.append({"role":role,"choice":choice,"combat":g.snapshot(),"route":g.route.snapshot(),"visited_upper":visited})
	g=Combat.new();g.reset("Guardian")
	for i in 4200:
		if g.mode!="play":break
		var input:Dictionary=command(g,"ridge") if g.route.kind=="road" else {}
		g.step(1.0/60,input)
	check(g.mode=="lost","route choice alone cannot finish the escort")
	check(g.route.covered>0,"neutral control actually received partial filter protection")
	var a=Arena.new();root.add_child(a);a.set_physics_process(false);a.begin_crossing()
	a.game.player=Route.BOARD;a.advance_crossing(1.0/60,{"interact_pressed":true})
	check(a.game.route.kind=="ridge","actual normal scene consumes interaction press")
	a.advance_crossing(1.0/60,{"interact":true})
	check(a.game.route.kind=="ridge","held interaction never cycles route")
	check(a.errand.state=="waiting" and a.errand.progress==0,"board press cannot recover medicine")
	a.game.courier=Vector2(400,390);a.game.route.locked=true;a.game.player=a.errand.CASE
	for i in 48:a.advance_crossing(1.0/60,{"interact":true,"interact_pressed":i==0})
	check(a.errand.state=="carried" and a.game.route.kind=="ridge","same interaction still recovers medicine away from locked board")
	a.game.mode="paused";a.advance_crossing(1.0/60,{"interact_pressed":true})
	check(a.game.route.kind=="ridge","pause cannot change committed intent")
	a.abandon();a.rehearsal.start("Guardian");a.game=a.rehearsal.game
	a.game.player=Route.BOARD;a.advance_crossing(1.0/60,{"interact_pressed":true})
	check(a.game.route.kind=="road","isolated rehearsal never signals a route")
	a.abandon();a.begin_crossing();a.game.player=Route.BOARD
	a.bindings.keys.interact=KEY_F;a.bindings.refresh_labels()
	var event=InputEventKey.new();event.physical_keycode=KEY_F;event.keycode=KEY_F;event.pressed=true
	a._unhandled_key_input(event);a.advance_crossing(1.0/60,a.taps)
	check(a.game.route.kind=="ridge","remapped actual scene key signals route")
	check(a.bindings.describe("E AT SIGN")=="F AT SIGN","route hint follows actual binding")
	a.free()
	var hashes={}
	for name in ["route.gd","combat.gd","arena.gd","actors.gd","tests/route_checks.gd","tests/policy.gd"]:hashes[name]=FileAccess.get_sha256("res://"+name)
	var report={"checks":{"passed":passed,"failed":failed},"consumer_hashes":hashes,"routes":routes}
	var args=OS.get_cmdline_user_args()
	if args.size()==1:
		var file=FileAccess.open(args[0],FileAccess.WRITE);file.store_string(JSON.stringify(report,"  ")+"\n")
	print("ROUTE_CHECKS ",passed," passed / ",failed," failed")
	quit(1 if failed else 0)
