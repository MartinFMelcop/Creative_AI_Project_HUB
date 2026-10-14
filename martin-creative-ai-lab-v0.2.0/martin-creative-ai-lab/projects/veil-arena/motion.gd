extends RefCounted
## Select atlas poses from combat clocks, never wall time or a second gameplay timer.
const RUNNER = preload("res://media/art/runner-motion.png")
const WARDEN = preload("res://media/art/warden-motion.png")
const CATALOG = preload("res://media/motion-catalog.json")

static func runner_frame(arena) -> int:
	if arena.dash_time > 0:
		return 8 + mini(3,int((0.20-arena.dash_time)/0.20*4))
	if arena.player_action == "strike":
		if not arena.action_emitted: return 4
		if arena.action_time < 0.16: return 5
		if arena.action_time < 0.24: return 6
		return 7
	if arena.player_action == "seal":
		if not arena.action_emitted: return 12
		if arena.action_time < 0.13: return 13
		if arena.action_time < 0.21: return 14
		return 15
	if arena.player_action == "parry":
		# Reuse the held blade pose with a guard arc; no new animation asset.
		return 4 if arena.action_time < arena.PARRY_END else 7
	if arena.damage_flash > 0: return 8
	return int(arena.runner_walk_clock*10)%4 if arena.runner_moving else 3

static func warden_frame(arena) -> int:
	if arena.boss_stage == "transition": return 13 if arena.stage_time < 0.55 else 14
	if arena.boss_stage == "approach":
		return int(arena.warden_walk_clock*6)%4 if arena.warden_moving else 3
	var base := 4 if arena.pattern == "sweep" else 8 if arena.pattern == "charge" else 12
	if arena.boss_stage == "windup": return base
	if arena.boss_stage == "active":
		if arena.pattern=="charge": return 9
		return base + (1 if arena.stage_time < arena.stage_duration*0.55 else 2)
	if arena.pattern=="charge" and arena.stage_time<0.14: return 10
	return base+3

static func draw_actor(canvas: Node2D,position: Vector2,actor: String,frame: int,flipped: bool,tint: Color) -> void:
	var spec: Dictionary = CATALOG.data.actors[actor]
	var item: Dictionary = spec.frames[frame]
	var region := Rect2(item.region[0],item.region[1],item.region[2],item.region[3])
	var pivot := Vector2(item.pivot[0],item.pivot[1])
	var scale: float = spec.scale
	canvas.draw_set_transform(position+Vector2(0,22),0,Vector2(-1 if flipped else 1,1))
	canvas.draw_texture_rect_region(RUNNER if actor=="runner" else WARDEN,Rect2(-pivot*scale,region.size*scale),region,tint)
	canvas.draw_set_transform(Vector2.ZERO)
