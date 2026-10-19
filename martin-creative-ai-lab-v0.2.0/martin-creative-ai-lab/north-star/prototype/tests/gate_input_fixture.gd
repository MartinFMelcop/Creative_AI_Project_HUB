extends SceneTree
## Execute a real wounded escort before OS input; no teleported win or manual stats.
const Policy=preload("res://tests/policy.gd")
func _initialize() -> void:call_deferred("run")
func run() -> void:
	var scene=load("res://arena.tscn").instantiate();root.add_child(scene);scene.begin_crossing()
	for i in 4200:
		if scene.game.mode!="play":break
		scene.advance_crossing(1.0/60,{} if i<170 else Policy.command(scene.game))
	if scene.game.mode!="won" or scene.game.hp>=scene.game.health_limit:
		push_error("Input fixture failed its real wounded crossing");quit(1)
	scene.sound.observe(scene.game,true)
