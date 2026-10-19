extends SceneTree
## Shared native event probe runnable externally against the preserved prior PCK.
const Arena=preload("res://arena.gd")
const Policy=preload("res://tests/policy.gd")
func _initialize() -> void:call_deferred("run")
func run() -> void:
	var a=Arena.new();root.add_child(a);a.set_physics_process(false);a.begin_crossing()
	for i in 4200:
		if a.game.mode!="play":break
		a.advance_crossing(1.0/60,{} if i<170 else Policy.command(a.game))
	if a.game.mode!="won" or a.game.hp!=4:push_error("Invalid wounded before-control");quit(1);return
	var original=a.game;a.sound.observe(original,true)
	var event=InputEventKey.new();event.physical_keycode=KEY_F2;event.keycode=KEY_F2;event.pressed=true
	a._unhandled_key_input(event)
	var report={"first_mode":original.mode,"first_hp":original.hp,"first_tick":roundi(original.elapsed*60),
		"after_mode":a.game.mode,"after_hp":a.game.hp,"model_replaced":a.game!=original}
	var args=OS.get_cmdline_user_args()
	if args.size()!=1:quit(2);return
	var file=FileAccess.open(args[0],FileAccess.WRITE);file.store_string(JSON.stringify(report,"  ")+"\n")
	a.free();quit(0)
