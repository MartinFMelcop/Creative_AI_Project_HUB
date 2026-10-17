extends SceneTree
## Controlled presentation diagnostics. One-frame captures are not human validation.
const Route = preload("res://tests/errand_policy.gd")
const Policy = preload("res://tests/policy.gd")
var scene
var folder: String
var frames: Array[Dictionary]=[]

func _initialize() -> void:
	call_deferred("run")

func shot(name: String) -> void:
	scene.queue_redraw()
	await process_frame
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(folder+"/"+name+".png")
	frames.append({"frame":name,"combat":scene.game.snapshot(),"errand":scene.errand.snapshot(),"player":[scene.game.player.x,scene.game.player.y],"courier":[scene.game.courier.x,scene.game.courier.y]})

func run() -> void:
	var args=OS.get_cmdline_user_args()
	if args.size()!=1 or OS.get_environment("CROSSING_PROFILE").is_empty():quit(2);return
	folder=args[0]
	scene=load("res://arena.tscn").instantiate();root.add_child(scene);scene.set_physics_process(false)
	await shot("selection")
	for role in ["Guardian","Duelist"]:
		scene.selected=role;scene.begin_crossing()
		var seen: Array[String]=[]
		for i in 2400:
			scene.advance_crossing(1.0/60.0,Route.command(scene))
			var e=scene.errand
			var frame := ""
			if role=="Guardian":
				if e.state=="available" and "dropped" not in seen: frame="dropped"
				elif e.channel and e.progress>0.35 and e.state=="available" and "recovering" not in seen:frame="recovering"
				elif e.channel and e.progress>0.25 and e.state=="carried" and "handoff" not in seen:frame="handoff"
			if not frame.is_empty():seen.append(frame);await shot(frame)
			if scene.game.mode!="play":break
		if scene.game.mode!="won" or scene.errand.state!="delivered":quit(1);return
		await shot(role.to_lower()+"-delivered")
	scene.selected="Guardian";scene.begin_crossing()
	for i in 2400:
		scene.advance_crossing(1.0/60.0,Policy.command(scene.game))
		if scene.game.mode!="play":break
	await shot("direct-escort")
	var file=FileAccess.open(folder+"/render.json",FileAccess.WRITE)
	file.store_string(JSON.stringify({"kind":"controlled_scene_presentation","frames":frames},"  ")+"\n");file.close()
	print("Rendered actual drop, commitment, handoff and both delivered/direct outcomes.")
	quit(0)
