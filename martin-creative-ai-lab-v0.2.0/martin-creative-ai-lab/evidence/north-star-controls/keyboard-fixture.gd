extends SceneTree
# Prepared interaction fixture; not evidence of navigating a full crossing.
func _initialize() -> void:
 call_deferred("run")
func run() -> void:
 var scene=load("res://arena.tscn").instantiate()
 root.add_child(scene)
 scene.begin_crossing()
 scene.game.courier.x=400
 scene.game.player=Vector2(400,550)
 scene.game.elapsed=8.6
 scene.game.phase="rest"
 scene.game.clock=0
 scene.game.mode="paused"
