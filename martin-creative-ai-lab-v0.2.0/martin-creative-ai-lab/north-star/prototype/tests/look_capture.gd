extends SceneTree
## Shared external default-art control also runs against the preserved prior PCK.
const Policy=preload("res://tests/policy.gd")
var scene
var folder:=""
var frames:={}
func _initialize() -> void:call_deferred("run")
func frame(label: String) -> void:
	scene.queue_redraw();await process_frame;await process_frame;await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(folder+"/"+label+".png")
	frames[label]={"game":scene.game.snapshot(),"actors":scene.actors.snapshot(scene.game)}
	if scene.get("character_look")!=null:frames[label].look=scene.character_look.snapshot()
func tick(command: Dictionary,count: int=1) -> void:
	for i in count:scene.advance_crossing(1.0/60,command);scene.sync_sound()
func run() -> void:
	var args=OS.get_cmdline_user_args()
	if args.size()!=1:quit(2);return
	folder=args[0];DirAccess.make_dir_recursive_absolute(folder)
	scene=load("res://arena.tscn").instantiate();root.add_child(scene);scene.set_physics_process(false)
	for role in ["Guardian","Duelist"]:
		scene.selected=role;scene.begin_crossing();await frame(role.to_lower()+"-original")
	if scene.get("character_look")!=null:
		scene.abandon();scene.character_look.enter("Guardian","Steady","riveted")
		scene.character_look.draft={"skin":3,"hair":2,"dye":3};scene.look_actor.attach(scene.character_look.preview)
		scene._physics_process(1.0/60);await frame("editor-rest")
		scene.character_look.pose_index=2;scene.character_look.reset_preview()
		for i in 6:scene._physics_process(1.0/60)
		await frame("editor-guard")
		scene.character_look.role="Duelist";scene.character_look.outfit=2;scene.character_look.pose_index=4
		scene.character_look.draft={"skin":2,"hair":1,"dye":1};scene.character_look.reset_preview()
		scene._physics_process(1.0/60);await frame("editor-blade")
		scene.character_look.confirm()
		scene.selected="Guardian";scene.begin_crossing();tick({"move":Vector2.RIGHT},8);await frame("guardian-custom-walk")
		scene.workshop.outfit="riveted";scene.begin_crossing();tick({"skill":true},8);await frame("guardian-custom-guard")
		scene.selected="Duelist";scene.workshop.outfit="trail";scene.begin_crossing()
		scene.game.phase="bolt";scene.game.target=scene.game.courier;tick({"skill_pressed":true});await frame("duelist-custom-draw")
		tick({"dodge":true,"move":Vector2.UP});await frame("duelist-custom-step")
		scene.workshop.outfit="standard";scene.begin_crossing()
		for i in 4200:
			if scene.game.mode!="play":break
			tick(Policy.command(scene.game))
		if not scene.begin_return_gate():push_error("No actual crossing for appearance continuation");quit(1);return
		await frame("custom-return-gate")
	var file=FileAccess.open(folder+"/frames.json",FileAccess.WRITE);file.store_string(JSON.stringify(frames,"  ")+"\n")
	scene.sound.silence();await create_timer(.1).timeout;scene.free();await process_frame;quit(0)
