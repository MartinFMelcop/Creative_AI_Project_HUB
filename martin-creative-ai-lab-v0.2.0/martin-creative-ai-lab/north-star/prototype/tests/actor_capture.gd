extends SceneTree
## Controlled real-consumer action sequence. No participant or real-time claim.
const Policy=preload("res://tests/policy.gd")
const Combat=preload("res://combat.gd")
var scene
var folder := ""
var observations := {}
func _initialize():call_deferred("run")
func capture(name: String):
	scene.queue_redraw()
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(folder.path_join(name+".png"))
	var actors=scene.get("actors")
	observations[name]={"game":scene.game.snapshot(),"impact":scene.game.last_impact.duplicate(),"guard_state":scene.game.guard_state(),"opening":scene.game.opening,"actors":actors.snapshot(scene.game) if actors!=null else {"baseline_static_shapes":true}}
func advance(command: Dictionary, count: int=1):
	for i in count:scene.advance_crossing(1.0/60.0,command);scene.sync_sound()
func start(role: String,style: String="Steady"):
	scene.selected=role;scene.guardian_style=style;scene.begin_crossing()
func run():
	var args=OS.get_cmdline_user_args()
	if args.size()!=1:quit(2);return
	folder=args[0];DirAccess.make_dir_recursive_absolute(folder)
	scene=load("res://arena.tscn").instantiate();root.add_child(scene);scene.set_physics_process(false)
	await capture("selection")
	start("Guardian");await capture("guardian-idle")
	advance({"move":Vector2.RIGHT},8);await capture("guardian-walk")
	# Actual line interception with unchanged 60ms startup and frontal facing.
	scene.game.phase="bolt";scene.game.target=scene.game.courier;scene.game.clock=.89
	advance({"skill":true,"aim":Vector2.RIGHT});await capture("guardian-startup")
	advance({"skill":true,"aim":Vector2.RIGHT},4);await capture("guardian-live")
	advance({"skill":true,"aim":Vector2.RIGHT},3);await capture("guardian-block")
	# Release, approach and use the real opening; no pose is assigned directly.
	scene.game.player=Combat.ENEMY+Vector2(-100,0)
	advance({"strike":true});await capture("counter-00")
	for i in 12:
		advance({});await capture("counter-%02d"%(i+1))
	advance({},20);advance({"strike":true});await capture("armor-strike")
	start("Guardian","Riposte");advance({"skill":true},26);await capture("guardian-stale")
	scene.game.phase="bolt";scene.game.target=scene.game.courier;scene.game.clock=.99
	advance({"skill":true});await capture("guardian-hurt")
	start("Duelist");await capture("duelist-idle")
	advance({"move":Vector2.UP},8);await capture("duelist-walk")
	scene.game.phase="bolt";scene.game.target=scene.game.courier
	advance({"skill_pressed":true});await capture("draw-00")
	for i in 12:
		advance({"move":Vector2.UP});await capture("draw-%02d"%(i+1))
	advance({"move":Vector2.UP,"dodge":true});await capture("duelist-step")
	# Courier first-contact control, with the player clearly outside the beam.
	start("Guardian");scene.game.player.y=600
	scene.game.phase="bolt";scene.game.target=scene.game.courier;scene.game.clock=.99
	advance({});await capture("courier-hit")
	start("Guardian");scene.game.player=Vector2(900,390);scene.game.courier=Vector2(960,390);scene.game.target=scene.game.courier;scene.game.phase="bolt";scene.game.clock=.89
	advance({"skill":true,"aim":Vector2.LEFT},8);await capture("guardian-west-block")
	scene.keepsakes.earned.clear();scene.keepsakes.earned.append("held_line");scene.keepsakes.equipped="held_line";await capture("worn-mark")
	scene.keepsakes.equipped="";scene.keepsakes.earned.clear()
	start("Duelist")
	for i in 2400:
		advance(Policy.command(scene.game))
		if scene.game.get("enemy_focus")==0:break
	await capture("sentinel-disabled")
	var file=FileAccess.open(folder.path_join("presentation.json"),FileAccess.WRITE)
	file.store_string(JSON.stringify({"scope":"Prepared actual scene with controlled model ticks between rendered frames. Original code-drawn art; no external source images. Not real-time performance or a participant.","observations":observations},"  ")+"\n");file.close()
	scene.queue_free();await create_timer(.8).timeout;quit(0)
