extends SceneTree
const Arena=preload("res://arena.gd")
const Policy=preload("res://tests/policy.gd")
const GatePolicy=preload("res://tests/gate_policy.gd")
var output:=""
var frames:={}
func _initialize() -> void:
	var args=OS.get_cmdline_user_args()
	if args.size()!=1:quit(2);return
	output=args[0];DirAccess.make_dir_recursive_absolute(output);call_deferred("run")
func frame(a,label: String) -> void:
	a.queue_redraw();await process_frame;await process_frame;await RenderingServer.frame_post_draw
	get_root().get_texture().get_image().save_png(output+"/"+label+".png")
	frames[label]={"gate":a.return_gate.snapshot(),"player":[a.game.player.x,a.game.player.y],"sound":a.sound.snapshot()}
func run() -> void:
	for role in ["Guardian","Duelist"]:
		var a=Arena.new();root.add_child(a);a.set_physics_process(false);a.selected=role;a.begin_crossing()
		for i in 4200:
			if a.game.mode!="play":break
			a.advance_crossing(1.0/60,{} if i<170 else Policy.command(a.game))
		if not a.begin_return_gate():push_error("No real arrival for render");quit(1);return
		var working:=false;var opened:=false
		for i in 6000:
			if a.game.mode!="play":break
			a.advance_crossing(1.0/60,GatePolicy.command(a.return_gate,"work"));a.sync_sound()
			if not working and a.return_gate.progress>0.4:
				working=true;await frame(a,role.to_lower()+"-working")
			if not opened and a.return_gate.opened():
				opened=true;await frame(a,role.to_lower()+"-opened")
		if a.game.mode!="won":push_error("Rendered continuation failed");quit(1);return
		await frame(a,role.to_lower()+"-result");a.sound.silence()
		# Let the audio thread retire its last playback before destroying this fixture.
		await create_timer(0.1).timeout
		a.free()
		await process_frame
		await process_frame
	var file=FileAccess.open(output+"/frames.json",FileAccess.WRITE);file.store_string(JSON.stringify(frames,"  ")+"\n")
	print("RETURN_GATE_RENDER complete actual two-stage scenes");quit(0)
