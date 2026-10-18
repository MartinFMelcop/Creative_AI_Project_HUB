extends SceneTree
## Prepared medicine geometry, not a navigated crossing or player evidence.
func _initialize() -> void:call_deferred("run")
func run() -> void:
	var scene=load("res://arena.tscn").instantiate();root.add_child(scene)
	scene.begin_crossing();scene.game.courier.x=400;scene.game.player=Vector2(400,550)
	scene.errand.state="available";scene.game.mode="paused"
