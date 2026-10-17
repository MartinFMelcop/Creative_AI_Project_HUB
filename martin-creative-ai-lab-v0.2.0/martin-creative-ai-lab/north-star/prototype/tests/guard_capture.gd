extends SceneTree
## Controlled scene presentation/input, not independent player learning.
const Trial=preload("res://tests/rehearsal_checks.gd")
class LiveProbe:
 extends Node
 var consumer
 var path := ""
 var input_log := []
 func _input(event):
  if event is InputEventKey and not event.echo:
   input_log.append({"physical":event.physical_keycode,"logical":event.keycode,"pressed":event.pressed,"tick":roundi(consumer.game.elapsed*60),"mode":consumer.game.mode})
   if input_log.size()>32:input_log.pop_front()
 func _physics_process(_dt):
  var record=consumer.game.snapshot()
  record.rehearsal=consumer.rehearsal.snapshot();record.last_impact=consumer.game.last_impact.duplicate(true);record.inputs=input_log
  var file=FileAccess.open(path,FileAccess.WRITE)
  if file!=null:file.store_string(JSON.stringify(record));file.close()
var scene
var folder := ""
var observations := {}
func _initialize():call_deferred("run")
func held(pressed: bool):
 var event=InputEventKey.new();event.pressed=pressed;event.keycode=KEY_K;event.physical_keycode=KEY_K
 Input.parse_input_event(event);Input.flush_buffered_events()
func frames(count: int):
 for i in count:
  scene._physics_process(1.0/60.0)
  await process_frame
func capture(name: String):
 scene.queue_redraw()
 await RenderingServer.frame_post_draw
 root.get_texture().get_image().save_png(folder.path_join(name+".png"))
 observations[name]={"game":scene.game.snapshot(),"guard_state":scene.game.guard_state(),"guard_age":scene.game.guard_age,"opening":scene.game.opening,"impact":scene.game.last_impact.duplicate(),"sound":scene.sound.snapshot(),"rehearsal":scene.rehearsal.snapshot()}
func run():
 var args=OS.get_cmdline_user_args()
 if args.size()==2 and args[0]=="--probe":
  scene=load("res://arena.tscn").instantiate();root.add_child(scene)
  var probe=LiveProbe.new();probe.consumer=scene;probe.path=args[1];root.add_child(probe)
  return
 if args.size()!=1:quit(2);return
 folder=args[0];DirAccess.make_dir_recursive_absolute(folder)
 scene=load("res://arena.tscn").instantiate();root.add_child(scene);scene.set_physics_process(false)
 Trial.key(scene,KEY_TAB);await capture("choice")
 Trial.key(scene,KEY_T);await capture("ready")
 Trial.key(scene,KEY_ENTER);held(true);await frames(45);await capture("stale-guard");await frames(17);held(false)
 await capture("early-review")
 Trial.key(scene,KEY_ENTER);Trial.key(scene,KEY_ENTER);await frames(45);await capture("raise-now")
 held(true);await frames(17);held(false);await capture("timed-review")
 var file=FileAccess.open(folder.path_join("presentation.json"),FileAccess.WRITE)
 file.store_string(JSON.stringify({"scope":"Prepared actual rehearsal with synthetic input and controlled model ticks between rendered frames; not real-time performance or a human participant.","observations":observations},"  ")+"\n");file.close()
 scene.queue_free();await create_timer(.8).timeout
 quit(0)
