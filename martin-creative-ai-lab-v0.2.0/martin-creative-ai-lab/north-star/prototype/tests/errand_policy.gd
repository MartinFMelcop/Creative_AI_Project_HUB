extends RefCounted
## A repeatable feasible route, not an optimal policy or simulated participant.
const Policy = preload("res://tests/policy.gd")
const Errand = preload("res://errand.gd")

static func command(scene) -> Dictionary:
	var g=scene.game
	var e=scene.errand
	if e.state in ["available","carried"]:
		if e.channel and e.state=="carried" and g.player.distance_to(g.courier)<=Errand.HANDOFF_RADIUS:
			return {"interact":true}
		var goal: Vector2=Errand.CASE if e.state=="available" else g.courier+Vector2(8,0)
		if g.player.distance_to(goal)<=25: return {"interact":true}
		return {"move":(goal-g.player).normalized()}
	return Policy.command(g)
