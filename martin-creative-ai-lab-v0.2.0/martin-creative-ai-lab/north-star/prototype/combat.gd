extends RefCounted
## A local experimental model, consumed by both the playable scene and native checks.
## Paid commitment and facing checks adapt P06's action/contact method; no P06 fiction.
const FIELD := Rect2(50, 185, 1052, 460)
const ENEMY := Vector2(790, 390)
const FINISH := 1000.0
var role := "Guardian"
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
var events: Array[Dictionary] = []
var counters := {"blocks":0,"redirects":0,"dodges":0,"counters":0,"courier_hits":0,"player_hits":0,"rejected":0}

func reset(kind: String) -> void:
	role = kind
	mode = "play"
	player = Vector2(550,390)
	courier = Vector2(160,390)
	facing = Vector2.RIGHT
	locked_face = facing
	hp = 5
	cargo = 3
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
	events.clear()
	for key in counters: counters[key]=0
	note("Keep the courier alive until the far gate. Read the first amber line.")

func note(text: String) -> void:
	message = text
	message_left = 3.0

func record(kind: String) -> void:
	events.append({"tick":roundi(elapsed*60),"kind":kind,"energy":snappedf(energy,0.001),"hp":hp,"cargo":cargo})

static func live_window(age: float, start: float, finish: float) -> bool:
	return age >= start and age <= finish

static func segment_distance(point: Vector2, a: Vector2, b: Vector2) -> float:
	var ab := b-a
	if ab.length_squared()<0.001: return point.distance_to(a)
	return point.distance_to(a+ab*clampf((point-a).dot(ab)/ab.length_squared(),0,1))

func guards_from(origin: Vector2) -> bool:
	return guard and live_window(guard_age,0.06,10000) and energy>=22 and locked_face.dot((origin-player).normalized())>=0.6

func reject(text: String) -> void:
	counters.rejected += 1
	note(text)
	record("rejected")

func step(delta: float, input: Dictionary) -> void:
	if mode != "play": return
	var dt := clampf(delta,0,0.05)
	elapsed += dt
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
			if phase!="bolt": reject("Feint waits for an amber bolt warning.")
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
		player+=step_dir*dt*(620 if role=="Duelist" else 470)
		step_left=maxf(0,step_left-dt)
	else: player+=move.limit_length()*dt*(250 if not guard else 85)
	player=player.clamp(FIELD.position+Vector2(20,20),FIELD.end-Vector2(20,20))
	if bool(input.get("strike",false)):
		if strike_cooldown<=0 and energy>=12 and step_left<=0 and not guard:
			energy-=12
			strike_cooldown=0.45
			if player.distance_to(ENEMY)<=130 and opening>0:
				counters.counters+=1
				opening=0
				clock=-1.2 # A reachable counter buys a real interval for the courier.
				record("counter")
				note("Clean counter. The courier gains breathing room.")
			else:
				if player.distance_to(ENEMY)>130: note("Blade fell short. Close within 130px during OPEN.")
				else: note("Armor held. Wait for an OPEN response window.")
		else: reject("Finish guard / step recovery and keep 12 resolve to strike.")
	courier.x=minf(FINISH,courier.x+dt*28)
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
			target=courier+Vector2(28,0)
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
	if phase=="pulse":
		if player.distance_to(pulse)<90:
			hp-=1
			counters.player_hits+=1
			record("pulse_hit")
			note("Ground pulse hit. Guard protects a direction, not the floor.")
		else:
			opening=0.8
			record("pulse_avoided")
		return
	# Finite beam extends only as far as its locked target; nearest interception owns impact.
	var intercepted := segment_distance(player,ENEMY,target)<24 and (player-ENEMY).dot(target-ENEMY)>0 and player.distance_to(ENEMY)<target.distance_to(ENEMY)+24
	var courier_contact := segment_distance(courier,ENEMY,target)<18 and (courier-ENEMY).dot(target-ENEMY)>0 and courier.distance_to(ENEMY)<target.distance_to(ENEMY)+18
	if courier_contact and (not intercepted or courier.distance_to(ENEMY)<player.distance_to(ENEMY)):
		cargo-=1
		counters.courier_hits+=1
		record("courier_hit")
		note("The line reached the courier first. Draw danger away from the road.")
		return
	if intercepted:
		if guards_from(ENEMY):
			energy-=22
			opening=1.0
			counters.blocks+=1
			record("protected")
			note("Frontal block: courier safe. Release guard; counter if you can reach.")
		else:
			hp-=1
			counters.player_hits+=1
			record("bolt_hit")
			note("You intercepted the bolt without a live frontal guard.")
	else:
		opening=1.0 if redirected else 0.5
		record("bolt_missed")
		note("The drawn bolt missed. Close the distance for an optional counter.")

func snapshot() -> Dictionary:
	return {"role":role,"mode":mode,"tick":roundi(elapsed*60),"hp":hp,"cargo":cargo,"energy":snappedf(energy,0.001),"courier_x":snappedf(courier.x,0.001),"counters":counters.duplicate(),"events":events.duplicate(true)}
