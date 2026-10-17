extends RefCounted
const Combat = preload("res://combat.gd")
static func command(g) -> Dictionary:
	var c={"move":Vector2.ZERO,"aim":(Combat.ENEMY-g.player).normalized()}
	if g.role=="Guardian":
		if g.phase=="bolt":
			var destination: Vector2=(Combat.ENEMY+g.target)*0.5
			if g.player.distance_to(destination)>3: c.move=(destination-g.player).normalized()
			else: c.skill=true
		elif g.phase=="pulse" and g.player.distance_to(g.pulse)<110: c.move=Vector2.UP
		elif g.opening>0 and g.player.distance_to(Combat.ENEMY)<=130: c.strike=true
	else:
		if g.phase=="bolt":
			if not g.redirected:
				c.skill_pressed=true
				c.dodge=true
			c.move=Vector2.UP
		elif g.phase=="pulse" and g.player.distance_to(g.pulse)<110: c.move=Vector2.LEFT
		else:
			var destination: Vector2=Combat.ENEMY+Vector2(-100,-60)
			if g.player.distance_to(destination)>4: c.move=(destination-g.player).normalized()
			if g.opening>0 and g.player.distance_to(Combat.ENEMY)<=130: c.strike=true
	return c
