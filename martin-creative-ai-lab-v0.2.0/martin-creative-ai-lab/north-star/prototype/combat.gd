extends RefCounted
## A local experimental model, consumed by both the playable scene and native checks.
## Paid commitment and facing checks adapt P06's action/contact method; no P06 fiction.
const Route = preload("res://route.gd")
var route = Route.new()
const FIELD := Rect2(50, 185, 1052, 460)
const ENEMY := Vector2(790, 390)
const FINISH := 1000.0
const SENTINEL_FOCUS := 3
var enemy_focus := SENTINEL_FOCUS
var role := "Guardian"
var outfit := "standard"
var outfit_fitted := false
var health_limit := 5
var movement_scale := 1.0
var guard_style := "Steady"
var mode := "title"
var player := Vector2(550, 390)
var courier := Vector2(160, 390)
var facing := Vector2.RIGHT
var locked_face := Vector2.RIGHT
var hp := 5
var cargo := 3
var energy := 100.0
var elapsed := 0.0
var phase := "rest"
var clock := 0.0
var cycle := 0
var target := Vector2.ZERO
var pulse := Vector2.ZERO
var guard := false
var guard_age := 0.0
var step_left := 0.0
var step_dir := Vector2.ZERO
var step_cooldown := 0.0
var feint_cooldown := 0.0
var strike_cooldown := 0.0
var opening := 0.0
var redirected := false
var message := "Choose an approach."
var message_left := 0.0
var last_impact: Dictionary = {}
var events: Array[Dictionary] = []
var counters := {"blocks":0,"redirects":0,"dodges":0,"counters":0,"courier_hits":0,"player_hits":0,"rejected":0}

func reset(kind: String, style: String="Steady") -> void:
	role = kind
	route=Route.new()
	guard_style = "Riposte" if kind=="Guardian" and style=="Riposte" else ("Steady" if kind=="Guardian" else "none")
	mode = "play"
	player = Vector2(550,390)
	courier = Vector2(160,390)
	facing = Vector2.RIGHT
	locked_face = facing
	outfit="standard";outfit_fitted=false;health_limit=5;movement_scale=1.0
	hp = 5
	cargo = 3
	enemy_focus = SENTINEL_FOCUS
	energy = 100
	elapsed = 0
	phase = "rest"
	clock = 0
	cycle = 0
	guard = false
	guard_age = 0
	step_left = 0
	step_cooldown = 0
	feint_cooldown = 0
	strike_cooldown = 0
	opening = 0
	redirected = false
	last_impact.clear()
	events.clear()
	for key in counters: counters[key]=0
	note("Keep the courier alive until the far gate. Read the first amber line.")

func signal_route(next: String) -> bool:
	if mode!="play" or player.distance_to(Route.BOARD)>Route.SIGNAL_RADIUS:return false
	if not route.choose(next,courier):
		note("Route locked at MARK 1. The courier keeps the committed path.");return false
	note("RIDGE signalled: longer walk; the raised filter stops crossing bolts, not ground pulses." if next=="ridge" else "ROAD signalled: direct crossing; the upper filter is lowered.")
	return true

func fit_outfit(id: String) -> bool:
	# Only a clean normal start can accept equipment; never heal or swap during play.
	if outfit_fitted or mode!="play" or elapsed!=0.0 or id not in ["standard","riveted","trail"]:return false
	outfit=id;outfit_fitted=true
	health_limit=6 if id=="riveted" else (4 if id=="trail" else 5)
	movement_scale=0.8 if id=="riveted" else (1.2 if id=="trail" else 1.0)
	hp=health_limit
	return true

func note(text: String) -> void:
	message = text
	message_left = 3.0

func record(kind: String) -> void:
	events.append({"tick":roundi(elapsed*60),"kind":kind,"energy":snappedf(energy,0.001),"hp":hp,"cargo":cargo})

func retain_impact(code: String, explanation: String, tip: String) -> void:
	last_impact={"code":code,"explanation":explanation,"tip":tip}

static func live_window(age: float, start: float, finish: float) -> bool:
	return age >= start and age <= finish

static func segment_distance(point: Vector2, a: Vector2, b: Vector2) -> float:
	var ab := b-a
	if ab.length_squared()<0.001: return point.distance_to(a)
	return point.distance_to(a+ab*clampf((point-a).dot(ab)/ab.length_squared(),0,1))

func sentinel_disabled() -> bool:
	return enemy_focus==0

func courier_speed() -> float:
	return 56.0 if sentinel_disabled() else 28.0

func sentinel_status() -> String:
	return "DISABLED / ROAD CLEAR" if sentinel_disabled() else "FOCUS %d / 3"%enemy_focus

func guard_limit() -> float:
	return 0.30 if guard_style=="Riposte" else 10000.0

func guard_state() -> String:
	if not guard:return "DOWN"
	if guard_age<0.06:return "STARTUP"
	if guard_age>guard_limit():return "STALE"
	return "LIVE"

func guards_from(origin: Vector2) -> bool:
	return guard and live_window(guard_age,0.06,guard_limit()) and energy>=22 and locked_face.dot((origin-player).normalized())>=0.6

func reject(text: String) -> void:
	counters.rejected += 1
	note(text)
	record("rejected")

func step(delta: float, input: Dictionary) -> void:
	if mode != "play": return
	var dt := clampf(delta,0,0.05)
	elapsed += dt
	if input.get("route_signal",false):signal_route("ridge" if route.kind=="road" else "road")
	message_left = maxf(0,message_left-dt)
	step_cooldown = maxf(0,step_cooldown-dt)
	feint_cooldown = maxf(0,feint_cooldown-dt)
	strike_cooldown = maxf(0,strike_cooldown-dt)
	opening = maxf(0,opening-dt)
	var move: Vector2 = input.get("move",Vector2.ZERO)
	var aim: Vector2 = input.get("aim",Vector2.ZERO)
	if not guard and aim.length()>0.1: facing=aim.normalized()
	if not guard and aim.length()<0.1 and move.length()>0.1: facing=move.normalized()
	var wants_guard := role=="Guardian" and bool(input.get("skill",false)) and step_left<=0
	if wants_guard and not guard:
		guard=true
		guard_age=0
		locked_face=facing
	if not wants_guard:
		guard=false
		guard_age=0
	if guard:
		guard_age+=dt
		energy=maxf(0,energy-dt*12)
		if energy<=0:
			guard=false
			note("Posture spent. Release K and reposition to recover.")
	else: energy=minf(100,energy+dt*18)
	if bool(input.get("skill_pressed",false)) and role=="Duelist":
		if phase=="bolt" and not redirected and feint_cooldown<=0 and energy>=16 and player.distance_to(ENEMY)<=340:
			energy-=16
			redirected=true
			target=player
			feint_cooldown=1.4
			counters.redirects+=1
			record("redirect")
			note("You drew the bolt. Leave the locked amber line.")
		else:
			if sentinel_disabled(): reject("Sentinel disabled. The courier runs; medicine is still optional.")
			elif phase!="bolt": reject("Feint waits for an amber bolt warning.")
			elif redirected: reject("This bolt is already drawn. Leave its locked line.")
			elif player.distance_to(ENEMY)>340: reject("Outside feint range. Move inside the sentinel's ring.")
			elif energy<16: reject("Feint needs 16 resolve. Keep moving while it recovers.")
			else: reject("Feint is still recovering.")
	if bool(input.get("dodge",false)):
		if step_cooldown<=0 and energy>=25:
			energy-=25
			step_left=0.20
			step_cooldown=0.8
			step_dir=move.normalized() if move.length()>0.1 else facing
			guard=false
			counters.dodges+=1
			record("step")
		else: reject("Step needs 25 resolve and its recovery to finish.")
	if step_left>0:
		player+=step_dir*dt*(620 if role=="Duelist" else 470)*movement_scale
		step_left=maxf(0,step_left-dt)
	else: player+=move.limit_length()*dt*(250 if not guard else 85)*movement_scale
	player=player.clamp(FIELD.position+Vector2(20,20),FIELD.end-Vector2(20,20))
	if bool(input.get("strike",false)):
		if sentinel_disabled():
			reject("Sentinel disabled. Keep the courier alive to the gate.")
		elif strike_cooldown<=0 and energy>=12 and step_left<=0 and not guard:
			energy-=12
			strike_cooldown=0.45
			if player.distance_to(ENEMY)<=130 and opening>0:
				counters.counters+=1
				opening=0
				clock=-1.2 # A reachable counter buys a real interval for the courier.
				record("counter")
				enemy_focus=maxi(0,enemy_focus-1)
				if sentinel_disabled():
					phase="disabled";clock=0;redirected=false
					record("sentinel_disabled")
					note("Sentinel disabled. The courier runs along the cleared road.")
					retain_impact("sentinel_disabled","Three close counters broke the sentinel's focus.","The courier runs at twice its walking speed. Reach the gate; medicine remains optional.")
				else:note("Clean counter. Sentinel focus %d / 3; courier gains time."%enemy_focus)
			else:
				if player.distance_to(ENEMY)>130: note("Blade fell short. Close within 130px during OPEN.")
				else: note("Armor held. Wait for an OPEN response window.")
		else: reject("Finish guard / step recovery and keep 12 resolve to strike.")
	courier=route.advance(courier,dt*courier_speed(),dt)
	if not sentinel_disabled():
		clock+=dt
		if phase=="rest" and clock>=1.8:
			cycle+=1
			clock=0
			redirected=false
			if cycle%3==0:
				phase="pulse"
				pulse=player
				note("PULSE: walk or step out of the red circle. Shield cannot stop the ground.")
			else:
				phase="bolt"
				target=route.predict(courier,courier_speed()) if route.kind=="ridge" else courier+Vector2(28,0)
				note("BOLT: intercept facing the sentinel, or draw its aim with a feint.")
		elif phase in ["bolt","pulse"] and clock>=1.0:
			resolve_threat()
			phase="rest"
			clock=0
	if cargo<=0 or hp<=0:
		mode="lost"
		note("The crossing failed. Read the last impact, then try a different response.")
	elif courier.x>=FINISH:
		mode="won"
		note("The courier reached the gate. Your approach changed how the line was held.")

func resolve_threat() -> void:
	if sentinel_disabled():return
	if phase=="pulse":
		if player.distance_to(pulse)<90:
			hp-=1
			counters.player_hits+=1
			record("pulse_hit")
			note("Ground pulse hit. Guard protects a direction, not the floor.")
			retain_impact("pulse_hit","You were inside the ground pulse when it landed.","Walk or step beyond the circle. Guard cannot protect the floor.")
		else:
			opening=0.8
			record("pulse_avoided")
			retain_impact("pulse_avoided","You left the ground pulse before it landed.","An OPEN window follows. Close the distance before a blade counter.")
		return
	# Finite beam extends only as far as its locked target; nearest interception owns impact.
	var intercepted := segment_distance(player,ENEMY,target)<24 and (player-ENEMY).dot(target-ENEMY)>0 and player.distance_to(ENEMY)<target.distance_to(ENEMY)+24
	var courier_contact := segment_distance(courier,ENEMY,target)<18 and (courier-ENEMY).dot(target-ENEMY)>0 and courier.distance_to(ENEMY)<target.distance_to(ENEMY)+18
	var screen_distance:float=route.cover_distance(ENEMY,target)
	if screen_distance>=0 and (not intercepted or screen_distance<player.distance_to(ENEMY)) and (not courier_contact or screen_distance<courier.distance_to(ENEMY)):
		route.hit(ENEMY,target);record("cover_blocked")
		note("The ridge filter caught this bolt. Bodies in front and ground pulses remain exposed.")
		retain_impact("cover_blocked","The raised filter was the nearest contact on this bolt segment.","It grants no personal block or OPEN. Protect the courier outside its cover.")
		return
	if courier_contact and (not intercepted or courier.distance_to(ENEMY)<player.distance_to(ENEMY)):
		cargo-=1
		counters.courier_hits+=1
		record("courier_hit")
		note("The line reached the courier first. Draw danger away from the road.")
		retain_impact("courier_first_contact","The courier was the first body on the locked bolt line.","Move between sentinel and courier. Face the sentinel and hold K." if role=="Guardian" else "Press K inside the ring, then leave the locked line away from the courier.")
		return
	if intercepted:
		if guards_from(ENEMY):
			energy-=22
			opening=1.6 if guard_style=="Riposte" else 1.0
			counters.blocks+=1
			record("protected")
			note("Timed guard: courier safe. Release K; reach the longer OPEN window." if guard_style=="Riposte" else "Frontal block: courier safe. Release guard; counter if you can reach.")
			retain_impact("riposte_blocked" if guard_style=="Riposte" else "bolt_blocked","Your timed frontal guard intercepted the bolt." if guard_style=="Riposte" else "Your live frontal guard intercepted the bolt before the courier.","Release K; reach within 130px and press J during the 1.6s opening." if guard_style=="Riposte" else "Release guard to recover posture. Strike only when OPEN and close.")
		else:
			hp-=1
			counters.player_hits+=1
			record("bolt_hit")
			note("You intercepted the bolt without a live frontal guard.")
			if not guard:
				retain_impact("guard_not_held",("The bolt hit you without an active guard." if role=="Guardian" else "The locked bolt caught you before you left its line."),"Face the sentinel and hold K before impact." if role=="Guardian" else "After drawing a bolt, leave its locked line. A step grants no immunity.")
			elif guard_age<0.06:
				retain_impact("guard_startup","The bolt landed before your guard became live.","Begin holding K earlier. Guard needs 60ms to become live.")
			elif guard_age>guard_limit():
				retain_impact("guard_stale","Your Riposte guard expired before the bolt landed.","Release K, wait for RAISE K, then raise it again. Live age is 60-300ms.")
			elif energy<22:
				retain_impact("guard_insufficient_posture","Your guard had less than the 22 posture needed for impact.","Release K between bolts to recover. Holding guard also spends posture.")
			elif locked_face.dot((ENEMY-player).normalized())<0.6:
				retain_impact("guard_wrong_facing","Your guard faced away from the incoming bolt.","Release K, aim toward the sentinel, then hold K to lock that direction.")
			else:
				retain_impact("guard_not_live","Your guard was outside its live protection window.","Release K and raise a fresh frontal guard before the next bolt.")
	else:
		opening=1.0 if redirected else 0.5
		record("bolt_missed")
		note("The drawn bolt missed. Close the distance for an optional counter.")
		retain_impact("bolt_missed","The locked bolt hit neither you nor the courier.","An OPEN window follows. Close the distance before a blade counter.")

func snapshot() -> Dictionary:
	var result={"role":role,"guard_style":guard_style,"enemy_focus":enemy_focus,"courier_speed":courier_speed(),"mode":mode,"tick":roundi(elapsed*60),"hp":hp,"cargo":cargo,"energy":snappedf(energy,0.001),"courier_x":snappedf(courier.x,0.001),"counters":counters.duplicate(),"events":events.duplicate(true)}
	if outfit!="standard":result.outfit={"id":outfit,"health_limit":health_limit,"movement_scale":movement_scale}
	if route.kind=="ridge":result.route=route.snapshot();result.courier_y=snappedf(courier.y,0.001)
	return result
