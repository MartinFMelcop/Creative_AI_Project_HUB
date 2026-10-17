extends RefCounted
const Store = preload("res://keepsakes.gd")
const Policy = preload("res://tests/policy.gd")
const Trial = preload("res://tests/rehearsal_checks.gd")
class RefuseReplace:
	extends "res://keepsakes.gd"
	var refuse := true
	func _replace_file(from: String, to: String) -> Error:
		return ERR_CANT_CREATE if refuse else super._replace_file(from,to)

static func put(path: String, content: String) -> void:
	var file=FileAccess.open(path,FileAccess.WRITE)
	file.store_string(content)
	file.close()

static func complete(scene, role: String) -> void:
	scene.selected=role
	scene.begin_crossing()
	for i in 2400:
		scene.advance_crossing(1.0/60.0,Policy.command(scene.game))
		if scene.game.mode!="play":break

static func fresh_scene(tree, name: String):
	var scene=load("res://arena.tscn").instantiate()
	scene.profile_path="user://keepsake-checks/"+name+".json"
	DirAccess.remove_absolute(scene.profile_path)
	tree.root.add_child(scene)
	scene.set_physics_process(false)
	return scene

static func run(checker) -> Dictionary:
	DirAccess.make_dir_recursive_absolute("user://keepsake-checks")
	var path="user://keepsake-checks/store.json"
	DirAccess.remove_absolute(path)
	var store=Store.new()
	checker.check(store.load_profile(path) and store.earned.is_empty() and store.equipped=="" and not FileAccess.file_exists(path),"Fresh profile grants no mark and does not create a save")
	checker.check(not store.earn("Unknown") and not store.dirty,"Unknown approach cannot mint a mark")
	checker.check(store.earn("Guardian") and store.equipped=="" and not store.dirty,"New mark saves without automatic equipment")
	var prior=FileAccess.get_file_as_bytes(path)
	checker.check(not store.earn("Guardian") and FileAccess.get_file_as_bytes(path)==prior,"Repeated award remains one mark")
	store.cycle_equipped()
	var opened=Store.new();opened.load_profile(path)
	checker.check(opened.earned==["held_line"] and opened.equipped=="held_line","A new store restores earned and explicitly worn mark")
	store.earn("Duelist");store.cycle_equipped()
	checker.check(store.equipped=="drew_danger" and store.earned==["held_line","drew_danger"],"Equipment cycles in stable acquisition-independent order")
	store.cycle_equipped();opened.load_profile(path)
	checker.check(opened.equipped=="" and opened.earned.size()==2,"Putting away is saved without losing achievements")
	var invalid=["{",'{"schema_version":2,"earned":[],"equipped":""}',
		'{"schema_version":1,"earned":["unknown"],"equipped":""}',
		'{"schema_version":1,"earned":["held_line","held_line"],"equipped":""}',
		'{"schema_version":1,"earned":[],"equipped":"held_line"}',
		'{"schema_version":1,"earned":[],"equipped":"","extra":true}'," ".repeat(4097)]
	for index in invalid.size():
		put(path,invalid[index]);store=Store.new()
		var accepted: bool=store.load_profile(path)
		store.earn("Guardian");store.cycle_equipped();store.retry_save()
		checker.check(not accepted and store.blocked and store.dirty and FileAccess.get_file_as_string(path)==invalid[index],"Invalid profile "+str(index)+" is never silently replaced")
	var file=FileAccess.open(path,FileAccess.WRITE);file.store_buffer(PackedByteArray([255,254,255]));file.close()
	store=Store.new();checker.check(not store.load_profile(path) and store.blocked,"Invalid UTF-8 is rejected")
	put(path,"{");store=Store.new();store.load_profile(path);store.earn("Guardian")
	put(path,'{"schema_version":1,"earned":["drew_danger"],"equipped":"drew_danger"}')
	checker.check(store.retry_save() and store.earned.size()==2 and store.equipped=="drew_danger","Repair merges pending award and preserves untouched restored selection")
	put(path,"{");store=Store.new();store.load_profile(path);store.earn("Guardian");store.cycle_equipped()
	put(path,'{"schema_version":1,"earned":["drew_danger"],"equipped":"drew_danger"}')
	checker.check(store.retry_save() and store.equipped=="held_line","Repair respects explicit session equipment intent")
	put(path,'{"schema_version":1,"earned":["held_line"],"equipped":"held_line"}')
	store=Store.new();store.load_profile(path);put(path,"{");store.earn("Duelist")
	checker.check(store.blocked and store.dirty and FileAccess.get_file_as_string(path)=="{","Corruption after load preserves unknown bytes and all known marks")
	DirAccess.remove_absolute(path)
	checker.check(store.retry_save() and store.earned==["held_line","drew_danger"],"Recovery after removal retains previously saved and newly earned marks")
	# A real missing parent exercises open failure; an injected rename exercises prior-byte safety.
	var missing="user://keepsake-checks/missing/marks.json"
	DirAccess.remove_absolute(missing);DirAccess.remove_absolute(missing.get_base_dir())
	store=Store.new();store.load_profile(missing);store.earn("Guardian")
	checker.check(store.dirty and store.earned==["held_line"] and not FileAccess.file_exists(missing),"Actual write failure retains session achievement and pending state")
	DirAccess.make_dir_recursive_absolute(missing.get_base_dir())
	checker.check(store.retry_save() and not store.dirty and FileAccess.file_exists(missing),"Write retry saves pending achievement after path repair")
	put(path,'{"schema_version":1,"earned":["held_line"],"equipped":""}')
	prior=FileAccess.get_file_as_bytes(path)
	var failing=RefuseReplace.new();failing.load_profile(path);failing.earn("Duelist")
	checker.check(failing.dirty and FileAccess.get_file_as_bytes(path)==prior,"Injected replacement failure preserves prior complete profile")
	failing.refuse=false
	checker.check(failing.retry_save() and not failing.dirty and failing.earned.size()==2,"Replacement retry preserves old and new achievements")
	var scene=fresh_scene(checker,"consumer")
	checker.check(scene.keepsakes.earned.is_empty(),"Actual consumer begins with no earned reward")
	Trial.key(scene,KEY_C)
	checker.check(scene.keepsakes.equipped=="" and not FileAccess.file_exists(scene.profile_path),"Equipment button cannot create a reward")
	Trial.key(scene,KEY_T)
	for exercise in 3:
		Trial.key(scene,KEY_ENTER);Trial.attempt(scene.rehearsal,true);Trial.key(scene,KEY_ENTER)
	checker.check(scene.keepsakes.earned.is_empty() and scene.game.mode=="play","Complete rehearsal grants nothing before the actual crossing")
	for i in 1100:
		scene.advance_crossing(1.0/60.0,{})
		if scene.game.mode=="lost":break
	checker.check(scene.game.mode=="lost" and scene.keepsakes.earned.is_empty(),"Normal defeat grants no keepsake")
	scene.abandon();scene.settle_crossing()
	checker.check(scene.keepsakes.earned.is_empty(),"Abandon and result calls cannot grant a keepsake")
	var outcomes: Array[Dictionary]=[]
	for role in ["Guardian","Duelist"]:
		complete(scene,role)
		checker.check(scene.game.mode=="won" and scene.keepsakes.earned.size()==(1 if role=="Guardian" else 2),role+" real full crossing grants its mark")
		outcomes.append(scene.game.snapshot())
		var before: Dictionary=scene.keepsakes.snapshot()
		scene.settle_crossing();scene.advance_crossing(0.05,{})
		checker.check(scene.keepsakes.snapshot()==before,role+" won screen cannot re-award every frame")
	Trial.key(scene,KEY_C)
	var earned_and_worn: Dictionary=scene.keepsakes.snapshot()
	checker.check(earned_and_worn.equipped=="held_line","Actual C input explicitly equips a won keepsake")
	var fresh=fresh_scene(checker,"unchanged")
	complete(fresh,"Guardian");scene.selected="Guardian";scene.begin_crossing()
	for i in 2400:
		scene.advance_crossing(1.0/60.0,Policy.command(scene.game))
		if scene.game.mode!="play":break
	checker.check(scene.game.snapshot()==fresh.game.snapshot(),"Worn appearance leaves every combat observation unchanged")
	# Crafted terminal fixture isolates eligibility from merely drawing a won overlay.
	var terminal=fresh_scene(checker,"fixture");terminal.begin_crossing();terminal.game.mode="won";terminal.game.courier.x=1000
	terminal.settle_crossing()
	checker.check(terminal.keepsakes.earned.is_empty() and terminal.reward_message.contains("at least one"),"Terminal fixture without signature response does not earn a mark")
	var pending=fresh_scene(checker,"pending")
	var parent="user://keepsake-checks/consumer-missing"
	pending.profile_path=parent+"/profile.json"
	DirAccess.remove_absolute(pending.profile_path);DirAccess.remove_absolute(parent)
	pending.keepsakes.load_profile(pending.profile_path)
	complete(pending,"Guardian")
	checker.check(pending.game.mode=="won" and pending.keepsakes.dirty and pending.footer().contains("Not saved"),"Actual won consumer retains award and explains failed save")
	pending.begin_crossing();pending.game.energy=0;pending.advance_crossing(1.0/60.0,{"dodge":true})
	checker.check(pending.footer()==pending.game.message and pending.game.message.contains("25"),"Pending save cannot hide live rejected-action feedback")
	Trial.key(pending,KEY_ESCAPE)
	checker.check(pending.footer()==pending.keepsakes.status,"Pause exposes pending save recovery without hiding live feedback")
	DirAccess.make_dir_recursive_absolute(parent);Trial.key(pending,KEY_F5)
	checker.check(not pending.keepsakes.dirty and FileAccess.file_exists(pending.profile_path),"Actual F5 input retries the consumer's pending write")
	var paused: Dictionary=pending.game.snapshot()
	Trial.key(pending,KEY_C);Trial.key(pending,KEY_F5)
	checker.check(pending.game.snapshot()==paused and pending.keepsakes.equipped=="held_line","Pause equipment and retry preserve every combat observation")
	pending.begin_crossing();Trial.key(pending,KEY_C)
	checker.check(pending.keepsakes.equipped=="held_line","Live crossing ignores equipment changes")
	var summary={"completion_outcomes":outcomes,"earned_and_worn":earned_and_worn,"no_combat_stat_change":true}
	for node in [scene,fresh,terminal,pending]:node.queue_free()
	return summary
