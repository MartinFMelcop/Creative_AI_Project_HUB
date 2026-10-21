extends SceneTree
var scene
func _initialize():call_deferred("run")
func tap(id):
	for down in [true,false]:
		var e=InputEventJoypadButton.new();e.button_index=id;e.pressed=down
		Input.parse_input_event(e);Input.flush_buffered_events()
func shot(name):
	scene._physics_process(0)
	scene.queue_redraw()
	await process_frame
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(OS.get_environment("PAD_SHOTS")+"/"+name+".png")
func run():
	scene=load("res://arena.tscn").instantiate();root.add_child(scene)
	await process_frame
	scene.set_physics_process(false)
	tap(JOY_BUTTON_DPAD_RIGHT);await shot("title")
	tap(JOY_BUTTON_BACK);await shot("guide");tap(JOY_BUTTON_B)
	tap(JOY_BUTTON_RIGHT_SHOULDER);await shot("appearance");tap(JOY_BUTTON_B)
	tap(JOY_BUTTON_A);await shot("play")
	scene.free();quit()
