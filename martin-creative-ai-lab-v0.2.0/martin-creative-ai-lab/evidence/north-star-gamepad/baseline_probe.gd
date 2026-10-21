extends SceneTree
func _initialize():call_deferred("run")
func run():
 var scene=load("res://arena.tscn").instantiate();root.add_child(scene);await process_frame
 for down in [true,false]:
  var event=InputEventJoypadButton.new();event.device=0;event.button_index=JOY_BUTTON_A;event.pressed=down;Input.parse_input_event(event);Input.flush_buffered_events();await process_frame
 var args=OS.get_cmdline_user_args();var file=FileAccess.open(args[0],FileAccess.WRITE);file.store_string(JSON.stringify({"mode_after_south":scene.game.mode,"tick":scene.game.snapshot().tick,"supports_pad":scene.get("pad")!=null})+"\n");file.close();scene.free();await create_timer(.2).timeout;quit()
