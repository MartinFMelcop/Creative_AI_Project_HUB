extends RefCounted
## A second, voluntary destination objective. No new account, inventory or canon.
const Combat=preload("res://combat.gd")
const WINCH:=Vector2(600,390)
const CATCHES:=[Vector2(330,270),Vector2(960,530)]
const EXIT:=Vector2(1060,390)
const RADIUS:=32.0
const WORK_TIME:=1.0
var active:=false
var entry:Dictionary={}
var game=Combat.new()
var raised:=[false,false]
var progress:=0.0
var channel:=false
var working:=-1
var events:Array[Dictionary]=[]

func begin(source, medicine: String) -> bool:
	if active or source.mode!="won" or source.hp<=0 or source.cargo<=0 or source.courier.x<Combat.FINISH:return false
	entry={"role":source.role,"style":source.guard_style,"outfit":source.outfit,
		"hp":source.hp,"energy":source.energy,"route":source.route.kind,"medicine":medicine}
	active=true;retry();return true

func retry() -> void:
	if not active:return
	game=Combat.new();game.reset(entry.role,entry.style);game.fit_outfit(entry.outfit)
	game.hp=entry.hp;game.energy=entry.energy
	# The protected-contact fields represent this room's stationary device.
	game.stationary_relay=true;game.courier=WINCH;game.cargo=2
	game.player=Vector2(700,390);game.facing=Vector2.RIGHT
	raised=[false,false];progress=0;channel=false;working=-1;events.clear()
	game.note("Courier safe. Raise both catches, protect the winch, then pass the gate.")

func pending_nearby() -> int:
	for i in CATCHES.size():
		if not raised[i] and game.player.distance_to(CATCHES[i])<=RADIUS:return i
	return -1

func eligible(command: Dictionary) -> bool:
	return game.mode=="play" and pending_nearby()>=0 and game.step_left<=0 and command.get("move",Vector2.ZERO)==Vector2.ZERO

func suspend() -> void:
	progress=0;channel=false;working=-1

func step(delta: float, command: Dictionary) -> void:
	if not active or game.mode!="play":return
	var index:=pending_nearby()
	var work:bool=eligible(command) and bool(command.get("interact",false))
	var effective:=command.duplicate()
	if work:
		if working!=index:progress=0
		working=index;channel=true
		for key in ["skill","skill_pressed","dodge","strike"]:effective[key]=false
	else:suspend()
	var previous_hp:int=game.hp
	var previous_hits:int=game.counters.courier_hits
	game.step(delta,effective)
	# Closed bars are a real movement boundary, not only a drawn promise.
	if not opened():game.player.x=minf(game.player.x,1000)
	if game.counters.courier_hits>previous_hits:
		game.retain_impact("winch_hit","The locked bolt reached the winch before a protecting body.","Intercept in front, or draw the bolt away before leaving to work.")
		game.note("Winch hit. Only %d integrity remains."%game.cargo)
	if game.mode=="lost":
		suspend();game.note("Return gate failed. Retry from the arrival checkpoint or leave.");return
	if game.hp<previous_hp:
		suspend();game.note("Hit interrupted the catch. Reposition, then start that work again.")
	elif work:
		progress+=clampf(delta,0,0.05)
		if progress+0.000001>=WORK_TIME:
			raised[index]=true
			events.append({"tick":roundi(game.elapsed*60),"action":"catch_raised","index":index})
			suspend()
			game.note("Both catches raised. Pass through the open gate alive." if opened() else "One catch raised. The winch is still exposed; reach the other catch.")
	if opened() and game.player.x>=1040 and game.player.distance_to(EXIT)<=24:
		game.mode="won";suspend()
		events.append({"tick":roundi(game.elapsed*60),"action":"return_opened"})
		game.note("Return passage opened. The courier's safe crossing now has a way back.")

func opened() -> bool:
	return raised[0] and raised[1]

func snapshot() -> Dictionary:
	return {"active":active,"entry":entry.duplicate(true),"raised":raised.duplicate(),
		"progress":snappedf(progress,0.000001),"channel":channel,"working":working,
		"events":events.duplicate(true),"game":game.snapshot()}
