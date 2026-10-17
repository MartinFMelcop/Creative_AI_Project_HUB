extends SceneTree
const Route = preload("res://tests/errand_policy.gd")
var scene
var started: int
var ticks := 0
var presented := 0
var output: String

func _initialize() -> void:
	call_deferred("run")

func presented_frame() -> void:
	presented += 1

func elapsed() -> float:
	return (Time.get_ticks_usec()-started)/1000000.0

func report() -> Dictionary:
	return {"baseline":"8c51b2f1d9d315a5dc0ef991a07968799da9f124","wall_seconds":elapsed(),"ticks":ticks,"presented_frames":presented,"engine_fps":Engine.get_frames_per_second(),"physics_delta":1.0/60.0,"snapshot":scene.game.snapshot(),"errand":scene.errand.snapshot(),"limitation":"Synthetic scene policy on one dummy-Xorg/software-rendered environment, not human gameplay or general performance validation."}

func save_report() -> void:
	var f=FileAccess.open(output,FileAccess.WRITE)
	if f: f.store_string(JSON.stringify(report(),"\t"));f.close()

func run() -> void:
	var args=OS.get_cmdline_user_args()
	if args.size()!=1:quit(2);return
	output=args[0]
	scene=load("res://arena.tscn").instantiate()
	root.add_child(scene)
	scene.set_physics_process(false)
	scene.selected="Guardian"
	scene.begin_crossing()
	RenderingServer.frame_post_draw.connect(presented_frame)
	started=Time.get_ticks_usec()
	print("BEGIN realtime final recovery Guardian policy")
	while scene.game.mode=="play" and ticks<2400:
		await physics_frame
		scene.advance_crossing(1.0/60.0,Route.command(scene))
		ticks+=1
		scene.queue_redraw()
		if ticks%120==0:
			save_report()
			print("PROGRESS ",JSON.stringify(report()))
	save_report()
	print("RESULT ",JSON.stringify(report()))
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(output.get_basename()+".png")
	quit(0 if scene.game.mode=="won" else 1)
