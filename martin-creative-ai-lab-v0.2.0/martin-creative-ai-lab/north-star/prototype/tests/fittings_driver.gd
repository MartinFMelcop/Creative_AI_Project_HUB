extends RefCounted
## Execute authored content through the real scene, workshop and both objectives.
const Policy=preload("res://tests/policy.gd")
const GatePolicy=preload("res://tests/gate_policy.gd")
var labels: Array[String]=[]
var failures: Array[String]=[]

func check(value: bool, label: String) -> void:
	labels.append(label)
	if not value: failures.append(label)

func key(scene, code: int) -> void:
	var event:=InputEventKey.new()
	event.keycode=code;event.physical_keycode=code;event.pressed=true
	scene._unhandled_key_input(event)

func result(game) -> Dictionary:
	var snapshot: Dictionary=game.snapshot()
	return {"mode":game.mode,"tick":snapshot.tick,"hp":game.hp,"cargo":game.cargo,
		"energy":snapshot.energy,"counters":snapshot.counters,"outfit":game.outfit,
		"health_limit":game.health_limit,"movement":game.movement_scale,"recovery":game.recovery_rate,
		"events":snapshot.events}

func run(scene, output: String) -> Dictionary:
	var catalog: Dictionary=scene.Combat.Fittings.load_catalog()
	var journeys: Array=[]
	var probes: Array=[]
	if not catalog.ok:
		key(scene,KEY_ENTER);key(scene,KEY_F2)
		check(scene.game.mode=="content_error" and not scene.workshop.active,"Invalid data blocks the actual scene and workshop")
	else:
		for id in catalog.items:
			var definition: Dictionary=catalog.items[id]
			for role in ["Guardian","Duelist"]:
				var g=scene.Combat.new();g.reset(role)
				check(g.fit_outfit(id),role+" accepts authored "+id)
				check(g.hp==definition.health and is_equal_approx(g.movement_scale,definition.movement),"Authored health and movement reach combat: "+role+"/"+id)
				g.energy=40
				var before: Vector2=g.player
				g.step(.05,{"move":Vector2.RIGHT})
				check(is_equal_approx(g.player.x-before.x,250*definition.movement*.05),"Actual displacement follows data: "+id)
				check(is_equal_approx(g.energy,40+definition.recovery*.05),"Actual recovery follows data: "+id)
				check(not g.fit_outfit("standard"),"Live fitting cannot heal or swap: "+id)
				g.mode="paused";var frozen: Dictionary=g.snapshot();g.step(.05,{})
				check(g.snapshot()==frozen,"Pause cannot recover energy: "+id)
				g.reset(role);check(g.recovery_rate==18 and g.hp==5,"Reset removes authored advantages: "+id)
				g.fit_outfit(id);g.energy=40;g.step(.05,{"skill":true})
				if role=="Guardian":check(is_equal_approx(g.energy,39.4),"Guard keeps its original drain: "+id)
				probes.append({"role":role,"id":id,"health":definition.health,"walk":250*definition.movement,"recovery":definition.recovery})
				scene.workshop=scene.Workshop.new()
				scene.selected=role;scene.abandon()
				if id!="standard":
					key(scene,KEY_F2)
					check(scene.workshop.active and scene.game.mode=="title","Scene opens data-driven preparation: "+id)
					scene.workshop.player=scene.workshop.stations[id]
					for tick in 60:scene.workshop.step(1.0/60,Vector2.ZERO,true)
					check(scene.workshop.outfit==id and scene.workshop.blank==0,"One completion makes the authored piece: "+id)
					for tick in 60:scene.workshop.step(1.0/60,Vector2.ZERO,true)
					check(scene.workshop.made==1 and scene.workshop.blank==0,"Holding cannot duplicate output: "+id)
				key(scene,KEY_ENTER)
				check(scene.game.outfit==id and is_equal_approx(scene.game.recovery_rate,definition.recovery),"Actual crossing consumes worn data: "+id)
				for tick in 4200:
					if scene.game.mode!="play":break
					scene.advance_crossing(1.0/60,Policy.command(scene.game))
				check(scene.game.mode=="won" and scene.game.hp>0 and scene.game.cargo>0,"Authored escort completes: "+role+"/"+id)
				var escort:=result(scene.game)
				var entry_hp: int=scene.game.hp
				key(scene,KEY_F4);key(scene,KEY_2);key(scene,KEY_ENTER)
				check(scene.begin_return_gate(),"Authored journey enters return objective: "+id)
				check(scene.game.hp==entry_hp and scene.game.outfit==id and is_equal_approx(scene.game.recovery_rate,definition.recovery),"Return carries gear and health without healing: "+id)
				for tick in 6000:
					if scene.game.mode!="play":break
					scene.advance_crossing(1.0/60,GatePolicy.command(scene.return_gate,"work"))
				check(scene.game.mode=="won" and scene.return_gate.opened(),"Authored return completes: "+role+"/"+id)
				journeys.append({"role":role,"id":id,"escort":escort,"return_gate":result(scene.game)})
		# A matched prefix demonstrates a concrete resource trade-off, not a balance claim.
		if catalog.items.has("field_sash"):
			var observed:=[]
			for id in ["standard","field_sash"]:
				var g=scene.Combat.new();g.reset("Duelist");g.fit_outfit(id);g.energy=24
				g.step(.05,{});g.step(0,{"dodge":true})
				observed.append(g.counters.dodges)
			check(observed==[0,1],"Same 24-energy prefix opens a sash step sooner, at one less health")
	var identities: Dictionary={}
	if FileAccess.file_exists("res://runtime_identity.json"):
		var identity=JSON.parse_string(FileAccess.get_file_as_string("res://runtime_identity.json"))
		for name in identity.sources:
			identities[name]=FileAccess.get_sha256("res://"+name)
			check(identities[name]==identity.sources[name],"Embedded identity: "+name)
	var hashes: Dictionary={}
	for name in ["data/fittings.json","fittings.gd","combat.gd","workshop.gd","arena.gd","actors.gd","character_look.gd","tests/fittings_driver.gd","tests/fittings_probe.gd"]:
		hashes[name]=FileAccess.get_sha256("res://"+name)
	var report: Dictionary={"schema_version":1,"valid":catalog.ok,"errors":catalog.errors,"consumer_hashes":hashes,
		"catalog_sha256":FileAccess.get_sha256(scene.Combat.Fittings.PATH),"checks":{"passed":labels.size()-failures.size(),"failed":failures.size()},
		"labels":labels,"failures":failures,"items":catalog.items,"probes":probes,"journeys":journeys,"sources":identities}
	var file:=FileAccess.open(output,FileAccess.WRITE)
	if file==null:push_error("Cannot write fitting report");return {}
	file.store_string(JSON.stringify(report,"  ")+"\n");file.close()
	print("FITTING_CHECKS ",report.checks.passed," passed / ",report.checks.failed," failed; valid=",catalog.ok)
	return report
