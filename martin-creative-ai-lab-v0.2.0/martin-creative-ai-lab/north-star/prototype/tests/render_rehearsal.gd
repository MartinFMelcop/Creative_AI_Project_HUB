extends SceneTree
## Controlled presentation diagnostic, not independent player behavior or frame timing.
const Trial = preload("res://tests/rehearsal_checks.gd")
const Policy = preload("res://tests/policy.gd")
var scene
var folder: String
func _initialize() -> void:
	call_deferred("run")
func shot(name: String) -> void:
	scene.queue_redraw()
	await process_frame
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(folder+"/"+name+".png")
func ticks(count: int, command: Dictionary) -> void:
	for i in count: scene.rehearsal.step(1.0/60.0,command)
func run() -> void:
	var args=OS.get_cmdline_user_args()
	if args.size()!=1:quit(2);return
	folder=args[0]
	scene=load("res://arena.tscn").instantiate()
	root.add_child(scene)
	await process_frame
	scene.set_physics_process(false)
	await shot("selection")
	Trial.key(scene,KEY_T);Trial.key(scene,KEY_ENTER)
	ticks(65,{"skill":true,"aim":Vector2.LEFT})
	await shot("guardian-facing-review")
	if scene.rehearsal.passed:quit(1);return
	Trial.key(scene,KEY_R);Trial.key(scene,KEY_2);Trial.key(scene,KEY_T);Trial.key(scene,KEY_ENTER)
	ticks(1,{"skill_pressed":true})
	await shot("duelist-drawn-line")
	ticks(64,{"move":Vector2.UP})
	await shot("duelist-safe-review")
	if not scene.rehearsal.passed:quit(1);return
	Trial.key(scene,KEY_ENTER);Trial.key(scene,KEY_ENTER)
	ticks(65,{})
	await shot("pulse-impact-review")
	Trial.key(scene,KEY_ENTER);Trial.key(scene,KEY_ENTER)
	ticks(65,{"move":Vector2.UP})
	Trial.key(scene,KEY_ENTER);Trial.key(scene,KEY_ENTER)
	ticks(20,{"move":Vector2.RIGHT})
	await shot("counter-range")
	ticks(1,{"strike":true})
	await shot("counter-verified")
	if not scene.rehearsal.passed:quit(1);return
	Trial.key(scene,KEY_ENTER)
	for i in 1100:
		scene.game.step(1.0/60.0,{})
		if scene.game.mode=="lost":break
	await shot("crossing-loss-review")
	if scene.game.mode!="lost":quit(1);return
	scene.game.reset("Guardian")
	for i in 2200:
		scene.game.step(1.0/60.0,Policy.command(scene.game))
		if scene.game.mode=="won":break
	await shot("crossing-win-review")
	if scene.game.mode!="won":quit(1);return
	print("Rendered actual scene states after controlled rehearsal responses and crossing loss; no human learning or real-time performance claim.")
	quit(0)
