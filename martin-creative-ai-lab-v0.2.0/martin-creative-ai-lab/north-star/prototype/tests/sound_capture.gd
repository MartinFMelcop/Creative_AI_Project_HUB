extends SceneTree
## Actual AudioServer capture with prepared exercise positions, not human play.
const Trial = preload("res://tests/rehearsal_checks.gd")
var scene
var recorder=AudioEffectRecord.new()
var folder := ""
var records := []

func _initialize() -> void:call_deferred("run")

func held(code: int,pressed: bool) -> void:
	var event=InputEventKey.new();event.pressed=pressed;event.keycode=code;event.physical_keycode=code
	Input.parse_input_event(event);Input.flush_buffered_events()

func frames(count: int,move: int=0) -> void:
	if move:held(move,true)
	for i in count:
		scene._physics_process(1.0/60.0)
		await physics_frame
	if move:held(move,false)

func begin() -> void:
	recorder.set_recording_active(true)
	await create_timer(0.12).timeout

func finish(name: String) -> void:
	await create_timer(0.65).timeout
	recorder.set_recording_active(false)
	var recording=recorder.get_recording()
	if recording==null or recording.save_to_wav(folder.path_join(name+".wav"))!=OK:quit(1);return
	records.append({"name":name,"bytes":recording.data.size(),"rate":recording.mix_rate,"stereo":recording.stereo,"combat":scene.game.snapshot(),"sound":scene.sound.snapshot() if scene.get("sound")!=null else {"baseline_no_audio":true}})

func picture(name: String) -> void:
	if DisplayServer.get_name()=="headless":return
	scene.queue_redraw()
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(folder.path_join(name+".png"))

func run() -> void:
	var args=OS.get_cmdline_user_args()
	if args.size()!=1:quit(2);return
	folder=args[0];DirAccess.make_dir_recursive_absolute(folder)
	scene=load("res://arena.tscn").instantiate()
	root.add_child(scene);scene.set_physics_process(false)
	AudioServer.add_bus_effect(0,recorder)
	await create_timer(0.15).timeout
	await begin();await finish("title-silence")

	scene.rehearsal.start("Guardian");scene.game=scene.rehearsal.game
	await begin();Trial.key(scene,KEY_ENTER);held(KEY_K,true)
	await frames(16);await picture("guardian-warning")
	await frames(48);held(KEY_K,false)
	await picture("guardian-review");await finish("guardian-block")

	scene.rehearsal.start("Duelist");scene.game=scene.rehearsal.game
	await begin();Trial.key(scene,KEY_ENTER);Trial.key(scene,KEY_K)
	await frames(64,KEY_W);await picture("duelist-review");await finish("duelist-draw")

	scene.rehearsal.stage=1;scene.rehearsal.prepare("Guardian");scene.game=scene.rehearsal.game
	await begin();Trial.key(scene,KEY_ENTER)
	await frames(16);await picture("pulse-warning");await frames(48,KEY_W)
	await finish("pulse-avoided")

	if scene.get("sound")!=null:
		# Same warning/contact setup, muted via actual controls. No output is replayed.
		Trial.key(scene,KEY_F1);Trial.key(scene,KEY_F5);await picture("sound-off");Trial.key(scene,KEY_ESCAPE)
		scene.rehearsal.start("Guardian");scene.game=scene.rehearsal.game
		await begin();Trial.key(scene,KEY_ENTER);held(KEY_K,true);await frames(64);held(KEY_K,false)
		await finish("muted-block")
		Trial.key(scene,KEY_F1);Trial.key(scene,KEY_F5);Trial.key(scene,KEY_ESCAPE)
		scene.rehearsal.start("Guardian");scene.game=scene.rehearsal.game
		await begin();Trial.key(scene,KEY_ENTER);await frames(4);Trial.key(scene,KEY_ESCAPE)
		await create_timer(.15).timeout
		recorder.set_recording_active(false) # Drain pre-pause blocks before the silence probe.
		await begin();await frames(24);await finish("paused-silence")
		scene.rehearsal.start("Guardian","Riposte");scene.game=scene.rehearsal.game
		await begin();Trial.key(scene,KEY_ENTER);await frames(45);held(KEY_K,true);await frames(19);held(KEY_K,false)
		await finish("riposte-block")

		# Real normal-consumer consequences from explicitly prepared short setups.
		scene.begin_crossing();scene.game.player=Vector2(690,390);scene.game.opening=1
		await begin();Trial.key(scene,KEY_J);await frames(1);await finish("counter-contact")
		scene.begin_crossing();scene.game.phase="pulse";scene.game.pulse=scene.game.player;scene.game.clock=0.99
		await begin();await frames(1);await finish("pulse-damage")
		scene.begin_crossing();scene.game.courier.x=999.9
		await begin();await frames(1);await finish("crossing-won")
		scene.begin_crossing();scene.game.hp=1;scene.game.phase="pulse";scene.game.pulse=scene.game.player;scene.game.clock=0.99
		await begin();await frames(1);await finish("crossing-lost")
		for name in scene.sound.NAMES:
			var stream=scene.sound.stream_for(name)
			stream.save_to_wav(folder.path_join("cue-"+name+".wav"))

	var file=FileAccess.open(folder.path_join("capture.json"),FileAccess.WRITE)
	file.store_string(JSON.stringify({"driver":AudioServer.get_driver_name(),"mix_rate":AudioServer.get_mix_rate(),"records":records,"scope":"Real engine mixer; prepared native exercises and synthetic input; no physical listening, latency or human perception validation."},"  ")+"\n");file.close()
	scene.queue_free();await create_timer(.15).timeout
	for i in range(AudioServer.get_bus_effect_count(0)-1,-1,-1):
		if AudioServer.get_bus_effect(0,i)==recorder:AudioServer.remove_bus_effect(0,i)
	print("PASS: native mixer capture complete")
	quit(0)
