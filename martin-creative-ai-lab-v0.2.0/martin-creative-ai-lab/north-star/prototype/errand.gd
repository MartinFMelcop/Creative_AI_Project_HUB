extends RefCounted
## Optional session-only world action. Combat remains the owner of time and survival.
const CASE := Vector2(400, 550)
const RADIUS := 36.0
const HANDOFF_RADIUS := 54.0
const RECOVER_TIME := 0.8
const HANDOFF_TIME := 0.6
var active := false
var state := "waiting"
var progress := 0.0
var channel := false
var finished := false
var events: Array[Dictionary] = []

func reset() -> void:
	active = true
	state = "waiting"
	progress = 0.0
	channel = false
	finished = false
	events.clear()

func prepare(game, delta: float, command: Dictionary) -> Dictionary:
	var result := command.duplicate()
	# Pause preserves even partial work. Terminal interaction cannot add credit.
	if not active or finished or game.mode != "play": return result
	if state == "waiting" and game.courier.x >= 400.0:
		state = "available"
		_record(game, "dropped")
	if state not in ["available", "carried"]: return result
	var destination: Vector2 = CASE if state == "available" else game.courier
	var radius: float = RADIUS if state == "available" else HANDOFF_RADIUS
	var moving: Vector2 = command.get("move", Vector2.ZERO)
	if not bool(command.get("interact", false)) or moving != Vector2.ZERO or game.step_left>0 or game.player.distance_to(destination) > radius:
		progress = 0.0
		channel = false
		return result
	channel = true
	progress += clampf(delta, 0.0, 0.05)
	# An eligible hold commits attention; movement above always cancels and escapes.
	result.move = Vector2.ZERO
	result.skill = false
	result.skill_pressed = false
	result.dodge = false
	result.strike = false
	var required: float = RECOVER_TIME if state == "available" else HANDOFF_TIME
	if progress + 0.000001 >= required:
		state = "carried" if state == "available" else "delivered"
		_record(game, "recovered" if state == "carried" else "delivered")
		progress = 0.0
		channel = false
	return result

func settle(game) -> void:
	if not active or finished or game.mode not in ["won", "lost"]: return
	finished = true
	channel = false
	_record(game, "crossing_won" if game.mode == "won" else "crossing_lost")
	# The sealed state distinguishes a carried case from a real handoff.

func snapshot() -> Dictionary:
	return {"state":state, "progress":snappedf(progress, 0.000001),
		"channel":channel, "events":events.duplicate(true), "finished":finished}

func hint() -> String:
	if channel and not finished:
		return "Hold E to "+("recover" if state=="available" else "hand over")+". No guard / step / blade. Move or release E to cancel."
	if finished:
		if state == "delivered": return "The medicine case was handed back."
		if state == "carried": return "Case recovered, but not handed back before the crossing ended."
		if state == "waiting": return "The crossing ended before the medicine case fell."
		return "The medicine case was left behind."
	if state == "waiting": return "Optional: the courier's loose medicine case reaches the first marker."
	if state == "available": return "Optional: stand by the case and hold E for 0.8s. Move or release to cancel."
	if state == "carried": return "Return beside the moving courier and hold E for 0.6s to hand it back."
	return "Medicine handed back. Keep the courier alive to the gate."

func outcome() -> String:
	if not finished: return "Optional medicine recovery is separate from completing the escort."
	if not events.is_empty() and events[-1].action=="crossing_lost":
		return "Escort failed. No safe medicine delivery is confirmed."
	if state=="delivered": return "Courier: 'Still sealed. I'll take the medicine to the clinic.'"
	if state=="carried": return "Case recovered, not delivered. You did not hand it to the courier."
	return "Courier: 'We're across. I'll report where the medicine case fell.'"

func _record(game, action: String) -> void:
	events.append({"tick":roundi(game.elapsed * 60.0), "action":action})
