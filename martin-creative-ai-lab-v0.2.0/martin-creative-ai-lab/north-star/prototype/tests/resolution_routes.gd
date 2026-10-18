extends SceneTree
## Matched policies in the actual consumer, including a prior unmodified PCK.
const Guard=preload("res://tests/guard_checks.gd")
var rows := {}
func _initialize():call_deferred("run")
func common(game) -> Dictionary:
	var state: Dictionary=game.snapshot()
	state.erase("enemy_focus");state.erase("courier_speed")
	state.position=[game.player.x,game.player.y];state.phase=game.phase;state.clock=game.clock
	state.face=[game.facing.x,game.facing.y];state.guard=game.guard;state.guard_age=game.guard_age
	state.locked_face=[game.locked_face.x,game.locked_face.y];state.step=[game.step_left,game.step_dir.x,game.step_dir.y];state.redirected=game.redirected;state.cycle=game.cycle
	state.opening=game.opening;state.cooldowns=[game.step_cooldown,game.strike_cooldown,game.feint_cooldown]
	state.target=[game.target.x,game.target.y];state.pulse=[game.pulse.x,game.pulse.y]
	return state
func run():
	var args=OS.get_cmdline_user_args()
	if args.size()!=1:quit(2);return
	for setup in [["Guardian","Steady"],["Guardian","Riposte"],["Duelist","Steady"]]:
		var id: String=setup[0]+"-"+setup[1];rows[id]={}
		for policy in ["protect","counter"]:
			var scene=load("res://arena.tscn").instantiate()
			scene.profile_path=args[0]+id+policy+"-marks.json";scene.controls_path=args[0]+id+policy+"-controls.json"
			root.add_child(scene);scene.set_physics_process(false)
			scene.selected=setup[0];scene.guardian_style=setup[1];scene.begin_crossing()
			var hash_context=HashingContext.new();hash_context.start(HashingContext.HASH_SHA256)
			var prefix_ticks := 0
			for tick in 2400:
				var command: Dictionary=Guard.command(scene.game)
				if policy=="protect":command.strike=false
				scene.advance_crossing(1.0/60.0,command)
				# Compare every common state before the new causal transition, not only a score.
				if scene.game.counters.counters<3:
					hash_context.update(JSON.stringify(common(scene.game)).to_utf8_buffer());prefix_ticks+=1
				if scene.game.mode!="play":break
			rows[id][policy]={"combat":scene.game.snapshot(),"phase":scene.game.phase,"prefix_ticks":prefix_ticks,"common_prefix_sha256":hash_context.finish().hex_encode(),"medicine":scene.errand.state}
			scene.queue_free()
	var file=FileAccess.open(args[0],FileAccess.WRITE);file.store_string(JSON.stringify(rows,"  ")+"\n");file.close()
	for child in root.get_children():child.queue_free()
	await create_timer(.8).timeout;quit(0)
