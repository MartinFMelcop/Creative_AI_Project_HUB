extends RefCounted
## Player-paced exercises use the same Combat model, costs and one-second threats.
## Setup is controlled; no command, defense or success is supplied for the player.
const Combat = preload("res://combat.gd")
var guard_style := "Steady"
var active := false
var stage := 0
var state := "ready"
var passed := false
var paused := false
var attempts := 0
var results: Array[Dictionary] = []
var game = Combat.new()

func start(role: String, style: String="Steady") -> void:
	guard_style=style
	active = true
	stage = 0
	attempts = 0
	results.clear()
	prepare(role)

func prepare(role: String) -> void:
	game = Combat.new()
	game.reset(role,guard_style)
	game.courier = Vector2(310,390)
	game.player = Vector2(550,330) if role=="Duelist" and stage==0 else Vector2(550,390)
	game.phase = "bolt" if stage==0 else ("pulse" if stage==1 else "rest")
	game.target = game.courier+Vector2(28,0)
	game.pulse = game.player
	if stage==2:
		game.player = Vector2(600,390)
		game.opening = 1.0
	game.mode = "paused"
	state = "ready"
	passed = false
	paused = false
	game.note(instruction())

func heading() -> String:
	if stage==0: return ("TIMED PROTECTION" if game.guard_style=="Riposte" else "FRONTAL PROTECTION") if game.role=="Guardian" else "DRAW AND LEAVE"
	return "LEAVE THE FLOOR" if stage==1 else "REACH THE OPENING"

func instruction() -> String:
	if stage==0:
		if game.role=="Guardian" and game.guard_style=="Riposte":return "RIGHT arrow to face. Wait for RAISE K; then hold K briefly."
		return "RIGHT arrow to face the sentinel + hold K through contact." if game.role=="Guardian" else "Press K to draw the bolt, then W to leave its locked line."
	if stage==1: return "WASD out of the marked circle. Guard cannot block the floor."
	return "D toward the sentinel, then J within the OPEN ring."+(" Release K first." if game.role=="Guardian" else "")

func confirm() -> bool:
	# True means leave rehearsal for a clean, normal crossing, never a carried buff.
	if paused: return false
	if state=="ready":
		attempts += 1
		state = "live"
		game.mode = "play"
	elif state=="review":
		if passed:
			if stage==2:
				active = false
				return true
			stage += 1
		prepare(game.role)
	return false

func repeat() -> void:
	prepare(game.role)

func toggle_pause() -> void:
	if state!="live": return
	paused = not paused
	game.mode = "paused" if paused else "play"

func finish(success: bool) -> void:
	passed = success
	state = "review"
	game.mode = "paused"
	results.append({"stage":stage,"attempt":attempts,"passed":passed,"snapshot":game.snapshot(),"impact":game.last_impact.duplicate(true)})

func step(dt: float, command: Dictionary) -> void:
	if not active or state!="live" or paused: return
	game.step(dt,command)
	if stage==2:
		if game.counters.counters>0: finish(true)
		elif game.opening<=0: finish(false)
	elif game.phase=="rest":
		if stage==0:
			finish(game.counters.blocks==1 if game.role=="Guardian" else game.counters.redirects==1 and game.hp==5 and game.cargo==3)
		else: finish(game.hp==5)

func snapshot() -> Dictionary:
	return {"active":active,"stage":stage,"state":state,"passed":passed,"paused":paused,"attempts":attempts,"results":results.duplicate(true)}
