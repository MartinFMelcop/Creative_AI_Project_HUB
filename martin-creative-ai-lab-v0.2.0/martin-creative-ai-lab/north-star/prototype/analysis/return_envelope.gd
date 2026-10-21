extends SceneTree
## Instrument, not shipped gameplay. Load the actual source or PCK rules.
const Combat=preload("res://combat.gd")
const Gate=preload("res://return_gate.gd")
const EscortPolicy=preload("res://tests/policy.gd")
const GatePolicy=preload("res://tests/gate_policy.gd")
var failed:Array[String]=[]
var passed:Array[String]=[]

func check(value:bool,label:String) -> void:
	if value:passed.append(label)
	else:failed.append(label)

func timed(g,input:Dictionary) -> Dictionary:
	# Same 0.76s late raise as the maintained Riposte regression policy.
	if g.guard_style=="Riposte" and g.phase=="bolt" and g.clock<0.76:input.skill=false
	return input

func escort(approach:String,outfit:String):
	var g=Combat.new();g.reset("Duelist" if approach=="duelist" else "Guardian","Riposte" if approach=="riposte" else "Steady")
	if not g.fit_outfit(outfit):push_error("Cannot fit requested outfit");return null
	for tick in 4200:
		if g.mode!="play":break
		g.step(1.0/60,{} if tick<170 else timed(g,EscortPolicy.command(g)))
	return g

func command(room,strategy:String) -> Dictionary:
	if strategy=="idle":return {}
	if strategy=="ground" and not room.game.sentinel_disabled():
		var offset:Vector2=Gate.GROUND-room.game.player
		return {"move":offset.normalized() if offset.length()>20 else Vector2.ZERO,"interact":offset.length()<=20}
	return timed(room.game,GatePolicy.command(room,"work" if strategy=="ground" else strategy))

func take(source,aid:String,strategy:String,delay:int,budget:int,off_line:bool=false) -> Dictionary:
	var room=Gate.new()
	if not room.begin(source,"available","" if aid=="none" else aid):return {"error":"Arrival/aid rejected"}
	if off_line:room.game.player=Vector2(330,270)
	var first_hit:=-1;var first_work:=-1;var ground_tick:=-1;var interruptions:=0;var min_energy:float=room.game.energy
	for tick in budget:
		if room.game.mode!="play":break
		var before_hits:int=room.game.counters.courier_hits
		var was_grounding:bool=room.channel and room.working==Gate.GROUND_INDEX and room.progress>0
		room.step(1.0/60,{} if tick<delay else command(room,strategy))
		if first_hit<0 and room.game.counters.courier_hits>before_hits:first_hit=tick+1
		if first_work<0 and room.channel:first_work=tick+1
		if ground_tick<0 and room.grounded:ground_tick=tick+1
		if was_grounding and not room.channel and not room.grounded:interruptions+=1
		min_energy=minf(min_energy,room.game.energy)
	var snapshot:Dictionary=room.snapshot()
	return {"mode":room.game.mode,"ticks":snapshot.game.tick,"hp":room.game.hp,"integrity":room.game.cargo,
		"energy":snappedf(room.game.energy,.001),"min_energy":snappedf(min_energy,.001),
		"grounded":room.grounded,"ward_disabled":room.game.sentinel_disabled(),"raised":room.raised.duplicate(),
		"exit_reached":room.game.player.x>=1040 and room.game.player.distance_to(Gate.EXIT)<=24,
		"first_winch_hit_tick":first_hit,"first_work_tick":first_work,"ground_tick":ground_tick,
		"ground_interruptions":interruptions,"counters":room.game.counters.duplicate(),
		"end_reason":"winch" if room.game.cargo<=0 else ("player" if room.game.hp<=0 else ("exit" if room.game.mode=="won" else "budget")),
		"trace_sha256":JSON.stringify(snapshot).sha256_text()}

func _initialize() -> void:call_deferred("run")
func run() -> void:
	var args=OS.get_cmdline_user_args()
	if args.size()!=2:quit(2);return
	var protocol:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	var entries:Dictionary={};var checkpoints:Array=[]
	for approach in protocol.approaches:
		for outfit in protocol.outfits:
			var source=escort(approach,outfit)
			if source==null:quit(1);return
			check(source.mode=="won" and source.hp>0 and source.cargo>0,"Real escort: "+approach+"/"+outfit)
			check(source.hp<source.health_limit,"Real damage before arrival: "+approach+"/"+outfit)
			entries[approach+"/"+outfit]=source
			checkpoints.append({"approach":approach,"outfit":outfit,"hp":source.hp,"health_limit":source.health_limit,
				"energy":snappedf(source.energy,.001),"ticks":roundi(source.elapsed*60),"trace_sha256":JSON.stringify(source.snapshot()).sha256_text()})
	# Fixed positive/negative controls run independently of the requested matrix.
	var control_source=escort("steady","standard")
	var idle=take(control_source,"none","idle",0,3600)
	check(idle.mode=="lost" and idle.hp==0 and idle.integrity==2,"Idle control detects body interception and player failure")
	var exposed=take(control_source,"none","idle",0,3600,true)
	check(exposed.mode=="lost" and exposed.integrity==0 and exposed.first_winch_hit_tick>0,"Off-line fixture detects exposed winch failure")
	var positive=take(control_source,"none","ground",0,3600)
	check(positive.mode=="won" and positive.grounded and positive.integrity==1 and positive.counters.counters==0,"Positive control grounds and exits for the exact cost")
	for strategy in ["work","quiet"]:
		var result=take(control_source,"none",strategy,0,3600)
		check(result.mode=="won" and result.ward_disabled==(strategy=="quiet"),"Legacy positive control: "+strategy)
	var r=Gate.new();r.begin(control_source,"available");r.game.player=Gate.GROUND;r.game.cargo=1
	for tick in 90:r.step(1.0/60,{"interact":true})
	check(not r.grounded and r.progress==0 and r.game.cargo==1,"Insufficient integrity negative control")
	r=Gate.new();r.begin(control_source,"available");r.game.player=Gate.GROUND;r.step(.05,{"interact":true});r.suspend();r.game.mode="paused"
	var frozen:String=JSON.stringify(r.snapshot())
	for tick in 90:r.step(1.0/60,{"interact":true})
	check(JSON.stringify(r.snapshot())==frozen,"Paused negative control cannot accumulate hidden work")
	var cases:Array=[]
	for approach in protocol.approaches:
		for outfit in protocol.outfits:
			var source=entries[approach+"/"+outfit]
			for aid in protocol.aids:
				for strategy in protocol.strategies:
					for delay in protocol.delay_ticks:
						var takes:Array=[]
						for repeat in int(protocol.repetitions):takes.append(take(source,aid,strategy,int(delay),int(protocol.max_ticks)))
						cases.append({"id":"%s/%s/%s/%s/%d"%[approach,outfit,aid,strategy,delay],"takes":takes})
	var hashes:Dictionary={}
	for name in ["combat.gd","return_gate.gd","route.gd","fittings.gd","data/fittings.json","tests/policy.gd","tests/gate_policy.gd"]:hashes[name]=FileAccess.get_sha256("res://"+name)
	var report:Dictionary={"schema_version":1,"checks":{"passed":passed,"failed":failed},"consumer_hashes":hashes,
		"checkpoints":checkpoints,"controls":{"idle":idle,"off_line":exposed,"ground":positive},"cases":cases}
	var file=FileAccess.open(args[1],FileAccess.WRITE);file.store_string(JSON.stringify(report,"  ")+"\n");file.close()
	print("ENVELOPE ",cases.size()," conditions; ",failed.size()," control failures: ",failed)
	quit(1 if not failed.is_empty() else 0)
