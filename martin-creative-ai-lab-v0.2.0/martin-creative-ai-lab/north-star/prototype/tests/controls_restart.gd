extends SceneTree
## Separate process invocations exercise actual scene apply/reload/restore behavior.
const Checks = preload("res://tests/controls_checks.gd")
const Trial = preload("res://tests/rehearsal_checks.gd")

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var args=OS.get_cmdline_user_args()
	if args.size()!=3 or args[0] not in ["apply","read","restore"]:quit(2);return
	var scene=load("res://arena.tscn").instantiate()
	scene.controls_path=args[1]
	root.add_child(scene);scene.set_physics_process(false)
	if args[0] in ["apply","restore"]:
		Trial.key(scene,KEY_F1)
		if args[0]=="apply":
			for change in [[8,KEY_G],[9,KEY_H],[10,KEY_B],[11,KEY_F],[2,KEY_I]]:Checks.choose(scene,change[0],change[1])
		else:Trial.key(scene,KEY_DELETE)
		Trial.key(scene,KEY_S);Trial.key(scene,KEY_ESCAPE)
	var file=FileAccess.open(args[2],FileAccess.WRITE)
	if file==null:quit(1);return
	file.store_string(JSON.stringify({"profile":scene.bindings.snapshot(),"game":scene.game.snapshot(),"hint":scene.bindings.describe("WASD move / K ability / J blade / E interact / SPACE step")},"  ")+"\n");file.close()
	quit(0)
