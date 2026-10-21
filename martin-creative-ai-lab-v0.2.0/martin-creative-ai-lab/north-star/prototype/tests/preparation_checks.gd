extends SceneTree
const Server=preload("../authority/server.gd")
const Remote=preload("../authority/remote.gd")
const Model=preload("res://combat.gd")
const View=preload("../authority/view.gd")
var passed:=0
var failures:Array=[]
func check(ok:bool,label:String) -> void:
	if ok:passed+=1
	else:failures.append(label)
func _initialize() -> void:
	var model=Model.new();var before:String=JSON.stringify(model.snapshot())
	var catalog:Dictionary=Server.preparation_catalog(model)
	check(Remote.valid_catalog(catalog),"Actual catalog satisfies bounded DTO")
	check(JSON.stringify(model.snapshot())==before,"Catalog does not begin or mutate the encounter")
	for item in catalog.outfits:
		for role in catalog.techniques:
			for technique in catalog.techniques[role]:
				var game=Model.new();game.reset(role,technique.id);game.fit_outfit(item.id)
				check(game.health_limit==item.health and game.movement_scale==item.movement and game.recovery_rate==item.recovery and game.guard_style==technique.id,"Advertised tuple matches actual prepared model: "+role+"/"+technique.id+"/"+item.id)
	for mutation in [{"health":true},{"movement":NAN},{"movement":0},{"recovery":INF},{"id":""},{"name":[]},{"health":99}]:
		var invalid:Dictionary=catalog.duplicate(true);invalid.outfits[0].merge(mutation,true)
		check(not Remote.valid_catalog(invalid),"Malformed fitting cannot be advertised: "+str(mutation.keys()[0]))
	var duplicate:Dictionary=catalog.duplicate(true);duplicate.outfits.append(duplicate.outfits[0].duplicate())
	check(not Remote.valid_catalog(duplicate),"Duplicate outfit cannot replace an offered item")
	var wrong:Dictionary=catalog.duplicate(true);wrong.techniques.Guardian[1].id="Steady"
	check(not Remote.valid_catalog(wrong),"Duplicate technique cannot erase its alternative")
	var unsolicited=Remote.new();unsolicited.receive_message(catalog)
	check(unsolicited.status=="error","Unsolicited catalog fails closed")
	var remote=Remote.new();remote.prepare_only=true;remote.status="connecting";remote.receive_message(catalog)
	check(remote.status=="preparing" and remote.session.is_empty() and not remote.can_send(),"Inspection never grants a session or active input")
	check(not remote.start_prepared("Guardian","none","standard") and not remote.start_prepared("Guardian","Steady","invented"),"Unadvertised tuple cannot be committed")
	remote.receive_message(catalog)
	check(remote.status=="error","Repeated catalog fails closed")
	var bound=Remote.new();bound.prepare_only=true;bound.catalog=catalog;bound.hello={"role":"Guardian","style":"Steady","outfit":"standard"}
	var state={"role":"Guardian","guard_style":"Steady","health_limit":5,"preparation":{"role":"Guardian","style":"Steady","outfit":"standard","health":5,"movement":1.0,"recovery":18.0}}
	check(bound.matches_preparation(state),"Confirmed resources match the selected catalog tuple")
	for mutation in [{"health":6},{"movement":1.2},{"recovery":26},{"outfit":"trail"},{"health":true}]:
		var invalid:Dictionary=state.duplicate(true);invalid.preparation.merge(mutation,true)
		check(not bound.matches_preparation(invalid),"Confirmation cannot silently substitute a prepared resource: "+str(mutation.keys()[0]))
	var early=Remote.new();early.prepare_only=true;early.status="preparing"
	early.receive_message({"v":1,"kind":"welcome","session":"0123456789abcdef0123456789abcdef"})
	check(early.status=="error","Welcome cannot bypass explicit commitment")
	var view=View.new();view.remote.catalog=catalog;view.remote.status="preparing"
	var event=InputEventKey.new();event.keycode=KEY_C;event.pressed=true;view._input(event)
	check(view.preparation_preview().id=="riveted" and view.preparation_preview().health==6,"Native selection consumes server fitting values")
	view.started=true;view._input(event)
	check(view.preparation_preview().id=="riveted","Entry locks native preparation selection")
	view.free()
	print(JSON.stringify({"passed":passed,"failed":failures.size(),"failures":failures}))
	quit(0 if failures.is_empty() else 1)
