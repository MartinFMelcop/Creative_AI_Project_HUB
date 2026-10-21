extends RefCounted
## A second, voluntary destination objective. No new account, inventory or canon.
const Combat=preload("res://combat.gd")
const WINCH:=Vector2(600,390)
const CATCHES:=[Vector2(330,270),Vector2(960,530)]
const EXIT:=Vector2(1060,390)
const RADIUS:=32.0
const WORK_TIME:=1.0
const GROUND:=Vector2(550,560)
const GROUND_TIME:=1.5
const GROUND_COST:=1
var grounding_review:Dictionary={}
const GROUND_INDEX:=2
var grounded:=false
var active:=false
var entry:Dictionary={}
var game=Combat.new()
var raised:=[false,false]
var progress:=0.0
var channel:=false
var working:=-1
var events:Array[Dictionary]=[]

func begin(source, medicine: String, aid: String="") -> bool:
	if active or source.mode!="won" or source.hp<=0 or source.cargo<=0 or source.courier.x<Combat.FINISH:return false
	if not aid in ["","heal","brace"] or (aid=="heal" and source.hp>=source.health_limit):return false
	entry={"role":source.role,"style":source.guard_style,"outfit":source.outfit,
		"hp":source.hp,"energy":source.energy,"route":source.route.kind,"medicine":medicine}
	if not aid.is_empty():entry.aid=aid
	active=true;retry();return true

static func winch_capacity(aid:String) -> int:
	return 3 if aid=="brace" else 2

static func preparation(hp:int,limit:int,aid:String) -> Dictionary:
	if hp<=0 or limit<hp or not aid in ["","heal","brace","keep"]:return {}
	var integrity:int=winch_capacity(aid)
	return {"hp":mini(limit,hp+(1 if aid=="heal" else 0)),"health_limit":limit,"integrity":integrity,
		"ground_cost":GROUND_COST,"ground_left":integrity-GROUND_COST,"after_hit":integrity-1,
		"ground_after_hit":integrity-1>GROUND_COST}

static func preparation_line(hp:int,limit:int,aid:String) -> String:
	var plan:Dictionary=preparation(hp,limit,aid)
	if plan.is_empty():return "No valid arrival preparation."
	return "HP %d/%d / winch %d -> %d if grounded / OR 1 winch hit first: %d, %s"%[plan.hp,plan.health_limit,
		plan.integrity,plan.ground_left,plan.after_hit,"can still ground" if plan.ground_after_hit else "cannot ground"]

func cargo_limit() -> int:
	return winch_capacity(entry.get("aid",""))

func retry() -> void:
	if not active:return
	game=Combat.new();game.reset(entry.role,entry.style);game.fit_outfit(entry.outfit)
	var plan:Dictionary=preparation(entry.hp,game.health_limit,entry.get("aid",""))
	game.hp=plan.hp;game.energy=entry.energy
	# The protected-contact fields represent this room's stationary device.
	game.stationary_relay=true;game.courier=WINCH;game.cargo=plan.integrity
	game.player=Vector2(700,390);game.facing=Vector2.RIGHT
	grounding_review.clear();grounded=false;raised=[false,false];progress=0;channel=false;working=-1;events.clear()
	game.note("Courier safe. Raise both catches, protect the winch, then pass the gate.")

func pending_nearby() -> int:
	for i in CATCHES.size():
		if not raised[i] and game.player.distance_to(CATCHES[i])<=RADIUS:return i
	if not game.sentinel_disabled() and game.cargo>GROUND_COST and game.player.distance_to(GROUND)<=RADIUS:return GROUND_INDEX
	return -1

func eligible(command: Dictionary) -> bool:
	return game.mode=="play" and pending_nearby()>=0 and game.step_left<=0 and command.get("move",Vector2.ZERO)==Vector2.ZERO

func suspend(reason:String="suspended") -> void:
	if channel and working==GROUND_INDEX and progress>0 and not grounded:
		grounding_review.merge({"status":"interrupted","cause":reason,"seconds":snappedf(progress,.001),
			"tick":roundi(game.elapsed*60),"integrity":game.cargo,"spent":0},true)
	progress=0;channel=false;working=-1

func feedback_lines() -> Array[String]:
	if grounding_review.is_empty():return []
	var first:String="Last ground: %s at %.2f / %.2fs. Cost %d."%[grounding_review.cause.to_upper(),
		grounding_review.seconds,GROUND_TIME,grounding_review.spent]
	if grounding_review.status=="completed":first="Grounded: paid %d winch integrity (%d -> %d)."%[GROUND_COST,grounding_review.start_integrity,grounding_review.integrity]
	var next:String="Raise both catches and cross the exit alive; shutdown alone is not the goal."
	if game.mode=="won":next="Both catches raised and exit reached alive. The return passage is open."
	elif game.mode=="lost":next="This attempt is over. Retry restores the prepared arrival; aid never stacks."
	elif not game.sentinel_disabled():
		next="Winch now %d: grounding needs %d+. Work under threat or earn 3 close counters."%[game.cargo,GROUND_COST+1] if game.cargo<=GROUND_COST else "Winch now %d: grounding is still available. A new attempt needs the full %.1fs."%[game.cargo,GROUND_TIME]
	return [first,next]

func step(delta: float, command: Dictionary) -> void:
	if not active or game.mode!="play":return
	var index:=pending_nearby()
	var work:bool=eligible(command) and bool(command.get("interact",false))
	var effective:=command.duplicate()
	if work:
		if working!=index:
			progress=0
			if index==GROUND_INDEX:grounding_review={"status":"working","cause":"working","seconds":0.0,
				"started_tick":roundi(game.elapsed*60),"start_integrity":game.cargo,"integrity":game.cargo,"spent":0}
		working=index;channel=true
		for key in ["skill","skill_pressed","dodge","strike"]:effective[key]=false
	else:suspend("movement" if command.get("move",Vector2.ZERO)!=Vector2.ZERO else ("release" if not command.get("interact",false) else "unavailable"))
	var previous_hp:int=game.hp
	var previous_hits:int=game.counters.courier_hits
	game.step(delta,effective)
	# Closed bars are a real movement boundary, not only a drawn promise.
	if not opened():game.player.x=minf(game.player.x,1000)
	if game.counters.courier_hits>previous_hits:
		game.retain_impact("winch_hit","The locked bolt reached the winch before a protecting body.","Intercept in front, or draw the bolt away before leaving to work.")
		game.note("Winch hit. Only %d integrity remains."%game.cargo)
	if game.mode=="lost":
		suspend("winch destroyed" if game.cargo<=0 else "player fell");game.note("Return gate failed. Retry from the arrival checkpoint or leave.");return
	if work and index==GROUND_INDEX and game.counters.courier_hits>previous_hits:
		suspend("winch hit");game.note("Winch damage interrupted grounding. At least 2 integrity is required.")
	elif game.hp<previous_hp:
		suspend("player hit");game.note("Hit interrupted the work. Reposition, then start that work again.")
	elif work:
		progress+=clampf(delta,0,0.05)
		if index==GROUND_INDEX:grounding_review.seconds=snappedf(progress,.001)
		if progress+0.000001>=(GROUND_TIME if index==GROUND_INDEX else WORK_TIME):
			if index==GROUND_INDEX:
				game.cargo-=GROUND_COST;grounded=true
				grounding_review.merge({"status":"completed","cause":"completed","seconds":GROUND_TIME,
					"tick":roundi(game.elapsed*60),"integrity":game.cargo,"spent":GROUND_COST},true)
				game.enemy_focus=0;game.phase="disabled";game.clock=0;game.opening=0;game.redirected=false
				events.append({"tick":roundi(game.elapsed*60),"action":"ward_grounded","integrity_spent":GROUND_COST})
				suspend();game.note("Ward grounded. Spent 1 winch integrity; both catches and the exit still need work.")
			else:
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
	var result={"active":active,"entry":entry.duplicate(true),"raised":raised.duplicate(),
		"progress":snappedf(progress,0.000001),"channel":channel,"working":working,
		"events":events.duplicate(true),"game":game.snapshot()}
	if grounded:result.grounded=true
	if not grounding_review.is_empty():result.grounding_review=grounding_review.duplicate(true)
	return result
