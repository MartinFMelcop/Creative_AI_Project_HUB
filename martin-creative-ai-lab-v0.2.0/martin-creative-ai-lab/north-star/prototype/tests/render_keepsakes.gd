extends SceneTree
## Controlled actual-scene presentation, not real-time or independent player evidence.
const Checks = preload("res://tests/keepsake_checks.gd")
const Trial = preload("res://tests/rehearsal_checks.gd")
var scene
var folder: String

func _initialize() -> void:
	call_deferred("run")

func shot(name: String) -> void:
	scene.queue_redraw()
	await process_frame
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(folder+"/"+name+".png")

func run() -> void:
	var args=OS.get_cmdline_user_args()
	if args.size()!=1 or OS.get_environment("CROSSING_PROFILE").is_empty():quit(2);return
	folder=args[0]
	scene=load("res://arena.tscn").instantiate()
	root.add_child(scene);scene.set_physics_process(false)
	await shot("fresh-selection")
	Checks.complete(scene,"Guardian")
	if scene.game.mode!="won" or scene.keepsakes.equipped!="":quit(1);return
	await shot("guardian-earned")
	Trial.key(scene,KEY_C);scene.begin_crossing()
	await shot("guardian-worn")
	scene.abandon();Checks.complete(scene,"Duelist")
	if scene.keepsakes.earned.size()!=2:quit(1);return
	await shot("duelist-earned")
	Trial.key(scene,KEY_C);scene.begin_crossing()
	await shot("duelist-worn")
	scene.abandon();Trial.key(scene,KEY_C)
	await shot("put-away")
	# Leave an explicitly selected earned mark for the separately executed keyboard journey.
	Trial.key(scene,KEY_C);Trial.key(scene,KEY_C)
	print("Rendered earned, explicitly worn and put-away keepsakes through the actual consumer.")
	quit(0)
