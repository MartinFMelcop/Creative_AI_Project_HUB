extends SceneTree
## Execute candidate data through the real model, without replacing live inputs.
const Model=preload("model.gd")
const Policy=preload("../tests/policy.gd")
func _initialize() -> void:
	var args=OS.get_cmdline_user_args()
	if args.size()!=2:printerr("Expected candidate catalog and output paths");quit(2);return
	var source=Model.new(args[0])
	var report={"schema_version":1,"valid":source.catalog.ok,"error":source.catalog.error,"profiles":[]}
	if source.catalog.ok:
		for id in source.catalog.items:
			var model=Model.new(args[0]);model.prepare(id);model.begin()
			var start=model.game.player
			model.step(0,{"rush":true,"aim":Vector2.RIGHT})
			var paid=model.game.energy
			for tick in 100:
				if model.travel_left<=0:break
				model.step(1.0/60.0,{})
			var travel={"distance":model.game.player.distance_to(start),"energy_after_payment":paid,"energy_after_travel":model.game.energy,"elapsed":model.game.elapsed,"starts":model.starts}
			var journey=Model.new(args[0]);journey.prepare(id);journey.begin()
			for tick in 4000:
				var command:Dictionary=Policy.command(journey.game)
				if tick==0:command.rush=true
				journey.step(1.0/60.0,command)
				if journey.game.mode!="play":break
			report.profiles.append({"id":id,"definition":source.catalog.items[id],"travel":travel,"journey":{"starts":journey.starts,"combat":journey.game.snapshot()}})
	var file=FileAccess.open(args[1],FileAccess.WRITE)
	if file==null:printerr("Cannot write probe result");quit(1);return
	file.store_string(JSON.stringify(report,"  ")+"\n");quit(0 if source.catalog.ok else 2)
