extends SceneTree
## Compare the drawn pulse boundary against actual model contacts, not a second formula.
const View=preload("../authority/view.gd")
const Model=preload("res://combat.gd")
var passed:=0
var failed:Array=[]
func check(condition:bool,label:String) -> void:
	if condition:passed+=1
	else:failed.append(label)
func _initialize() -> void:
	for distance in [0.0,78.0,85.0,89.9,90.0,95.0]:
		var model=Model.new();model.reset("Guardian");model.phase="pulse"
		model.pulse=Vector2(550,390);model.player=model.pulse+Vector2(distance,0)
		var before:int=model.hp;model.resolve_threat()
		check((distance<View.PULSE_RADIUS)==(model.hp<before),"Pulse drawing matches real damage at distance "+str(distance))
	print(JSON.stringify({"passed":passed,"failed":failed.size(),"failures":failed}))
	quit(0 if failed.is_empty() else 1)
