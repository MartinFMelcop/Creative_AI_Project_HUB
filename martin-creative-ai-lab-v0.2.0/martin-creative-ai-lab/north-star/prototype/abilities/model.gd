extends RefCounted
## Developer experiment: wrap the unchanged crossing; no production or network seam.
const Combat=preload("../combat.gd")
const Catalog=preload("catalog.gd")
var game=Combat.new()
var catalog:Dictionary
var selected:="none"
var travel_left:=0.0
var recovery_left:=0.0
var cooldown:=0.0
var direction:=Vector2.RIGHT
var starts:=0
var refusals:=0
var reason:="Choose before entering."
func _init(path:String=Catalog.PATH) -> void:
	catalog=Catalog.load_catalog(path)
func prepare(id:String) -> bool:
	if game.mode!="title" or not catalog.ok or (id!="none" and not catalog.items.has(id)):return false
	selected=id;return true
func begin() -> bool:
	if game.mode!="title" or not catalog.ok:return false
	game.reset("Guardian","Steady")
	if game.mode!="play":return false
	reason="Crossing live. Rush adds no immunity."
	return true
func status() -> String:
	if game.mode!="play":return game.mode.to_upper()
	if travel_left>0:return "COMMITTED"
	if recovery_left>0:return "RECOVERING"
	if cooldown>0:return "COOLDOWN"
	return "NO RUSH" if selected=="none" else "READY"
func step(delta:float,command:Dictionary) -> void:
	if game.mode!="play":return
	var dt=clampf(delta,0,0.05)
	cooldown=maxf(0,cooldown-dt)
	if command.get("rush",false):
		if selected=="none":reason="Baseline has no rush.";refusals+=1
		elif travel_left>0 or recovery_left>0 or cooldown>0 or game.guard or game.step_left>0 or game.energy<float(catalog.items[selected].cost):
			reason="Rush refused: release guard, finish step/recovery and keep its resolve cost.";refusals+=1
		else:
			var row:Dictionary=catalog.items[selected]
			var aim:Vector2=command.get("aim",Vector2.ZERO)
			direction=aim.normalized() if aim.length()>0.1 else game.facing
			game.facing=direction;game.energy-=row.cost
			travel_left=row.travel;cooldown=row.cooldown;starts+=1
			game.record("rush_started");reason="Direction locked. No guard, strike or step until recovery ends."
	var next=command.duplicate()
	if travel_left>0:
		var active=minf(dt,travel_left)
		game.player+=direction*float(catalog.items[selected].speed)*active*game.movement_scale
		game.player=game.player.clamp(Combat.FIELD.position+Vector2(20,20),Combat.FIELD.end-Vector2(20,20))
		travel_left=maxf(0,travel_left-dt)
		if travel_left<0.0000001:travel_left=0
		next={"aim":direction}
		var before=game.energy
		game.step(dt,next)
		game.energy=minf(game.energy,before) # No passive recovery during paid travel.
		if travel_left<=0:
			recovery_left=catalog.items[selected].recovery
			game.record("rush_arrived");reason="Rush arrived. Recover before guarding or countering."
	elif recovery_left>0:
		recovery_left=maxf(0,recovery_left-dt)
		next.erase("skill");next.erase("skill_pressed");next.erase("dodge");next.erase("strike")
		game.step(dt,next)
	else:game.step(dt,next)
