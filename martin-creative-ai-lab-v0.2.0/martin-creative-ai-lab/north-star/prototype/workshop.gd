extends RefCounted
## Experimental session-only fitting, not profession progression or an item economy.
const Fittings = preload("res://fittings.gd")
var fittings := {}
var names := {}
var stations := {}
var content_errors: Array = []
const RADIUS := 46.0
const MAKE_TIME := 1.0
var active := false
var paused := false
var player := Vector2(575,540)
var outfit := "standard"
var blank := 1
var progress := 0.0
var target := ""
var needs_release := false
var made := 0
var recycled := 0
var message := "One blank. Choose resistance, mobility or recovery; both approaches can wear any piece."

func _init(path: String=Fittings.PATH) -> void:
	var content := Fittings.load_catalog(path)
	fittings=content.items;content_errors=content.errors
	for id in fittings:
		names[id]=fittings[id].name
		if fittings[id].station != null: stations[id]=Vector2(fittings[id].station[0],fittings[id].station[1])

func enter() -> void:
	if not content_errors.is_empty(): return
	active=true;paused=false;player=Vector2(575,540);cancel()

func cancel() -> void:
	progress=0.0;target=""

func suspend() -> void:
	paused=true;cancel()

func leave() -> void:
	active=false;paused=false;cancel()

func recycle() -> bool:
	if not active or paused or outfit=="standard":return false
	outfit="standard";blank=1;recycled+=1;needs_release=true;cancel()
	message="Fitting recovered. Choose again; no permanent materials or progress are lost."
	return true

func near_station() -> String:
	for id in stations:
		if player.distance_to(stations[id])<=RADIUS:return id
	return ""

func inspected_fitting() -> String:
	var nearest := "standard"
	var distance := INF
	for id in stations:
		var current: float=player.distance_to(stations[id])
		if current < distance: nearest=id;distance=current
	return nearest

func step(delta: float, move: Vector2, interact: bool) -> void:
	if not active or paused:return
	var dt:=clampf(delta,0,0.05)
	player=(player+move.limit_length()*250.0*dt).clamp(Vector2(75,270),Vector2(1075,600))
	if not interact:needs_release=false
	if needs_release:cancel();return
	var id:=near_station()
	if move!=Vector2.ZERO or not interact or id.is_empty():cancel();return
	if blank==0:
		cancel();message="Already fitted: "+names[outfit]+". C recycles it before another make.";return
	if target!=id:cancel();target=id
	progress+=dt
	if progress+0.000001>=MAKE_TIME:
		outfit=id;blank=0;made+=1;needs_release=true;cancel()
		message="Made and worn: "+names[outfit]+". ENTER starts the crossing; C recycles here."

func snapshot() -> Dictionary:
	return {"active":active,"paused":paused,"player":[snappedf(player.x,0.001),snappedf(player.y,0.001)],
		"outfit":outfit,"blank":blank,"progress":snappedf(progress,0.000001),"target":target,"needs_release":needs_release,"made":made,"recycled":recycled}
