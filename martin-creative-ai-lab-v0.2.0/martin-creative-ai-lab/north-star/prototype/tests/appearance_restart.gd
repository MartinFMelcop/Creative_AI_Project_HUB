extends SceneTree
## Each invocation loads the real scene in a new engine process.
const Policy=preload("res://tests/policy.gd")
const GatePolicy=preload("res://tests/gate_policy.gd")
func _initialize() -> void:call_deferred("run")
func key(scene,code: int) -> void:
	var event=InputEventKey.new();event.pressed=true;event.keycode=code;event.physical_keycode=code;scene._unhandled_key_input(event)
func run() -> void:
	var args=OS.get_cmdline_user_args()
	if args.size()!=3 or args[0] not in ["apply","read","cancel","defaults","earn","journey"]:quit(2);return
	var scene=load("res://arena.tscn").instantiate();scene.profile_path=args[1];root.add_child(scene);scene.set_physics_process(false)
	var prior:PackedByteArray=FileAccess.get_file_as_bytes(args[1]) if FileAccess.file_exists(args[1]) else PackedByteArray()
	var observations={}
	if args[0]=="apply":
		for code in [KEY_F3,KEY_RIGHT,KEY_RIGHT,KEY_DOWN,KEY_RIGHT,KEY_RIGHT,KEY_DOWN,KEY_RIGHT,KEY_ENTER]:key(scene,code)
	elif args[0]=="cancel":
		for code in [KEY_F3,KEY_RIGHT,KEY_ESCAPE]:key(scene,code)
	elif args[0]=="defaults":
		for code in [KEY_F3,KEY_DELETE,KEY_ENTER]:key(scene,code)
	elif args[0] in ["earn","journey"]:
		scene.selected="Guardian" if args[0]=="earn" else "Duelist";scene.begin_crossing()
		for i in 4200:
			if scene.game.mode!="play":break
			scene.advance_crossing(1.0/60,Policy.command(scene.game))
		if scene.game.mode!="won":push_error("Appearance restart did not complete actual escort");quit(1);return
		observations.crossing=scene.game.snapshot();observations.crossing_look=scene.character_look.applied.duplicate()
		if args[0]=="journey":
			if not scene.begin_return_gate():push_error("No actual arrival for return");quit(1);return
			for i in 6000:
				if scene.game.mode!="play":break
				scene.advance_crossing(1.0/60,GatePolicy.command(scene.return_gate,"work"))
			if scene.game.mode!="won":push_error("Appearance restart did not complete actual return");quit(1);return
			observations.return_gate=scene.return_gate.snapshot();observations.return_look=scene.character_look.applied.duplicate()
	var bytes=FileAccess.get_file_as_bytes(args[1])
	var result={"operation":args[0],"look":scene.character_look.applied.duplicate(),"profile":scene.keepsakes.snapshot(),"stored":JSON.parse_string(bytes.get_string_from_utf8()),"unchanged_bytes":prior==bytes,"mode":scene.game.mode,"tick":scene.game.snapshot().tick,"observations":observations}
	var file=FileAccess.open(args[2],FileAccess.WRITE);file.store_string(JSON.stringify(result,"  ")+"\n");file.close()
	scene.sound.silence();scene.free();await create_timer(.2).timeout;quit(0)
