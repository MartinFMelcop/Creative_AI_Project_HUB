extends SceneTree
func _initialize() -> void:
	var args=OS.get_cmdline_user_args()
	if args.size()!=1:quit(2);return
	var pack=PCKPacker.new()
	if pack.pck_start(args[0])!=OK:quit(1);return
	for name in ["route.gd","tests/route_checks.gd","tests/render_routes.gd","workshop.gd","tests/workshop_checks.gd","project.godot","arena.tscn","arena.gd","combat.gd","tests/run_checks.gd","tests/policy.gd","rehearsal.gd","tests/rehearsal_checks.gd","keepsakes.gd","tests/keepsake_checks.gd","tests/keepsake_restart.gd","errand.gd","tests/errand_checks.gd","tests/errand_policy.gd","controls.gd","tests/controls_checks.gd","tests/controls_restart.gd","sound.gd","tests/sound_checks.gd","tests/sound_capture.gd","tests/guard_checks.gd","tests/guard_capture.gd","actors.gd","tests/actor_checks.gd","tests/actor_capture.gd","tests/resolution_checks.gd","tests/resolution_routes.gd","tests/toggle_checks.gd","tests/toggle_fixture.gd"]:
		if pack.add_file("res://"+name,"res://"+name)!=OK:quit(1);return
	if pack.flush()!=OK:quit(1);return
	print("Packed current source consumer and native checks; Godot 4.6.3 required.")
	quit(0)
