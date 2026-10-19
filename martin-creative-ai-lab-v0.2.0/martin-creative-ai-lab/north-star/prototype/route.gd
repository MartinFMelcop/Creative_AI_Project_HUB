extends RefCounted
## Experimental route commitment and projectile-only screen, not body physics.
const BOARD := Vector2(350,260)
const SIGNAL_RADIUS := 38.0
const FORK := 400.0
const SCREEN_X := 650.0
const SCREEN_TOP := 215.0
const SCREEN_BOTTOM := 365.0
const RIDGE := [Vector2(400,390),Vector2(400,250),Vector2(700,250),Vector2(700,390),Vector2(1000,390)]
var kind := "road"
var locked := false
var leg := 0
var covered := 0
var flash := 0.0
var last_contact := Vector2.ZERO

func choose(next: String, courier: Vector2) -> bool:
	if locked or courier.x>=FORK or next not in ["road","ridge"]:return false
	kind=next;leg=0
	return true

func walk(position: Vector2, distance: float, index: int) -> Dictionary:
	var budget:=maxf(0,distance)
	if kind=="road":return {"position":Vector2(minf(1000,position.x+budget),position.y),"leg":index}
	while budget>0 and index<RIDGE.size():
		var gap:float=position.distance_to(RIDGE[index])
		if gap<=budget:position=RIDGE[index];budget-=gap;index+=1
		else:position=position.move_toward(RIDGE[index],budget);budget=0
	return {"position":position,"leg":index}

func predict(position: Vector2, distance: float) -> Vector2:
	return walk(position,distance,leg).position

func advance(position: Vector2, distance: float, dt: float) -> Vector2:
	flash=maxf(0,flash-dt)
	var result:=walk(position,distance,leg)
	leg=result.leg
	if result.position.x>=FORK:locked=true
	return result.position

func progress(position: Vector2) -> float:
	if kind=="road":return clampf((position.x-160.0)/840.0,0,1)
	var remaining:=0.0
	var at:=position
	for index in range(leg,RIDGE.size()):remaining+=at.distance_to(RIDGE[index]);at=RIDGE[index]
	return clampf(1.0-remaining/1120.0,0,1)

func cover_distance(origin: Vector2, target: Vector2) -> float:
	if kind!="ridge" or is_zero_approx(target.x-origin.x):return -1.0
	var t:float=(SCREEN_X-origin.x)/(target.x-origin.x)
	if t<0 or t>1:return -1.0
	var point:Vector2=origin.lerp(target,t)
	if point.y<SCREEN_TOP or point.y>SCREEN_BOTTOM:return -1.0
	return origin.distance_to(point)

func hit(origin: Vector2, target: Vector2) -> void:
	covered+=1;flash=0.35
	last_contact=origin.lerp(target,(SCREEN_X-origin.x)/(target.x-origin.x))

func snapshot() -> Dictionary:
	return {"kind":kind,"locked":locked,"leg":leg,"covered_bolts":covered}
