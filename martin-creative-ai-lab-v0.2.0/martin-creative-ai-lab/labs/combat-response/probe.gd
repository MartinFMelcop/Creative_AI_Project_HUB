extends SceneTree
## Controlled observations of the unchanged P06 native scene, not player research.
var arena
var protocol: Dictionary

func _initialize() -> void:
	call_deferred("run")

func snapshot(tick: int, kind: String) -> Dictionary:
	return {"tick":tick,"kind":kind,"hp":arena.hp,"boss_hp":arena.boss_hp,
		"resolve":snappedf(arena.stamina,0.000001),"distance_px":snappedf(arena.player.position.distance_to(arena.boss.position),0.000001),
		"stage":arena.boss_stage,"action":arena.player_action,"action_age_s":snappedf(arena.action_time,0.000001),
		"invulnerable_s":snappedf(arena.invulnerable,0.000001)}

func take(case: Dictionary, contact_tick: int) -> Dictionary:
	arena.reset_encounter()
	arena.set_physics_process(false)
	arena.mode = "fight"
	arena.player.position = Vector2(650-float(case.get("distance_px",85)),400)
	arena.boss.position = Vector2(650,400)
	arena._start_pattern() # Actual phase-one sweep, warning, collision and recovery.
	var response_tick := contact_tick-int(case.get("lead_ticks",0))
	var events: Array[Dictionary] = []
	var first_contact := -1
	var first_open := -1
	var minimum_resolve := 100.0
	for tick in range(1,int(protocol.duration_ticks)+1):
		await physics_frame
		var before: Dictionary = arena.stats.duplicate(true)
		var previous_hp: float = arena.boss_hp
		var previous_stage: String = arena.boss_stage
		var response := str(case.get("response","none")) if tick==response_tick else "none"
		var move := Vector2.LEFT if response=="dodge_away" else Vector2.RIGHT if response=="dodge_inward" else Vector2.ZERO
		if tick==response_tick and case.has("resolve_at_press"):
			arena.stamina = float(case.resolve_at_press)
		if bool(case.get("echo_at_contact",false)) and tick==contact_tick:
			arena.echo_origin = arena.player.position
			arena.echo_time = 0.65-1.0/float(protocol.physics_hz)
			arena.echo_hit = false
		var strike := tick==int(case.get("counter_tick",protocol.counter_tick))
		if response!="none": events.append(snapshot(tick,"request_"+response))
		if strike: events.append(snapshot(tick,"request_strike"))
		if tick==contact_tick: events.append(snapshot(tick,"calibrated_contact_before_step"))
		arena.step_fight(1.0/float(protocol.physics_hz),move,strike,response=="seal",response.begins_with("dodge"),response=="parry")
		minimum_resolve = minf(minimum_resolve,arena.stamina)
		for key in ["damage_taken","parries","dodges","parry_attempts","seals","strikes","hits"]:
			if int(arena.stats[key])!=int(before[key]): events.append(snapshot(tick,key))
		if arena.boss_hp!=previous_hp: events.append(snapshot(tick,"boss_damage"))
		if arena.boss_stage!=previous_stage: events.append(snapshot(tick,"stage_"+arena.boss_stage))
		if first_contact<0 and (arena.stats.damage_taken>0 or arena.stats.parries>0): first_contact=tick
		if first_open<0 and arena._boss_open(): first_open=tick
	var result := {"id":case.id,"response_tick":response_tick,"first_contact_tick":first_contact,
		"hp":arena.hp,"boss_damage":160-arena.boss_hp,"resolve":snappedf(arena.stamina,0.000001),
		"minimum_resolve":snappedf(minimum_resolve,0.000001),"first_open_tick":first_open,"ward_pressure":arena.ward,
		"distance_px":snappedf(arena.player.position.distance_to(arena.boss.position),0.000001),
		"parries":arena.stats.parries,"parry_attempts":arena.stats.parry_attempts,
		"dodges":arena.stats.dodges,"seals":arena.stats.seals,"strikes":arena.stats.strikes,
		"damage_taken":arena.stats.damage_taken,"events":events}
	return result

func run() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size()!=1:
		push_error("Expected one absolute protocol path after --")
		quit(2)
		return
	var data = JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	if not data is Dictionary:
		push_error("Protocol must be a JSON object")
		quit(2)
		return
	protocol = data
	Engine.physics_ticks_per_second = int(protocol.physics_hz)
	arena = load("res://arena.tscn").instantiate()
	root.add_child(arena)
	await physics_frame
	arena.set_physics_process(false)
	var calibration: Dictionary = await take({"id":"calibration","counter_tick":-1},0)
	var contact_tick := int(calibration.first_contact_tick)
	if contact_tick<1:
		push_error("Neutral control did not observe a real sweep collision")
		quit(1)
		return
	var rows: Array[Dictionary] = []
	for repetition in int(protocol.repetitions):
		for case in protocol.cases:
			var row: Dictionary = await take(case,contact_tick)
			row["repetition"] = repetition+1
			rows.append(row)
	arena.sound.stop()
	print("COMBAT_RESPONSE_RESULT ",JSON.stringify({"schema_version":1,"engine":Engine.get_version_info().string,
		"physics_hz":protocol.physics_hz,"calibration":calibration,"contact_tick":contact_tick,"rows":rows}))
	quit(0)
