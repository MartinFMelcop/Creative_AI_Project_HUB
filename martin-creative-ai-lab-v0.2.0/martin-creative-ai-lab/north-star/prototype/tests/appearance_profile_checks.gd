extends SceneTree
## Execute migration and failure contracts against actual files and the real scene.
const Store=preload("res://keepsakes.gd")
const Look=preload("res://character_look.gd")
const Arena=preload("res://arena.gd")
const Helpers=preload("res://tests/keepsake_checks.gd")
const CUSTOM:={"skin":2,"hair":2,"dye":1}
const OTHER:={"skin":3,"hair":1,"dye":3}
var passed:=0
var failed:=0
var labels:Array[String]=[]
func check(value: bool,label: String) -> void:
	labels.append(label)
	if value:passed+=1
	else:failed+=1;push_error(label)
func key(scene,code: int) -> void:
	var event=InputEventKey.new();event.keycode=code;event.physical_keycode=code;event.pressed=true;scene._unhandled_key_input(event)
func data(marks: Array=[],worn: String="",look: Dictionary={}) -> Dictionary:
	var result={"schema_version":1,"earned":marks,"equipped":worn}
	if not look.is_empty():result.schema_version=2;result.look=look
	return result
func put(path: String,value: Variant) -> void:Helpers.put(path,JSON.stringify(value))
func fresh(name: String):
	var scene=Arena.new();scene.profile_path="user://appearance-profile-checks/"+name+".json"
	DirAccess.remove_absolute(scene.profile_path);root.add_child(scene);scene.set_physics_process(false);return scene
func _initialize() -> void:call_deferred("run")
func run() -> void:
	DirAccess.make_dir_recursive_absolute("user://appearance-profile-checks")
	var path="user://appearance-profile-checks/store.json"
	put(path,data(["held_line"],"held_line"));var prior=FileAccess.get_file_as_bytes(path)
	var store=Store.new();check(store.load_profile(path) and store.look.is_empty(),"Legacy profile loads with no invented appearance")
	check(FileAccess.get_file_as_bytes(path)==prior,"Loading legacy data does not migrate or rewrite bytes")
	store.earn("Duelist")
	check(JSON.parse_string(FileAccess.get_file_as_string(path)).schema_version==1,"Mark-only updates keep the legacy schema")
	check(store.set_look(CUSTOM),"Explicit appearance apply migrates and saves")
	var saved=JSON.parse_string(FileAccess.get_file_as_string(path))
	# Compare parsed JSON to parsed JSON: dictionary equality distinguishes numeric Variants.
	check(saved==JSON.parse_string(JSON.stringify(data(["held_line","drew_danger"],"held_line",CUSTOM))),"Migration preserves all earned marks and worn selection")
	var loaded=Store.new();check(loaded.load_profile(path) and loaded.look==CUSTOM,"A new reader loads the saved appearance")
	var copy=loaded.snapshot();copy.look.skin=0
	check(loaded.look==CUSTOM,"Snapshot does not alias stored appearance")
	DirAccess.remove_absolute(path);store=Store.new();store.load_profile(path);store.set_look(CUSTOM)
	check(store.earned.is_empty() and store.equipped=="" and FileAccess.file_exists(path),"Saving a free look neither requires nor awards a mark")
	store.earn("Guardian");store.cycle_equipped();loaded.load_profile(path)
	check(loaded.look==CUSTOM and loaded.equipped=="held_line","Later earning and wearing preserve the saved free look")
	var invalid=[data([],"",{"skin":4,"hair":0,"dye":0}),data([],"",{"skin":0,"hair":3,"dye":0}),data([],"",{"skin":0,"hair":0,"dye":-1}),
		data([],"",{"skin":1.5,"hair":0,"dye":0}),data([],"",{"skin":true,"hair":0,"dye":0}),data([],"",{"skin":"1","hair":0,"dye":0}),
		data([],"",{"skin":0,"hair":0}),data([],"",{"skin":0,"hair":0,"dye":0,"gear":"riveted"}),{"schema_version":3,"earned":[],"equipped":"","look":CUSTOM},
		{"schema_version":2,"earned":[],"equipped":""},data([],"",CUSTOM)]
	invalid[-1].extra="unknown"
	for i in invalid.size():
		put(path,invalid[i]);prior=FileAccess.get_file_as_bytes(path);store=Store.new()
		check(not store.load_profile(path) and store.blocked,"Malformed/future appearance profile rejected: "+str(i))
		store.set_look(CUSTOM);store.earn("Guardian");store.retry_save()
		check(FileAccess.get_file_as_bytes(path)==prior and store.dirty and store.look==CUSTOM,"Unknown bytes survive pending look and award: "+str(i))
	put(path,{"schema_version":2.0,"earned":[],"equipped":"","look":{"skin":2.0,"hair":2.0,"dye":1.0}})
	store=Store.new();check(store.load_profile(path) and store.look==CUSTOM and typeof(store.look.skin)==TYPE_INT,"Whole JSON numbers normalize to stable palette IDs")
	Helpers.put(path,"{");store=Store.new();store.load_profile(path);store.set_look(CUSTOM);store.earn("Guardian")
	put(path,data(["drew_danger"],"drew_danger",OTHER));check(store.retry_save(),"A valid restored profile unblocks the queued appearance")
	check(store.look==CUSTOM and store.earned==["held_line","drew_danger"] and store.equipped=="drew_danger","Repair preserves explicit look intent, merges marks and accepts untouched restored wear")
	put(path,data(["held_line"],"held_line",CUSTOM));store=Store.new();store.load_profile(path);Helpers.put(path,"{");store.earn("Duelist")
	put(path,data(["drew_danger"],"drew_danger",OTHER));store.retry_save()
	check(store.look==OTHER and store.earned.size()==2,"Untouched appearance accepts an explicit restored v2 choice")
	# A missing appearance in a legacy repair must not erase a known saved look.
	store=Store.new();put(path,data(["held_line"],"held_line",CUSTOM));store.load_profile(path)
	Helpers.put(path,"{");store.earn("Duelist");put(path,data());store.retry_save()
	check(store.look==CUSTOM and store.earned.size()==2,"Legacy repair retains previously known appearance and all marks")
	Helpers.put(path,"{");store.set_look(OTHER);DirAccess.remove_absolute(path);store.retry_save()
	check(store.look==OTHER and not store.dirty and JSON.parse_string(FileAccess.get_file_as_string(path)).look==JSON.parse_string(JSON.stringify(OTHER)),"Removal recovery writes pending appearance without requiring a new award")
	var missing="user://appearance-profile-checks/missing/profile.json"
	DirAccess.remove_absolute(missing);DirAccess.remove_absolute(missing.get_base_dir())
	store=Store.new();store.load_profile(missing);check(not store.set_look(CUSTOM) and store.dirty and store.look==CUSTOM,"Actual missing-parent write failure retains the applied look")
	DirAccess.make_dir_recursive_absolute(missing.get_base_dir());check(store.retry_save() and not store.dirty,"Path repair saves the pending look")
	put(path,data(["held_line"],"held_line",OTHER));prior=FileAccess.get_file_as_bytes(path)
	var refusing=Helpers.RefuseReplace.new();refusing.load_profile(path);refusing.set_look(CUSTOM)
	check(refusing.dirty and FileAccess.get_file_as_bytes(path)==prior,"Replacement failure preserves prior complete mark and look bytes")
	refusing.refuse=false;check(refusing.retry_save() and not refusing.dirty and refusing.look==CUSTOM,"Replacement retry saves intended appearance")
	var scene=fresh("consumer");var before=scene.game.snapshot()
	key(scene,KEY_F3);key(scene,KEY_RIGHT);key(scene,KEY_DELETE);key(scene,KEY_ESCAPE)
	check(not FileAccess.file_exists(scene.profile_path) and scene.character_look.applied==Look.DEFAULTS,"Cancelled preview/defaults never create or save a profile")
	key(scene,KEY_F3);key(scene,KEY_RIGHT);key(scene,KEY_ENTER)
	check(scene.character_look.applied.skin==1 and scene.keepsakes.look.skin==1 and not scene.keepsakes.dirty,"Actual editor apply reaches persistent storage")
	check(scene.game.snapshot()==before and scene.keepsakes.earned.is_empty(),"Appearance apply grants no gameplay progress or reward")
	prior=FileAccess.get_file_as_bytes(scene.profile_path)
	key(scene,KEY_F3);key(scene,KEY_RIGHT);key(scene,KEY_2);key(scene,KEY_TAB);key(scene,KEY_ESCAPE)
	check(FileAccess.get_file_as_bytes(scene.profile_path)==prior,"Preview approach/fitting and cancelled edits leave saved bytes unchanged")
	var reopened=Arena.new();reopened.profile_path=scene.profile_path;root.add_child(reopened);reopened.set_physics_process(false)
	check(reopened.character_look.applied==scene.character_look.applied and reopened.game.mode=="title","New actual scene loads appearance without restoring a game session")
	Helpers.put(scene.profile_path,"{");key(scene,KEY_F3);key(scene,KEY_RIGHT);key(scene,KEY_ENTER)
	check(scene.keepsakes.blocked and scene.keepsakes.dirty and scene.character_look.applied.skin==2,"Unavailable profile keeps the actual chosen session look playable")
	scene.begin_crossing();scene.game.energy=0;scene.advance_crossing(1.0/60,{"dodge":true})
	check(scene.footer()==scene.game.message and scene.game.message.contains("25"),"Pending look save cannot displace live rejected-action feedback")
	key(scene,KEY_ESCAPE);check(scene.footer()==scene.keepsakes.status,"Pause exposes pending appearance recovery")
	scene.abandon();key(scene,KEY_F3);key(scene,KEY_RIGHT);var draft=scene.character_look.draft.duplicate()
	put(scene.profile_path,data(["drew_danger"],"drew_danger",OTHER));key(scene,KEY_F5)
	check(not scene.keepsakes.blocked and not scene.keepsakes.dirty and scene.character_look.applied.skin==2,"Actual F5 repairs the pending applied appearance")
	check(scene.character_look.draft==draft and scene.keepsakes.look.skin==2,"Retry does not apply or discard the separate current draft")
	key(scene,KEY_ESCAPE);key(scene,KEY_F3);key(scene,KEY_DELETE);key(scene,KEY_ENTER)
	check(scene.keepsakes.look==Look.DEFAULTS and scene.keepsakes.equipped=="drew_danger","Explicit defaults save appearance without erasing restored marks")
	var report={"checks":{"passed":passed,"failed":failed},"labels":labels,"final_profile":scene.keepsakes.snapshot(),"consumer_hashes":{}}
	for name in ["keepsakes.gd","character_look.gd","arena.gd","tests/appearance_profile_checks.gd"]:report.consumer_hashes[name]=FileAccess.get_sha256("res://"+name)
	var args=OS.get_cmdline_user_args()
	if args.size()==1:
		var file=FileAccess.open(args[0],FileAccess.WRITE);file.store_string(JSON.stringify(report,"  ")+"\n");file.close()
	print("APPEARANCE_PROFILE_CHECKS ",passed," passed / ",failed," failed")
	for node in [scene,reopened]:node.free()
	await create_timer(.8).timeout;quit(1 if failed else 0)
