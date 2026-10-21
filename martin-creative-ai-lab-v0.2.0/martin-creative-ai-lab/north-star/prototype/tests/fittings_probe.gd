extends SceneTree
const Arena=preload("res://arena.gd")
const Driver=preload("res://tests/fittings_driver.gd")
func _initialize() -> void:call_deferred("run")
func run() -> void:
	var args:=OS.get_cmdline_user_args()
	if args.size()!=1:quit(2);return
	var scene=Arena.new();root.add_child(scene);scene.set_physics_process(false)
	var report: Dictionary=Driver.new().run(scene,args[0])
	scene.sound.silence();scene.queue_free()
	await create_timer(.2).timeout
	quit(0 if report.get("valid",false) and report.get("failures",["missing"]).is_empty() else 1)
