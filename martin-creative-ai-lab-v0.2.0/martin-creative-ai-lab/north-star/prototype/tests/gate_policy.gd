extends RefCounted
const Combat=preload("res://combat.gd")
const Gate=preload("res://return_gate.gd")
const Policy=preload("res://tests/policy.gd")

static func command(room, strategy: String) -> Dictionary:
	var g=room.game
	if strategy=="quiet" and not g.sentinel_disabled():return Policy.command(g)
	var c={"move":Vector2.ZERO,"aim":(Combat.ENEMY-g.player).normalized()}
	if not g.sentinel_disabled() and g.phase=="bolt":
		if g.role=="Guardian":
			var spot:Vector2=(Combat.ENEMY+g.target)*0.5
			if room.raised[0] or g.player.distance_to(spot)<150:
				if g.player.distance_to(spot)>3:c.move=(spot-g.player).normalized()
				else:c.skill=true
				return c
		elif g.player.x>630 and g.player.distance_to(Combat.ENEMY)<=340:
			if not g.redirected:c.skill_pressed=true
			c.move=Vector2.UP;return c
	if g.phase=="pulse" and g.player.distance_to(g.pulse)<110:
		c.move=Vector2.LEFT if g.player.x>600 else Vector2.DOWN;return c
	var destination:Vector2=Gate.EXIT
	for i in Gate.CATCHES.size():
		if not room.raised[i]:destination=Gate.CATCHES[i];break
	if g.player.distance_to(destination)>20:c.move=(destination-g.player).normalized()
	elif not room.opened():c.interact=true
	return c
