extends SceneTree
const Model=preload("model.gd")
const Catalog=preload("catalog.gd")
const View=preload("view.gd")
const Policy=preload("../tests/policy.gd")
var passed:=0
var failed:=0
var outcomes:Array=[]
func check(value:bool,label:String) -> void:
	if value:passed+=1
	else:failed+=1;printerr("FAIL: "+label)
func ticks(model,n:int,command:Dictionary={}) -> void:
	for i in n:model.step(1.0/60.0,command if i==0 else {})
func sample(id:String,distance:float,opening:float) -> Dictionary:
	var m=Model.new();m.prepare(id if id not in ["walk","step"] else "none");m.begin()
	m.game.player=Model.Combat.ENEMY-Vector2(distance,0);m.game.opening=opening
	if id in ["snap","reach"]:
		m.step(1.0/60.0,{"rush":true,"aim":Vector2.RIGHT})
		for i in 80:
			if m.travel_left<=0 and m.recovery_left<=0:break
			m.step(1.0/60.0,{})
	if id in ["walk","step"]:
		for tick in 120:
			if m.game.player.distance_to(Model.Combat.ENEMY)<=130 and m.game.step_left<=0:break
			var command={"aim":Vector2.RIGHT}
			if m.game.player.distance_to(Model.Combat.ENEMY)>125:command.move=Vector2.RIGHT
			if id=="step" and tick==0:command.dodge=true
			m.step(1.0/60.0,command)
	m.step(1.0/60.0,{"strike":true})
	return {"id":id,"distance":distance,"initial_opening":opening,"counters":m.game.counters.counters,"energy":m.game.energy,"elapsed":m.game.elapsed,"remaining_opening":m.game.opening,"final_distance":m.game.player.distance_to(Model.Combat.ENEMY)}
func _initialize() -> void:
	run.call_deferred()
func run() -> void:
	var loaded=Catalog.load_catalog()
	check(loaded.ok and loaded.items.size()==2,"shipped catalog")
	var raw=JSON.parse_string(FileAccess.get_file_as_string(Catalog.PATH))
	for field in ["cost","speed","travel","recovery","cooldown"]:
		for bad in [true,"1",null,-1,100000]:
			var mutant=raw.duplicate(true);mutant.rushes[0][field]=bad
			check(not Catalog.validate(mutant).ok,"reject typed/range mutant "+field+str(bad))
	for mutation in ["unknown","duplicate","version","short_cooldown","non_ascii","reserved_id"]:
		var mutant=raw.duplicate(true)
		match mutation:
			"unknown":mutant.rushes[0].script="res://arbitrary.gd"
			"duplicate":mutant.rushes.append(mutant.rushes[0])
			"version":mutant.schema_version=true
			"short_cooldown":mutant.rushes[0].cooldown=0.1
			"non_ascii":mutant.rushes[0].name="é"
			"reserved_id":mutant.rushes[0].id="none"
		check(not Catalog.validate(mutant).ok,"reject "+mutation)
	check(not Model.new("res://missing-rush.json").begin(),"missing content blocks entry")
	var m=Model.new();check(not m.prepare("unknown"),"unknown selection refused");m.prepare("reach");m.begin()
	check(not m.prepare("snap") and not m.begin(),"entry locks selection and restart")
	m.game.energy=29;m.step(0,{"rush":true});check(m.starts==0 and m.game.energy==29,"insufficient energy cannot spend")
	m.game.energy=100;m.step(0,{"rush":true,"aim":Vector2.RIGHT})
	check(m.starts==1 and m.game.energy==70,"exact single upfront cost")
	var x=m.game.player.x
	for i in 18:m.step(1.0/60.0,{"rush":true,"move":Vector2.LEFT,"aim":Vector2.LEFT,"skill":true,"dodge":true,"strike":true})
	check(absf(m.game.player.x-x-240)<0.01 and m.starts==1,"locked 240px trajectory and no repeated spend")
	check(not m.game.guard and m.game.counters.dodges==0 and m.game.counters.counters==0 and m.game.energy==70,"conflicting actions suppressed; no travel regeneration")
	check(m.recovery_left>0,"arrival recovery exists")
	m.step(1.0/60.0,{"skill":true,"dodge":true,"strike":true})
	check(not m.game.guard and m.game.counters.dodges==0,"recovery blocks action inputs")
	ticks(m,24);check(not m.game.guard and m.game.counters.dodges==0,"suppressed edges do not replay")
	var hit=Model.new();hit.prepare("reach");hit.begin();hit.game.phase="pulse";hit.game.clock=0.99;hit.game.pulse=hit.game.player
	hit.step(1.0/60.0,{"rush":true,"aim":Vector2.RIGHT})
	check(hit.game.hp==4 and hit.game.counters.player_hits==1 and hit.travel_left>0,"rush takes real pulse damage and stays committed while threats advance")
	var boundary=Model.new();boundary.prepare("reach");boundary.begin();boundary.game.player.x=1080
	boundary.step(0.05,{"rush":true,"aim":Vector2.RIGHT});ticks(boundary,30)
	check(boundary.game.player.x==1082,"movement obeys field boundary")
	var guard=Model.new();guard.prepare("snap");guard.begin();guard.step(0.02,{"skill":true});guard.step(0,{"rush":true})
	check(guard.starts==0,"held guard cannot be bypassed")
	var stepper=Model.new();stepper.prepare("snap");stepper.begin();stepper.step(0.01,{"dodge":true});stepper.step(0,{"rush":true})
	check(stepper.starts==0,"paid step cannot be bypassed")
	for condition in [[360.0,0.7],[170.0,0.4]]:
		for id in ["none","snap","reach","walk","step"]:outcomes.append(sample(id,condition[0],condition[1]))
	check(outcomes[0].counters==0 and outcomes[1].counters==0 and outcomes[2].counters==1 and outcomes[3].counters==0 and outcomes[4].counters==0,"far brief opening distinguishes reach from walk and ordinary step")
	check(outcomes[5].counters==0 and outcomes[6].counters==1 and outcomes[7].counters==0 and outcomes[8].counters==1 and outcomes[9].counters==1,"near short opening admits snap, walking and step; reach recovery misses it")
	var journeys=[]
	for id in ["none","snap","reach"]:
		var current=Model.new();current.prepare(id);current.begin()
		var baseline=Model.Combat.new();baseline.reset("Guardian")
		for tick in 4000:
			var command:Dictionary=Policy.command(current.game)
			if tick==0 and id!="none":command.rush=true
			current.step(1.0/60.0,command)
			if id=="none":baseline.step(1.0/60.0,command)
			if current.game.mode!="play":break
		check(current.game.mode=="won" and current.game.hp>0 and current.game.cargo>0,"complete living crossing "+id)
		check(current.starts==(0 if id=="none" else 1),"journey consumes actual selected rush "+id)
		if id=="none":check(current.game.snapshot()==baseline.snapshot(),"no-rush wrapper exactly preserves base model journey")
		journeys.append({"selected":id,"starts":current.starts,"combat":current.game.snapshot()})
	var view=View.new();root.add_child(view)
	view._notification(Node.NOTIFICATION_APPLICATION_FOCUS_OUT)
	check(not view.paused,"preparation focus loss cannot leave hidden pause")
	view._notification(Node.NOTIFICATION_APPLICATION_FOCUS_IN)
	var enter=InputEventKey.new();enter.keycode=KEY_ENTER;enter.pressed=true
	view._input(enter)
	check(view.model.game.mode=="play" and not view.paused,"actual view entry starts unpaused")
	view._notification(Node.NOTIFICATION_APPLICATION_FOCUS_OUT)
	var prior=view.model.game.snapshot();view._physics_process(0.05)
	check(view.paused and view.model.game.snapshot()==prior,"actual local focus loss freezes world")
	view._notification(Node.NOTIFICATION_APPLICATION_FOCUS_IN)
	var escape=InputEventKey.new();escape.keycode=KEY_ESCAPE;escape.pressed=true;view._input(escape)
	view._physics_process(0.05)
	check(not view.paused and view.model.game.elapsed>0,"actual view explicit resume")
	view.model.game.mode="won";view._input(enter)
	check(view.model.game.mode=="title" and view.model.cooldown==0,"terminal retry creates fresh preparation, never active respec")
	view.free()
	var result={"kind":"native_ability_controls","passed":passed,"failed":failed,"matched_windows":outcomes,"journeys":journeys}
	var args=OS.get_cmdline_user_args()
	if args.size()==1:
		var file=FileAccess.open(args[0],FileAccess.WRITE);file.store_string(JSON.stringify(result,"  ")+"\n")
	print("Ability controls: %d passed, %d failed"%[passed,failed]);quit(1 if failed else 0)
