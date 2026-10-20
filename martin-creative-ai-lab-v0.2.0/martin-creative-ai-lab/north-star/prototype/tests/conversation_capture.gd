extends SceneTree
## Real escort preparation, rendered conversation, and an explicitly assisted OS fixture.
const Policy=preload("res://tests/policy.gd")
var scene
var folder:=""
var frames:={}

func _initialize() -> void:call_deferred("run")

func key(code: int) -> void:
	var event=InputEventKey.new();event.keycode=code;event.physical_keycode=code;event.pressed=true
	scene._unhandled_key_input(event)

func escort(role: String,wounded: bool=true) -> bool:
	scene.abandon();scene.selected=role;scene.begin_crossing()
	for i in 4200:
		if scene.game.mode!="play":break
		scene.advance_crossing(1.0/60,{} if wounded and i<170 else Policy.command(scene.game));scene.sync_sound()
	return scene.game.mode=="won" and scene.game.hp>0 and (scene.game.hp<scene.game.health_limit if wounded else scene.game.hp==scene.game.health_limit)

func frame(label: String) -> void:
	scene.queue_redraw();await process_frame;await process_frame;await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(folder+"/"+label+".png")
	frames[label]={"game":scene.game.snapshot(),"talk":scene.courier_talk.snapshot(),
		"gate":scene.return_gate.snapshot(),"look":scene.character_look.applied.duplicate(),
		"actors":scene.actors.snapshot(scene.game)}

func finish() -> void:
	scene.sound.silence();await create_timer(.1).timeout;scene.free();await process_frame

func fail(message: String) -> void:
	push_error(message);await finish();quit(1)

func run() -> void:
	var args=OS.get_cmdline_user_args()
	if args.size()<1 or args.size()>2 or (args.size()==2 and args[1]!="--os"):quit(2);return
	folder=args[0];DirAccess.make_dir_recursive_absolute(folder)
	scene=load("res://arena.tscn").instantiate();root.add_child(scene);scene.set_physics_process(false)
	if scene.get("courier_talk")==null:await fail("Conversation consumer is unavailable");return
	if not escort("Guardian"):await fail("Actual wounded Guardian escort did not arrive");return
	if args.size()==2:
		# The fixture completes the escort; real OS keys own every subsequent choice.
		# Physics stays deliberately frozen to isolate receipt from observer timing.
		var ready=FileAccess.open(folder+"/os-ready.json",FileAccess.WRITE)
		ready.store_string(JSON.stringify({"mode":scene.game.mode,"hp":scene.game.hp,"health_limit":scene.game.health_limit,
			"fixture":"Actual completed escort; frozen arrival and gate entry; OS conversation keys only."})+"\n")
		return
	var arrival:Dictionary=scene.game.snapshot()
	key(KEY_F4)
	if not scene.courier_talk.active:await fail("Actual F4 did not open the conversation");return
	await frame("courier-offer")
	key(KEY_TAB);await frame("courier-road");key(KEY_TAB)
	key(KEY_1);await frame("courier-heal-selected")
	key(KEY_ENTER)
	if scene.courier_talk.choice!="heal" or scene.game.snapshot()!=arrival:
		await fail("Confirmed conversation mutated the completed escort");return
	await frame("courier-heal-confirmed")
	key(KEY_F2)
	if not scene.return_gate.active or scene.game.hp!=mini(arrival.hp+1,scene.game.health_limit) or scene.game.cargo!=2:
		await fail("The selected bandage did not reach the actual return consumer");return
	await frame("healed-return")
	if not escort("Duelist"):await fail("Actual wounded Duelist escort did not arrive");return
	arrival=scene.game.snapshot();key(KEY_F4);key(KEY_2);key(KEY_ENTER);key(KEY_F2)
	if not scene.return_gate.active or scene.game.hp!=arrival.hp or scene.game.cargo!=3:
		await fail("The selected brace did not reach the actual return consumer");return
	await frame("braced-return")
	if not escort("Guardian",false):await fail("Actual unwounded Guardian escort did not arrive");return
	arrival=scene.game.snapshot();key(KEY_F4);key(KEY_1)
	if scene.courier_talk.enabled("heal") or not scene.courier_talk.draft.is_empty():
		await fail("Full-health arrival incorrectly accepted a healing choice");return
	await frame("full-health-offer")
	key(KEY_2);key(KEY_ENTER)
	if scene.courier_talk.choice!="brace" or scene.game.snapshot()!=arrival:
		await fail("Full-health arrival could not agree to bracing");return
	await frame("full-health-brace-confirmed")
	key(KEY_F2)
	if not scene.return_gate.active or scene.game.hp!=arrival.hp or scene.game.cargo!=3:
		await fail("Full-health brace changed health or failed to reach the winch");return
	var file=FileAccess.open(folder+"/frames.json",FileAccess.WRITE)
	file.store_string(JSON.stringify(frames,"  ")+"\n")
	await finish();quit(0)
