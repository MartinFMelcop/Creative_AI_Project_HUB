extends SceneTree
## Each invocation is a new engine process consuming the same local profile.
const Checks = preload("res://tests/keepsake_checks.gd")
const Trial = preload("res://tests/rehearsal_checks.gd")

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var args=OS.get_cmdline_user_args()
	if args.size()!=3 or args[0] not in ["earn","read","remove"]: quit(2);return
	var scene=load("res://arena.tscn").instantiate()
	scene.profile_path=args[1]
	root.add_child(scene)
	scene.set_physics_process(false)
	var outcomes: Array[Dictionary]=[]
	if args[0]=="earn":
		for role in ["Guardian","Duelist"]:
			Checks.complete(scene,role)
			if scene.game.mode!="won": quit(1);return
			outcomes.append(scene.game.snapshot())
		Trial.key(scene,KEY_C);Trial.key(scene,KEY_C)
	elif args[0]=="remove": Trial.key(scene,KEY_C)
	var report={"profile":scene.keepsakes.snapshot(),"game":scene.game.snapshot(),"outcomes":outcomes}
	var file=FileAccess.open(args[2],FileAccess.WRITE)
	if file==null:quit(1);return
	file.store_string(JSON.stringify(report,"  ")+"\n");file.close()
	quit(0)
