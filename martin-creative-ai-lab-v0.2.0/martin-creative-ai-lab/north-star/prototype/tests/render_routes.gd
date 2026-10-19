extends SceneTree
const Arena=preload("res://arena.gd")
const RouteChecks=preload("res://tests/route_checks.gd")
var output:=""
var records:={}
func _initialize() -> void:
	var args=OS.get_cmdline_user_args()
	if args.size()!=1:quit(2);return
	output=args[0];DirAccess.make_dir_recursive_absolute(output);call_deferred("run")
func frame(a, label: String) -> void:
	a.queue_redraw()
	await process_frame
	await process_frame
	await RenderingServer.frame_post_draw
	get_root().get_texture().get_image().save_png(output+"/"+label+".png")
	records[label]={"route":a.game.route.snapshot(),"courier":[a.game.courier.x,a.game.courier.y],"game":a.game.snapshot()}
func run() -> void:
	for role in ["Guardian","Duelist"]:
		var a=Arena.new();root.add_child(a);a.set_physics_process(false);a.selected=role;a.begin_crossing()
		var turn:=false;var cover:=false
		for tick in 4200:
			if a.game.mode!="play":break
			var input:Dictionary=RouteChecks.command(a.game,"ridge")
			input.interact_pressed=input.get("route_signal",false)
			a.advance_crossing(1.0/60,input);a.sync_sound()
			if not turn and a.game.courier.y<300:
				turn=true;await frame(a,role.to_lower()+"-turn")
			if not cover and a.game.route.covered>0:
				cover=true;await frame(a,role.to_lower()+"-cover")
		if a.game.mode!="won":push_error("Rendered route failed");quit(1);return
		await frame(a,role.to_lower()+"-result");a.free()
	var file=FileAccess.open(output+"/frames.json",FileAccess.WRITE);file.store_string(JSON.stringify(records,"  ")+"\n")
	print("ROUTE_RENDER complete actual-scene routes");quit(0)
