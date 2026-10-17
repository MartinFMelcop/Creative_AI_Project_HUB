extends SceneTree
const Checks = preload("res://tests/policy.gd")
var scene
func _initialize() -> void:
	call_deferred("run")
func shot(path: String) -> void:
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(path)
func run() -> void:
	var args=OS.get_cmdline_user_args()
	if args.size()!=1:quit(2);return
	scene=load("res://arena.tscn").instantiate()
	root.add_child(scene)
	await process_frame
	scene.set_physics_process(false)
	for role in ["Guardian","Duelist"]:
		scene.game.reset(role)
		for i in 220:
			await physics_frame
			for substep in 10:
				if scene.game.mode=="play":scene.game.step(1.0/60.0,Checks.command(scene.game))
			scene.queue_redraw()
			if i==14: await shot(args[0]+"/"+role.to_lower()+"-threat.png")
			if scene.game.mode!="play":break
		await shot(args[0]+"/"+role.to_lower()+"-complete.png")
		if scene.game.mode!="won":quit(1);return
	print("Rendered accelerated complete scene policies; no real-time or human playtest.")
	quit(0)
