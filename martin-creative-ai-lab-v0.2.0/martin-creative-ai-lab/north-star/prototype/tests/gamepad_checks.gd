extends SceneTree
func _initialize() -> void:call_deferred("run")
func run() -> void:
	var scene=load("res://arena.tscn").instantiate();root.add_child(scene)
	await process_frame
	var args=OS.get_cmdline_user_args()
	if args.size()!=1:quit(2);return
	var driver=load("res://tests/gamepad_driver.gd").new()
	var report=driver.run(scene,args[0])
	scene.free()
	quit(0 if report.checks.failed==0 else 1)
