extends RefCounted
const Controls = preload("res://controls.gd")
const Trial = preload("res://tests/rehearsal_checks.gd")
const Store = preload("res://tests/keepsake_checks.gd")
const Errand = preload("res://errand.gd")
class RefuseReplace:
	extends "res://controls.gd"
	var refuse := true
	func replace_file(from: String,to: String) -> Error:
		return ERR_CANT_CREATE if refuse else super.replace_file(from,to)

static func scene(tree,name: String):
	DirAccess.make_dir_recursive_absolute("user://controls-checks")
	var node=load("res://arena.tscn").instantiate()
	node.controls_path="user://controls-checks/"+name+".json"
	node.profile_path="user://controls-checks/"+name+"-marks.json"
	DirAccess.remove_absolute(node.controls_path);DirAccess.remove_absolute(node.profile_path)
	tree.root.add_child(node);node.set_physics_process(false)
	return node

static func physical(code: int,pressed: bool=true) -> void:
	var event=InputEventKey.new();event.keycode=code;event.physical_keycode=code;event.pressed=pressed
	Input.parse_input_event(event);Input.flush_buffered_events()

static func choose(node,row: int,code: int) -> void:
	node.controls_row=row;Trial.key(node,KEY_ENTER);Trial.key(node,code)

static func run(checker) -> Dictionary:
	DirAccess.make_dir_recursive_absolute("user://controls-checks")
	var path="user://controls-checks/profile.json"
	DirAccess.remove_absolute(path)
	var controls=Controls.new()
	checker.check(controls.load_profile(path) and controls.keys==Controls.DEFAULTS and not FileAccess.file_exists(path),"Fresh controls preserve defaults without creating a profile")
	var draft=controls.keys.duplicate()
	checker.check(not Controls.assign(draft,"interact",KEY_K).is_empty() and draft==controls.keys,"Duplicate action key is rejected without changing draft")
	checker.check(not Controls.assign(draft,"interact",KEY_ESCAPE).is_empty() and draft==controls.keys,"Recovery/navigation key cannot be captured by gameplay")
	checker.check(Controls.assign(draft,"interact",KEY_F).is_empty() and controls.keys.interact==KEY_E,"A valid binding first changes only the draft")
	checker.check(controls.apply(draft) and controls.keys.interact==KEY_F and not controls.dirty,"Explicit apply activates and saves the chosen binding")
	var reopened=Controls.new();reopened.load_profile(path)
	checker.check(reopened.keys==draft,"Fresh control object reloads exact applied map")
	checker.check(reopened.describe("Hold E, then K; LOCKED BOLT. ENTER retries.")=="Hold F, then K; LOCKED BOLT. ENTER retries.","Prompt replacement changes key tokens without corrupting words or fixed navigation")
	var invalid=["{",'{"schema_version":2,"keys":{}}',JSON.stringify({"schema_version":1,"keys":{"interact":KEY_F}})," ".repeat(4097)]
	var duplicate=draft.duplicate();duplicate.interact=KEY_K
	invalid.append(JSON.stringify({"schema_version":1,"keys":duplicate}))
	var reserved=draft.duplicate();reserved.interact=KEY_ESCAPE
	invalid.append(JSON.stringify({"schema_version":1,"keys":reserved}))
	for index in invalid.size():
		Store.put(path,invalid[index]);controls=Controls.new()
		var accepted: bool=controls.load_profile(path)
		controls.apply(draft)
		checker.check(not accepted and controls.blocked and controls.dirty and controls.keys==draft and FileAccess.get_file_as_string(path)==invalid[index],"Invalid control profile "+str(index)+" preserves bytes while explicit session controls work")
	DirAccess.remove_absolute(path)
	checker.check(controls.save() and not controls.blocked and not controls.dirty,"Removing unavailable profile permits an explicit pending save retry")
	var prior=FileAccess.get_file_as_bytes(path)
	var failing=RefuseReplace.new();failing.load_profile(path)
	var alternate=draft.duplicate();alternate.skill=KEY_H
	checker.check(not failing.apply(alternate) and failing.keys==alternate and failing.dirty and FileAccess.get_file_as_bytes(path)==prior,"Replacement failure retains prior bytes and applied session map")
	failing.refuse=false
	checker.check(failing.save() and not failing.dirty,"Retry saves the already applied map after replacement failure")
	var parent="user://controls-checks/missing"
	DirAccess.remove_absolute(parent+"/map.json");DirAccess.remove_absolute(parent)
	controls=Controls.new();controls.load_profile(parent+"/map.json")
	checker.check(not controls.apply(draft) and controls.dirty and controls.keys==draft,"Actual missing-parent write failure retains applied controls")
	DirAccess.make_dir_recursive_absolute(parent)
	checker.check(controls.save() and not controls.dirty,"Actual path repair permits save retry")
	var node=scene(checker,"ui")
	Trial.key(node,KEY_F1)
	var navigation=InputEventKey.new();navigation.pressed=true;navigation.keycode=KEY_DOWN;navigation.physical_keycode=KEY_KP_2
	node._unhandled_key_input(navigation)
	checker.check(node.controls_row==1,"Panel navigation follows logical arrow identity when physical code differs")
	Trial.key(node,KEY_ESCAPE)
	Trial.key(node,KEY_ENTER);node.game.note("Keep this feedback.")
	var combat: Dictionary=node.game.snapshot()
	Trial.key(node,KEY_F1)
	checker.check(node.controls_open and node.game.mode=="paused","F1 pauses an actual live crossing before settings")
	var paused: Dictionary=node.game.snapshot()
	choose(node,11,KEY_F);node._physics_process(0.05)
	checker.check(node.game.snapshot()==paused and node.bindings.keys.interact==KEY_E and node.controls_draft.interact==KEY_F,"Editing a draft freezes actual gameplay and leaves active controls unchanged")
	Trial.key(node,KEY_ESCAPE)
	checker.check(not node.controls_open and node.game.mode=="paused" and node.bindings.keys.interact==KEY_E,"Closing an unapplied draft discards it without resuming")
	Trial.key(node,KEY_F1);choose(node,11,KEY_K)
	checker.check(node.controls_listening and node.controls_message.contains("Already used"),"Capture conflict remains recoverable and identifies the owning action")
	Trial.key(node,KEY_ESCAPE)
	checker.check(node.controls_open and not node.controls_listening,"Escape cancels capture before closing the panel")
	choose(node,11,KEY_F);choose(node,9,KEY_H);choose(node,8,KEY_G);choose(node,10,KEY_B);choose(node,2,KEY_I)
	Trial.key(node,KEY_S);Trial.key(node,KEY_ESCAPE)
	checker.check(node.bindings.keys.interact==KEY_F and node.bindings.keys.skill==KEY_H and node.game.snapshot()==paused,"Applying and closing changes controls without changing paused combat")
	Trial.key(node,KEY_ENTER)
	node.game.phase="bolt";node.game.target=node.game.courier;node.game.player=Vector2(550,390)
	physical(KEY_K);node._physics_process(1.0/60.0);physical(KEY_K,false)
	checker.check(not node.game.guard,"Old guard key stops activating after rebind")
	physical(KEY_H);node._physics_process(1.0/60.0)
	checker.check(node.game.guard,"Remapped held ability reaches Guardian's actual guard")
	physical(KEY_H,false);node._physics_process(1.0/60.0)
	node.selected="Duelist";node.begin_crossing();node.game.phase="bolt";node.game.target=node.game.courier
	Trial.key(node,KEY_H);node._physics_process(1.0/60.0)
	checker.check(node.game.counters.redirects==1,"Same remapped discrete ability reaches Duelist's actual feint")
	node.begin_crossing();var start: Vector2=node.game.player
	physical(KEY_W);node._physics_process(1.0/60.0);physical(KEY_W,false)
	checker.check(node.game.player==start,"Old movement key is inactive after rebind")
	physical(KEY_I);node._physics_process(1.0/60.0);physical(KEY_I,false)
	checker.check(node.game.player.y<start.y,"Remapped held movement reaches the actual scene")
	node.game.courier.x=400;node.game.player=Errand.CASE
	physical(KEY_E);node._physics_process(0.05);physical(KEY_E,false)
	checker.check(node.errand.progress==0,"Old interaction key cannot acquire optional medicine after rebind")
	physical(KEY_F)
	for i in 16:node._physics_process(0.05)
	physical(KEY_F,false)
	checker.check(node.errand.state=="carried","Remapped held interaction recovers the real medicine case")
	# Held input before opening must be released, never leak through resume/apply.
	node.begin_crossing();physical(KEY_I);Trial.key(node,KEY_F1);Trial.key(node,KEY_ESCAPE);Trial.key(node,KEY_ENTER)
	start=node.game.player;node._physics_process(0.05)
	checker.check(node.game.player==start,"Input held across settings is quarantined after explicit resume")
	physical(KEY_I,false);physical(KEY_I);node._physics_process(0.05);physical(KEY_I,false)
	checker.check(node.game.player.y<start.y,"Releasing and pressing again restores deliberate input")
	Trial.key(node,KEY_ESCAPE);Trial.key(node,KEY_R);Trial.key(node,KEY_T);Trial.key(node,KEY_ENTER);Trial.key(node,KEY_F1)
	var rehearsal: Dictionary=node.rehearsal.snapshot()
	node._physics_process(0.05)
	checker.check(node.rehearsal.paused and node.rehearsal.snapshot()==rehearsal,"Controls freeze a live rehearsal without changing its result")
	Trial.key(node,KEY_ESCAPE)
	checker.check(node.rehearsal.paused and not node.controls_open,"Closing settings leaves rehearsal explicitly paused")
	Trial.key(node,KEY_F1);Trial.key(node,KEY_DELETE);Trial.key(node,KEY_ESCAPE)
	checker.check(node.bindings.keys.interact==KEY_F,"Restore defaults is also a cancellable draft")
	Trial.key(node,KEY_F1);Trial.key(node,KEY_DELETE);Trial.key(node,KEY_S);Trial.key(node,KEY_ESCAPE)
	checker.check(node.bindings.keys==Controls.DEFAULTS and not node.bindings.dirty,"Explicitly applied restore recovers the complete default map")
	var report={"restored_profile":node.bindings.snapshot(),"rebound_interaction":"F","rebound_ability":"H","model_rules_unchanged":true}
	node.queue_free()
	return report
