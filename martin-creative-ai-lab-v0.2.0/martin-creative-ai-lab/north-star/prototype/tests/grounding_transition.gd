extends SceneTree
func _initialize() -> void:
	var source=load("res://combat.gd").new();source.reset("Guardian");source.mode="won";source.courier.x=1000
	var room=load("res://return_gate.gd").new();room.begin(source,"carried");room.game.player=Vector2(550,560)
	for tick in 90:room.step(1.0/60,{"interact":true})
	var result={"integrity":room.game.cargo,"ward_disabled":room.game.sentinel_disabled(),"counters":room.game.counters.counters,"mode":room.game.mode,"raised":room.raised}
	var args=OS.get_cmdline_user_args();var file=FileAccess.open(args[0],FileAccess.WRITE);file.store_string(JSON.stringify(result,"  ")+"\n");quit()
